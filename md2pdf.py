#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path
from typing import Any


def configure_native_library_path() -> None:
    """Make Homebrew native libraries visible to WeasyPrint on macOS."""
    if sys.platform != "darwin":
        return

    existing = [
        value
        for value in os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "").split(os.pathsep)
        if value
    ]
    for candidate in (Path("/opt/homebrew/lib"), Path("/usr/local/lib")):
        value = str(candidate)
        if candidate.is_dir() and value not in existing:
            existing.insert(0, value)
    if existing:
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = os.pathsep.join(existing)


def default_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def inline_text(token: Any) -> str:
    parts: list[str] = []
    for child in token.children or []:
        if child.type in {"text", "code_inline", "image"}:
            parts.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            parts.append(" ")
    return "".join(parts).strip()


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug or "section"


def add_heading_ids(tokens: list[Any]) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, str]] = []
    seen: dict[str, int] = {}

    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue

        level = int(token.tag[1:])
        if index + 1 >= len(tokens) or tokens[index + 1].type != "inline":
            continue

        text = inline_text(tokens[index + 1])
        base = slugify(text)
        count = seen.get(base, 0) + 1
        seen[base] = count
        anchor = base if count == 1 else f"{base}-{count}"
        token.attrSet("id", anchor)

        if 2 <= level <= 4:
            headings.append((level, text, anchor))

    return headings


def build_toc(headings: list[tuple[int, str, str]]) -> str:
    items = "\n".join(
        f'<li class="toc-level-{level}"><a href="#{html.escape(anchor, quote=True)}">'
        f"{html.escape(text)}</a></li>"
        for level, text, anchor in headings
    )
    return (
        '<nav class="toc" aria-label="Table of contents">\n'
        '  <div class="toc-title">Table of contents</div>\n'
        f"  <ol>\n{items}\n  </ol>\n"
        "</nav>\n"
    )


def render_markdown(markdown: str, with_toc: bool) -> str:
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("linkify")
    tokens = md.parse(markdown)
    if not with_toc:
        return md.renderer.render(tokens, md.options, {})

    headings = add_heading_ids(tokens)
    if not headings:
        return md.renderer.render(tokens, md.options, {})

    insert_at = 0
    for index, token in enumerate(tokens):
        if token.type == "heading_close" and token.tag == "h1":
            insert_at = index + 1
            break

    env: dict[str, Any] = {}
    before = md.renderer.render(tokens[:insert_at], md.options, env)
    after = md.renderer.render(tokens[insert_at:], md.options, env)
    return before + build_toc(headings) + after


def convert(input_path: Path, output_path: Path, css_path: Path, with_toc: bool) -> None:
    configure_native_library_path()

    from weasyprint import CSS, HTML

    markdown = input_path.read_text(encoding="utf-8")
    body = render_markdown(markdown, with_toc)
    title = default_title(markdown, input_path.stem)
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
</head>
<body>
{body}
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=document, base_url=str(input_path.parent.resolve())).write_pdf(
        output_path,
        stylesheets=[CSS(filename=str(css_path))],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF")
    parser.add_argument("input", type=Path, help="Markdown input file")
    parser.add_argument("output", nargs="?", type=Path, help="PDF output file (default: input.pdf)")
    parser.add_argument(
        "--css",
        type=Path,
        default=Path(__file__).with_name("style.css"),
        help="CSS stylesheet (default: style.css next to this script)",
    )
    parser.add_argument(
        "--toc",
        action="store_true",
        help="insert a table of contents from H2-H4 headings after the first H1",
    )
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    output_path = (args.output or input_path.with_suffix(".pdf")).expanduser().resolve()
    css_path = args.css.expanduser().resolve()

    if not input_path.is_file():
        parser.error(f"input file not found: {input_path}")
    if input_path.suffix.lower() not in {".md", ".markdown"}:
        parser.error(f"input must be Markdown: {input_path}")
    if not css_path.is_file():
        parser.error(f"CSS file not found: {css_path}")

    try:
        convert(input_path, output_path, css_path, args.toc)
    except (OSError, ValueError) as error:
        print(f"md2pdf: {error}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
