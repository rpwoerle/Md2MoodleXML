"""Minimal Markdown -> simple HTML conversion (tables, lists, math, inline styles)."""
from __future__ import annotations

import re
from html import escape
from typing import List, Tuple

_PLACEHOLDER = "\x00{}\x00"
_PLACEHOLDER_RE = re.compile(r"\x00(\d+)\x00")

CODE_SPAN_RE = re.compile(r"`([^`\n]+)`")
# Order matters: display math before inline math; Moodle-style \( \) / \[ \] are kept as-is.
DISPLAY_DOLLAR_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
MOODLE_INLINE_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
MOODLE_DISPLAY_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
# $...$ must not start/end with whitespace and must not be followed by a digit (avoids "$5 and $6").
INLINE_DOLLAR_RE = re.compile(r"(?<![\\$])\$(?=\S)([^$\n]*?\S)\$(?![\d$])")

# Regex source matching any math span; used to keep braces inside math away from gap parsing.
MATH_PATTERN = (
    r"\$\$.+?\$\$|\\\(.+?\\\)|\\\[.+?\\\]"
    r"|(?<![\\$])\$(?=\S)[^$\n]*?\S\$(?![\d$])"
)

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*|(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)")
ITALIC_RE = re.compile(r"(?<![*\w])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![*\w])|(?<![_\w])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![_\w])")
STRIKE_RE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")

LIST_ITEM_RE = re.compile(r"^(?P<indent>\s*)(?P<marker>[-*+]|\d+[.)])\s+(?P<text>.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*```")


def inline_html(text: str) -> str:
    """Convert inline markdown to HTML, escaping everything else."""
    stash: List[str] = []

    def keep(html: str) -> str:
        stash.append(html)
        return _PLACEHOLDER.format(len(stash) - 1)

    text = CODE_SPAN_RE.sub(lambda m: keep(f"<code>{escape(m.group(1))}</code>"), text)
    text = DISPLAY_DOLLAR_RE.sub(lambda m: keep(r"\[" + escape(m.group(1).strip()) + r"\]"), text)
    text = MOODLE_INLINE_RE.sub(lambda m: keep(r"\(" + escape(m.group(1)) + r"\)"), text)
    text = MOODLE_DISPLAY_RE.sub(lambda m: keep(r"\[" + escape(m.group(1)) + r"\]"), text)
    text = INLINE_DOLLAR_RE.sub(lambda m: keep(r"\(" + escape(m.group(1)) + r"\)"), text)

    text = escape(text, quote=False)
    text = LINK_RE.sub(lambda m: f'<a href="{escape(m.group(2), quote=True)}">{m.group(1)}</a>', text)
    text = BOLD_RE.sub(lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", text)
    text = ITALIC_RE.sub(lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)
    text = STRIKE_RE.sub(lambda m: f"<del>{m.group(1)}</del>", text)

    # Placeholders may be nested inside other placeholders' replacements only via text, so one pass suffices.
    return _PLACEHOLDER_RE.sub(lambda m: stash[int(m.group(1))], text)


def _split_row(line: str) -> List[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.replace("\\|", "|").strip() for c in cells]


def _aligns(sep_line: str) -> List[str]:
    result = []
    for cell in _split_row(sep_line):
        left, right = cell.startswith(":"), cell.endswith(":")
        result.append("center" if left and right else "right" if right else "left" if left else "")
    return result


def _is_table_start(lines: List[str], i: int) -> bool:
    return (
        i + 1 < len(lines)
        and "|" in lines[i]
        and "|" in lines[i + 1]
        and bool(TABLE_SEP_RE.match(lines[i + 1]))
    )


def _render_table(lines: List[str]) -> str:
    aligns = _aligns(lines[1])

    def cell(tag: str, idx: int, content: str) -> str:
        align = aligns[idx] if idx < len(aligns) else ""
        attr = f' style="text-align: {align};"' if align else ""
        return f"<{tag}{attr}>{inline_html(content)}</{tag}>"

    head = "".join(cell("th", i, c) for i, c in enumerate(_split_row(lines[0])))
    rows = [
        "<tr>" + "".join(cell("td", i, c) for i, c in enumerate(_split_row(ln))) + "</tr>"
        for ln in lines[2:]
    ]
    return (
        '<table border="1">\n<thead><tr>' + head + "</tr></thead>\n<tbody>\n"
        + "\n".join(rows) + "\n</tbody>\n</table>"
    )


def _list_kind(marker: str) -> str:
    return "ol" if marker[0].isdigit() else "ul"


def _render_list(items: List[Tuple[int, str, str]]) -> str:
    """items: (indent, marker, text); nested by increasing indent."""
    out: List[str] = []
    stack: List[Tuple[int, str]] = []  # (indent, tag)
    for indent, marker, text in items:
        kind = _list_kind(marker)
        while stack and indent < stack[-1][0]:
            out.append(f"</li></{stack.pop()[1]}>")
        if stack and indent == stack[-1][0]:
            if stack[-1][1] != kind:
                out.append(f"</li></{stack.pop()[1]}>")
            else:
                out.append("</li>")
                out.append(f"<li>{inline_html(text)}")
                continue
        out.append(f"<{kind}>")
        stack.append((indent, kind))
        out.append(f"<li>{inline_html(text)}")
    while stack:
        out.append(f"</li></{stack.pop()[1]}>")
    return "".join(out)


def block_html(text: str) -> str:
    """Convert block-level markdown (paragraphs, headings, lists, tables, code) to HTML."""
    lines = text.splitlines()
    blocks: List[str] = []
    para: List[str] = []
    i = 0

    def flush() -> None:
        if para:
            blocks.append("<p>" + "<br>\n".join(inline_html(p.strip()) for p in para) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush()
            i += 1
        elif FENCE_RE.match(line):
            flush()
            i += 1
            code: List[str] = []
            while i < len(lines) and not FENCE_RE.match(lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append("<pre><code>" + escape("\n".join(code), quote=False) + "</code></pre>")
        elif _is_table_start(lines, i):
            flush()
            j = i + 2
            while j < len(lines) and lines[j].strip() and "|" in lines[j]:
                j += 1
            blocks.append(_render_table(lines[i:j]))
            i = j
        elif LIST_ITEM_RE.match(line):
            flush()
            items: List[Tuple[int, str, str]] = []
            while i < len(lines):
                m = LIST_ITEM_RE.match(lines[i])
                if not m:
                    break
                items.append((len(m.group("indent").expandtabs(4)), m.group("marker"), m.group("text")))
                i += 1
            blocks.append(_render_list(items))
        elif HEADING_RE.match(line):
            flush()
            m = HEADING_RE.match(line)
            level = len(m.group(1))
            blocks.append(f"<h{level}>{inline_html(m.group(2).strip())}</h{level}>")
            i += 1
        else:
            para.append(line)
            i += 1
    flush()
    return "\n".join(blocks)
