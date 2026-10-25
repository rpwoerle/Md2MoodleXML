import unittest
import xml.etree.ElementTree as ET

from parser import ParseError, parse_markdown_text
from xml_generator import questions_to_moodle_xml


class MultiChoicePercentageTests(unittest.TestCase):
    def test_renders_explicit_percentages_for_options(self) -> None:
        questions = parse_markdown_text(
            "# Quiz\n"
            "## Multi-choice: Select all correct answers\n"
            "- Correct answer [70%]\n"
            "- Another correct answer [30%]\n"
            "- Incorrect answer [-100%]\n"
        )

        question = ET.fromstring(questions_to_moodle_xml(questions, author="test")).find("question")
        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(
            [answer.attrib["fraction"] for answer in question.findall("answer")],
            ["70", "30", "-100"],
        )

    def test_rejects_positive_percentages_not_adding_to_100(self) -> None:
        with self.assertRaisesRegex(
            ParseError,
            r"Positive Multi-choice percentages add up to 90%, which is 10% short of 100%",
        ):
            parse_markdown_text(
                "# Quiz\n"
                "## Multi-choice: Select all correct answers\n"
                "- Correct answer [60%]\n"
                "- Another correct answer [30%]\n"
                "- Incorrect answer [-100%]\n"
            )

    def test_treats_three_33_percent_answers_as_thirds(self) -> None:
        questions = parse_markdown_text(
            "# Quiz\n"
            "## Multi-choice: Select all correct answers\n"
            "- First correct answer [33%]\n"
            "- Second correct answer [33%]\n"
            "- Third correct answer [33%]\n"
            "- Incorrect answer [-100%]\n"
        )

        question = ET.fromstring(questions_to_moodle_xml(questions, author="test")).find("question")
        self.assertIsNotNone(question)
        assert question is not None
        fractions = [float(answer.attrib["fraction"]) for answer in question.findall("answer")]
        for fraction in fractions[:3]:
            self.assertAlmostEqual(fraction, 100 / 3, places=7)
        self.assertEqual(fractions[3], -100)

    def test_accepts_percentage_without_space_before_bracket(self) -> None:
        questions = parse_markdown_text(
            "# Quiz\n"
            "## Multi-choice: Select all correct answers\n"
            "- First correct answer[33%]\n"
            "- Second correct answer [33%]\n"
            "- Third correct answer [33%]\n"
            "- Incorrect answer[-100%]\n"
        )

        self.assertEqual([option.fraction for option in questions[0].options], [100 / 3, 100 / 3, 100 / 3, -100])

    def test_requires_percentage_for_every_option_in_explicit_mode(self) -> None:
        with self.assertRaisesRegex(ParseError, "Every Multi-choice option must specify a percentage"):
            parse_markdown_text(
                "# Quiz\n"
                "## Multi-choice: Select all correct answers\n"
                "- Correct answer [100%]\n"
                "- Incorrect answer\n"
            )

    def test_rejects_star_combined_with_percentage(self) -> None:
        with self.assertRaisesRegex(ParseError, "cannot use both '\\*' and a percentage"):
            parse_markdown_text(
                "# Quiz\n"
                "## Multi-choice: Select all correct answers\n"
                "- Correct answer [100%]*\n"
                "- Incorrect answer [0%]\n"
            )

    def test_preserves_automatic_scoring_without_percentages(self) -> None:
        questions = parse_markdown_text(
            "# Quiz\n"
            "## Multi-choice: Select all correct answers\n"
            "- Correct answer*\n"
            "- Another correct answer*\n"
            "- Incorrect answer\n"
        )

        question = ET.fromstring(questions_to_moodle_xml(questions, author="test")).find("question")
        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(
            [answer.attrib["fraction"] for answer in question.findall("answer")],
            ["50", "50", "-100"],
        )


if __name__ == "__main__":
    unittest.main()
