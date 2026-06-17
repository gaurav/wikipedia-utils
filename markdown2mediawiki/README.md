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
| `--indented-as-bullets` / `--no-indented-as-bullets` | per-dialect (on for etherpad) | Convert indented non-bullet text to list items |
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
| `    text` (indented non-bullet) | `:text` (or `** text` bullet with `--indented-as-bullets`) |
| `[text](url)` | `[url text]` |
| `**bold**` | `'''bold'''` |
| `*italic*` | `''italic''` |
| `1. item` / `    1. item` | `* 1. item` / `** 1. item` (bullet with number as text) |
| Etherpad preamble lines | *(stripped in `etherpad` dialect)* |

Checkboxes (`- [ ]` and `- [x]`) are converted to plain bullets (MediaWiki
has no native checkbox syntax).

## Project setup

Dependencies (`click`, `tqdm`) are declared in the repo-root `pyproject.toml`
(`wikipedia-utils`). There is no per-script `pyproject.toml`; `uv` finds the
root file automatically when you run from inside the subdirectory.
