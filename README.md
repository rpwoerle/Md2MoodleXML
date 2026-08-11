# Md2MoodleXML

CLI that converts Markdown quiz files into Moodle XML for import.

## Requirements

- Python 3.14+
- No external dependencies are required; optional `python-dotenv` support is available for loading a `.env` file

## Usage

```bash
python md2moodlexml.py samples/questions.md
```

### Options

- `--nooverwrite`: skip writing output if the XML file already exists
- `--author <text>`: set the `<createdby>` value in the generated XML
- `-o, --output <folder>`: write generated XML files into a specific folder

## Markdown input format

The input file must start with `# Quiz`.

Each question starts with a heading in the form:

```markdown
## <Type Prefix>: <Question text> [points]
```

The points part is optional. Defaults are:

- 4 points for most question types
- number of pairs for matching questions
- sum of Cloze gap points for Cloze questions

### Supported question types

- `Single-choice`
- `Multi-choice`
- `Matching`
- `Cloze`
- `True/False`
- `Short Answer`
- `Numerical`
- `Essay`

### Type-specific syntax

- Single-choice: use `- option` lines and mark exactly one answer with `*`
- Multi-choice: use `- option` lines and mark one or more answers with `*`
- Matching: use lines like `- left side = right side`
- Cloze: use gaps such as `{answer}` or `{2:answer1|answer2}`
- Essay: place the student-visible prompt in the body and optional grading guidance in `{...}`

## Output

- Writes `<basename>.xml` next to the source Markdown file, or into the chosen output folder
- Writes UTF-8 XML
- Only processes Markdown files that start with `# Quiz`
- Logs each handled file as `[run]`, `[done]`, or `[fail]`

## Author override

You can set a default author in a `.env` file:

```env
TEXT2MOODLE_AUTHOR=Your Name
```

The CLI `--author` value overrides the `.env` value.

## Disclaimer

This project is provided as-is, without warranty of any kind, express or implied. The developers and contributors shall not be liable for any damages, losses, or issues arising from the use of this software.

## Acknowledgement

This project has been developed with major support from the GitHub Copilot Agent. So use with appropriate caution.

## Project structure

```text
Md2MoodleXML/
├── md2moodlexml.py
├── parser.py
├── xml_generator.py
├── samples/
│   ├── questions.md
│   └── questions.xml
└── README.md
```
