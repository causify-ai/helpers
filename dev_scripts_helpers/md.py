#!/usr/bin/env python
"""
Unified markdown file manager for research, blog, story, and skill content.

Provides a single interface to manage markdown files across multiple directories:
- skill: .claude/skills/ directory
- blog: blog/posts/ directory
- research: research/ideas/ directory
- story: short_stories/ directory

Usage:
  md.py <type> <action> [name]
    type:   research, blog, story, skill (prefix matching supported)
    action: list, edit, directory (prefix matching supported)
    name:   optional for 'list' action (filter pattern), required for 'edit'

Examples:
  md.py sk list                     # List all skills
  md.py blog edit My_Post           # Edit or create a blog post
  md.py res l causal                # List research items containing 'causal'
  md.py story dir                   # Print short stories directory path

Import as:

import dev_scripts_helpers.md as devmd
"""

import argparse
import glob
import logging
import os
from datetime import date
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################

_VALID_TYPES = ["research", "blog", "story", "skill"]
_VALID_ACTIONS = ["list", "edit", "directory", "full_list"]

# #############################################################################
# Helper functions
# #############################################################################


def _match_prefix(value: str, valid_options: List[str]) -> str:
    """
    Match a value to the first valid option that starts with it (case-insensitive).

    :param value: the prefix to match
    :param valid_options: list of valid full option names
    :return: the first matching option
    """
    value_lower = value.lower()
    matches = [opt for opt in valid_options if opt.lower().startswith(value_lower)]
    hdbg.dassert_eq(
        len(matches),
        1,
        "Expected exactly one match for prefix",
        value,
        "in",
        valid_options,
        "got",
        matches,
    )
    return matches[0]


def _normalize_name(name: Optional[str]) -> Optional[str]:
    """
    Normalize a name by stripping .md suffix if present.

    :param name: the name to normalize
    :return: the normalized name (with .md suffix removed if it was present)
    """
    if name is None:
        return None
    if name.endswith(".md"):
        return name[:-3]
    return name


def _get_repo_root() -> str:
    """
    Get the path to helpers_root directory (2 levels up from this script).

    :return: absolute path to helpers_root
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    return repo_root


def _get_directory(type_: str) -> str:
    """
    Get the directory path for the given type by searching from workspace root.

    :param type_: the type (research, blog, story, skill)
    :return: absolute path to the directory
    """
    repo_root = _get_repo_root()
    workspace_root = os.path.dirname(repo_root)
    if type_ == "skill":
        return os.path.join(repo_root, ".claude", "skills")
    elif type_ == "blog":
        target_dir = os.path.join(workspace_root, "blog", "posts")
        if not os.path.isdir(target_dir):
            cmd = (
                f"find {workspace_root} -maxdepth 3 -type d -name 'posts'"
                " 2>/dev/null | head -1"
            )
            _, result = hsystem.system_to_string(cmd)
            result = result.strip()
            hdbg.dassert_ne(result, "", "Could not find posts directory")
            target_dir = result
        return os.path.abspath(target_dir)
    elif type_ == "research":
        target_dir = os.path.join(workspace_root, "research", "ideas")
        if not os.path.isdir(target_dir):
            cmd = (
                f"find {workspace_root} -maxdepth 3 -type d"
                " -path '*/research/ideas' 2>/dev/null | head -1"
            )
            _, result = hsystem.system_to_string(cmd)
            result = result.strip()
            hdbg.dassert_ne(result, "", "Could not find research/ideas directory")
            target_dir = result
        return os.path.abspath(target_dir)
    elif type_ == "story":
        target_dir = os.path.join(workspace_root, "short_stories")
        if not os.path.isdir(target_dir):
            cmd = (
                f"find {workspace_root} -maxdepth 3 -type d"
                " -name 'short_stories' 2>/dev/null | head -1"
            )
            _, result = hsystem.system_to_string(cmd)
            result = result.strip()
            hdbg.dassert_ne(result, "", "Could not find short_stories directory")
            target_dir = result
        return os.path.abspath(target_dir)
    hdbg.dfatal("Unknown type", type_)


def _get_template(type_: str, name: str) -> str:
    """
    Get the template content for creating a new file of the given type.

    :param type_: the type (research, blog, story, skill)
    :param name: the name to include in the template
    :return: template string
    """
    if type_ == "blog":
        today = date.today().isoformat()
        text = f"""
        ---
        title: "{name}"
        authors:
          - gpsaggese
        date: {today}
        description:
        categories:
          - Causal AI
        ---

        TL;DR: <Summary here>

        <!-- more -->

        ## Introduction

        <Your content here>
        """
        return hprint.dedent(text)
    elif type_ == "skill":
        text = f"""
        ---
        description: <Brief description of what this skill does>
        ---

        # Summary

        <Brief description of what this skill does>

        ## Usage

        <Usage examples and patterns>

        ## Implementation Details

        <Technical details>
        """
        return hprint.dedent(text)
    elif type_ == "research":
        return f"# {name}\n\n<Research notes here>\n"
    elif type_ == "story":
        return ""
    hdbg.dfatal("Unknown type", type_)


def _list_markdown_files(
    dir_: str, type_: str, *, pattern: Optional[str] = None, full_path: bool = False
) -> None:
    """
    List markdown files in a directory, optionally filtered by pattern.

    For skills, 'list' mode shows skill names only, 'full_path' mode shows full paths.
    For other types, both modes show full paths.
    Pattern matching matches against skill names for skills, and filenames for other types.

    :param dir_: the directory to search
    :param type_: the type (research, blog, story, skill)
    :param pattern: optional filter pattern
    :param full_path: if True, show full paths; if False, show skill names for skills
    """
    hdbg.dassert_dir_exists(dir_)
    files = glob.glob(os.path.join(dir_, "**/*.md"), recursive=True)
    files.sort()
    if pattern:
        pattern_lower = pattern.lower()
        if type_ == "skill":
            files = [
                f
                for f in files
                if pattern_lower in os.path.basename(os.path.dirname(f)).lower()
            ]
        else:
            files = [f for f in files if pattern_lower in os.path.basename(f).lower()]
    if files:
        for f in files:
            if type_ == "skill" and not full_path:
                skill_name = os.path.basename(os.path.dirname(f))
                print(skill_name)
            else:
                print(f)
    else:
        _LOG.info("No markdown files found in %s", dir_)


def _find_file_for_edit(type_: str, dir_: str, name: str) -> str:
    """
    Find or create a file for editing based on type and name.

    :param type_: the type (research, blog, story, skill)
    :param dir_: the base directory for this type
    :param name: the name/pattern to find or create
    :return: absolute path to the file
    """
    if type_ == "skill":
        skill_dir = os.path.join(dir_, name)
        file_path = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(file_path):
            hio.create_dir(skill_dir, incremental=True)
            template = _get_template(type_, name)
            hio.to_file(file_path, template)
            _LOG.info("Created new skill: %s", file_path)
        return file_path
    elif type_ == "research":
        idea_dir = os.path.join(dir_, name)
        file_path = os.path.join(idea_dir, "README.md")
        if not os.path.exists(file_path):
            hio.create_dir(idea_dir, incremental=True)
            template = _get_template(type_, name)
            hio.to_file(file_path, template)
            _LOG.info("Created new research idea: %s", file_path)
        return file_path
    elif type_ == "blog":
        candidates = glob.glob(os.path.join(dir_, f"*{name}*.md"))
        if candidates:
            return candidates[0]
        file_path = os.path.join(dir_, f"draft.{name}.md")
        if not os.path.exists(file_path):
            template = _get_template(type_, name)
            hio.to_file(file_path, template)
            _LOG.info("Created new blog post: %s", file_path)
        return file_path
    elif type_ == "story":
        candidates = glob.glob(os.path.join(dir_, f"*{name}*.*"))
        if candidates:
            return candidates[0]
        file_path = os.path.join(dir_, f"{name}.md")
        if not os.path.exists(file_path):
            template = _get_template(type_, name)
            hio.to_file(file_path, template)
            _LOG.info("Created new story: %s", file_path)
        return file_path
    hdbg.dfatal("Unknown type", type_)


def _action_list(type_: str, dir_: str, *, pattern: Optional[str] = None) -> None:
    """
    List markdown files in a directory (concise format).

    For skills: shows skill names only.
    For other types: shows full file paths.

    :param type_: the type (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _list_markdown_files(dir_, type_, pattern=pattern, full_path=False)


def _action_full_list(type_: str, dir_: str, *, pattern: Optional[str] = None) -> None:
    """
    List markdown files in a directory (full paths).

    :param type_: the type (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _list_markdown_files(dir_, type_, pattern=pattern, full_path=True)


def _action_edit(type_: str, dir_: str, name: str) -> None:
    """
    Open a file for editing (creating it if necessary).

    :param type_: the type (research, blog, story, skill)
    :param dir_: the base directory for this type
    :param name: the file name to edit
    """
    file_path = _find_file_for_edit(type_, dir_, name)
    _LOG.info("Opening file in vim: %s", file_path)
    os.system(f"vim {file_path}")


def _action_directory(dir_: str) -> None:
    """
    Print the directory path.

    :param dir_: the directory path
    """
    print(dir_)


# #############################################################################
# Parser and main
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "type",
        help="Type: research, blog, story, skill (supports prefix matching)",
    )
    parser.add_argument(
        "action",
        help="Action: list, edit, directory (supports prefix matching)",
    )
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Name/pattern (optional for list, required for edit)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    type_ = _match_prefix(args.type, _VALID_TYPES)
    action = _match_prefix(args.action, _VALID_ACTIONS)
    args.name = _normalize_name(args.name)
    dir_ = _get_directory(type_)
    if action == "list":
        _action_list(type_, dir_, pattern=args.name)
    elif action == "full_list":
        _action_full_list(type_, dir_, pattern=args.name)
    elif action == "edit":
        hdbg.dassert_ne(
            args.name,
            None,
            "Name is required for edit action",
        )
        _action_edit(type_, dir_, args.name)
    elif action == "directory":
        _action_directory(dir_)
    else:
        hdbg.dfatal("Unknown action", action)


if __name__ == "__main__":
    _main(_parse())
