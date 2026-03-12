# markdown2mediawiki

Converts Etherpad-flavoured Markdown to MediaWiki wikitext. The primary use
case is copying North Carolina Wikipedians meeting notes (and similar Etherpad
pads) into MediaWiki pages.

## Usage

```bash
cd markdown2mediawiki
uv run markdown2mediawiki.py [OPTIONS] [INPUT_FILE]
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `-o FILE` / `--output FILE` | stdout | Write output to a file |
| `--dialect [etherpad\|markdown]` | `etherpad` | Input dialect |
| `--strip-preamble` / `--no-strip-preamble` | per-dialect | Override preamble stripping |
| `-v` / `--verbose` | off | Enable DEBUG logging |

### Run with sample data and log output

```bash
cd markdown2mediawiki
uv run markdown2mediawiki.py data/ncp.md -o data/ncp.mediawiki 2>&1 | tee data/last-run.log
```

## Conversion rules

| Input (Markdown) | Output (MediaWiki) |
|---|---|
| `# H1` | `= H1 =` |
| `## H2` | `== H2 ==` |
| `- item` | `* item` |
| `    - item` (4 sp indent) | `** item` |
| `    text` (indented non-bullet) | `:text` |
| `[text](url)` | `[url text]` |
| `**bold**` | `'''bold'''` |
| `*italic*` | `''italic''` |
| `1. item` | `# item` |
| Etherpad preamble lines | *(stripped in `etherpad` dialect)* |

Checkboxes (`- [ ]` and `- [x]`) are converted to plain bullets (MediaWiki
has no native checkbox syntax).

## Project setup

Dependencies (`click`, `tqdm`) are declared in the repo-root `pyproject.toml`
(`wikipedia-utils`). There is no per-script `pyproject.toml`; `uv` finds the
root file automatically when you run from inside the subdirectory.

## Architecture

The script is deliberately line-by-line and function-per-rule so contributors
can find and change any single rule in isolation:

- **`classify_line(raw)`** — returns `(line_type, indent_level, content)` using
  first-match priority: blank → header → checkbox → bullet → ordered → indented
  text → paragraph.
- **`convert_line(line_type, level, content)`** — maps a classified line to
  MediaWiki markup.
- **`convert_inline(text)`** — applies link, bold, and italic substitutions.
- **`convert_lines(lines, dialect, strip_preamble)`** — orchestrates the loop
  with tqdm progress bar and preamble gating.

## Adding a new dialect or rule

1. Add a new `elif` branch in `classify_line` (or a new regex at the top).
2. Handle the new type in `convert_line`.
3. For dialect-specific logic, gate on the `dialect` argument inside
   `convert_lines`.
