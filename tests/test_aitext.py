import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from parser import parse_markdown_text
from xml_generator import questions_to_moodle_xml


class AITextTests(unittest.TestCase):
    def test_matches_sample_aitext_structure_and_content(self) -> None:
        samples = Path(__file__).parents[1] / "samples"
        markdown = (samples / "question_new.md").read_text(encoding="utf-8")
        expected_xml = ET.parse(samples / "question_new.xml").getroot()

        questions = parse_markdown_text(markdown)
        xml = ET.fromstring(questions_to_moodle_xml(questions, author="test"))
        question = xml.find("question")
        expected_question = expected_xml.find("question")

        self.assertIsNotNone(question)
        self.assertIsNotNone(expected_question)
        assert question is not None
        assert expected_question is not None
        self.assertEqual(question.attrib["type"], "aitext")
        self.assertEqual(question.findtext("name/text"), expected_question.findtext("name/text"))
        expected_question_text = expected_question.findtext("questiontext/text") or ""
        expected_question_text = expected_question_text.replace("\u00a0</h5>", "</h5>")
        self.assertEqual(question.findtext("questiontext/text"), expected_question_text)
        self.assertEqual(question.findtext("aiprompt"), expected_question.findtext("aiprompt"))
        self.assertEqual(question.findtext("markscheme"), expected_question.findtext("markscheme"))
        self.assertEqual(question.findtext("defaultgrade"), "4.0000000")
        self.assertEqual(question.findtext("penalty"), "0.0000000")
        for tag in (
            "responseformat",
            "responsefieldlines",
            "minwordlimit",
            "maxwordlimit",
            "graderinfo",
            "responsetemplate",
            "model",
            "spellcheck",
        ):
            self.assertEqual(question.findtext(tag), expected_question.findtext(tag))

    def test_escapes_prompt_and_mark_scheme_as_xml_text(self) -> None:
        questions = parse_markdown_text(
            "# Quiz\n"
            "## AI-Text: Explain this\n"
            "Prompt & <context>\n"
            "{Use <criteria> & examples.}\n"
        )

        question = ET.fromstring(questions_to_moodle_xml(questions, author="test")).find("question")
        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(question.findtext("aiprompt"), "Prompt & <context>")
        self.assertEqual(question.findtext("markscheme"), "Use <criteria> & examples.")


if __name__ == "__main__":
    unittest.main()
