# markdown2mediawiki — LLM notes

See README.md for usage and conversion rules.

## Architecture

The script is deliberately line-by-line and function-per-rule so contributors
can find and change any single rule in isolation:

- **`classify_line(raw)`** — returns `(line_type, indent_level, content)` using
  first-match priority: blank → header → checkbox → bullet → ordered → indented
  text → paragraph.
- **`convert_line(line_type, level, content)`** — maps a classified line to
  MediaWiki markup.
- **`convert_inline(text)`** — applies link, bold, and italic substitutions.
- **`convert_lines(lines, dialect, strip_preamble, indent_as_bullets)`** — orchestrates the loop
  with tqdm progress bar and preamble gating.

## Adding a new dialect or rule

1. Add a new `elif` branch in `classify_line` (or a new regex at the top).
2. Handle the new type in `convert_line`.
3. For dialect-specific logic, gate on the `dialect` argument inside
   `convert_lines`.
