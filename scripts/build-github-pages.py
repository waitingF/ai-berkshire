#!/usr/bin/env python3
"""Build a static GitHub Pages site from reports/*.md files."""

from __future__ import annotations

import argparse
import html
import shutil
from pathlib import Path
from urllib.parse import quote

import markdown


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


def title_from_markdown(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or fallback
    return fallback


def encoded_href(path: Path) -> str:
    return quote(path.as_posix(), safe="/-._~")


def render_markdown(markdown_text: str) -> str:
    renderer = markdown.Markdown(
        extensions=MARKDOWN_EXTENSIONS,
        output_format="html5",
    )
    return renderer.convert(markdown_text)


def render_page(title: str, body_html: str, root_prefix: str) -> str:
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <link rel="stylesheet" href="{root_prefix}assets/site.css">
</head>
<body>
  <header class="site-header">
    <a class="site-title" href="{root_prefix}index.html">AI Berkshire Reports</a>
  </header>
  <main class="content">
{body_html}
  </main>
</body>
</html>
"""


def render_report(markdown_path: Path, output_path: Path, reports_dir: Path, output_dir: Path) -> None:
    markdown_text = markdown_path.read_text(encoding="utf-8")
    title = title_from_markdown(markdown_text, markdown_path.stem)
    body_html = render_markdown(markdown_text)
    root_prefix = "../" * (len(output_path.relative_to(output_dir).parents) - 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_page(title, body_html, root_prefix), encoding="utf-8")


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
            f'        <li class="{item_type}"><a href="{encoded_href(href)}">{html.escape(label)}</a></li>'
        )
    return "\n".join(rows)


def output_root_prefix(output_path: Path, output_dir: Path) -> str:
    return "../" * (len(output_path.relative_to(output_dir).parents) - 1)


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
        subtitle = f"{total_reports} reports generated from <code>reports/</code>."
        breadcrumb_html = ""
    else:
        title = source_relative_dir.as_posix()
        subtitle = f"{len(report_items)} reports in this folder."
        breadcrumb_html = f'      <p class="breadcrumb"><a href="{output_root_prefix(output_path, output_dir)}index.html">Reports</a> / {html.escape(title)}</p>\n'

    body_html = f"""    <section class="index-hero">
{breadcrumb_html}      <h1>{html.escape(title)}</h1>
      <p>{subtitle}</p>
    </section>
    <section class="report-list">
      <h2>Folders</h2>
      <ul>
{render_navigation_list(directory_items)}
      </ul>
    </section>
    <section class="report-list">
      <h2>Reports</h2>
      <ul>
{render_navigation_list(report_items)}
      </ul>
    </section>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_page(title, body_html, output_root_prefix(output_path, output_dir)),
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
  --bg: #f8f7f4;
  --panel: #ffffff;
  --text: #1c1c1c;
  --muted: #626262;
  --line: #dedbd2;
  --accent: #0f766e;
  --accent-strong: #0b5f59;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 17px;
  line-height: 1.72;
}

a {
  color: var(--accent);
  text-decoration-thickness: 0.08em;
  text-underline-offset: 0.18em;
}

a:hover {
  color: var(--accent-strong);
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid var(--line);
  background: rgba(248, 247, 244, 0.94);
  backdrop-filter: blur(8px);
}

.site-title {
  display: block;
  max-width: 980px;
  margin: 0 auto;
  padding: 14px 24px;
  color: var(--text);
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
}

.content {
  max-width: 980px;
  margin: 0 auto;
  padding: 36px 24px 72px;
}

.index-hero {
  margin-bottom: 28px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 20px;
}

.index-hero h1,
.content h1 {
  margin: 0 0 16px;
  font-size: 34px;
  line-height: 1.2;
}

.content h2 {
  margin-top: 42px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 8px;
  font-size: 25px;
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

.report-list ul {
  margin: 0;
  margin-bottom: 24px;
  padding: 0;
  list-style: none;
}

.report-list li {
  border-bottom: 1px solid var(--line);
}

.report-list a {
  display: block;
  padding: 12px 0;
  overflow-wrap: anywhere;
}

.report-list li.directory a {
  font-weight: 700;
}

.report-list li.directory a::before {
  content: "目录 ";
  color: var(--muted);
  font-weight: 600;
}

.report-list li.report a::before {
  content: "报告 ";
  color: var(--muted);
  font-weight: 600;
}

.report-list li.empty {
  padding: 12px 0;
  color: var(--muted);
}

.breadcrumb {
  margin-bottom: 12px;
  color: var(--muted);
  font-size: 15px;
}

code {
  border-radius: 4px;
  background: #ece8de;
  padding: 0.12em 0.32em;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.92em;
}

pre {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #202124;
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
  background: rgba(15, 118, 110, 0.07);
  padding: 12px 18px;
  color: #333333;
}

table {
  display: block;
  width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
}

th,
td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  vertical-align: top;
}

th {
  background: #ece8de;
}

img {
  max-width: 100%;
  height: auto;
}

@media (max-width: 640px) {
  body {
    font-size: 16px;
  }

  .site-title,
  .content {
    padding-left: 16px;
    padding-right: 16px;
  }

  .content {
    padding-top: 26px;
  }

  .index-hero h1,
  .content h1 {
    font-size: 28px;
  }
}
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
    for markdown_path in sorted(reports_dir.rglob("*.md")):
        source_relative = markdown_path.relative_to(reports_dir)
        output_relative = Path("reports") / source_relative.with_suffix(".html")
        output_path = output_dir / output_relative
        render_report(markdown_path, output_path, reports_dir, output_dir)
        report_links.append((source_relative, output_relative))

    copy_static_assets(reports_dir, output_reports_dir)
    write_styles(output_dir)
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
