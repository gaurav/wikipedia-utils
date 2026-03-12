#!/usr/bin/env python3
"""Convert Etherpad-flavoured Markdown to MediaWiki wikitext."""

import re
import sys
import logging

import click
from tqdm import tqdm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inline transformations (applied to every non-blank line after block markup)
# ---------------------------------------------------------------------------

INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
# Italic: a single * not adjacent to another *
ITALIC_RE = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)')


def convert_inline(text: str) -> str:
    """Apply inline Markdown → MediaWiki substitutions."""
    text = INLINE_LINK_RE.sub(r'[\2 \1]', text)
    text = BOLD_RE.sub(r"'''\1'''", text)
    text = ITALIC_RE.sub(r"''\1''", text)
    return text


# ---------------------------------------------------------------------------
# Line classification
# ---------------------------------------------------------------------------

HEADER_RE = re.compile(r'^(#{1,6})\s*(.+)')
CHECKBOX_UNCHECKED_RE = re.compile(r'^- \[ \] ')
CHECKBOX_CHECKED_RE = re.compile(r'^- \[x\] ', re.IGNORECASE)
BULLET_RE = re.compile(r'^- ')
ORDERED_RE = re.compile(r'^\d+\. (.*)')
ETHERPAD_PREAMBLE_RE = re.compile(r'^Welcome to the WMF Etherpad installation\.')


def classify_line(raw: str):
    """Return (line_type, indent_level, content) for a raw input line."""
    # Blank line
    if not raw.strip():
        return ('blank', 0, '')

    # Header (no indent stripping — headers must start at column 0)
    m = HEADER_RE.match(raw)
    if m:
        return ('header', len(m.group(1)), m.group(2).strip())

    # Measure indent
    stripped = raw.lstrip(' ')
    spaces = len(raw) - len(stripped)
    level = spaces // 4  # 4 spaces per Etherpad indent level

    # Bullet variants (after stripping leading spaces)
    if CHECKBOX_UNCHECKED_RE.match(stripped):
        content = stripped[6:]  # len('- [ ] ') == 6
        return ('bullet', level, content)

    if CHECKBOX_CHECKED_RE.match(stripped):
        content = stripped[6:]  # len('- [x] ') == 6
        return ('bullet', level, content)

    if BULLET_RE.match(stripped):
        content = stripped[2:]  # len('- ') == 2
        return ('bullet', level, content)

    m = ORDERED_RE.match(stripped)
    if m:
        return ('ordered', level, m.group(1))

    # Indented non-bullet text
    if level > 0:
        return ('indented_text', level, stripped)

    # Plain paragraph
    return ('paragraph', 0, stripped)


# ---------------------------------------------------------------------------
# Block conversion
# ---------------------------------------------------------------------------

def convert_line(line_type: str, level: int, content: str) -> str:
    """Convert a classified line to MediaWiki markup."""
    content = convert_inline(content)

    if line_type == 'blank':
        return ''

    if line_type == 'header':
        marks = '=' * level
        return f'{marks} {content} {marks}'

    if line_type == 'bullet':
        marks = '*' * (level + 1)
        return f'{marks} {content}'

    if line_type == 'ordered':
        marks = '#' * (level + 1)
        return f'{marks} {content}'

    if line_type == 'indented_text':
        colons = ':' * level
        return f'{colons}{content}'

    # paragraph
    return content


# ---------------------------------------------------------------------------
# Post-processing
# ---------------------------------------------------------------------------

_LIST_LINE_RE = re.compile(r'^[*#]')


def collapse_list_blanks(lines: list[str]) -> list[str]:
    """Remove blank lines that fall between two MediaWiki list items.

    MediaWiki resets a list whenever a blank line appears, so consecutive
    list items must not be separated by blank lines.
    """
    result = []
    i = 0
    while i < len(lines):
        if lines[i] == '':
            # Find the next non-blank line
            j = i + 1
            while j < len(lines) and lines[j] == '':
                j += 1
            prev = next((l for l in reversed(result) if l != ''), None)
            nxt = lines[j] if j < len(lines) else None
            if (prev and _LIST_LINE_RE.match(prev) and
                    nxt and _LIST_LINE_RE.match(nxt)):
                # Skip blank(s) between two list lines
                i = j
                continue
        result.append(lines[i])
        i += 1
    return result


# ---------------------------------------------------------------------------
# Preamble stripping
# ---------------------------------------------------------------------------

def should_strip_preamble(dialect: str, strip_preamble_override) -> bool:
    """Decide whether to strip preamble given dialect and CLI flag."""
    if dialect == 'markdown':
        return False
    # etherpad dialect: default True, overridable
    if strip_preamble_override is None:
        return True
    return strip_preamble_override


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def convert_lines(lines: list[str], dialect: str, strip_preamble: bool) -> list[str]:
    """Convert a list of raw input lines to MediaWiki wikitext lines."""
    output = []
    preamble_active = strip_preamble  # True until we see the first header

    for raw in tqdm(lines, desc='Converting', unit='line', disable=not sys.stderr.isatty()):
        raw = raw.rstrip('\n')

        if preamble_active:
            line_type, level, content = classify_line(raw)
            if line_type == 'header':
                preamble_active = False
                # Fall through to normal conversion below
            else:
                logger.debug('Stripping preamble line: %r', raw)
                continue

        line_type, level, content = classify_line(raw)
        result = convert_line(line_type, level, content)
        logger.debug('%s (lvl=%d) -> %r', line_type, level, result)
        output.append(result)

    return collapse_list_blanks(output)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option('-o', '--output', 'output_file', type=click.Path(), default=None,
              help='Write output to FILE instead of stdout.')
@click.option('--dialect', type=click.Choice(['etherpad', 'markdown']), default='etherpad',
              show_default=True, help='Input dialect.')
@click.option('--strip-preamble/--no-strip-preamble', default=None,
              help='Override preamble stripping within etherpad dialect.')
@click.option('-v', '--verbose', is_flag=True, help='Enable DEBUG logging.')
def main(input_file, output_file, dialect, strip_preamble, verbose):
    """Convert a Markdown file to MediaWiki wikitext.

    Reads from INPUT_FILE or stdin. Writes to stdout or --output file.
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(levelname)s: %(message)s',
    )

    do_strip = should_strip_preamble(dialect, strip_preamble)
    logger.info('Dialect: %s | strip_preamble: %s', dialect, do_strip)

    if input_file:
        logger.info('Reading from %s', input_file)
        with open(input_file, encoding='utf-8') as f:
            lines = f.readlines()
    else:
        logger.info('Reading from stdin')
        lines = sys.stdin.readlines()

    result_lines = convert_lines(lines, dialect=dialect, strip_preamble=do_strip)

    output_text = '\n'.join(result_lines) + '\n'

    if output_file:
        logger.info('Writing to %s', output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
    else:
        sys.stdout.write(output_text)


if __name__ == '__main__':
    main()
