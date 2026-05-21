#!/usr/bin/env -S uv run

# /// script
# dependencies = ["tqdm"]
# ///

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
from typing import cast, List, Optional, Tuple

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser


_LOG = logging.getLogger(__name__)


def _get_rules_for_topic(
    topic: str,
) -> Tuple[List[str], List[str]]:
    """
    Get rules and templates for a given topic.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Tuple of (rules list, templates list)
    """
    # TODO(ai_gp): Add a parameter "role" pointing to one of the files below
    # .claude/skills/role.ai_researcher.md
    # .claude/skills/role.python.md
    # TODO(ai_gp): In rules factor out the string .claude/skills/ so that it's added at the end
    # Same thing for template -> .claude/templates/
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
        TOPIC_TO_RULES,
        "Topic not found in rules",
    )
    rules_and_templates = TOPIC_TO_RULES[topic]
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
    # TODO(ai_gp): Add rules for
    # .claude/skills/blog.rules.md
    # .claude/skills/book.rules.md
    # .claude/skills/latex.rules.md
    # .claude/skills/readme.rules.md
    # .claude/skills/skill.rules.md
    # .claude/skills/tool_X_in_30_mins.rules.md
    # .claude/skills/tool_X_in_60_mins.rules.md
    # TODO(ai_gp): Keep the check in alphabetical order per topic.
    if basename.startswith("test_") and basename.endswith(".py"):
        topic = "testing"
    elif basename.endswith(".py"):
        topic = "coding"
    elif basename.endswith(".sh"):
        topic = "bash"
    elif basename.endswith(".md"):
        topic = "markdown"
    elif basename.endswith(".txt"):
        # Assume those are slides.
        topic = "slides"
    elif basename.endswith(".ipynb"):
        topic = "notebook"
    else:
        raise ValueError(f"Invalid topic for filename '{file_path}'")
    return topic


def _build_prompt(topic: str) -> str:
    """
    Build a Claude Code prompt for the given skill.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Prompt string
    """
    rules, templates = _get_rules_for_topic(topic)
    prompt_parts = []
    prompt_parts.append("You are a ...")
    if rules:
        prompt_parts.append("You MUST look for each rule below that is not followed and apply them:")
        for rule_file in rules:
            prompt_parts.append(f"- {rule_file}")
    if templates:
        prompt_parts.append("You MUST follow the templates below:")
        for template_file in templates:
            prompt_parts.append(f"- {template_file}")
    prompt_parts.append("You MUST make sure not to change the behavior or the intent of the passed file")
    txt = "\n".join(prompt_parts)
    return txt


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
    hparser.add_file_selection_args(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> int:
    """
    Main entry point.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # TODO(ai_gp): Use hgit.get_files_to_process to extract the files given the
    # command line options.
    files = hgit.get_files_to_process(args.modified)
    if args.topic and len(files) != 1:
        raise ValueError("--topic can only be used with a single file")
    _LOG.info("Processing %d file(s)", len(files))
    ret = 0
    for file_path in tqdm(files, desc="Processing files"):
        if args.topic:
            topic_str = args.topic
        else:
            topic = _detect_file_type(file_path)
            hdbg.dassert_is_not(topic, None, "Topic detection failed")
            topic_str = cast(str, topic)
        prompt = _build_prompt(topic_str)
        rc = _run_claude_code(prompt, dry_run=args.dry_run)
        ret |= rc
    return ret

#- I will pass you a Python file `<FILE.py>` paired with Jupyter notebook with
#  `Jupytext` using a `py:percent` format
#
#- Read the file with the conventions and guidelines
#  `.claude/skills/notebook.rules.md` and apply them without changing the intent
#  and behavior of the notebook
#
## Use Jupytext
#- Remember to modify only the Python file paired with Jupytext to the notebook
#  and then sync them with Jupytext


#- After all the transformations apply the linter
#  ```
#  > lint_txt.py -i <file>
#  ```
#


if __name__ == "__main__":
    ret = _main(_parse())
    exit(ret)
