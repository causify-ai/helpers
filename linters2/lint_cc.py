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
from typing import cast, Dict, Optional, Tuple

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hparser as hparser
import helpers.hsystem as hsystem


_LOG = logging.getLogger(__name__)


def _get_rules_for_topic(topic: str) -> Dict:
    """
    Get rules and templates for a given topic.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Dict with role, rules list, templates list, and other config
    """
    TOPIC_TO_INFO = {
        "skill": {
            "role": "python",
            "rules": ["skill.rules.md"],
            "templates": [],
        },
        "blog": {
            "role": "ai_researcher",
            "rules": [
                "blog.rules.md",
                "markdown.rules.md",
                "text.rules.bullet_points.md",
            ],
            "templates": [],
        },
        "book": {
            "role": "ai_researcher",
            "rules": ["book.rules.md"],
            "templates": [],
        },
        "slides": {
            "role": "ai_researcher",
            "rules": ["slides.rules.md"],
            "templates": [],
        },
        "testing": {
            "role": "python",
            "rules": ["testing.rules.md"],
            "templates": ["testing.template.py"],
        },
        "coding": {
            "role": "python",
            "rules": ["coding.rules.md"],
            "templates": ["code.template.py"],
        },
        "bash": {
            "role": "python",
            "rules": [],
            "templates": [],
        },
        "latex": {
            "role": "ai_researcher",
            "rules": ["latex.rules.md"],
            "templates": [],
        },
        "notebook": {
            "role": "python",
            "rules": ["notebook.rules.md"],
            "templates": ["notebook_template.ipynb"],
        },
        "interactive_notebook": {
            "role": "python",
            "rules": [
                "interactive_notebook.rules.md",
                "notebook.rules.md",
            ],
            "templates": [
                "interactive_notebook.template.py",
                "interactive_notebook_utils_template.py",
            ],
        },
        "markdown": {
            "role": "ai_researcher",
            "rules": [
                "markdown.rules.md",
                "text.rules.bullet_points.md",
            ],
            "templates": [],
        },
        "readme": {
            "role": "ai_researcher",
            "rules": ["readme.rules.md"],
            "templates": [],
        },
        "cxo_slidesformat": {
            "role": "ai_researcher",
            "rules": [],
            "templates": [],
        },
        "tool_X_in_30_mins": {
            "role": "ai_researcher",
            "rules": ["tool_X_in_30_mins.rules.md"],
            "templates": [],
        },
        "tool_X_in_60_mins": {
            "role": "ai_researcher",
            "rules": ["tool_X_in_60_mins.rules.md"],
            "templates": [],
        },
    }
    hdbg.dassert_in(
        topic,
        TOPIC_TO_INFO,
        "Topic not found in rules",
    )
    topic_info = TOPIC_TO_INFO[topic]
    topic_info["role"] = f".claude/skills/role.%s.md" % topic_info["role"]
    topic_info["rules"] = [f".claude/skills/{r}" for r in topic_info["rules"]]
    topic_info["templates"] = [f".claude/templates/{t}" for t in topic_info["templates"]]
    topic_info["run_jupytext"] = topic in ("notebook", )
    topic_info["run_lint"] = topic in ("readme", "markdown", )
    return topic_info


def _detect_file_type(file_path: str) -> Optional[str]:
    """
    Detect the file type and return the corresponding skill name.

    :param file_path: Path to the file
    :return: Skill name (e.g., 'coding.format') or None if no match found
    """
    basename = os.path.basename(file_path)
    if basename.startswith("test_") and basename.endswith(".py"):
        topic = "testing"
    elif basename.endswith(".py"):
        topic = "coding"
    elif basename.endswith(".sh"):
        topic = "bash"
    elif basename.startswith("README") and basename.endswith(".md"):
        topic = "readme"
    elif basename.endswith("_in_30_mins.md"):
        topic = "tool_X_in_30_mins"
    elif basename.endswith("_in_60_mins.md"):
        topic = "tool_X_in_60_mins"
    elif basename.endswith(".tex"):
        topic = "latex"
    elif basename.endswith(".md"):
        topic = "markdown"
    elif basename.endswith(".txt"):
        topic = "slides"
    elif basename.endswith(".ipynb"):
        topic = "notebook"
    else:
        raise ValueError(f"Invalid topic for filename '{file_path}'")
    return topic


def _build_prompt(topic: str) -> Tuple[str, Dict]:
    """
    Build a Claude Code prompt for the given skill.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Tuple of (prompt string, topic_info dict)
    """
    topic_info = _get_rules_for_topic(topic)
    role = topic_info["role"]
    rules = topic_info["rules"]
    templates = topic_info["templates"]
    prompt_parts = []
    hdbg.dassert_file_exists(role, "Role file not found")
    role_content = hio.from_file(role)
    prompt_parts.append(role_content)
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
    return txt, topic_info


def _run_claude_code(prompt: str, file_path: str, *, dry_run: bool = False) -> int:
    """
    Run Claude Code with the given prompt.

    :param prompt: Claude Code prompt
    :param dry_run: If True, print command but don't execute
    :return: Return code (0 on success, or subprocess return code)
    """
    # Add the file.
    hdbg.dassert_file_exists(file_path)
    prompt += f"\nThe file to process is {file_path}"
    _LOG.info("Prompt:\n%s", prompt)
    # Create the file.
    prompt_file = "tmp.lint_cc.prompt.txt"
    hio.to_file(prompt_file, prompt)
    #
    cmd_parts = [
        "claude",
        "-p",
        "--dangerously-skip-permissions",
        "--output-format=text",
        f"'Execute the file {prompt_file}'"
    ]
    cmd = " ".join(cmd_parts)
    _LOG.info("Claude command: %s", cmd)
    if dry_run:
        _LOG.info("Dry run: command not executed")
        return 0
    _LOG.debug("Executing: %s", " ".join(cmd_parts[:4]))
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
    all_files = False
    mutually_exclusive = True
    remove_dirs = False
    files = hgit.get_files_to_process(
        args.modified,
        args.branch,
        args.last_commit,
        all_files,
        args.files,
        mutually_exclusive,
        remove_dirs,
    )
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
        prompt, topic_info = _build_prompt(topic_str)
        rc = _run_claude_code(prompt, file_path, dry_run=args.dry_run)
        ret |= rc
        # Post-process.
        if topic_info["run_jupytext"]:
            cmd = ["jupytext", "--sync", file_path]
            hsystem.system(" ".join(cmd))
        if topic_info["run_lint"]:
            hlint.lint_file(file_path)
    return ret


if __name__ == "__main__":
    ret = _main(_parse())
    exit(ret)
