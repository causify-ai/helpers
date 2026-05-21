#!/usr/bin/env python

# TODO(ai_gp): Use the uv to install packages on the fly

"""
Format or lint files using Claude Code.

This script detects file types (by extension and path pattern) builds a prompt,
and invokes Claude Code with that prompt.

Examples:
# Lint Python .py files:
> lint_cc.py file1.py file2.py

# Lint Python testing files test_*.py:
> lint_cc.py test_foo.py test_bar.py

# Call a specific set of rules on a single file:
> lint_cc.py --topic coding file.py

# Print the command without executing:
> lint_cc.py --dry_run *.md

# Run with debug logging:
> lint_cc.py *.py - DEBUG
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


def _get_rules_for_topic(
    topic: str,
) -> Tuple[List[str], List[str]]:
    """
    Get rules and templates for a given topic.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Tuple of (rules list, templates list)
    """
    # TODO(gp): Add role.
    #_PYTHON_ROLE = "You are 
    TOPIC_TO_RULES = {
        "skill": {
            "rules": [".claude/skills/skill.rules.md"],
            "templates": [],
        },
        "blog": {
            "rules": [
                ".claude/skills/blog.rules.md",
                ".claude/skills/markdown.rules.md",
                ".claude/skills/text.rules.bullet_points.md",
            ],
            "templates": [],
        },
        "slides": {
            "rules": [".claude/skills/slides.rules.md"],
            "templates": [],
        },
        "testing": {
            "rules": [".claude/skills/testing.rules.md"],
            "templates": [".claude/templates/testing.template.py"],
        },
        "coding": {
            "rules": [".claude/skills/coding.rules.md"],
            "templates": [".claude/templates/code.template.py"],
        },
        "bash": {
            "rules": [],
            "templates": [],
        },
        "notebook": {
            "rules": [".claude/skills/notebook.rules.md"],
            "templates": [".claude/templates/notebook_template.ipynb"],
        },
        "interactive_notebook": {
            "rules": [
                ".claude/skills/interactive_notebook.rules.md",
                ".claude/skills/notebook.rules.md",
            ],
            "templates": [
                ".claude/templates/interactive_notebook.template.py",
                ".claude/templates/interactive_notebook_utils_template.py",
            ],
        },
        "markdown": {
            "rules": [
                ".claude/skills/markdown.rules.md",
                ".claude/skills/text.rules.bullet_points.md",
            ],
            "templates": [],
        },
        "cxo_slidesformat": {
            "rules": [],
            "templates": [],
        },
        "tool_X_in_30_mins": {
            "rules": [".claude/skills/tool_X_in_30_mins.rules.md"],
            "templates": [],
        },
        "tool_X_in_60_mins": {
            "rules": [".claude/skills/tool_X_in_60_mins.rules.md"],
            "templates": [],
        },
    }
    hdbg.dassert_in(
        topic,
        TYPE_TO_RULES,
        "Topic not found in rules",
    )
    rules_and_templates = TYPE_TO_RULES[topic]
    rules = rules_and_templates["rules"]
    templates = rules_and_templates["templates"]
    return (rules, templates)


def _detect_file_type(file_path: str) -> Optional[str]:
    """
    Detect the file type and return the corresponding skill name.

    :param file_path: Path to the file
    :return: Skill name (e.g., 'coding.format') or None if no match found
    """
    basename = os.path.basename(file_path)
    if basename.startswith("test_") and f.endswith(".py"):
        topic = "testing.format"
    elif basename.endswith(".py"):
        topic ="coding.format"
    # TODO(ai_gp): Add this.
    #    (lambda f: f.endswith(".sh"), "bash.format"),
    #    (lambda f: f.endswith(".md"), "markdown.format"),
    #    (lambda f: f.endswith(".ipynb"), "notebook.format"),
    return topic


def _build_prompt(file, topic) -> str:
    """
    Build a Claude Code prompt for the given skill and files.

    :return: Prompt string
    """
    # TODO(ai_gp): Create a prompt using a role, a set of rules and templates.
    return 


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
    # TODO(ai_gp): Add add_file_selection_args
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
    _LOG.info("Processing %d file(s) with %s", len(files), skill)
    for file in tqdm(files, desc="Processing files"):
        if args.topic:
            topic = args.topic
        else:
            topic = _detect_file_type(file)
        prompt = _build_prompt(file, topic)
        rc = _run_claude_code(prompt, dry_run=args.dry_run)
        ret |= rc
    return ret


if __name__ == "__main__":
    _main(_parse())
