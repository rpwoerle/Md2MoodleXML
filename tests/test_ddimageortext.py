import base64
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from parser import ParseError, parse_markdown_file
from xml_generator import questions_to_moodle_xml


class DragDropImageTests(unittest.TestCase):
    def test_parses_and_renders_drag_drop_image_question(self) -> None:
        image_data = b"test-image-data"
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "quiz.md"
            image = Path(temp_dir) / "test image.png"
            image.write_bytes(image_data)
            source.write_text(
                "# Quiz\n"
                "## Drag-Drop-Image: Match these labels || Example [3]\n"
                'image = "test image.png"\n'
                "dropcount = 2\n"
                "dragtext = First label;Second label;Unused label\n",
                encoding="utf-8",
            )

            questions = parse_markdown_file(source)
            xml = questions_to_moodle_xml(questions, author="test")

        question = ET.fromstring(xml).find("question")
        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(question.attrib["type"], "ddimageortext")
        self.assertEqual(question.findtext("name/text"), "Example")
        self.assertEqual(question.findtext("defaultgrade"), "3.0000000")
        self.assertIsNotNone(question.find("shuffleanswers"))

        image_element = question.find("file")
        self.assertIsNotNone(image_element)
        assert image_element is not None
        self.assertEqual(image_element.attrib, {"name": "test image.png", "encoding": "base64"})
        self.assertEqual(base64.b64decode(image_element.text or ""), image_data)

        drags = question.findall("drag")
        self.assertEqual([drag.findtext("no") for drag in drags], ["1", "2", "3"])
        self.assertEqual([drag.findtext("text") for drag in drags], ["First label", "Second label", "Unused label"])
        self.assertEqual([drag.findtext("draggroup") for drag in drags], ["1", "1", "1"])

        drops = question.findall("drop")
        self.assertEqual([drop.findtext("no") for drop in drops], ["1", "2"])
        self.assertEqual([drop.findtext("choice") for drop in drops], ["1", "2"])
        self.assertEqual([drop.findtext("xleft") for drop in drops], ["0", "0"])
        self.assertEqual([drop.findtext("ytop") for drop in drops], ["0", "0"])

    def test_requires_image_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "quiz.md"
            source.write_text(
                "# Quiz\n"
                "## Drag-Drop-Image: Match these labels\n"
                "image = missing.png\n"
                "dropcount = 1\n"
                "dragtext = Label\n",
                encoding="utf-8",
            )

            with self.assertRaises(ParseError):
                parse_markdown_file(source)


if __name__ == "__main__":
    unittest.main()
