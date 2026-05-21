#!/usr/bin/env python

"""
Format or lint files using Claude Code's slash-command skills.

This script detects file types (by extension and path pattern), groups them
by their corresponding Claude Code skill, builds a prompt, and invokes
Claude Code with that skill.

Examples:
# Call /coding.format on .py files:
> lint_cc.py file1.py file2.py

# Call /testing.format on test_*.py:
> lint_cc.py test_foo.py test_bar.py

# Call a specific skill on a single file:
> lint_cc.py --topic coding.format file.py

# Print the command without executing:
> lint_cc.py --dry_run *.md

# Run with debug logging:
> lint_cc.py --log_level debug *.py
"""

import argparse
import logging
import os
import subprocess
from typing import Callable, Dict, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

_LOG = logging.getLogger(__name__)

_FILE_TYPE_RULES = {
    "skill.format": {
        "rules": [".claude/skills/skill.rules.md"],
        "templates": [],
    },
    "blog.format": {
        "rules": [
            ".claude/skills/blog.rules.md",
            ".claude/skills/markdown.rules.md",
            ".claude/skills/text.rules.bullet_points.md",
        ],
        "templates": [],
    },
    "slides.format": {
        "rules": [".claude/skills/slides.rules.md"],
        "templates": [],
    },
    "testing.format": {
        "rules": [".claude/skills/testing.rules.md"],
        "templates": [".claude/templates/testing.template.py"],
    },
    "coding.format": {
        "rules": [".claude/skills/coding.rules.md"],
        "templates": [".claude/templates/code.template.py"],
    },
    "bash.format": {
        "rules": [],
        "templates": [],
    },
    "notebook.format": {
        "rules": [".claude/skills/notebook.rules.md"],
        "templates": [".claude/templates/notebook_template.ipynb"],
    },
    "interactive_notebook.format": {
        "rules": [
            ".claude/skills/interactive_notebook.rules.md",
            ".claude/skills/notebook.rules.md",
        ],
        "templates": [
            ".claude/templates/interactive_notebook.template.py",
            ".claude/templates/interactive_notebook_utils_template.py",
        ],
    },
    "markdown.format": {
        "rules": [
            ".claude/skills/markdown.rules.md",
            ".claude/skills/text.rules.bullet_points.md",
        ],
        "templates": [],
    },
    "cxo_slides.format": {
        "rules": [],
        "templates": [],
    },
    "notebook.lint": {
        "rules": [
            ".claude/skills/notebook.rules.md",
            ".claude/skills/interactive_notebook.rules.md",
        ],
        "templates": [],
    },
    "tool_X_in_30_mins.format": {
        "rules": [".claude/skills/tool_X_in_30_mins.rules.md"],
        "templates": [],
    },
    "tool_X_in_60_mins.format": {
        "rules": [".claude/skills/tool_X_in_60_mins.rules.md"],
        "templates": [],
    },
}


def _get_rules_for_topic(
    topic: str,
) -> Tuple[List[str], List[str]]:
    """
    Get rules and templates for a given topic.

    :param topic: Topic name (e.g., 'coding.format', 'testing.format')
    :return: Tuple of (rules list, templates list)
    """
    hdbg.dassert_in(
        topic,
        _FILE_TYPE_RULES,
        "Topic not found in rules",
    )
    rules_and_templates = _FILE_TYPE_RULES[topic]
    rules = rules_and_templates["rules"]
    templates = rules_and_templates["templates"]
    return (rules, templates)


_FILE_TYPE_MAP: List[Tuple[Callable[[str], bool], str]] = [
    (lambda f: f.startswith("test_") and f.endswith(".py"), "testing.format"),
    (lambda f: f.endswith(".py"), "coding.format"),
    (lambda f: f.endswith(".sh"), "bash.format"),
    (lambda f: f.endswith(".md"), "markdown.format"),
    (lambda f: f.endswith(".ipynb"), "notebook.format"),
]


def _detect_file_type(file_path: str) -> Optional[str]:
    """
    Detect the file type and return the corresponding skill name.

    :param file_path: Path to the file
    :return: Skill name (e.g., 'coding.format') or None if no match found
    """
    basename = os.path.basename(file_path)
    for pattern_fn, skill_name in _FILE_TYPE_MAP:
        if pattern_fn(basename):
            return skill_name
    return None


def _build_prompt(skill: str, files: List[str]) -> str:
    """
    Build a Claude Code prompt for the given skill and files.

    :param skill: Skill name (e.g., 'coding.format')
    :param files: List of file paths to process
    :return: Prompt string
    """
    _get_rules_for_topic(skill)
    prompt_parts = [f"/{skill}"]
    for file_path in files:
        prompt_parts.append(file_path)
    return " ".join(prompt_parts)


def _run_claude_code(prompt: str, *, dry_run: bool = False) -> int:
    """
    Run Claude Code with the given prompt.

    :param prompt: Claude Code prompt (e.g., '/coding.format file1.py file2.py')
    :param dry_run: If True, print command but don't execute
    :return: Return code (0 on success, or subprocess return code)
    """
    prompt_file = "tmp.lint_cc.prompt.txt"
    hio.to_file(prompt_file, prompt)
    cmd_parts = [
        "claude",
        "--dangerously-skip-permissions",
        "--output-format=text",
        f"-p={prompt}",
    ]
    cmd = " ".join(cmd_parts)
    _LOG.info("Claude command: %s", cmd)
    if dry_run:
        _LOG.info("Dry run: command not executed")
        return 0
    _LOG.debug("Executing: %s", cmd)
    result = subprocess.run(cmd_parts, capture_output=False)
    return result.returncode


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Files to format/lint",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Claude Code skill topic (e.g., 'coding.format'). "
        "Can only be used with a single file.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the command but don't execute",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> int:
    """
    Main entry point.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if args.topic and len(args.files) != 1:
        raise ValueError("--topic can only be used with a single file")
    groups: Dict[str, List[str]] = {}
    for file_path in args.files:
        hdbg.dassert_file_exists(file_path, "File not found")
        if args.topic:
            skill = args.topic
        else:
            skill = _detect_file_type(file_path)
            if skill is None:
                _LOG.warning("Could not detect file type for %s", file_path)
                continue
        if skill not in groups:
            groups[skill] = []
        groups[skill].append(file_path)
    ret = 0
    total_files = sum(len(files) for files in groups.values())
    pbar = tqdm(total=total_files, desc="Processing files") if tqdm else None
    try:
        for skill in sorted(groups.keys()):
            files = groups[skill]
            _LOG.info("Processing %d file(s) with %s", len(files), skill)
            prompt = _build_prompt(skill, files)
            rc = _run_claude_code(prompt, dry_run=args.dry_run)
            ret |= rc
            if pbar:
                pbar.update(len(files))
    finally:
        if pbar:
            pbar.close()
    return ret


if __name__ == "__main__":
    _main(_parse())
