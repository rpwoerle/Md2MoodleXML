from __future__ import annotations

import argparse
import glob
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import os

# Optional support for python-dotenv if available
try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None  # type: ignore

from parser import parse_markdown_file, ParseError, is_quiz_file
from xml_generator import questions_to_moodle_xml


@dataclass
class Args:
    inputs: List[str]
    nooverwrite: bool
    author: str
    output: Optional[Path]


def validate_markdown_input(value: str) -> str:
    normalized = value.replace("\\", "/")
    if "**" in normalized:
        raise argparse.ArgumentTypeError("recursive patterns using '**' are not supported")
    if not normalized.lower().endswith(".md"):
        raise argparse.ArgumentTypeError("input must be a .md file path or a .md glob pattern")
    path = Path(value)
    if path.exists() and path.is_dir():
        raise argparse.ArgumentTypeError("directory inputs are not supported; pass a .md file path or pattern")
    return value


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert markdown quizzes to Moodle XML")
    p.add_argument(
        "inputs",
        nargs="+",
        type=validate_markdown_input,
        help=".md file paths or non-recursive .md glob patterns",
    )
    p.add_argument("--nooverwrite", action="store_true", help="Do not overwrite existing XML files")
    p.add_argument(
        "--author",
        help="Author string to include in <createdby> tags (overrides .env TEXT2MOODLE_AUTHOR)",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional output folder; writes <basename>.xml here instead of next to the source",
    )
    return p


def expand_inputs(inputs: Iterable[str]) -> List[Path]:
    paths: List[Path] = []
    cwd = Path.cwd()
    for item in inputs:
        item_path = Path(item)
        resolved_input = item_path if item_path.is_absolute() else (cwd / item_path)
        if any(ch in item for ch in ["*", "?", "["]):
            for match in glob.glob(str(resolved_input)):
                match_path = Path(match)
                if match_path.is_file() and match_path.suffix.lower() == ".md":
                    paths.append(match_path)
        else:
            paths.append(resolved_input)
    return paths


def load_env_author() -> Optional[str]:
    """Load author from .env or environment variable.

    Precedence outside of CLI: .env TEXT2MOODLE_AUTHOR, then OS env TEXT2MOODLE_AUTHOR.
    """
    # First see if OS env already defines it
    env_author = os.environ.get("TEXT2MOODLE_AUTHOR")

    # If python-dotenv is available, use it to load .env (without overriding OS env)
    if load_dotenv is not None:
        try:
            load_dotenv(override=False)
            return os.environ.get("TEXT2MOODLE_AUTHOR") or env_author
        except Exception:
            # Ignore and fall back to manual parsing
            pass

    # Manual .env parsing if python-dotenv isn't available
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == "TEXT2MOODLE_AUTHOR":
                    return value
        except Exception:
            # Ignore .env parse errors and fall back
            pass
    return env_author


def iter_markdown_files(paths: Iterable[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_file() and p.suffix.lower() == ".md":
            yield p


def target_xml_path(md_path: Path, output_dir: Optional[Path]) -> Path:
    if output_dir is None:
        return md_path.with_suffix(".xml")
    # Write into provided directory, preserving only the basename
    return output_dir / f"{md_path.stem}.xml"


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ns = build_parser().parse_args(argv)
    # Determine author precedence: CLI --author > .env TEXT2MOODLE_AUTHOR > default
    default_author = "none"
    env_author = load_env_author()
    author_val = ns.author if ns.author else (env_author if env_author else default_author)
    args = Args(inputs=ns.inputs, nooverwrite=ns.nooverwrite, author=author_val, output=ns.output)

    # Resolve .md file paths and non-recursive .md glob matches.
    input_paths = expand_inputs(args.inputs)
    handled_any = False

    for md in iter_markdown_files(input_paths):
        if not is_quiz_file(md):
            # Skip silently as per instructions (no [skip] log required)
            continue
        handled_any = True
        print(f"[run] {md}")
        try:
            questions = parse_markdown_file(md)
            xml = questions_to_moodle_xml(questions, author=args.author)

            out_path = target_xml_path(md, args.output)
            # Ensure output directory exists if specified
            if args.output is not None:
                args.output.mkdir(parents=True, exist_ok=True)
            if out_path.exists() and args.nooverwrite:
                print(f"[fail] {md}: output exists and --nooverwrite set")
                continue
            out_path.write_text(xml, encoding="utf-8")
            print(f"[done] {out_path}")
        except ParseError as e:
            print(f"[fail] {md}: {e}")
        except Exception as e:
            print(f"[fail] {md}: {e}")

    if not handled_any:
        print(
            "No matching .md quiz files found (ensure paths are correct, patterns are non-recursive, and files start with '# Quiz')",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
