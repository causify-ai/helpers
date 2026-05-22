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
from typing import cast, Dict, Tuple

from tqdm import tqdm

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hlint as hlint
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem


_LOG = logging.getLogger(__name__)


def _get_rules_for_topic(topic: str) -> Dict:
    """
    Get rules and templates for a given topic.

    :param topic: Topic name (e.g., 'coding', 'testing')
    :return: Dict with role, rules list, templates list, and other config
    """
    TOPIC_TO_INFO = {
        "bash": {
            "role": "role.coding.md",
            "rules": [],
            "templates": [],
        },
        "blog": {
            "role": "role.ai_researcher.md",
            "rules": [
                "blog.rules.md",
                "markdown.rules.md",
                "text.rules.bullet_points.md",
            ],
            "templates": [],
        },
        "book": {
            "role": "role.ai_researcher.md",
            "rules": ["book.rules.md"],
            "templates": [],
        },
        "coding": {
            "role": "role.coding.md",
            "rules": ["coding.rules.md"],
            "templates": ["code.template.py"],
        },
        "cxo_slidesformat": {
            "role": "role.ai_researcher.md",
            "rules": [],
            "templates": [],
        },
        "interactive_notebook": {
            "role": "role.notebook.md",
            "rules": [
                "interactive_notebook.rules.md",
                "notebook.rules.md",
            ],
            "templates": [
                "interactive_notebook.template.py",
                "interactive_notebook_utils_template.py",
            ],
        },
        "latex": {
            "role": "role.ai_researcher.md",
            "rules": ["latex.rules.md"],
            "templates": [],
        },
        "markdown": {
            "role": "role.ai_researcher.md",
            "rules": [
                "markdown.rules.md",
                "text.rules.bullet_points.md",
            ],
            "templates": [],
        },
        "notebook": {
            "role": "role.notebook.md",
            "rules": ["notebook.rules.md"],
            "templates": ["notebook.template.ipynb"],
        },
        "readme": {
            "role": "role.ai_researcher.md",
            "rules": ["readme.rules.md"],
            "templates": [],
        },
        "skill": {
            "role": "role.coding.md",
            "rules": ["skill.rules.md"],
            "templates": [],
        },
        "slides": {
            "role": "role.ai_researcher.md",
            "rules": ["slides.rules.md"],
            "templates": [],
        },
        "testing": {
            "role": "role.coding.md",
            "rules": ["testing.rules.md"],
            "templates": ["testing.template.py"],
        },
        "tool_X_in_30_mins": {
            "role": "role.coding.md",
            "rules": ["tool_X_in_30_mins.rules.md"],
            "templates": [],
        },
        "tool_X_in_60_mins": {
            "role": "role.coding.md",
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
    topic_info["role"] = ".claude/skills/%s" % topic_info["role"]
    topic_info["rules"] = [f".claude/skills/{r}" for r in topic_info["rules"]]
    topic_info["templates"] = [
        f".claude/templates/{t}" for t in topic_info["templates"]
    ]
    topic_info["run_jupytext"] = topic in ("notebook",)
    topic_info["run_lint"] = topic in (
        "readme",
        "markdown",
    )
    return topic_info


# TODO(ai_gp): Add unit tests for the functions.
def _infer_topic_from_filename(file_path: str) -> str:
    """
    Detect the file type and return the corresponding topic.

    :param file_path: Path to the file
    :return: topic (e.g., 'coding.format')
    """
    basename = os.path.basename(file_path)
    if basename.endswith(".ipynb"):
        topic = "notebook"
    elif basename.endswith(".md"):
        if basename.startswith("README"):
            topic = "readme"
        elif "_in_30_mins.md" in file_path:
            topic = "tool_X_in_30_mins"
        elif "_in_60_mins.md" in file_path:
            topic = "tool_X_in_60_mins"
        elif ".claude/skills/" in file_path:
            topic = "skill"
        else:
            topic = "markdown"
    elif basename.endswith(".py"):
        if basename.startswith("test_"):
            topic = "testing"
        else:
            topic = "coding"
    elif basename.endswith(".sh"):
        topic = "bash"
    elif basename.endswith(".tex"):
        topic = "latex"
    elif basename.endswith(".txt"):
        topic = "slides"
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
        prompt_parts.append(
            "You MUST look for each rule below that is not followed and apply them:"
        )
        for rule_file in rules:
            prompt_parts.append(f"- {rule_file}")
    if templates:
        prompt_parts.append("You MUST follow the templates below:")
        for template_file in templates:
            prompt_parts.append(f"- {template_file}")
    prompt_parts.append(
        "You MUST make sure not to change the behavior or the intent of the passed file"
    )
    txt = "\n".join(prompt_parts)
    return txt, topic_info


def _run_claude_code(
    prompt: str, file_path: str, *, dry_run: bool = False
) -> int:
    """
    Run Claude Code with the given prompt.

    :param prompt: Claude Code prompt
    :param dry_run: If True, print command but don't execute
    :return: Return code (0 on success, or subprocess return code)
    """
    # Add the file.
    hdbg.dassert_file_exists(file_path)
    # Create the prompt file.
    prompt += f"\n\nProcess the file {file_path} and make the changes according to the rules and conventions without asking questions to the user"
    _LOG.info("%s\n%s", hprint.frame("Prompt"), prompt)
    prompt_file = "tmp.lint_cc.prompt.txt"
    hio.to_file(prompt_file, prompt)
    #
    cmd_parts = [
        "claude",
        "-p",
        "--dangerously-skip-permissions",
        "--output-format=text",
        f"'Execute the file {prompt_file}'",
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
            topic = _infer_topic_from_filename(file_path)
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
