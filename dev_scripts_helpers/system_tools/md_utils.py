"""
Utility functions for the markdown file manager.

Provides helpers for managing markdown files across research, blog, story,
and skill content types.

Import as:

import dev_scripts_helpers.system_tools.md_utils as dshstmdut
"""

import glob
import logging
import os
import shutil
from datetime import date
from typing import List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################


_VALID_TYPES = ["research", "blog", "story", "skill"]
_VALID_ACTIONS = [
    "list",
    "edit",
    "directory",
    "full_list",
    "describe",
    "types",
    "copy",
]

# #############################################################################
# Helper functions
# #############################################################################


def _match_prefix(value: str, valid_options: List[str]) -> str:
    """
    Match a value to the first valid option that starts with it
    (case-insensitive).

    :param value: the prefix to match
    :param valid_options: list of valid full option names
    :return: the first matching option
    """
    value_lower = value.lower()
    matches = [
        opt for opt in valid_options if opt.lower().startswith(value_lower)
    ]
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
    Get the path to helpers_root directory (3 levels up from this script).

    :return: absolute path to helpers_root
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
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
        target_dir = os.path.join(repo_root, ".claude", "skills")
    elif type_ == "blog":
        cmd = (
            f"find {workspace_root} -maxdepth 5 -type d -path '*/posts'"
            " 2>/dev/null | head -1"
        )
        _, result = hsystem.system_to_string(cmd)
        result = result.strip()
        hdbg.dassert_ne(result, "", "Could not find posts directory")
        target_dir = result
    elif type_ == "research":
        cmd = (
            f"find {workspace_root} -maxdepth 3 -type d"
            " -path '*/research/ideas' 2>/dev/null | head -1"
        )
        _, result = hsystem.system_to_string(cmd)
        result = result.strip()
        hdbg.dassert_ne(result, "", "Could not find 'research/ideas' directory")
        target_dir = result
    elif type_ == "story":
        cmd = (
            f"find {workspace_root} -maxdepth 3 -type d"
            " -name 'short_stories' 2>/dev/null | head -1"
        )
        _, result = hsystem.system_to_string(cmd)
        result = result.strip()
        hdbg.dassert_ne(result, "", "Could not find 'short_stories' directory")
        target_dir = result
    else:
        hdbg.dfatal("Unknown type '%s'" % type_)
    return os.path.abspath(target_dir)


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
        text = """
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
    dir_: str,
    type_: str,
    *,
    pattern: Optional[str] = None,
    full_path: bool = False,
) -> None:
    """
    List markdown files in a directory, optionally filtered by pattern.

    For skills, 'list' mode shows skill names only, 'full_path' mode shows
    full paths. For other types, both modes show full paths. Pattern matching
    matches against skill names for skills, and filenames for other types.

    :param dir_: the directory to search
    :param type_: the type (research, blog, story, skill)
    :param pattern: optional filter pattern
    :param full_path: if True, show full paths; if False, show skill names for
        skills
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
            files = [
                f for f in files if pattern_lower in os.path.basename(f).lower()
            ]
    if files:
        for f in files:
            if not full_path:
                if type_ == "skill":
                    skill_name = os.path.basename(os.path.dirname(f))
                    print(skill_name)
                else:
                    basename = os.path.basename(f)
                    print(basename)
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
        # Check if there are multiple matching skill directories.
        candidates = glob.glob(os.path.join(dir_, f"*{name}*", "SKILL.md"))
        if candidates:
            # Check for exact match first.
            exact_match = os.path.join(dir_, name, "SKILL.md")
            if os.path.exists(exact_match):
                return exact_match
            # If multiple non-exact matches, fail.
            if len(candidates) > 1:
                msg = f"Multiple skills match pattern '{name}':\n"
                for candidate in candidates:
                    skill_name = os.path.basename(os.path.dirname(candidate))
                    msg += f"  - {skill_name}\n"
                hdbg.dfatal(msg)
            # Single non-exact match found.
            return candidates[0]
        # Create new skill with exact name.
        skill_dir = os.path.join(dir_, name)
        file_path = os.path.join(skill_dir, "SKILL.md")
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


def _action_list(
    type_: str, dir_: str, *, pattern: Optional[str] = None
) -> None:
    """
    List markdown files in a directory (concise format).

    For skills: shows skill names only.
    For other types: shows full file paths.

    :param type_: the type (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _list_markdown_files(dir_, type_, pattern=pattern, full_path=False)


def _action_full_list(
    type_: str, dir_: str, *, pattern: Optional[str] = None
) -> None:
    """
    List markdown files in a directory (full paths).

    :param type_: the type (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _list_markdown_files(dir_, type_, pattern=pattern, full_path=True)


def _action_edit(type_: str, dir_: str, names: List[str]) -> None:
    """
    Open file(s) for editing (creating if necessary).

    :param type_: the type (research, blog, story, skill)
    :param dir_: the base directory for this type
    :param names: list of file name(s) to edit
    """
    file_paths = [_find_file_for_edit(type_, dir_, name) for name in names]
    files_str = " ".join(f'"{path}"' for path in file_paths)
    _LOG.info("Opening %d file(s) in vim", len(file_paths))
    os.system(f"vim {files_str}")


def _get_description(file_path: str) -> str:
    """
    Extract the description from the YAML front matter of a markdown file.

    :param file_path: path to the markdown file
    :return: description string, or empty string if not found
    """
    try:
        content = hio.from_file(file_path)
    except Exception:
        return ""
    lines = content.splitlines()
    # Check for YAML front matter (starts with ---).
    if not lines or lines[0].strip() != "---":
        return ""
    # Search for "description:" within the front matter.
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("description:"):
            desc = line[len("description:") :].strip()
            return desc
    return ""


def _action_describe(
    type_: str, dir_: str, *, pattern: Optional[str] = None
) -> None:
    """
    List markdown files with their description from YAML front matter.

    Like list, but also prints the description line from each file.

    :param type_: the type (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
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
            files = [
                f for f in files if pattern_lower in os.path.basename(f).lower()
            ]
    if files:
        # Collect entries first to compute max name length for alignment.
        entries = []
        for f in files:
            if type_ == "skill":
                name = os.path.basename(os.path.dirname(f))
            else:
                name = os.path.basename(f)
            desc = _get_description(f)
            entries.append((name, desc))
        # Align descriptions with dots.
        max_name_len = max(len(name) for name, _ in entries)
        min_dots = 4
        for name, desc in entries:
            if desc:
                dots = "." * (max_name_len - len(name) + min_dots)
                print(f"{name} {dots} {desc}")
            else:
                print(name)
    else:
        _LOG.info("No markdown files found in %s", dir_)


def _action_directory(dir_: str) -> None:
    """
    Print the directory path.

    :param dir_: the directory path
    """
    print(dir_)


def _action_types(
    type_: str, dir_: str, *, pattern: Optional[str] = None
) -> None:
    """
    List unique prefixes before the first dot from markdown file names.

    For example, skill names like 'blog.add_figures' and 'blog.create_tldr'
    will both produce prefix 'blog'. Equivalent to cut -d'.' -f1 | sort -u.

    :param type_: the type (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    hdbg.dassert_dir_exists(dir_)
    files = glob.glob(os.path.join(dir_, "**/*.md"), recursive=True)
    if pattern:
        pattern_lower = pattern.lower()
        if type_ == "skill":
            files = [
                f
                for f in files
                if pattern_lower in os.path.basename(os.path.dirname(f)).lower()
            ]
        else:
            files = [
                f for f in files if pattern_lower in os.path.basename(f).lower()
            ]
    # Extract prefixes (part before the first dot).
    prefixes = set()
    for f in files:
        if type_ == "skill":
            name = os.path.basename(os.path.dirname(f))
        else:
            name = os.path.basename(f)
        # Remove .md extension if present.
        if name.endswith(".md"):
            name = name[:-3]
        # Extract prefix before the dot.
        prefix = name.split(".")[0]
        prefixes.add(prefix)
    # Print sorted prefixes.
    if prefixes:
        for prefix in sorted(prefixes):
            print(prefix)
    else:
        _LOG.info("No markdown files found in %s", dir_)


def _action_copy(
    type_: str, dir_: str, source_name: str, dest_name: str
) -> None:
    """
    Copy a directory (for skills) or file (for other types) to a new location.

    For skills, copies the entire skill directory. For other types, copies
    the file.

    :param type_: the type (research, blog, story, skill)
    :param dir_: the base directory for this type
    :param source_name: name of source to copy
    :param dest_name: name of destination
    """
    if type_ != "skill":
        hdbg.dfatal("Copy action is only supported for skills")
    source_dir = os.path.join(dir_, source_name)
    dest_dir = os.path.join(dir_, dest_name)
    hdbg.dassert_dir_exists(
        source_dir,
        f"Source skill '{source_name}' not found at {source_dir}",
    )
    hdbg.dassert(
        not os.path.exists(dest_dir),
        f"Destination skill '{dest_name}' already exists at {dest_dir}",
    )
    # Copy the directory recursively.
    shutil.copytree(source_dir, dest_dir)
    _LOG.info("Copied skill from '%s' to '%s'", source_name, dest_name)
    # TODO(ai_gp): Use _LOG.info
    print(f"Copied skill from '{source_name}' to '{dest_name}'")
    print(f"New skill location: {dest_dir}")
