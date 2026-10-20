from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from mdhtml import MATH_PATTERN


class ParseError(Exception):
    pass


@dataclass
class AnswerOption:
    text: str
    correct: bool = False
    fraction: Optional[float] = None


@dataclass
class Gap:
    answers: List[str]
    points: float = 1.0


@dataclass
class Question:
    qtype: str  # "multichoice", "matching", "cloze", "truefalse", "shortanswer", "numerical", "essay"
    name: str
    text: str
    points: float
    # Type-specific payloads
    options: List[AnswerOption] = field(default_factory=list)  # for multichoice
    pairs: List[Tuple[str, str]] = field(default_factory=list)  # for matching
    gaps: List[Gap] = field(default_factory=list)  # for cloze
    tf_answer: Optional[bool] = None  # truefalse
    short_answers: List[str] = field(default_factory=list)  # shortanswer acceptable answers
    numerical_answer: Optional[str] = None  # numerical string representation
    graderinfo: str = ""  # essay grader guidance


# Allow optional BOM and leading spaces before the header
HEADER_RE = re.compile(r"^\ufeff?\s*#\s+Quiz\s*$", re.IGNORECASE)
QUESTION_RE = re.compile(
    r"^##\s*(?P<prefix>[^:]+):\s*(?:\((?P<name>[^)]+)\)\s*)?(?P<text>.*?)(?:\s*\|\|\s*(?P<title>.*?))?(?:\s*\[(?P<points>\d+(?:\.\d+)?)\])?\s*$",
    re.IGNORECASE,
)
OPTION_RE = re.compile(r"^-\s*(?P<text>.*?)(?P<star>\s*\*)?\s*$")
SINGLE_OPTION_RE = re.compile(
    r"^-\s*(?P<text>.*?)(?:\s+\[(?P<fraction>\d+(?:\.\d+)?)%\])?(?P<star>\s*\*)?\s*$"
)
MATCH_PAIR_RE = re.compile(r"^-\s*(?P<left>.*?)\s*=\s*(?P<right>.*?)\s*$")
# Gaps must start with "{<points>:"; any other braces are plain text (e.g. inside $...$ math).
# Math spans are matched first (group "math") so that braces inside them are never gaps.
CLOZE_GAP_RE = re.compile(
    rf"(?P<math>{MATH_PATTERN})|\{{(?P<pts>\d+(?:\.\d+)?):(?P<body>(?:{MATH_PATTERN}|[^}}])*)\}}",
    re.DOTALL,
)
# Essay grader guidance: any {text} outside math.
ESSAY_GUIDANCE_RE = re.compile(
    rf"(?P<math>{MATH_PATTERN})|\{{(?P<body>(?:{MATH_PATTERN}|[^}}])*)\}}",
    re.DOTALL,
)
IGNORED_SEGMENT_RE = re.compile(r"\[\[.*?\]\]", re.DOTALL)
FORMULA_RE = re.compile(r"<<(.*?)>>", re.DOTALL)

SUPERSCRIPT_MAP = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
    "⁼": "=",
    "⁽": "(",
    "⁾": ")",
    "ᵃ": "a",
    "ᵇ": "b",
    "ᶜ": "c",
    "ᵈ": "d",
    "ᵉ": "e",
    "ᶠ": "f",
    "ᵍ": "g",
    "ʰ": "h",
    "ⁱ": "i",
    "ʲ": "j",
    "ᵏ": "k",
    "ˡ": "l",
    "ᵐ": "m",
    "ⁿ": "n",
    "ᵒ": "o",
    "ᵖ": "p",
    "ʳ": "r",
    "ˢ": "s",
    "ᵗ": "t",
    "ᵘ": "u",
    "ᵛ": "v",
    "ʷ": "w",
    "ˣ": "x",
    "ʸ": "y",
    "ᶻ": "z",
}

SUBSCRIPT_MAP = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "₊": "+",
    "₋": "-",
    "₌": "=",
    "₍": "(",
    "₎": ")",
    "ₐ": "a",
    "ₑ": "e",
    "ₕ": "h",
    "ᵢ": "i",
    "ⱼ": "j",
    "ₖ": "k",
    "ₗ": "l",
    "ₘ": "m",
    "ₙ": "n",
    "ₒ": "o",
    "ₚ": "p",
    "ᵣ": "r",
    "ₛ": "s",
    "ₜ": "t",
    "ᵤ": "u",
    "ᵥ": "v",
    "ₓ": "x",
}

SUPERSCRIPT_RE = re.compile("([" + re.escape("".join(SUPERSCRIPT_MAP.keys())) + r"]+)")
SUBSCRIPT_RE = re.compile("([" + re.escape("".join(SUBSCRIPT_MAP.keys())) + r"]+)")
SQRT_PAREN_RE = re.compile(r"√\s*\(([^()]+)\)")
SQRT_BRACE_RE = re.compile(r"√\s*\{([^{}]+)\}")
SQRT_TOKEN_RE = re.compile(r"√\s*(\\[A-Za-z]+(?:\{[^{}]+\})+|[A-Za-z0-9]+(?:\^\{[^{}]+\}|_\{[^{}]+\})*)")


PREFIX_MAP = {
    "single-choice": "singlechoice",
    "single choice": "singlechoice",
    "singlechoice": "singlechoice",
    "multi-choice": "multichoice",
    "multi choice": "multichoice",
    "multichoice": "multichoice",
    "matching": "matching",
    "cloze": "cloze",
    "true/false": "truefalse",
    "short answer": "shortanswer",
    "numerical": "numerical",
    "essay": "essay",
}


def normalize_prefix(pfx: str) -> Optional[str]:
    key = pfx.strip().lower()
    return PREFIX_MAP.get(key)


def strip_ignored_segments(text: str) -> str:
    """Remove non-content notes wrapped in [[...]] from the markdown source."""
    return IGNORED_SEGMENT_RE.sub("", text)


def _translate_scripts(value: str, mapping: dict[str, str], wrapper: str) -> str:
    translated = "".join(mapping.get(char, char) for char in value)
    return f"{wrapper}{{{translated}}}"


def _find_matching_delimiter(text: str, start: int) -> int:
    pairs = {"(": ")", "[": "]", "{": "}"}
    opener = text[start]
    closer = pairs[opener]
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    return -1


def _normalize_token(token: str) -> str:
    if len(token) >= 2 and token[0] in "({[" and token[-1] in ")}]":
        return token[1:-1]
    return token


def _tokenize_formula(expression: str) -> List[str]:
    tokens: List[str] = []
    index = 0
    operators = set("+-*/=,;<>|")

    while index < len(expression):
        char = expression[index]
        if char.isspace():
            index += 1
            continue

        if char in "({[":
            end = _find_matching_delimiter(expression, index)
            if end == -1:
                tokens.append(expression[index:])
                break
            tokens.append(expression[index : end + 1])
            index = end + 1
            continue

        if char == "\\":
            end = index + 1
            while end < len(expression) and expression[end].isalpha():
                end += 1
            while end < len(expression) and expression[end] in "[{":
                group_end = _find_matching_delimiter(expression, end)
                if group_end == -1:
                    break
                end = group_end + 1
            tokens.append(expression[index:end])
            index = end
            continue

        if char in operators:
            tokens.append(char)
            index += 1
            continue

        end = index
        while end < len(expression) and not expression[end].isspace() and expression[end] not in operators and expression[end] not in "()[]{}":
            end += 1
        tokens.append(expression[index:end])
        index = end

    return tokens


def _normalize_fraction_tokens(tokens: List[str]) -> str:
    working = tokens[:]
    while "/" in working:
        for index, token in enumerate(working):
            if token != "/" or index == 0 or index == len(working) - 1:
                continue
            numerator = _normalize_token(working[index - 1])
            denominator = _normalize_token(working[index + 1])
            working[index - 1 : index + 2] = [f"\\frac{{{numerator}}}{{{denominator}}}"]
            break
        else:
            break
    return "".join(working)


def _normalize_formula_expression(expression: str) -> str:
    parts: List[str] = []
    index = 0
    while index < len(expression):
        char = expression[index]
        if char in "({[":
            end = _find_matching_delimiter(expression, index)
            if end == -1:
                parts.append(expression[index:])
                break
            inner = _normalize_formula_expression(expression[index + 1 : end])
            parts.append(f"{char}{inner}{expression[end]}")
            index = end + 1
            continue
        parts.append(char)
        index += 1

    return _normalize_fraction_tokens(_tokenize_formula("".join(parts)))


def normalize_formula_content(formula: str) -> str:
    formula = " ".join(formula.split())
    formula = SUPERSCRIPT_RE.sub(lambda match: _translate_scripts(match.group(1), SUPERSCRIPT_MAP, "^"), formula)
    formula = SUBSCRIPT_RE.sub(lambda match: _translate_scripts(match.group(1), SUBSCRIPT_MAP, "_"), formula)
    formula = SQRT_PAREN_RE.sub(r"\\sqrt{\1}", formula)
    formula = SQRT_BRACE_RE.sub(r"\\sqrt{\1}", formula)
    formula = SQRT_TOKEN_RE.sub(r"\\sqrt{\1}", formula)
    return _normalize_formula_expression(formula)


def convert_formulas(text: str) -> str:
    """Convert <<formula>> to Moodle-compatible inline TeX: \\(formula\\)."""
    return FORMULA_RE.sub(lambda m: r"\(" + normalize_formula_content(m.group(1)) + r"\)", text)


def abbreviate_question_name(text: str, min_len: int = 25, max_len: int = 30) -> str:
    """Create a short question name, preferring 25-30 characters when possible."""
    cleaned = " ".join(text.split()).strip()
    if not cleaned:
        return "Question"
    if len(cleaned) <= max_len:
        return cleaned

    snippet = cleaned[:max_len].rstrip()
    split_at = snippet.rfind(" ")
    if split_at >= min_len:
        snippet = snippet[:split_at].rstrip()

    return snippet


def parse_markdown_file(path: Path) -> List[Question]:
    text = path.read_text(encoding="utf-8")
    return parse_markdown_text(text, source=str(path))


def parse_markdown_text(text: str, source: str = "<memory>") -> List[Question]:
    text = strip_ignored_segments(text)
    text = convert_formulas(text)
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    if not lines or not HEADER_RE.match(lines[0]):
        # Skip non-quiz files by returning empty list
        return []

    i = 1
    questions: List[Question] = []

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        m = QUESTION_RE.match(line)
        if not m:
            # Non-question line, skip
            i += 1
            continue

        prefix = m.group("prefix")
        qtype = normalize_prefix(prefix)
        if not qtype:
            raise ParseError(f"Unrecognized question type prefix '{prefix}' at line {i+1} in {source}")
        qtext = m.group("text").strip()
        explicit_name = (m.group("title") or m.group("name") or "").strip() or None

        points_str = m.group("points")
        points_explicit = points_str is not None
        # Default question points = 4 when not specified; Matching/Cloze may override below when not explicit
        points = float(points_str or 4)

        # Collect block until next question header or EOF
        block: List[str] = []
        i += 1
        while i < len(lines) and not QUESTION_RE.match(lines[i]):
            block.append(lines[i])
            i += 1

        # Parse block by type
        q = parse_block(qtype, qtext, points, block, source, points_explicit, explicit_name)
        questions.append(q)

    return questions


def parse_block(qtype: str, qtext: str, points: float, block: List[str], source: str, points_explicit: bool, explicit_name: Optional[str] = None) -> Question:
    if qtype == "essay":
        # Essay name should remain the full heading text unless an explicit name is provided.
        name = explicit_name if explicit_name else qtext
    else:
        name = explicit_name if explicit_name else abbreviate_question_name(qtext)

    if qtype not in ("cloze", "essay"):
        # Non-option lines (tables, paragraphs, "*"/"1." lists) belong to the question text.
        extra = "\n".join(ln for ln in block if not re.match(r"^-\s", ln)).strip()
        if extra:
            qtext = f"{qtext}\n{extra}"

    if qtype == "singlechoice" or qtype == "multichoice":
        options: List[AnswerOption] = []
        for ln in block:
            lm = SINGLE_OPTION_RE.match(ln) if qtype == "singlechoice" else OPTION_RE.match(ln)
            if lm:
                txt = lm.group("text").strip()
                star = bool(lm.group("star"))
                fraction = None
                if qtype == "singlechoice" and lm.group("fraction") is not None:
                    fraction = float(lm.group("fraction"))
                    if fraction > 100:
                        raise ParseError(
                            f"Single-choice percentage must be between 0% and 100% in {source}"
                        )
                if qtype == "singlechoice" and star:
                    fraction = 100.0
                options.append(AnswerOption(text=txt, correct=star, fraction=fraction))
        if qtype == "singlechoice" and not options:
            raise ParseError(f"Single-choice question must have at least one option in {source}")
        if qtype == "singlechoice" and not any(
            option.correct or option.fraction == 100.0 for option in options
        ):
            raise ParseError(
                f"Single-choice question must have at least one 100% or starred option in {source}"
            )
        return Question(qtype=qtype, name=name, text=qtext, points=points, options=options)

    if qtype == "matching":
        pairs: List[Tuple[str, str]] = []
        for ln in block:
            mm = MATCH_PAIR_RE.match(ln)
            if mm:
                left = mm.group("left").strip()
                right = mm.group("right").strip()
                pairs.append((left, right))
        # Default grade = number of pairs if points not explicitly set
        if not points_explicit and pairs:
            points = float(len(pairs))
        return Question(qtype=qtype, name=name, text=qtext, points=points, pairs=pairs)

    if qtype == "cloze":
        gaps: List[Gap] = []
        block_text = "\n".join(block).strip()
        for gm in CLOZE_GAP_RE.finditer(block_text):
            if gm.group("math"):
                continue
            pts_raw = gm.group("pts")
            pts = float(pts_raw)
            body = gm.group("body")
            answers = [a.strip() for a in body.split("|") if a.strip()]
            if not answers:
                continue
            gaps.append(Gap(answers=answers, points=pts))
        # points = sum of gap points if not explicitly provided
        if not points_explicit and gaps:
            points = float(sum(g.points for g in gaps))
        # For Cloze, use the block text (which contains the gaps) as the question text
        return Question(qtype=qtype, name=name, text=block_text or qtext, points=points, gaps=gaps)

    if qtype == "truefalse":
        # Expect one option line: - True* or - False*
        tf_val: Optional[bool] = None
        for ln in block:
            lm = OPTION_RE.match(ln)
            if lm and lm.group("star"):
                val = lm.group("text").strip().lower()
                if val in ("true", "wahr"):  # allow German sample hint
                    tf_val = True
                elif val in ("false", "falsch"):
                    tf_val = False
        return Question(qtype=qtype, name=name, text=qtext, points=points, tf_answer=tf_val)

    if qtype == "shortanswer":
        answers: List[str] = []
        for ln in block:
            lm = OPTION_RE.match(ln)
            if lm:
                answers.append(lm.group("text").strip())
        return Question(qtype=qtype, name=name, text=qtext, points=points, short_answers=answers)

    if qtype == "numerical":
        # Expect one numeric answer line: - 42*
        ans: Optional[str] = None
        for ln in block:
            lm = OPTION_RE.match(ln)
            if lm and lm.group("star"):
                ans = lm.group("text").strip()
        return Question(qtype=qtype, name=name, text=qtext, points=points, numerical_answer=ans)

    if qtype == "essay":
        block_text = "\n".join(block).strip()
        graderinfo = ""
        # Curly-brace segments are grader guidance; remove them from student-visible question text.
        for gm in ESSAY_GUIDANCE_RE.finditer(block_text):
            if gm.group("math"):
                continue
            body = gm.group("body").strip()
            if body:
                graderinfo = f"{graderinfo}\n{body}".strip() if graderinfo else body
        question_text = ESSAY_GUIDANCE_RE.sub(lambda m: m.group("math") or "", block_text).strip()
        return Question(qtype=qtype, name=name, text=question_text or qtext, points=points, graderinfo=graderinfo)

    raise ParseError(f"Unsupported question type '{qtype}' in {source}")


def is_quiz_file(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as f:
            first = f.readline()
            # Strip UTF-8 BOM if present and leading whitespace
            first = (first or "").lstrip("\ufeff").lstrip()
            return bool(HEADER_RE.match(first))
    except OSError:
        return False
