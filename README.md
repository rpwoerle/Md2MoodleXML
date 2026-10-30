# Md2MoodleXML

CLI that converts Markdown quiz files into Moodle XML for import.

## What's new

- Questions can have an optional Moodle name using `|| <question title>`; without one, a shortened question-text name is used.
- Single-choice answers support percentage fractions, for example `- option [50%]`.
- Multi-choice options support explicit percentages; all options must specify a percentage and positive percentages must total 100%.
- Matching questions support distractor answers with an empty left side, such as `= distractor`.
- new AI-Text questions as essay questions supporting a separate AI grading prompt and marking scheme (see blow).
- new Drag-Drop-Image questions supporting image-based matching with draggable labels and configurable drop areas (see blow).
- Markdown conversion now documents support for math, formatting, links, tables, lists, code, and headings, with escaping rules for other text.

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
- `AI-Text`
- `Drag-Drop-Image`

### Type-specific syntax

- Single-choice: use `- option` lines. Mark the full-credit answer with `*`, or assign each option a percentage such as `- option [50%]`; at least one option must be marked `*` or `[100%]`. The percentage option allows for poll like or scale-based questions

  Example: How did you like the topic?

  - not so much [25%]
  - was ok [50%]
  - was good [75%]
  - great, loved it [100%]

  with 4 points max for this question, you get scaled answers (1-4, bad to good)
- Multi-choice: use `- option` lines and mark one or more answers with `*`. Alternatively, assign a percentage to every option, such as `- option [60%]` and `- another option [40%]`; positive percentages must total 100%, and negative percentages can specify negative percentages as penalties. Do not mix `*` with percentage values.; **Note** when using the `*` (star) option: Max points will be evenly divided between the starred answers. All others will get evenly divided negative 100% penalties (change in moodle, if this is too strict, or use percentages instead)
- Matching: use lines like `- left side = right side`; an empty left side can be written as `= right side` and will add  distractors (choices that are not to be used)
- Cloze: gaps must start with the points, e.g. `{3:answer}` or `{2:answer1|answer2}`; other braces are plain text (e.g. inside `$...$` math)
- Essay: the text after `Essay:` and before `||` is rendered as an `<h5>` heading, followed by the student-visible body. Optional grading guidance can be placed in `{...}` (braces inside math are ignored).
- AI-Text: the text after `AI-Text:` and before `||` is rendered as an `<h5>` heading, followed by any normal student-visible body text. Put the AI guiding prompt in `{AI-Prompt: ...}` and the marking scheme in `{MarkScheme: ...}`. See [samples/questions.md](samples/questions.md).
- Drag-Drop-Image: add `image = "image.png"`, `dropcount = 2`, and `dragtext = First label;Second label` lines below the heading. The image must be beside the Markdown file. Drop areas are numbered with their coordinates set to `0`; draggable labels are numbered in assigned to the drop areas in the order they appear. Additional draggables as distractors are allowed, but must be added at the end of the `dragtext` list. **Note: you must distribute the drop areas to the correct location on the image whithin moodle**. Otherwise this question will not work!

### Markdown formatting

Question text, answers and grader info are converted to simple HTML. For Cloze and Essay questions the whole body is converted; for the other types, any non-option lines below the heading (paragraphs, tables, ordered lists, unordered lists) are appended to the question text.


| Markdown                                                   | HTML / Moodle output                                                  |
| ---------------------------------------------------------- | --------------------------------------------------------------------- |
| `$x^2$`                                                    | `\(x^2\)` (inline math)                                               |
| `$$x^2$$`                                                  | `\[x^2\]` (display math)                                              |
| `<<x^2>>`                                                  | `\(x^2\)` (legacy formula syntax, with sub/superscript normalization) |
| `**bold**`, `*italic*`, `_italic_`, `~~strike~~`           | `<strong>`, `<em>`, `<del>`                                           |
| `` `code` `` and fenced ```` ``` ```` blocks               | `<code>`, `<pre><code>`                                               |
| `[text](url)`                                              | `<a href>`                                                            |
| `| a | b |` tables (with `---` separator, `:-:` alignment) | `<table>` with 5px cell padding                                       |
| indented`- item`, `* item`, `+ item`                       | `<ul><li>` (nested by indentation)                                    |
| `1. item`                                                  | `<ol><li>`                                                            |
| `# Heading` inside a body                                  | `<h1>`…`<h6>`                                                        |
| blank line                                                 | new`<p>` paragraph                                                    |
| single newline inside a paragraph                          | `<br>`                                                                |

#### Notes:

- `$` is only treated as math when the opening `$` is followed by non-whitespace, the closing `$` is preceded by non-whitespace and is not followed by a digit, so `costs $5 or $6` stays plain text. Make sure each formula has a closing `$`.
- Answer options, matching pairs and similar lines must start with `-` in the **first column**. Indented dashes are treated as regular Markdown bullets and convertedto unordered HTML lists.
- Tables, (un-)ordered lists in cloze, essay and AI-Text must start in the first line
- A dash inside a line (`text - more text`) is ordinary text.
- Everything else is HTML-escaped.
- The XML `<name>` and plain-text fields (matching right-hand answers, short-answer and numerical answers) are not converted.

## Output

- Writes `<basename>.xml` next to the source Markdown file, or into the chosen output folder. Use the moodle question import function.
- Writes UTF-8 XML to be imported into Moodle.
- Only processes Markdown files that start with `# Quiz`.
- Logs each handled file as `[run]`, `[done]`, or `[fail]`.

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
