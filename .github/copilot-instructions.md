# AI agent instructions for this repo

## Purpose
CLI that converts markdown quiz files into Moodle XML for import.

## Current state
Greenfield: no Python code yet. Use `samples/questions.md` and `samples/questions.xml` as the source of truth.

## Markdown input rules (parser)
- File must start with `# Quiz`.
- Question line: `## <Type Prefix>: <Question text> [<points>]` (points optional; default 4).
- Recognized type prefixes: `Single-choice`, `Multi-choice`, `Matching`, `Cloze`, `True/False`, `Short Answer`, `Numerical`.
- Use the question text as the XML question `<name><text>`.

Details by type:
- Single-choice: answers are `- option` with either a `*` suffix or a percentage suffix such as `- option [50%]` → `<single>true</single>`. A `*` means `fraction="100"`; percentage values map directly to Moodle fractions. At least one option must have `100%` or `*`.
- Multi-choice: answers are `- option` with `*` suffix marking corrects (can be multiple) → `<single>false</single>`. Fractions: split +100% equally across correct answers; split -100% equally across all wrong answers (i.e., wrong fractions sum to -100%).
- Matching: items as `- subquestion = answer`. Score 1 point per correct pair. Default grade = number of pairs unless an explicit `[points]` is provided.
- Cloze: gaps like `{answer}` or `{<points>:answer1|answer2}`. If points omitted for a gap, default 1. `|` separates acceptable answers for that gap.
- True/False, Short Answer, Numerical: follow the structures in `samples/questions.xml` (numerical example provided) using the question’s `[points]` (or default 4) as `<defaultgrade>`.

## XML output rules
- Root: `<quiz>`. Per question: `<question type="...">` with defaults:
  `<generalfeedback format="html"><text></text></generalfeedback>`, `<penalty>0.3333333</penalty>`, `<hidden>0</hidden>`, `<idnumber></idnumber>`.
- Wrap question text in HTML CDATA as in samples (`<questiontext format="html"><text><![CDATA[<p>...</p>]]></text></questiontext>`).
- Always include `<shuffleanswers>true</shuffleanswers>` where applicable and empty feedback blocks.
- `<defaultgrade>` equals the question’s `[points]` (Multi-choice/True-False/Short/Numerical) or derived per type (Matching = pairs, Cloze = sum of gap points).
- Only generate XML for questions that appear in the input markdown; omit any question types not present in the markdown.
- If the input markdown uses a recognized type that isn’t illustrated in `samples/questions.md`, mirror the tag structure in `samples/questions.xml` exactly (use it as the template).

## CLI behavior (to implement)
- Accept files, folders, and globs (supports `**`). Walk directories for `.md`.
- Skip `.md` files not starting with `# Quiz`.
- Write `<basename>.xml` alongside source (UTF-8). Overwrite unless `--nooverwrite`.
- Logging: print only the handled file and any error, e.g. `[run] file.md`, `[done] file.md`, `[fail] file.md: <error>`.

## Dev workflow (Windows)
- Use `./rundev.cmd` (selects Python 3.14 via `setpyver.cmd`, opens VS Code).
- `runapp.cmd` is outdated (references `transcribe.py`) — ignore/replace.

## Implementation sketch
Modules: CLI entry → file walker → markdown parser → XML generator. Keep XML defaults identical to `samples/questions.xml`. Multi-choice fractions: corrects share +100% equally; wrongs share -100% equally (sum to -100%).
