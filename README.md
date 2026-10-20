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
## <Type Prefix>: <Question text> || <question title> [points]
```

The points part is optional. Defaults are:

- 4 points for most question types
- number of pairs for matching questions
- sum of Cloze gap points for Cloze questions

The question title is optional. If omitted, Moodle uses an abbreviated version of the question text as the question name.

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

- Single-choice: use `- option` lines. Mark the full-credit answer with `*`, or assign each option a percentage such as `- option [50%]`; at least one option must be marked `*` or `[100%]`.
- Multi-choice: use `- option` lines and mark one or more answers with `*`
- Matching: use lines like `- left side = right side`
- Cloze: gaps must start with the points, e.g. `{1:answer}` or `{2:answer1|answer2}`; other braces are plain text (e.g. inside `$...$` math)
- Essay: place the student-visible prompt in the body and optional grading guidance in `{...}` (braces inside math are ignored)

Answer options, matching pairs and similar lines must start with `-` in the **first column**. Indented dashes are regular Markdown bullets (see below).

### Markdown formatting

Question text, answers and grader info are converted to simple HTML. For Cloze and Essay questions the whole body is converted; for the other types, any non-option lines below the heading (paragraphs, tables, `*` / `1.` lists, indented `-` lists) are appended to the question text.

| Markdown | HTML / Moodle output |
| --- | --- |
| `$x^2$` | `\(x^2\)` (inline math) |
| `$$x^2$$` | `\[x^2\]` (display math) |
| `<<x^2>>` | `\(x^2\)` (legacy formula syntax, with sub/superscript normalization) |
| `**bold**`, `*italic*`, `_italic_`, `~~strike~~` | `<strong>`, `<em>`, `<del>` |
| `` `code` `` and fenced ```` ``` ```` blocks | `<code>`, `<pre><code>` |
| `[text](url)` | `<a href>` |
| `\| a \| b \|` tables (with `---` separator, `:-:` alignment) | `<table>` |
| indented `- item`, `* item`, `+ item` | `<ul><li>` (nested by indentation) |
| `1. item` | `<ol><li>` |
| `# Heading` inside a body | `<h1>`…`<h6>` |
| blank line | new `<p>` paragraph |
| single newline inside a paragraph | `<br>` |

Notes:

- `$` is only treated as math when the opening `$` is followed by non-whitespace, the closing `$` is preceded by non-whitespace and is not followed by a digit, so `costs $5 or $6` stays plain text. Make sure each formula has a closing `$`.
- A dash inside a line (`text - more text`) is ordinary text.
- Everything else is HTML-escaped.
- The XML `<name>` and plain-text fields (matching right-hand answers, short-answer and numerical answers) are not converted.

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

This project has been developed with major support from the GitHub Copilot KI Agent. Always review code and outputs and verify operation in your context before relying on the results.

## Project structure

```text
Md2MoodleXML/
├── md2moodlexml.py
├── parser.py
├── mdhtml.py
├── xml_generator.py
├── samples/
│   ├── questions.md
│   └── questions.xml
└── README.md
```
