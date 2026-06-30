#!/usr/bin/env -S uv run

# /// script
# dependencies = ["tqdm"]
# ///

"""
Format or lint files using Claude Code.

This script:
- Detects file types (by extension and path pattern)
- Builds a prompt
- Invokes Claude Code with that prompt on the selected files

Examples:
# Lint specific Python files using the proper rule file (for Python files
# use `.claude/skills/coding.rules.md`):
> lint_cc.py --files "file1.py file2.py"

# Lint Python testing files (with `claude/skills/testing.rules.md`):
> lint_cc.py --files "test_foo.py test_bar.py"

# Files can be selected with --files, --from_file, --branch
> lint_cc.py --branch

# Lint modified files in the client:
> lint_cc.py --modified

# Call a specific topic rules on a single file (in this case
# `.claude/skills/coding.rules.md`)
> lint_cc.py --topic coding --files "file.py"

# Execute a skill on a single file:
> lint_cc.py --skill coding.fix_inline --files "file.py"

# Execute a rule on a single file using one of these formats:
# - Full path (path:line:header format with header validation)
#   ```
#   --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions"
#   ```
# - Line number only (extracts the section starting at that line)
#   ```
#   --rule ".claude/skills/coding.rules.md:58"
#   ```
# - Keyword search: (searches for unique matching rule using rigrule)
#   ```
#   --rule "dassert"
#   ```
> lint_cc.py --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions" --files "file.py"

# Print the command without executing:
> lint_cc.py --dry_run --files "*.md"

# Run with debug logging:
> lint_cc.py --files "*.py" -v DEBUG
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
import helpers.hmarkdown_select as hmarsele
import helpers.hselect_input_output as hseinout
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
                "text.rules.md",
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
            "templates": ["coding.template.py"],
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
                "text.rules.md",
            ],
            "templates": [],
        },
        "notebook": {
            "role": "role.notebook.md",
            "rules": ["notebook.rules.md"],
            "templates": [
                "notebook.template.ipynb",
                "notebook_utils_template.py",
            ],
        },
        "readme": {
            "role": "role.ai_researcher.md",
            "rules": ["readme.rules.md"],
            "templates": [],
        },
        "skill": {
            "role": "role.skill.md",
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
    prompt: str,
    topic: str,
    file_path: str,
    dry_run: bool,
    model: str,
) -> int:
    """
    Run Claude Code with the given prompt via the cc wrapper.

    Delegates to `dev_scripts_helpers/ai/cc` which handles model routing
    (OpenRouter vs direct Anthropic) and environment variable setup.

    :param prompt: Claude Code prompt
    :param topic: Topic for logging purposes
    :param file_path: File to process
    :param dry_run: If True, print command but don't execute
    :param model: Model to use for Claude invocation
    :return: Return code (0 on success, or subprocess return code)
    """
    hdbg.dassert_file_exists(file_path)
    _LOG.info("Using model: %s", model)
    _LOG.info("\n%s\n%s", hprint.frame("Prompt (%s):") % topic, prompt)
    prompt_file = "tmp.lint_cc.prompt.txt"
    hio.to_file(prompt_file, prompt)
    # Call the cc wrapper which handles model routing and env setup.
    _CC_WRAPPER = hgit.find_file(
        "cc", dir_path=os.path.join(os.path.dirname(__file__), "..")
    )
    cmd_parts = [
        _CC_WRAPPER,
        "--model",
        model,
        "-p",
        f"Execute the file {prompt_file}",
    ]
    cmd = " ".join(cmd_parts)
    _LOG.info("Claude command: %s", cmd)
    if dry_run:
        _LOG.info("Dry run: command not executed")
        return 0
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
    hseinout.add_file_selection_args(parser)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--topic",
        type=str,
        default="",
        help="Claude Code skill topic (e.g., 'coding.format'). "
        "Can only be used with a single file.",
    )
    action_group.add_argument(
        "--skill",
        type=str,
        default="",
        help="Execute a skill on selected files. E.g., `coding.fix_inline`",
    )
    hmarsele.add_rule_cli_arg(action_group)
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print the command but don't execute",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Optional model name to use using cc conventions",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> int:
    """
    Main entry point.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Select files.
    num_exclusive = sum(
        [
            bool(args.topic),
            bool(args.skill),
            bool(args.rule),
        ]
    )
    hdbg.dassert_lte(
        num_exclusive,
        1,
        "Only one of --topic, --skill, or --rule can be used simultaneously",
    )
    files = hseinout.parse_file_selection_args(args, remove_dirs=False)
    if args.topic and len(files) != 1:
        raise ValueError("--topic can only be used with a single file")
    _LOG.info("Processing %d file(s)", len(files))
    #
    ret = 0
    for file_path in tqdm(files, desc="Processing files"):
        if args.skill:
            full_skill_name = hmarsele.find_skill(args.skill)
            prompt = f"/{full_skill_name} {file_path}"
            topic_str = "skill"
            inferred_topic = _infer_topic_from_filename(file_path)
            topic_info = _get_rules_for_topic(inferred_topic)
            rc = _run_claude_code(
                prompt,
                topic_str,
                file_path,
                dry_run=args.dry_run,
                model=args.model,
            )
        elif args.rule:
            _LOG.debug("Executing rigrule: %s", args.rule)
            rule_content = hmarsele.extract_rule_from_file(args.rule)
            prompt = (
                f"Execute the rule below on file {file_path}:\n\n{rule_content}"
            )
            topic_str = "rule"
            inferred_topic = _infer_topic_from_filename(file_path)
            topic_info = _get_rules_for_topic(inferred_topic)
            rc = _run_claude_code(
                prompt,
                topic_str,
                file_path,
                dry_run=args.dry_run,
                model=args.model,
            )
        else:
            if args.topic:
                topic_str = args.topic
                prompt, topic_info = _build_prompt(topic_str)
            else:
                topic = _infer_topic_from_filename(file_path)
                hdbg.dassert_is_not(topic, None, "Topic detection failed")
                topic_str = cast(str, topic)
            prompt, topic_info = _build_prompt(topic_str)
            prompt += (
                f"\n\nProcess the file {file_path} and make the changes "
                + "according to the rules and conventions without asking "
                + "questions to the user"
            )
            rc = _run_claude_code(
                prompt,
                topic_str,
                file_path,
                dry_run=args.dry_run,
                model=args.model,
            )
        ret |= rc
        if topic_info["run_jupytext"]:
            cmd = ["jupytext", "--sync", file_path]
            hsystem.system(" ".join(cmd))
        if topic_info["run_lint"]:
            hlint.lint_file(file_path)
    return ret


if __name__ == "__main__":
    ret = _main(_parse())
    exit(ret)
