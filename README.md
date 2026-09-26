# md2pdf

A small Markdown-to-PDF converter built around `uv`, `markdown-it-py`, and WeasyPrint.

This repository extracts only the PDF-generation path from `myab-yagamy-site` and removes resume-pipeline features that are not needed for standalone Markdown conversion (YAML metadata, Jinja templates, DOCX generation, manifests, Git checks, etc.).

## Requirements

- [`uv`](https://docs.astral.sh/uv/)
- Python 3.11 or newer (managed automatically by `uv` when available)
- WeasyPrint native libraries

On macOS, if WeasyPrint cannot load its native libraries, install it with Homebrew:

```bash
brew install weasyprint
```

The Python launcher also adds common Homebrew library paths to `DYLD_FALLBACK_LIBRARY_PATH` before importing WeasyPrint.

## Usage

Convert `document.md` to `document.pdf`:

```bash
./md2pdf.sh document.md
```

Choose the output path explicitly:

```bash
./md2pdf.sh document.md output.pdf
```

Generate a table of contents:

```bash
./md2pdf.sh --toc document.md
```

The TOC is generated from H2-H4 headings and inserted after the first H1. If the document has no H1, the TOC is inserted before the document body. TOC entries are clickable and include PDF page numbers.

Use a custom stylesheet:

```bash
./md2pdf.sh --css custom.css document.md output.pdf
```

Options can be combined:

```bash
./md2pdf.sh --toc --css custom.css document.md output.pdf
```

You can also call the Python script directly through `uv`:

```bash
uv run python md2pdf.py --toc document.md output.pdf
```

The first `uv run` resolves the two project dependencies and creates/updates `uv.lock`.

## What is included

- CommonMark Markdown rendering
- Automatic links for bare URLs
- Optional TOC generated from H2-H4 headings
- Clickable TOC entries with PDF page numbers
- A4 PDF output with page numbers
- Relative local images/files resolved from the Markdown file's directory
- Optional custom CSS

## Dependencies

Only two direct Python dependencies are required:

- `markdown-it-py[linkify]`
- `weasyprint`
