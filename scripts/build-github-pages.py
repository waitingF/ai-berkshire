#!/usr/bin/env python3
"""Build a static GitHub Pages site from reports/*.md files."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from xml.etree.ElementTree import Element

import markdown
from markdown.extensions import Extension
from markdown.extensions.toc import slugify_unicode
from markdown.treeprocessors import Treeprocessor


MARKDOWN_EXTENSIONS = [
    "extra",
    "toc",
    "footnotes",
    "sane_lists",
]

STATIC_SUFFIX_ALLOWLIST = {
    ".css",
    ".gif",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".pdf",
    ".png",
    ".svg",
    ".webp",
}

REPORTS_BANNER_START = "<!-- REPORTS-BANNER:START 由 tools/reports_index.py 自动更新，勿手改 -->"
REPORTS_BANNER_END = "<!-- REPORTS-BANNER:END -->"

# Living docs pinned on the homepage and site nav.
HOME_PINNED_REPORTS = (
    {
        "filename": "重点标的看板.md",
        "title": "重点标的看板",
        "nav_label": "看板",
        "eyebrow": "Thesis 总览",
        "description": "thesis / 指定标的一页总览：阶段、健康度、本周关注与下次动作。",
    },
    {
        "filename": "标的跟踪表.md",
        "title": "标的跟踪表",
        "nav_label": "标的跟踪",
        "eyebrow": "标的跟踪",
        "description": "研究报告里的买卖/观望建议：条件是否触发、事后对不对。",
    },
    {
        "filename": "daily-monitor/daily-monitor-latest.md",
        "title": "每日监控",
        "nav_label": "每日监控",
        "eyebrow": "自动监控",
        "description": "已登记价格区间与腾讯行情快照的工作日监控，支持脚本主动刷新。",
    },
    {
        "filename": "portfolio-latest.md",
        "title": "组合最新报告",
        "nav_label": "组合",
        "eyebrow": "组合检视",
        "description": "组合持仓与检视结论的持续更新入口。",
    },
)


def title_from_markdown(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or fallback
    return fallback


def encoded_href(path: Path) -> str:
    return quote(path.as_posix(), safe="/-._~")


def rewrite_markdown_href(href: str) -> str:
    """Rewrite relative *.md links to *.html; leave absolute URLs and anchors alone."""
    scheme, netloc, path, query, fragment = urlsplit(href)
    if scheme or netloc or not path:
        return href
    if path.lower().endswith(".md"):
        path = f"{path[:-3]}.html"
    return urlunsplit((scheme, netloc, path, query, fragment))


class MarkdownLinkRewriter(Treeprocessor):
    def run(self, root):
        for element in root.iter("a"):
            href = element.get("href")
            if href:
                rewritten = rewrite_markdown_href(href)
                if rewritten != href:
                    element.set("href", rewritten)
        return root


class MarkdownLinkRewriteExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(MarkdownLinkRewriter(md), "md_link_rewrite", 0)


def monitor_stock_code(quote_code: str) -> str:
    """Use familiar stock codes while preserving leading zeros and share classes."""
    prefix = quote_code[:2].lower()
    if prefix not in {"sh", "sz", "bj", "hk", "us", "kr", "jp"}:
        return quote_code.upper()
    code = quote_code[2:].upper()
    suffix = {"sh": ".SH", "sz": ".SZ", "bj": ".BJ", "hk": ".HK"}.get(prefix, "")
    return code + suffix


def load_monitor_labels(reports_dir: Path) -> dict[tuple[str, str], tuple[str, str]]:
    """Keep presentation names separate from human-authored price monitoring rules."""
    data_dir = reports_dir.parent / "data"
    triggers = data_dir / "triggers.json"
    if not triggers.exists():
        return {}
    names_path = data_dir / "monitor-display-names.json"
    names = json.loads(names_path.read_text(encoding="utf-8")) if names_path.exists() else {}
    labels = {}
    for target in json.loads(triggers.read_text(encoding="utf-8")).get("targets", []):
        target_id = target["id"]
        full_name = target.get("name") or target_id
        short_names = names.get(target_id, {})
        for market, quote_code in (target.get("codes") or {}).items():
            language = "zh" if market in {"A", "H"} else "en"
            short_name = short_names.get(language) or full_name.split("（", 1)[0].split("(", 1)[0].strip()
            label = f"{short_name} · {monitor_stock_code(quote_code)}"
            aliases = " ".join([target_id, full_name, *short_names.values(), quote_code])
            labels[(full_name, market)] = (label, aliases)
    return labels


class MonitorTableEnhancer(Treeprocessor):
    def __init__(self, md, labels):
        super().__init__(md)
        self.labels = labels

    def run(self, root):
        for table in root.iter("table"):
            header = table.find("thead/tr")
            if header is None:
                continue
            columns = ["".join(cell.itertext()).strip() for cell in header]
            if not {"优先级", "标的", "监控区间"}.issubset(columns):
                continue
            table.set("data-monitor-table", "")
            if "市场" in columns:
                for row in table.findall("tbody/tr"):
                    cells = list(row)
                    if len(cells) != len(columns):
                        continue
                    cell = cells[columns.index("标的")]
                    name = "".join(cell.itertext()).strip()
                    market = "".join(cells[columns.index("市场")].itertext()).strip()
                    display = self.labels.get((name, market))
                    if display is None:
                        continue
                    label, aliases = display
                    link = cell.find("a")
                    href = link.get("href") if link is not None else None
                    cell.clear()
                    if href:
                        link = Element("a", {"href": href})
                        link.text = label
                        cell.append(link)
                    else:
                        cell.text = label
                    row.set("data-monitor-aliases", aliases)
            if "序号" in columns:
                continue
            number_header = Element("th", {"scope": "col"})
            number_header.text = "序号"
            header.insert(0, number_header)
            for number, row in enumerate(table.findall("tbody/tr"), start=1):
                cell = Element("td", {"class": "monitor-row-number"})
                cell.text = str(number)
                row.insert(0, cell)
        return root


class MonitorTableExtension(Extension):
    def __init__(self, labels):
        super().__init__()
        self.labels = labels

    def extendMarkdown(self, md):
        md.treeprocessors.register(MonitorTableEnhancer(md, self.labels), "monitor_table", 1)


def render_markdown(markdown_text: str, *, monitor_tables: bool = False, monitor_labels=None) -> str:
    extensions = [*MARKDOWN_EXTENSIONS, MarkdownLinkRewriteExtension()]
    if monitor_tables:
        extensions.append(MonitorTableExtension(monitor_labels or {}))
    renderer = markdown.Markdown(
        extensions=extensions,
        extension_configs={"toc": {"slugify": slugify_unicode}},
        output_format="html5",
    )
    return renderer.convert(markdown_text)


def read_repository_reports_banner(reports_dir: Path) -> str:
    """Read the report-index banner maintained in the repository README."""
    readme_path = reports_dir.parent / "README.md"
    try:
        readme = readme_path.read_text(encoding="utf-8")
    except OSError:
        return ""

    start = readme.find(REPORTS_BANNER_START)
    end = readme.find(REPORTS_BANNER_END, start + len(REPORTS_BANNER_START))
    if start < 0 or end < 0:
        return ""
    return readme[start + len(REPORTS_BANNER_START):end].strip()


def render_repository_reports_banner(reports_dir: Path) -> str:
    markdown_text = read_repository_reports_banner(reports_dir)
    if not markdown_text:
        return ""
    return f"""    <section class=\"report-index-banner\" aria-labelledby=\"reports-banner-title\">
      <h2 id=\"reports-banner-title\">研究报告索引</h2>
{render_markdown(markdown_text)}
    </section>
"""


def render_site_nav(
    root_prefix: str,
    available_pinned: set[str] | None = None,
    current_nav: str | None = None,
) -> str:
    links: list[tuple[str, Path, str]] = []
    for pinned in HOME_PINNED_REPORTS:
        if available_pinned is not None and pinned["filename"] not in available_pinned:
            continue
        links.append(
            (
                pinned["nav_label"],
                Path("reports") / Path(pinned["filename"]).with_suffix(".html"),
                pinned["filename"],
            )
        )
    links.append(("研究库", Path("index.html"), "index"))
    items = []
    for label, href, nav_key in links:
        current_attr = ' aria-current="page"' if current_nav == nav_key else ""
        items.append(
            f'<a href="{root_prefix}{encoded_href(href)}"{current_attr}>{html.escape(label)}</a>'
        )
    return "\n        ".join(items)


def available_pinned_filenames(report_links: list[tuple[Path, Path]]) -> set[str]:
    pinned_names = {item["filename"] for item in HOME_PINNED_REPORTS}
    return {
        source_relative.as_posix()
        for source_relative, _ in report_links
        if source_relative.as_posix() in pinned_names
    }


def render_home_pinned_section(report_links: list[tuple[Path, Path]]) -> str:
    href_by_name = {
        source_relative.as_posix(): html_relative
        for source_relative, html_relative in report_links
    }
    cards = []
    for pinned in HOME_PINNED_REPORTS:
        href = href_by_name.get(pinned["filename"])
        if href is None:
            continue
        cards.append(
            "        <li>"
            f'<a class="pinned-card" href="{encoded_href(href)}">'
            f'<span class="pinned-eyebrow">{html.escape(pinned["eyebrow"])}</span>'
            f'<span class="pinned-title">{html.escape(pinned["title"])}</span>'
            f'<span class="pinned-desc">{html.escape(pinned["description"])}</span>'
            f"</a></li>"
        )
    if not cards:
        return ""
    return f"""    <section class="pinned-home" aria-labelledby="pinned-title">
      <div class="pinned-home-header">
        <h2 id="pinned-title">常用入口</h2>
        <p>跨公司汇总活文档，优先从这里跳转。</p>
      </div>
      <ul class="pinned-grid" role="list">
{chr(10).join(cards)}
      </ul>
    </section>
"""


def render_page(
    title: str,
    body_html: str,
    root_prefix: str,
    page_class: str = "",
    available_pinned: set[str] | None = None,
    current_nav: str | None = None,
) -> str:
    escaped_title = html.escape(title)
    content_class = "content"
    if page_class:
        content_class = f"{content_class} {page_class}"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="AI Berkshire 投资研究报告静态索引。">
  <title>{escaped_title}</title>
  <link rel="icon" href="{root_prefix}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{root_prefix}assets/site.css">
  <script defer src="{root_prefix}assets/site.js"></script>
</head>
<body>
  <a class="skip-link" href="#main-content">跳到正文</a>
  <header class="site-header">
    <div class="site-header-inner">
      <a class="site-title" href="{root_prefix}index.html" aria-label="AI Berkshire Reports 首页">
        <span class="site-mark" aria-hidden="true">AI</span>
        <span class="site-title-text">AI Berkshire Reports</span>
      </a>
      <nav class="site-nav" aria-label="站点导航">
        {render_site_nav(root_prefix, available_pinned, current_nav)}
      </nav>
    </div>
  </header>
  <main id="main-content" class="{content_class}">
{body_html}
  </main>
  <footer class="site-footer">
    <p>仅用于学习和研究，不构成投资建议。</p>
  </footer>
  <button type="button" class="back-to-top" data-back-to-top aria-label="返回顶部" title="返回顶部" hidden>
    <span aria-hidden="true">↑</span>
  </button>
</body>
</html>
"""


def render_report(
    markdown_path: Path,
    output_path: Path,
    reports_dir: Path,
    output_dir: Path,
    available_pinned: set[str] | None = None,
    monitor_labels=None,
) -> None:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    title = title_from_markdown(markdown_text, markdown_path.stem)
    source_relative = markdown_path.relative_to(reports_dir)
    root_prefix = "../" * (len(output_path.relative_to(output_dir).parents) - 1)
    breadcrumb_html = render_breadcrumb(source_relative.parent, root_prefix, title)
    content_html = render_markdown(
        markdown_text,
        monitor_tables=source_relative.parent == Path("daily-monitor"),
        monitor_labels=monitor_labels if source_relative.as_posix() == "daily-monitor/daily-monitor-latest.md" else None,
    )
    body_html = f"""    {breadcrumb_html}
    <article class="report-article">
{content_html}
    </article>"""
    current_nav = source_relative.as_posix()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_page(
            title,
            body_html,
            root_prefix,
            "report-page",
            available_pinned,
            current_nav,
        ),
        encoding="utf-8",
    )


def copy_static_assets(reports_dir: Path, output_reports_dir: Path) -> None:
    for source_path in sorted(reports_dir.rglob("*")):
        if not source_path.is_file():
            continue
        if source_path.suffix.lower() == ".md":
            continue
        if source_path.suffix.lower() not in STATIC_SUFFIX_ALLOWLIST:
            continue
        relative_path = source_path.relative_to(reports_dir)
        target_path = output_reports_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def render_navigation_list(items: list[tuple[str, Path, str]]) -> str:
    if not items:
        return '        <li class="empty">暂无内容</li>'
    rows = []
    for label, href, item_type in items:
        rows.append(
            f'        <li class="{item_type}" data-search-item>'
            f'<a href="{encoded_href(href)}">'
            f'<span class="item-label">{html.escape(label)}</span>'
            f"</a></li>"
        )
    return "\n".join(rows)


def output_root_prefix(output_path: Path, output_dir: Path) -> str:
    return "../" * (len(output_path.relative_to(output_dir).parents) - 1)


def render_breadcrumb(source_relative_dir: Path, root_prefix: str, current_label: str | None = None) -> str:
    if source_relative_dir == Path(".") and current_label is None:
        return ""

    parts = [f'<a href="{root_prefix}index.html">研究库</a>']
    accumulated = Path()
    for directory_name in source_relative_dir.parts:
        accumulated = accumulated / directory_name
        href = f'{root_prefix}{encoded_href(Path("reports") / accumulated / "index.html")}'
        parts.append(f'<a href="{href}">{html.escape(directory_name)}</a>')

    if current_label is not None:
        parts.append(f'<span aria-current="page">{html.escape(current_label)}</span>')
    elif source_relative_dir != Path("."):
        current = parts.pop()
        label = html.escape(source_relative_dir.parts[-1])
        parts.append(current.replace(f">{label}</a>", f' aria-current="page">{label}</a>'))

    return f'<nav class="breadcrumb" aria-label="面包屑">{"<span>/</span>".join(parts)}</nav>'


def render_directory_index(
    source_relative_dir: Path,
    output_path: Path,
    output_dir: Path,
    report_links: list[tuple[Path, Path]],
    total_reports: int,
    home_banner_html: str,
) -> None:
    directories = set()
    reports = []
    for source_relative, html_relative in report_links:
        try:
            relative_to_current = source_relative.relative_to(source_relative_dir)
        except ValueError:
            continue

        if len(relative_to_current.parts) == 1:
            if source_relative_dir == Path("."):
                report_href = html_relative
            else:
                report_href = relative_to_current.with_suffix(".html")
            reports.append((relative_to_current.name, report_href))
        elif relative_to_current.parts:
            child_dir = relative_to_current.parts[0]
            directories.add(child_dir)

    directory_items = []
    for directory_name in sorted(directories):
        if source_relative_dir == Path("."):
            directory_href = Path("reports") / directory_name / "index.html"
        else:
            directory_href = Path(directory_name) / "index.html"
        directory_items.append((f"{directory_name}/", directory_href, "directory"))
    report_items = [
        (report_name, report_href, "report")
        for report_name, report_href in sorted(reports, key=lambda item: item[0])
    ]

    if source_relative_dir == Path("."):
        title = "AI Berkshire Reports"
        subtitle = "从 <code>reports/</code> 自动生成的投资研究索引。"
        eyebrow = "研究库"
    else:
        title = source_relative_dir.as_posix()
        subtitle = "当前目录下的研究报告与子目录。"
        eyebrow = "目录"
    breadcrumb_html = render_breadcrumb(source_relative_dir, output_root_prefix(output_path, output_dir))
    visible_items = len(directory_items) + len(report_items)
    pinned_section = (
        render_home_pinned_section(report_links) if source_relative_dir == Path(".") else ""
    )
    report_index_banner = home_banner_html if source_relative_dir == Path(".") else ""

    body_html = f"""    <section class="index-hero">
      {breadcrumb_html}
      <p class="hero-eyebrow">{eyebrow}</p>
      <h1>{html.escape(title)}</h1>
      <p>{subtitle}</p>
      <dl class="hero-stats" aria-label="索引统计">
        <div>
          <dt>全部报告</dt>
          <dd>{total_reports}</dd>
        </div>
        <div>
          <dt>当前目录报告</dt>
          <dd>{len(report_items)}</dd>
        </div>
        <div>
          <dt>子目录</dt>
          <dd>{len(directory_items)}</dd>
        </div>
      </dl>
    </section>
{report_index_banner}{pinned_section}    <section class="index-tools" aria-labelledby="filter-title">
      <div>
        <h2 id="filter-title">筛选当前页</h2>
        <p id="filter-status" class="filter-status" data-filter-status aria-live="polite">共 {visible_items} 个条目</p>
      </div>
      <div class="filter-field">
        <label class="filter-label" for="report-filter">关键词</label>
        <input id="report-filter" data-report-filter type="search" autocomplete="off" aria-describedby="filter-status">
      </div>
    </section>
    <p class="filter-empty" data-filter-empty hidden>没有匹配的条目。</p>
    <div class="index-sections">
      <section class="report-list" aria-labelledby="folders-title">
        <h2 id="folders-title">目录 <span>{len(directory_items)}</span></h2>
        <ul data-filter-list>
{render_navigation_list(directory_items)}
        </ul>
      </section>
      <section class="report-list" aria-labelledby="reports-title">
        <h2 id="reports-title">报告 <span>{len(report_items)}</span></h2>
        <ul data-filter-list>
{render_navigation_list(report_items)}
        </ul>
      </section>
    </div>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    current_nav = "index" if source_relative_dir == Path(".") else None
    output_path.write_text(
        render_page(
            title,
            body_html,
            output_root_prefix(output_path, output_dir),
            "index-page",
            available_pinned_filenames(report_links),
            current_nav,
        ),
        encoding="utf-8",
    )


def render_indexes(
    report_links: list[tuple[Path, Path]],
    output_dir: Path,
    home_banner_html: str,
) -> None:
    directory_paths = {Path(".")}
    for source_relative, _ in report_links:
        parent = source_relative.parent
        while parent != Path("."):
            directory_paths.add(parent)
            parent = parent.parent

    for source_relative_dir in sorted(directory_paths):
        if source_relative_dir == Path("."):
            output_path = output_dir / "index.html"
        else:
            output_path = output_dir / "reports" / source_relative_dir / "index.html"
        render_directory_index(
            source_relative_dir,
            output_path,
            output_dir,
            report_links,
            len(report_links),
            home_banner_html,
        )


def write_styles(output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "site.css").write_text(
        """* {
  box-sizing: border-box;
}

:root {
  color-scheme: light;
  --bg: #f6f7f3;
  --surface: #fffefa;
  --surface-subtle: #eef2ea;
  --text: #1d221d;
  --muted: #5d665f;
  --line: #d9dfd4;
  --line-strong: #b9c2b4;
  --accent: #315f52;
  --accent-strong: #21483e;
  --accent-warm: #815c2d;
  --accent-soft: rgba(49, 95, 82, 0.08);
  --code-bg: #e9ede4;
  --shadow: 0 16px 36px rgba(31, 42, 31, 0.08);
  --page-gutter: clamp(16px, 3vw, 48px);
}

html {
  scroll-padding-top: 76px;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 17px;
  line-height: 1.74;
  text-rendering: optimizeLegibility;
}

a {
  color: var(--accent);
  text-decoration-thickness: 0.08em;
  text-underline-offset: 0.18em;
}

a:hover {
  color: var(--accent-strong);
}

a:focus-visible,
button:focus-visible,
input:focus-visible {
  outline: 3px solid rgba(49, 95, 82, 0.32);
  outline-offset: 3px;
}

.skip-link {
  position: fixed;
  left: 16px;
  top: 12px;
  z-index: 100;
  transform: translateY(-150%);
  border-radius: 6px;
  background: var(--text);
  padding: 8px 12px;
  color: var(--surface);
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
}

.skip-link:focus {
  transform: translateY(0);
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid var(--line);
  background: rgba(246, 247, 243, 0.94);
  backdrop-filter: blur(12px);
}

.site-header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin: 0 auto;
  padding: 12px var(--page-gutter);
  gap: 12px 16px;
}

.site-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  color: var(--text);
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
}

.site-title-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.site-mark {
  display: inline-grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: var(--surface);
  color: var(--accent-strong);
  font-size: 12px;
  letter-spacing: 0;
}

.site-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px 12px;
  font-size: 14px;
  font-weight: 650;
}

.site-nav a {
  color: var(--muted);
  text-decoration: none;
  padding: 6px 2px;
}

.site-nav a:hover {
  color: var(--accent-strong);
}

.site-nav a[aria-current="page"] {
  color: var(--text);
}

.content {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 40px var(--page-gutter) 76px;
}

.index-hero {
  margin-bottom: 24px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 28px;
}

.hero-eyebrow {
  margin: 0 0 12px;
  color: var(--accent-warm);
  font-size: 13px;
  font-weight: 760;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.index-hero h1,
.content h1 {
  margin: 0 0 14px;
  font-size: 40px;
  line-height: 1.16;
  letter-spacing: 0;
}

.index-hero > p {
  max-width: 72ch;
  margin: 0;
  color: var(--muted);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  margin: 28px 0 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--line);
}

.hero-stats div {
  background: var(--surface);
  padding: 16px;
}

.hero-stats dt {
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.hero-stats dd {
  margin: 4px 0 0;
  color: var(--text);
  font-size: 28px;
  font-weight: 780;
  line-height: 1.15;
}

.pinned-home {
  margin: 28px 0;
}

.report-index-banner {
  margin: 28px 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  padding: 18px;
  box-shadow: var(--shadow);
}

.report-index-banner h2 {
  margin: 0 0 8px;
  border: 0;
  padding: 0;
  font-size: 18px;
}

.report-index-banner blockquote {
  margin: 0;
  border-left: 3px solid var(--accent);
  padding-left: 12px;
  color: var(--muted);
}

.report-index-banner blockquote p {
  margin: 0;
}

.pinned-home-header {
  margin-bottom: 14px;
}

.pinned-home-header h2 {
  margin: 0 0 4px;
  border: 0;
  padding: 0;
  font-size: 18px;
}

.pinned-home-header p {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.pinned-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.pinned-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  padding: 16px;
  color: var(--text);
  text-decoration: none;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.pinned-card:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--text);
}

.pinned-card:focus-visible {
  outline: 3px solid rgba(49, 95, 82, 0.32);
  outline-offset: 3px;
}

.pinned-eyebrow {
  color: var(--accent-warm);
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0.04em;
}

.pinned-title {
  font-size: 18px;
  font-weight: 760;
  line-height: 1.3;
}

.pinned-desc {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.5;
}

.content h2 {
  margin-top: 44px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 10px;
  font-size: 24px;
  line-height: 1.3;
}

.content h3 {
  margin-top: 32px;
  font-size: 21px;
}

.content p,
.content ul,
.content ol,
.content table,
.content blockquote,
.content pre {
  margin-top: 0;
  margin-bottom: 18px;
}

.index-tools {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 420px);
  align-items: end;
  gap: 16px;
  margin: 28px 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  padding: 18px;
  box-shadow: var(--shadow);
}

.index-tools h2 {
  margin: 0 0 4px;
  border: 0;
  padding: 0;
  font-size: 18px;
}

.filter-status {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
}

.filter-field {
  min-width: 0;
}

.filter-label {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 720;
}

[data-report-filter],
[data-monitor-search] {
  width: 100%;
  min-height: 44px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: var(--surface);
  padding: 10px 12px;
  color: var(--text);
  font: inherit;
}

.monitor-filter {
  margin-bottom: 14px;
}

.monitor-filter .filter-status {
  margin-top: 8px;
}

.monitor-row-number {
  color: var(--muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

[data-monitor-table] th,
[data-monitor-table] td {
  white-space: nowrap;
}

.filter-empty {
  border: 1px dashed var(--line-strong);
  border-radius: 8px;
  background: var(--surface);
  padding: 18px;
  color: var(--muted);
}

.action-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  margin: 0 0 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  padding: 12px 14px;
}

.action-filter-label {
  color: var(--muted);
  font-size: 13px;
  font-weight: 720;
}

.action-filter-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-filter-button {
  min-height: 36px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: var(--surface);
  padding: 6px 12px;
  color: var(--text);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 650;
}

.action-filter-button:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.action-filter-button[aria-pressed="true"] {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--surface);
}

.action-filter-status {
  margin-left: auto;
  color: var(--muted);
  font-size: 13px;
}

.action-filter-empty {
  margin: 0 0 14px;
  border: 1px dashed var(--line-strong);
  border-radius: 8px;
  background: var(--surface);
  padding: 14px 16px;
  color: var(--muted);
  font-size: 14px;
}

.index-sections {
  display: grid;
  grid-template-columns: minmax(280px, 0.8fr) minmax(0, 1.2fr);
  gap: 28px;
  align-items: start;
}

.report-list {
  min-width: 0;
}

.report-list h2 {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}

.report-list h2 span {
  color: var(--muted);
  font-size: 14px;
  font-weight: 650;
}

.report-list ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.report-list li {
  border-bottom: 1px solid var(--line);
}

.report-list a {
  display: block;
  padding: 14px 0;
  color: var(--text);
  text-decoration: none;
  overflow-wrap: anywhere;
}

.report-list a:hover .item-label {
  color: var(--accent-strong);
  text-decoration: underline;
  text-decoration-thickness: 0.08em;
  text-underline-offset: 0.2em;
}

.item-label {
  min-width: 0;
}

.report-list li.directory .item-label {
  font-weight: 720;
}

.report-list li.empty {
  padding: 12px 0;
  color: var(--muted);
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
  color: var(--muted);
  font-size: 14px;
}

.breadcrumb a {
  color: var(--muted);
  text-decoration: none;
}

.breadcrumb a:hover {
  color: var(--accent-strong);
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.breadcrumb [aria-current="page"] {
  color: var(--text);
  font-weight: 650;
}

.report-page {
  max-width: none;
}

.report-article {
  border-top: 1px solid var(--line);
  padding-top: 28px;
}

.report-article > h1:first-child {
  margin-top: 0;
}

.report-article > p,
.report-article > ul,
.report-article > ol,
.report-article > blockquote {
  max-width: 80ch;
}

.content hr {
  border: 0;
  border-top: 1px solid var(--line);
  margin: 32px 0;
}

code {
  border-radius: 4px;
  background: var(--code-bg);
  padding: 0.12em 0.32em;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.92em;
}

pre {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #1f2724;
  padding: 16px;
  color: #f5f5f5;
}

pre code {
  background: transparent;
  padding: 0;
  color: inherit;
}

.mermaid-figure {
  min-width: 0;
  margin: 24px 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
}

.mermaid-viewport {
  overflow-x: auto;
  padding: 20px;
}

.mermaid-viewport > svg {
  display: block;
  height: auto;
  margin: 0 auto;
}

.mermaid-viewport p {
  margin: 0;
  max-width: none;
}

.mermaid-figure figcaption,
.mermaid-figure details {
  padding: 8px 16px;
  color: var(--muted);
  font-size: 14px;
}

.mermaid-figure summary {
  cursor: pointer;
}

.mermaid-figure pre {
  margin: 12px 0;
}

.mermaid-fallback {
  color: var(--muted);
  font-size: 14px;
}

blockquote {
  margin-left: 0;
  border-left: 4px solid var(--accent);
  background: rgba(49, 95, 82, 0.08);
  padding: 14px 18px;
  color: #2c332d;
}

table {
  display: block;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border-collapse: collapse;
}

th,
td {
  border: 1px solid var(--line);
  padding: 9px 11px;
  vertical-align: top;
}

th {
  background: var(--surface-subtle);
  font-weight: 750;
}

img {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
}

.site-footer {
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 14px;
}

.site-footer p {
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 18px var(--page-gutter) 28px;
}

.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 20;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--surface);
  color: var(--accent-strong);
  box-shadow: var(--shadow);
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.back-to-top:hover {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--surface);
}

.back-to-top:active {
  transform: translateY(1px);
}

@media (max-width: 900px) {
  .index-tools,
  .index-sections {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  body {
    font-size: 16px;
  }

  .site-header-inner {
    flex-wrap: wrap;
    align-items: flex-start;
  }

  .site-title {
    flex: 1 1 auto;
    max-width: 100%;
  }

  .site-nav {
    flex: 1 1 100%;
    justify-content: flex-start;
  }

  .content {
    padding-top: 26px;
    padding-bottom: 64px;
  }

  .index-hero h1,
  .content h1 {
    font-size: clamp(26px, 8vw, 30px);
  }

  .hero-stats {
    grid-template-columns: 1fr;
    margin-top: 22px;
  }

  .hero-stats dd {
    font-size: 24px;
  }

  .pinned-card {
    padding: 14px;
  }

  .action-filter-status {
    margin-left: 0;
    width: 100%;
  }

  .back-to-top {
    right: 16px;
    bottom: 16px;
  }
}

@media (max-width: 380px) {
  .site-title-text {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .pinned-card,
  .back-to-top {
    transition: none;
  }
}
""",
        encoding="utf-8",
    )
    (assets_dir / "favicon.svg").write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#fffefa"/>
  <path d="M14 48 28 16h8l14 32h-8l-3-8H25l-3 8h-8Zm14-15h8l-4-11-4 11Z" fill="#315f52"/>
</svg>
""",
        encoding="utf-8",
    )


def write_scripts(output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "site.js").write_text(
        """(() => {
  const initMermaid = async () => {
    const blocks = Array.from(document.querySelectorAll("pre > code.language-mermaid"));
    if (!blocks.length) {
      return;
    }

    const showFallback = (pre, message) => {
      const note = document.createElement("p");
      note.className = "mermaid-fallback";
      note.setAttribute("role", "status");
      note.textContent = message;
      pre.before(note);
    };

    let mermaid;
    try {
      // Pinned version; render API: https://mermaid.js.org/config/usage.html#api-usage
      ({ default: mermaid } = await import("https://cdn.jsdelivr.net/npm/mermaid@12.3.0/dist/mermaid.esm.min.mjs"));
      await document.fonts.ready;
      const colors = getComputedStyle(document.documentElement);
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "strict",
        suppressErrorRendering: true,
        theme: "base",
        fontFamily: getComputedStyle(document.body).fontFamily,
        themeVariables: {
          fontSize: "16px",
          primaryColor: colors.getPropertyValue("--surface-subtle").trim(),
          primaryTextColor: colors.getPropertyValue("--text").trim(),
          primaryBorderColor: colors.getPropertyValue("--accent").trim(),
          lineColor: colors.getPropertyValue("--muted").trim(),
        },
      });
    } catch {
      blocks.forEach((code) => showFallback(code.parentElement, "图表加载失败，已保留源码。"));
      return;
    }

    for (const [index, code] of blocks.entries()) {
      const pre = code.parentElement;
      const figure = document.createElement("figure");
      figure.className = "mermaid-figure";
      const viewport = document.createElement("div");
      viewport.className = "mermaid-viewport";
      viewport.tabIndex = 0;
      viewport.setAttribute("role", "region");
      viewport.setAttribute("aria-label", "报告图表，可横向滚动");
      figure.appendChild(viewport);
      pre.before(figure);

      try {
        const { svg } = await mermaid.render(`report-diagram-${index + 1}`, code.textContent || "", viewport);
        viewport.innerHTML = svg;
        const diagram = viewport.querySelector("svg");
        const width = diagram.viewBox.baseVal.width;
        if (width > 0) {
          diagram.style.width = `${width}px`;
          diagram.style.maxWidth = "none";
        }
        const caption = document.createElement("figcaption");
        caption.textContent = "图表超出宽度时可横向滚动。";
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        summary.textContent = "查看图表源码";
        details.appendChild(summary);
        details.appendChild(pre);
        figure.append(caption, details);
      } catch {
        figure.remove();
        showFallback(pre, "此图表暂时无法渲染，已保留源码。");
      }
    }
  };

  const initReportFilter = () => {
    const input = document.querySelector("[data-report-filter]");
    if (!input) {
      return;
    }

    const items = Array.from(document.querySelectorAll("[data-search-item]"));
    const status = document.querySelector("[data-filter-status]");
    const empty = document.querySelector("[data-filter-empty]");
    const total = items.length;

    const normalize = (value) => value.trim().toLocaleLowerCase("zh-CN");

    const update = () => {
      const query = normalize(input.value);
      let visible = 0;

      for (const item of items) {
        const text = normalize(item.textContent || "");
        const matched = query === "" || text.includes(query);
        item.hidden = !matched;
        if (matched) {
          visible += 1;
        }
      }

      if (status) {
        status.textContent = query === "" ? `共 ${total} 个条目` : `显示 ${visible} / ${total} 个结果`;
      }

      if (empty) {
        empty.hidden = visible !== 0;
      }
    };

    input.addEventListener("input", update);
    update();
  };

  const ACTION_ORDER = ["买入", "分批", "观望", "回避"];

  const initMonitorTableSearch = () => {
    document.querySelectorAll("[data-monitor-table]").forEach((table, index) => {
      const normalize = (value) => value.trim().toLocaleLowerCase("zh-CN");
      const rows = Array.from(table.querySelectorAll("tbody tr"), (row) => ({
        row,
        text: normalize([
          ...Array.from(row.cells, (cell) => cell.textContent || ""),
          row.dataset.monitorAliases || "",
        ].join(" ")),
      }));
      if (!rows.length) {
        return;
      }

      const bar = document.createElement("div");
      bar.className = "monitor-filter";
      const inputId = `monitor-search-${index + 1}`;
      const statusId = `${inputId}-status`;
      bar.innerHTML = `
        <label class="filter-label" for="${inputId}">搜索价格监控</label>
        <input id="${inputId}" data-monitor-search type="search" autocomplete="off"
          placeholder="输入简称、股票代码、市场或优先级，空格分隔多个条件" aria-describedby="${statusId}">
        <p id="${statusId}" class="filter-status" role="status" aria-live="polite"></p>`;
      const input = bar.querySelector("input");
      const status = bar.querySelector("[role='status']");
      const empty = document.createElement("p");
      empty.className = "filter-empty";
      empty.hidden = true;
      empty.textContent = "没有匹配的监控记录，请尝试其他关键词。";
      table.before(bar, empty);

      const update = () => {
        const query = normalize(input.value);
        const terms = query.split(/\\s+/).filter(Boolean);
        let visible = 0;
        for (const { row, text } of rows) {
          const matched = terms.every((term) => text.includes(term));
          row.hidden = !matched;
          if (matched) {
            visible += 1;
          }
        }
        status.textContent = query === "" ? `共 ${rows.length} 条` : `显示 ${visible} / ${rows.length} 条`;
        empty.hidden = visible !== 0;
      };
      input.addEventListener("input", update);
      update();
    });
  };

  const initActionColumnFilter = () => {
    const tables = Array.from(document.querySelectorAll(".report-article table"));

    for (const table of tables) {
      const headerCells = Array.from(table.querySelectorAll("thead th"));
      if (!headerCells.length) {
        continue;
      }

      const actionIndex = headerCells.findIndex((cell) => (cell.textContent || "").trim() === "动作");
      if (actionIndex < 0) {
        continue;
      }

      const rows = Array.from(table.querySelectorAll("tbody tr"));
      if (!rows.length) {
        continue;
      }

      const actionCounts = new Map();
      for (const row of rows) {
        const cell = row.children[actionIndex];
        const action = (cell?.textContent || "").trim();
        row.dataset.action = action;
        if (!action) {
          continue;
        }
        actionCounts.set(action, (actionCounts.get(action) || 0) + 1);
      }

      const actions = Array.from(actionCounts.keys()).sort((left, right) => {
        const leftRank = ACTION_ORDER.indexOf(left);
        const rightRank = ACTION_ORDER.indexOf(right);
        const leftScore = leftRank === -1 ? ACTION_ORDER.length : leftRank;
        const rightScore = rightRank === -1 ? ACTION_ORDER.length : rightRank;
        if (leftScore !== rightScore) {
          return leftScore - rightScore;
        }
        return left.localeCompare(right, "zh-CN");
      });

      if (!actions.length) {
        continue;
      }

      const bar = document.createElement("div");
      bar.className = "action-filter";
      bar.setAttribute("role", "group");
      bar.setAttribute("aria-label", "按动作筛选");

      const label = document.createElement("span");
      label.className = "action-filter-label";
      label.textContent = "动作筛选";
      bar.appendChild(label);

      const buttons = document.createElement("div");
      buttons.className = "action-filter-buttons";

      const makeButton = (value, text) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "action-filter-button";
        button.dataset.actionFilter = value;
        button.setAttribute("aria-pressed", "false");
        button.textContent = text;
        buttons.appendChild(button);
        return button;
      };

      makeButton("", `全部 (${rows.length})`);
      for (const action of actions) {
        makeButton(action, `${action} (${actionCounts.get(action)})`);
      }
      bar.appendChild(buttons);

      const status = document.createElement("span");
      status.className = "action-filter-status";
      status.setAttribute("aria-live", "polite");
      bar.appendChild(status);

      const empty = document.createElement("p");
      empty.className = "action-filter-empty";
      empty.hidden = true;
      empty.textContent = "没有匹配该动作的标的。";

      table.parentNode?.insertBefore(bar, table);
      table.parentNode?.insertBefore(empty, table);

      const syncUrl = (action) => {
        const url = new URL(window.location.href);
        if (action) {
          url.searchParams.set("action", action);
        } else {
          url.searchParams.delete("action");
        }
        window.history.replaceState(null, "", url);
      };

      const applyFilter = (action, updateUrl = true) => {
        let visible = 0;
        for (const row of rows) {
          const matched = action === "" || row.dataset.action === action;
          row.hidden = !matched;
          if (matched) {
            visible += 1;
          }
        }

        for (const button of buttons.querySelectorAll("[data-action-filter]")) {
          button.setAttribute("aria-pressed", button.dataset.actionFilter === action ? "true" : "false");
        }

        status.textContent =
          action === "" ? `共 ${rows.length} 条` : `显示 ${visible} / ${rows.length} 条 · ${action}`;
        empty.hidden = visible !== 0;

        if (updateUrl) {
          syncUrl(action);
        }
      };

      buttons.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
          return;
        }
        const button = target.closest("[data-action-filter]");
        if (!(button instanceof HTMLElement)) {
          return;
        }
        applyFilter(button.dataset.actionFilter || "");
      });

      const initial = new URLSearchParams(window.location.search).get("action") || "";
      const initialAction = actions.includes(initial) ? initial : "";
      applyFilter(initialAction, false);
    }
  };

  const initBackToTop = () => {
    const button = document.querySelector("[data-back-to-top]");
    if (!button) {
      return;
    }

    const threshold = 320;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const toggleVisibility = () => {
      button.hidden = window.scrollY < threshold;
    };

    button.addEventListener("click", () => {
      window.scrollTo({
        top: 0,
        behavior: prefersReducedMotion ? "auto" : "smooth",
      });
    });

    toggleVisibility();
    window.addEventListener("scroll", toggleVisibility, { passive: true });
  };

  initReportFilter();
  initMonitorTableSearch();
  initActionColumnFilter();
  initBackToTop();
  initMermaid();
})();
""",
        encoding="utf-8",
    )


def build_site(reports_dir: Path | str, output_dir: Path | str) -> None:
    reports_dir = Path(reports_dir).resolve()
    output_dir = Path(output_dir).resolve()
    output_reports_dir = output_dir / "reports"

    if not reports_dir.is_dir():
        raise FileNotFoundError(f"reports directory not found: {reports_dir}")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    report_links: list[tuple[Path, Path]] = []
    markdown_paths = sorted(reports_dir.rglob("*.md"))
    for markdown_path in markdown_paths:
        source_relative = markdown_path.relative_to(reports_dir)
        output_relative = Path("reports") / source_relative.with_suffix(".html")
        report_links.append((source_relative, output_relative))

    available_pinned = available_pinned_filenames(report_links)
    monitor_labels = load_monitor_labels(reports_dir)
    for markdown_path, (_, output_relative) in zip(markdown_paths, report_links):
        render_report(
            markdown_path,
            output_dir / output_relative,
            reports_dir,
            output_dir,
            available_pinned,
            monitor_labels,
        )

    copy_static_assets(reports_dir, output_reports_dir)
    write_styles(output_dir)
    write_scripts(output_dir)
    render_indexes(
        report_links,
        output_dir,
        render_repository_reports_banner(reports_dir),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build GitHub Pages site from reports directory.")
    parser.add_argument("--reports-dir", default="reports", help="Markdown report source directory.")
    parser.add_argument("--output-dir", default="site", help="Generated static site directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_site(Path(args.reports_dir), Path(args.output_dir))


if __name__ == "__main__":
    main()
