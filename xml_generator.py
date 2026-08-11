from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import List

from parser import Question, AnswerOption, Gap


def html_cdata(p: str) -> str:
    return f"<![CDATA[<p>{escape(p)}</p>]]>"


def question_cdata(p: str) -> str:
    """Wrap question text specifically in an H5 header within CDATA."""
    return f"<![CDATA[<h5>{escape(p)}</h5>]]>"


def quiz_header() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'


def quiz_footer() -> str:
    return "\n</quiz>\n"


def empty_feedback_blocks() -> str:
    return (
        "    <correctfeedback format=\"html\">\n      <text><![CDATA[<p>Die Antwort ist richtig</p>]]></text>\n    </correctfeedback>\n"
        "    <partiallycorrectfeedback format=\"html\">\n      <text><![CDATA[<p>Die Antwort ist teilweise richtig.</p>]]></text>\n    </partiallycorrectfeedback>\n"
        "    <incorrectfeedback format=\"html\">\n      <text><![CDATA[<p>Die Antwort ist falsch</p>]]></text>\n    </incorrectfeedback>\n    <shownumcorrect/>\n"
    )


def default_blocks(defaultgrade: float) -> str:
    return (
        f"    <generalfeedback format=\"html\">\n      <text></text>\n    </generalfeedback>\n"
        f"    <defaultgrade>{defaultgrade:.7f}</defaultgrade>\n"
        f"    <penalty>0.3333333</penalty>\n"
        f"    <hidden>0</hidden>\n"
        f"    <idnumber></idnumber>\n"
    )


def wrap_question_text(text: str) -> str:
    return (
        "    <questiontext format=\"html\">\n"
        f"      <text>{question_cdata(text)}</text>\n"
        "    </questiontext>\n"
    )


def questions_to_moodle_xml(questions: List[Question], author: str) -> str:
    parts: List[str] = [quiz_header()]
    for q in questions:
        if q.qtype == "singlechoice":
            parts.append(render_singlechoice(q, author))
        elif q.qtype == "multichoice":
            parts.append(render_multichoice(q, author))
        elif q.qtype == "matching":
            parts.append(render_matching(q, author))
        elif q.qtype == "cloze":
            parts.append(render_cloze(q, author))
        elif q.qtype == "truefalse":
            parts.append(render_truefalse(q, author))
        elif q.qtype == "shortanswer":
            parts.append(render_shortanswer(q, author))
        elif q.qtype == "numerical":
            parts.append(render_numerical(q, author))
        elif q.qtype == "essay":
            parts.append(render_essay(q, author))
        else:
            # Skip unknowns defensively
            continue
    parts.append(quiz_footer())
    return "\n".join(parts)


def render_name(name: str) -> str:
    return f"    <name>\n      <text>{escape(name)}</text>\n    </name>\n"


def render_singlechoice(q: Question, author: str) -> str:
    # Single-choice: exactly one correct answer, <single>true</single>, fraction="100" for correct, "0" for wrong
    corrects = [o for o in q.options if o.correct]
    wrongs = [o for o in q.options if not o.correct]

    parts = ["  <question type=\"multichoice\">\n"]
    parts.append(render_name(q.name))
    parts.append(wrap_question_text(q.text))
    parts.append(default_blocks(q.points))
    parts.append("    <single>true</single>\n")
    parts.append("    <shuffleanswers>true</shuffleanswers>\n")
    parts.append("    <answernumbering>none</answernumbering>\n")
    parts.append("    <showstandardinstruction>1</showstandardinstruction>\n")
    parts.append(empty_feedback_blocks())

    for o in q.options:
        frac = 100 if o.correct else 0
        parts.append(
            f"    <answer fraction=\"{frac}\" format=\"html\">\n      <text>{html_cdata(o.text)}</text>\n      <feedback format=\"html\">\n        <text></text>\n      </feedback>\n    </answer>\n"
        )

    parts.append(
        "    <createdby>\n      " + escape(author) + "\n    </createdby>\n"
    )
    parts.append("  </question>")
    return "".join(parts)


def render_multichoice(q: Question, author: str) -> str:
    # Multi-choice: multiple correct answers possible, <single>false</single>
    # Fractions: corrects share +100% equally; wrongs share -100% equally across wrongs
    corrects = [o for o in q.options if o.correct]
    wrongs = [o for o in q.options if not o.correct]

    pos_fraction = 100.0 / len(corrects) if corrects else 0.0
    neg_fraction = (-100.0 / len(wrongs)) if wrongs else 0.0

    parts = ["  <question type=\"multichoice\">\n"]
    parts.append(render_name(q.name))
    parts.append(wrap_question_text(q.text))
    parts.append(default_blocks(q.points))
    parts.append("    <single>false</single>\n")
    parts.append("    <shuffleanswers>true</shuffleanswers>\n")
    parts.append("    <answernumbering>none</answernumbering>\n")
    parts.append("    <showstandardinstruction>1\n    </showstandardinstruction>\n")
    parts.append(empty_feedback_blocks())

    for o in q.options:
        frac = pos_fraction if o.correct else neg_fraction
        parts.append(
            "    <answer fraction=\"{0:g}\" format=\"html\">\n      <text>{1}</text>\n      <feedback format=\"html\">\n        <text></text>\n      </feedback>\n    </answer>\n".format(
                frac, html_cdata(o.text)
            )
        )

    parts.append(
        "    <createdby>\n      " + escape(author) + "\n    </createdby>\n"
    )
    parts.append("  </question>")
    return "".join(parts)


def render_matching(q: Question, author: str) -> str:
    parts = ["  <question type=\"matching\">\n"]
    parts.append(render_name(q.name))
    parts.append(wrap_question_text(q.text))
    parts.append(default_blocks(q.points))
    parts.append("    <shuffleanswers>true</shuffleanswers>\n")
    parts.append(empty_feedback_blocks())

    for left, right in q.pairs:
        parts.append(
            "    <subquestion format=\"html\">\n"
            f"      <text>{html_cdata(left)}</text>\n"
            "      <answer>\n"
            f"        <text>{escape(right)}</text>\n"
            "      </answer>\n"
            "    </subquestion>\n"
        )

    parts.append(
        "    <createdby>\n      " + escape(author) + "\n    </createdby>\n"
    )
    parts.append("  </question>")
    return "".join(parts)


def render_cloze(q: Question, author: str) -> str:
    # Convert gaps in q.text from {<point>:<answer1>|<answer2>} to {<point>:SHORTANSWER:~=<answer1>~=<answer2>}
    # If no <point> prefix, default to 1: {SHORTANSWER:...} -> {1:SHORTANSWER:...}
    import re
    def cloze_gap_repl(match):
        pts = match.group('pts')
        body = match.group('body')
        answers = [a.strip() for a in body.split('|') if a.strip()]
        if not answers:
            return match.group(0)
        ans_str = '~=' + '~='.join(answers)
        pts_str = pts if pts is not None else '1'
        return f'{{{pts_str}:SHORTANSWER:{ans_str}}}'

    CLOZE_GAP_RE = re.compile(r'\{(?:(?P<pts>\d+(?:\.\d+)?):)?(?P<body>[^}]*)\}')
    cloze_text = CLOZE_GAP_RE.sub(cloze_gap_repl, q.text)

    parts = ["  <question type=\"cloze\">\n"]
    parts.append(render_name(q.name))
    parts.append(wrap_question_text(cloze_text))
    # Cloze in samples omit <defaultgrade>, leave penalty/hidden/idnumber
    parts.append("    <generalfeedback format=\"html\">\n      <text></text>\n    </generalfeedback>\n")
    parts.append("    <penalty>0.3333333</penalty>\n")
    parts.append("    <hidden>0</hidden>\n")
    parts.append("    <idnumber></idnumber>\n")
    parts.append(
        "    <createdby>\n      " + escape(author) + "\n    </createdby>\n"
    )
    parts.append("  </question>")
    return "".join(parts)


def render_truefalse(q: Question, author: str) -> str:
    # Minimal mapping using multichoice-like structure would be incorrect; implement truefalse tag shape
    # However, samples.xml provided patterns mainly for multichoice/matching/cloze/numerical.
    # Here, we render as a multichoice-compatible structure with single=true and fractions.
    # If a template is added to samples, this should be updated to mirror it exactly.
    correct_text = "True" if q.tf_answer else "False"
    options = [AnswerOption("True", correct=(correct_text == "True")), AnswerOption("False", correct=(correct_text == "False"))]
    proxy = Question(qtype="multichoice", name=q.name, text=q.text, points=q.points, options=options)
    return render_multichoice(proxy, author)


def render_shortanswer(q: Question, author: str) -> str:
    # Render as shortanswer per Moodle schema (simplified)
    parts = ["  <question type=\"shortanswer\">\n"]
    parts.append(render_name(q.name))
    parts.append(wrap_question_text(q.text))
    parts.append(default_blocks(q.points))
    parts.append("    <usecase>0</usecase>\n")
    for ans in q.short_answers:
        parts.append(
            "    <answer fraction=\"100\" format=\"moodle_auto_format\">\n"
            f"      <text>{escape(ans)}</text>\n"
            "      <feedback format=\"html\">\n        <text></text>\n      </feedback>\n"
            "    </answer>\n"
        )
    parts.append(
        "    <createdby>\n      " + escape(author) + "\n    </createdby>\n"
    )
    parts.append("  </question>")
    return "".join(parts)


def render_numerical(q: Question, author: str) -> str:
    parts = ["  <question type=\"numerical\">\n"]
    parts.append(render_name(q.name))
    parts.append(wrap_question_text(q.text))
    parts.append(default_blocks(q.points))
    parts.append(
        "    <answer fraction=\"100\" format=\"moodle_auto_format\">\n"
        f"      <text>{escape(q.numerical_answer or '')}</text>\n"
        "      <feedback format=\"html\">\n        <text></text>\n      </feedback>\n"
        "      <tolerance>0</tolerance>\n"
        "    </answer>\n"
    )
    parts.append("    <unitgradingtype>0</unitgradingtype>\n")
    parts.append("    <unitpenalty>0.1000000</unitpenalty>\n")
    parts.append("    <showunits>3</showunits>\n")
    parts.append("    <unitsleft>0</unitsleft>\n")
    parts.append(
        "    <createdby>\n      " + escape(author) + "\n    </createdby>\n"
    )
    parts.append("  </question>")
    return "".join(parts)


def render_essay(q: Question, author: str) -> str:
    parts = ["  <question type=\"essay\">\n"]
    parts.append(render_name(q.name))
    parts.append(
        "    <questiontext format=\"html\">\n"
        f"      <text>{html_cdata(q.text)}</text>\n"
        "    </questiontext>\n"
    )
    parts.append("    <generalfeedback format=\"html\">\n      <text></text>\n    </generalfeedback>\n")
    parts.append(f"    <defaultgrade>{q.points:.7f}</defaultgrade>\n")
    parts.append("    <penalty>0.0000000</penalty>\n")
    parts.append("    <hidden>0</hidden>\n")
    parts.append("    <idnumber></idnumber>\n")
    parts.append("    <responseformat>editor</responseformat>\n")
    parts.append("    <responserequired>1</responserequired>\n")
    parts.append("    <responsefieldlines>10</responsefieldlines>\n")
    parts.append("    <minwordlimit></minwordlimit>\n")
    parts.append("    <maxwordlimit></maxwordlimit>\n")
    parts.append("    <attachments>0</attachments>\n")
    parts.append("    <attachmentsrequired>0</attachmentsrequired>\n")
    parts.append("    <maxbytes>0</maxbytes>\n")
    parts.append("    <filetypeslist></filetypeslist>\n")
    parts.append(
        "    <graderinfo format=\"html\">\n"
        f"      <text>{html_cdata(q.graderinfo)}</text>\n"
        "    </graderinfo>\n"
    )
    parts.append("    <responsetemplate format=\"html\">\n      <text></text>\n    </responsetemplate>\n")
    parts.append(
        "    <createdby>\n      " + escape(author) + "\n    </createdby>\n"
    )
    parts.append("  </question>")
    return "".join(parts)
