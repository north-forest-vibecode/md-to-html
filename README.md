# Simple MD to HTML Converter

![Python](https://img.shields.io/badge/python-3.8.6-blue.svg)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey.svg)

**English** | [Русский](README.ru.md)

> A lightweight Markdown → HTML converter written in pure Python. No `pip install`, no dependencies, no build step. Drop the script next to your `.md` files and get a clean HTML document with embedded styles and a clickable table of contents.

The project follows the **"everything in one folder"** principle: the script scans the directory it lives in, shows a numbered list of `.md` files, and converts the selected one into a ready-to-view HTML document.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Usage Example](#usage-example)
- [Supported Syntax](#supported-syntax)
- [Navigation](#navigation)
- [Limitations](#limitations)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Diagnostics](#diagnostics)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

- **Zero dependencies** — Python standard library only (`os`, `sys`, `re`).
- **Single file** — all the code lives in `converter.py`, nothing to install.
- **Interactive selection** — a numbered list of `.md` files right in the console.
- **Modern minimal design** — embedded CSS: card layout on a light background, clean typography, dark code blocks, striped tables.
- **Automatic table of contents** — the "Contents" section becomes a list of working anchor links.
- **Heading anchors** — every `h1`–`h6` gets an `id`, so you can link to it from anywhere in the document.
- **Safe output** — raw HTML in the source is escaped, while generated tags stay intact.
- **Resilient to junk** — BOM, CRLF, and an accidentally copied ```` ```markdown ```` wrapper are handled automatically.
- **Self-diagnostics** — after conversion the script reports how many anchors and links were created.
- **Cross-platform** — Windows, Linux, macOS.

---

## Requirements

| Parameter | Value |
|---|---|
| Python | 3.8.6 or newer |
| Dependencies | none |
| Modules | `os`, `sys`, `re` |
| OS | Windows / Linux / macOS |

---

## Quick Start

**1. Clone the repository:**

```bash
git clone https://github.com/north-forest-vibecode/md-to-html.git
cd md-to-html
```

**2. Put your `.md` files next to the script:**

```
md-to-html/
├── md_to_html.py
├── my-notes.md
└── documentation.md
```

**3. Run it:**

```bash
python md_to_html.py
```

On Windows, `py md_to_html.py` works too, as does a plain double-click on the file.

**4. Enter the file number** — `my-notes.html` will appear next to it. Open it in your browser.

---

## Usage Example

> The CLI currently prints messages in Russian. English localization is on the roadmap.

```text
=== Simple MD to HTML Converter ===

Доступные файлы:
  1. documentation.md
  2. my-notes.md

Введите номер файла для конвертации: 2
Конвертация...

Готово! Файл сохранен как: my-notes.html

--- ДИАГНОСТИКА ---
Читаю файл:            C:\docs\my-notes.md
Заголовков с якорями:  14
Ссылок для перехода:   5
Навигация сгенерирована корректно.
Открывай этот файл:    C:\docs\my-notes.html
-------------------

Нажмите Enter для выхода...
```

---

## Supported Syntax

| Markdown | Result |
|---|---|
| `# … ######` | `<h1>` … `<h6>` with an `id` attribute |
| `**text**`, `__text__` | `<strong>` |
| `*text*`, `_text_` | `<em>` |
| `~~text~~` | `<del>` |
| `` `code` `` | `<code>` |
| ` ``` ` … ` ``` ` | `<pre><code>` |
| `- item`, `* item` | `<ul><li>` |
| `1. item` | `<ol><li>` |
| `> quote` | `<blockquote>` |
| `---`, `***`, `___` | `<hr>` |
| `[text](url)` | `<a href>` |
| `![alt](url)` | `<img>` |
| `\| cell \| cell \|` | `<table>` |
| A "Contents" section | automatic list of anchor links |

---

## Navigation

Just add a section with any of these names to your document:

```markdown
## Contents
```

Also recognized: `## Table of Contents`, `## Содержание`, `## Оглавление`.

The script finds it and **builds a clickable list automatically** from all level-2 headings (`##`). Whatever is written under that heading — a list, paragraphs, or nothing at all — is replaced with a working table of contents.

Anchor generation rules:

- Heading text is lowercased, spaces are replaced with hyphens.
- Emoji and special characters are stripped from the `id`, but **kept in the visible heading text**.
- Cyrillic is supported: `## Быстрый старт` → `id="быстрый-старт"`.
- Duplicate headings get unique suffixes: `-2`, `-3`, and so on.

Additionally, any list item whose text matches a heading automatically becomes a link to it.

---

## Limitations

The project is intentionally simple, so some GFM features are not implemented:

- Nested lists are not supported — all lists are flat.
- Task lists `- [x]` are rendered as plain text inside a list item.
- Column alignment in tables (`:---:`) is ignored.
- No syntax highlighting in code blocks (the language after ` ``` ` is not used).
- Raw HTML inside Markdown is escaped — inserts like `<div>` will not pass through.
- Footnotes, math, and diagrams are not supported.

---

## Project Structure

```
.
├── md_to_html.py     # the entire converter
├── README.md        # English documentation
├── README.ru.md     # Russian documentation
├── example.md       # demo document
└── example.html     # conversion result (generated)
```

---

## How It Works

| Function | Purpose |
|---|---|
| `get_script_dir()` | locates the folder the script lives in |
| `find_md_files()` | collects and sorts `.md` files |
| `normalize_source()` | strips BOM, CRLF, and an outer code fence |
| `make_slug()` | turns heading text into an `id` anchor |
| `process_inline()` | inline markup via protected placeholders |
| `convert_md_to_html()` | line-by-line block parsing + automatic TOC |
| `generate_html()` | assembles the document with embedded CSS |
| `main()` | interface, file I/O, diagnostics |

Conversion runs in two passes: first all headings and their `id`s are collected, then the HTML is built. This is why the table of contents knows about every section, including the ones further down the file.

---

## Diagnostics

After every conversion the script prints a report:

```text
--- ДИАГНОСТИКА ---
Заголовков с якорями:  14
Ссылок для перехода:   5
Навигация сгенерирована корректно.
-------------------
```

- `Headings with anchors: 0` — the file has no lines like `# Text`.
- `Navigation links: 0` with non-zero anchors — no "Contents" section was found.
- Both numbers above zero — navigation was built, open the file at the path from the last line.

---

## Troubleshooting

**The `#` character is visible in the HTML and the heading is not bold.**
The file started with a BOM — an invisible encoding marker. Fixed: files are read as `utf-8-sig`. Make sure you are on the latest version of the script.

**I click an item in the table of contents and nothing happens.**
Check the diagnostics block. If links were created, you probably have an old tab with an outdated HTML file open — open the fresh file using the path printed in the console.

**The whole document turned into one gray code block.**
You copied the text together with an outer ```` ```markdown ```` wrapper. The script strips it automatically, but double-check that there are no extra lines at the top of the file.

**The characters `<`, `>`, `&` show up as text.**
That is by design: raw HTML is escaped for safety.

---

## Roadmap

- [x] Basic conversion and embedded styles
- [x] Tables, blockquotes, code blocks
- [x] Automatic table of contents and anchors
- [x] Diagnostics and source normalization
- [ ] Nested lists
- [ ] Syntax highlighting in code blocks
- [ ] Batch conversion of all files at once
- [ ] Command-line arguments (`--input`, `--output`)
- [ ] English CLI localization
- [ ] Dark theme

---

## License

Released under the **MIT License** — use, modify, and distribute freely, keeping the copyright notice.

See [LICENSE](LICENSE) for details.

---

Built with pure Python. Not a single external dependency.
