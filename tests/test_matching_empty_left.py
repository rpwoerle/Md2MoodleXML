import unittest
import xml.etree.ElementTree as ET

from parser import parse_markdown_text
from xml_generator import questions_to_moodle_xml


class MatchingEmptyLeftTests(unittest.TestCase):
    def test_parses_empty_left_term_without_list_marker(self) -> None:
        questions = parse_markdown_text(
            "# Quiz\n"
            "## Matching: Match the terms\n"
            "- term 1 = answer 1\n"
            "= answer 2\n"
        )

        self.assertEqual(questions[0].pairs, [("term 1", "answer 1"), ("", "answer 2")])
        self.assertEqual(questions[0].points, 2.0)

        xml = questions_to_moodle_xml(questions, author="test")
        matching_question = ET.fromstring(xml).find("question")
        self.assertIsNotNone(matching_question)
        assert matching_question is not None
        subquestions = matching_question.findall("subquestion")
        self.assertEqual(subquestions[1].findtext("text"), "")
        self.assertEqual(subquestions[1].findtext("answer/text"), "answer 2")
        self.assertIn("Match the terms", matching_question.findtext("questiontext/text", ""))


if __name__ == "__main__":
    unittest.main()
