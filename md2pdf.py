#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import os
import sys
from pathlib import Path


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


def convert(input_path: Path, output_path: Path, css_path: Path) -> None:
    configure_native_library_path()

    from markdown_it import MarkdownIt
    from weasyprint import CSS, HTML

    markdown = input_path.read_text(encoding="utf-8")
    body = MarkdownIt("commonmark", {"html": False, "linkify": True}).enable("linkify").render(markdown)
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
        convert(input_path, output_path, css_path)
    except (OSError, ValueError) as error:
        print(f"md2pdf: {error}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())