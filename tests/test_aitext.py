import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from mdhtml import block_html
from parser import parse_markdown_text
from xml_generator import questions_to_moodle_xml


class MarkdownBlockHTMLTests(unittest.TestCase):
    def test_blank_lines_render_as_empty_paragraphs(self) -> None:
        self.assertEqual(
            block_html("First paragraph.\n\n\nSecond paragraph."),
            "<p>First paragraph.</p>\n<p></p>\n<p></p>\n<p>Second paragraph.</p>",
        )

    def test_table_cells_have_five_pixel_padding(self) -> None:
        self.assertEqual(
            block_html("| Left | Right |\n| :--- | ---: |\n| a | b |"),
            '<table border="1">\n<thead><tr><th style="text-align: left; padding: 5px;">Left</th>'
            '<th style="text-align: right; padding: 5px;">Right</th></tr></thead>\n<tbody>\n'
            '<tr><td style="text-align: left; padding: 5px;">a</td>'
            '<td style="text-align: right; padding: 5px;">b</td></tr>\n</tbody>\n</table>',
        )


class EssayAITextTests(unittest.TestCase):
    def test_questions_sample_uses_heading_and_tagged_ai_fields(self) -> None:
        sample_path = Path(__file__).parents[1] / "samples" / "questions.md"
        markdown = sample_path.read_text(encoding="utf-8")
        questions = parse_markdown_text(markdown, source=str(sample_path))
        xml = ET.fromstring(questions_to_moodle_xml(questions, author="test"))
        expected_xml = ET.parse(sample_path.with_suffix(".xml")).getroot()
        essay = xml.find("question[@type='essay']")
        ai_text = xml.find("question[@type='aitext']")
        expected_essay = expected_xml.find("question[@type='essay']")
        expected_ai_text = expected_xml.find("question[@type='aitext']")

        self.assertIsNotNone(essay)
        self.assertIsNotNone(ai_text)
        self.assertIsNotNone(expected_essay)
        self.assertIsNotNone(expected_ai_text)
        assert essay is not None
        assert ai_text is not None
        assert expected_essay is not None
        assert expected_ai_text is not None
        self.assertTrue(
            (essay.findtext("questiontext/text") or "").startswith(
                "<h5>Erarbeite möglichst physikalisch genau"
            )
        )
        self.assertIn("<table", essay.findtext("questiontext/text") or "")
        self.assertEqual(
            ai_text.findtext("questiontext/text"),
            "<h5>Erläutere kurz was das Internet und was das World-Wide-Web (WWW) ist.</h5>\n"
            "<p>Gehe dabei auch auf die unterschiedlichen Adressierung (URL und IP-Adresse) ein.</p>",
        )
        self.assertIn("INTERNET:", ai_text.findtext("aiprompt") or "")
        self.assertIn("Für jeden fehlenden Begriff", ai_text.findtext("markscheme") or "")
        self.assertEqual(
            essay.findtext("questiontext/text"),
            expected_essay.findtext("questiontext/text"),
        )
        self.assertEqual(
            ai_text.findtext("questiontext/text"),
            expected_ai_text.findtext("questiontext/text"),
        )
        self.assertEqual(ai_text.findtext("aiprompt"), expected_ai_text.findtext("aiprompt"))
        self.assertEqual(
            ai_text.findtext("markscheme"),
            expected_ai_text.findtext("markscheme"),
        )

    def test_essay_heading_and_body_are_question_text(self) -> None:
        markdown = (
            "# Quiz\n"
            "## Essay: Work through the task.||Essay [3]\n"
            "Give the result.\n"
            "{Use criteria & accuracy.}\n"
        )

        questions = parse_markdown_text(markdown)
        question = ET.fromstring(
            questions_to_moodle_xml(questions, author="test")
        ).find("question")

        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(question.findtext("name/text"), "Essay")
        self.assertEqual(
            question.findtext("questiontext/text"),
            "<h5>Work through the task.</h5>\n<p>Give the result.</p>",
        )
        self.assertEqual(
            question.findtext("graderinfo/text"),
            "<p>Use criteria &amp; accuracy.</p>",
        )

    def test_aitext_heading_body_and_tagged_grading_fields(self) -> None:
        markdown = (
            "# Quiz\n"
            "## AI-Text: Explain the topic.||AI [4]\n"
            "Add normal instruction & details.\n"
            "{AI-Prompt: Expected <answer> & details.}\n"
            "{MarkScheme: Deduct half a point for each error.}\n"
        )

        questions = parse_markdown_text(markdown)
        question = ET.fromstring(
            questions_to_moodle_xml(questions, author="test")
        ).find("question")

        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(question.findtext("name/text"), "AI")
        self.assertEqual(
            question.findtext("questiontext/text"),
            "<h5>Explain the topic.</h5>\n<p>Add normal instruction &amp; details.</p>",
        )
        self.assertEqual(question.findtext("aiprompt"), "Expected <answer> & details.")
        self.assertEqual(
            question.findtext("markscheme"),
            "Deduct half a point for each error.",
        )

    def test_aitext_preserves_unrecognized_braces_and_math_in_body(self) -> None:
        questions = parse_markdown_text(
            "# Quiz\n"
            "## AI-Text: Explain this.\n"
            "Literal {text} and $x^{2}$ remain visible.\n"
            "{AI-Prompt: Grading expectation.}\n"
        )

        question = ET.fromstring(
            questions_to_moodle_xml(questions, author="test")
        ).find("question")

        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(
            question.findtext("questiontext/text"),
            "<h5>Explain this.</h5>\n<p>Literal {text} and \\(x^{2}\\) remain visible.</p>",
        )
        self.assertEqual(question.findtext("aiprompt"), "Grading expectation.")
        self.assertEqual(question.findtext("markscheme"), "")


if __name__ == "__main__":
    unittest.main()
