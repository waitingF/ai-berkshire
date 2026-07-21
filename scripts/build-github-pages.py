#!/usr/bin/env python3
"""Build a static GitHub Pages site from reports/*.md files."""

from __future__ import annotations

import argparse
import html
import shutil
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import markdown
from markdown.extensions import Extension
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

# Root-level living docs pinned on the homepage and site nav.
HOME_PINNED_REPORTS = (
    {
        "filename": "重点标的看板.md",
        "title": "重点标的看板",
        "nav_label": "看板",
        "eyebrow": "Thesis 总览",
        "description": "thesis / 指定标的一页总览：阶段、健康度、本周关注与下次动作。",
    },
    {
        "filename": "买卖建议跟踪表.md",
        "title": "买卖建议跟踪表",
        "nav_label": "买卖建议",
        "eyebrow": "买卖建议",
        "description": "研究报告里的买卖/观望建议：条件是否触发、事后对不对。",
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


def render_markdown(markdown_text: str) -> str:
    renderer = markdown.Markdown(
        extensions=[*MARKDOWN_EXTENSIONS, MarkdownLinkRewriteExtension()],
        output_format="html5",
    )
    return renderer.convert(markdown_text)


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


def root_pinned_filenames(report_links: list[tuple[Path, Path]]) -> set[str]:
    pinned_names = {item["filename"] for item in HOME_PINNED_REPORTS}
    return {
        source_relative.name
        for source_relative, _ in report_links
        if source_relative.parent == Path(".") and source_relative.name in pinned_names
    }


def render_home_pinned_section(report_links: list[tuple[Path, Path]]) -> str:
    href_by_name = {
        source_relative.name: html_relative
        for source_relative, html_relative in report_links
        if source_relative.parent == Path(".")
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
) -> None:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    title = title_from_markdown(markdown_text, markdown_path.stem)
    source_relative = markdown_path.relative_to(reports_dir)
    root_prefix = "../" * (len(output_path.relative_to(output_dir).parents) - 1)
    breadcrumb_html = render_breadcrumb(source_relative.parent, root_prefix, title)
    body_html = f"""    {breadcrumb_html}
    <article class="report-article">
{render_markdown(markdown_text)}
    </article>"""
    current_nav = source_relative.name if source_relative.parent == Path(".") else None
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
{pinned_section}    <section class="index-tools" aria-labelledby="filter-title">
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
            root_pinned_filenames(report_links),
            current_nav,
        ),
        encoding="utf-8",
    )


def render_indexes(report_links: list[tuple[Path, Path]], output_dir: Path) -> None:
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

[data-report-filter] {
  width: 100%;
  min-height: 44px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: var(--surface);
  padding: 10px 12px;
  color: var(--text);
  font: inherit;
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
  initActionColumnFilter();
  initBackToTop();
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

    available_pinned = root_pinned_filenames(report_links)
    for markdown_path, (_, output_relative) in zip(markdown_paths, report_links):
        render_report(
            markdown_path,
            output_dir / output_relative,
            reports_dir,
            output_dir,
            available_pinned,
        )

    copy_static_assets(reports_dir, output_reports_dir)
    write_styles(output_dir)
    write_scripts(output_dir)
    render_indexes(report_links, output_dir)


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
