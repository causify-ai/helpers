"""
Utility functions for the markdown file manager.

Provides helpers for managing markdown files across research, blog, story,
and skill content topics.

Import as:

import dev_scripts_helpers.system_tools.mdm_utils as dshstmdut
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


# TODO(gp): This should be inferred automatically from the dir.
_VALID_TOPICS = ["research", "blog", "story", "skill", "rules"]
_VALID_ACTIONS = [
    "list",
    "edit",
    "directory",
    "full_list",
    "describe",
    "topics",
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
    # Find all options that start with the given prefix (case-insensitive).
    value_lower = value.lower()
    _LOG.debug("Matching prefix '%s' against options: %s", value, valid_options)
    matches = [
        opt for opt in valid_options if opt.lower().startswith(value_lower)
    ]
    _LOG.debug("Found %d matching option(s): %s", len(matches), matches)
    # Ensure prefix matches exactly one option to avoid ambiguity.
    hdbg.dassert_eq(
        len(matches),
        1,
        "Prefix '%s' must match exactly one option, found %d",
        value,
        len(matches),
    )
    return matches[0]


def _normalize_name(name: Optional[str]) -> Optional[str]:
    """
    Normalize a name by stripping .md suffix if present.

    :param name: the name to normalize
    :return: the normalized name (with .md suffix removed if it was present)
    """
    result = name
    if name is None:
        _LOG.debug("Name is None, returning None")
    elif name.endswith(".md"):
        result = name[:-3]
        _LOG.debug("Stripped .md suffix from '%s' -> '%s'", name, result)
    else:
        _LOG.debug("Name '%s' has no .md suffix, returning as-is", name)
    return result


def _get_repo_root() -> str:
    """
    Get the path to helpers_root directory (3 levels up from this script).

    :return: absolute path to helpers_root
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(script_dir))
    return repo_root


def _get_directory(topic_: str) -> str:
    """
    Get the directory path for the given topic by searching from workspace root.

    :param topic_: the topic (research, blog, story, skill)
    :return: absolute path to the directory
    """
    _LOG.debug("Getting directory for topic '%s'", topic_)
    repo_root = _get_repo_root()
    workspace_root = os.path.dirname(repo_root)
    _LOG.debug(
        "Repository root: %s, workspace root: %s", repo_root, workspace_root
    )
    # Resolve directory path based on topic: skills and rules use fixed paths,
    # others are discovered via filesystem search.
    target_dir = ""
    if topic_ == "skill":
        target_dir = os.path.join(repo_root, ".claude", "skills")
        _LOG.debug("Using static skill directory: %s", target_dir)
    elif topic_ == "blog":
        cmd = (
            f"find {workspace_root} -maxdepth 5 -topic d -path '*/posts'"
            " 2>/dev/null | head -1"
        )
        _LOG.debug("Searching for blog posts directory with command: %s", cmd)
        _, result = hsystem.system_to_string(cmd)
        result = result.strip()
        if result:
            target_dir = result
            _LOG.debug("Found blog posts directory: %s", target_dir)
        else:
            _LOG.warning("Could not find posts directory")
    elif topic_ == "research":
        cmd = (
            f"find {workspace_root} -maxdepth 3 -topic d"
            " -path '*/research/ideas' 2>/dev/null | head -1"
        )
        _LOG.debug(
            "Searching for research/ideas directory with command: %s", cmd
        )
        _, result = hsystem.system_to_string(cmd)
        result = result.strip()
        if result:
            target_dir = result
            _LOG.debug("Found research/ideas directory: %s", target_dir)
        else:
            _LOG.warning("Could not find 'research/ideas' directory")
    elif topic_ == "story":
        cmd = (
            f"find {workspace_root} -maxdepth 3 -topic d"
            " -name 'short_stories' 2>/dev/null | head -1"
        )
        _LOG.debug("Searching for short_stories directory with command: %s", cmd)
        _, result = hsystem.system_to_string(cmd)
        result = result.strip()
        if result:
            target_dir = result
            _LOG.debug("Found short_stories directory: %s", target_dir)
        else:
            _LOG.warning("Could not find 'short_stories' directory")
    elif topic_ == "rules":
        target_dir = os.path.join(repo_root, ".claude", "skills")
        _LOG.debug("Using static rules directory: %s", target_dir)
    else:
        hdbg.dfatal("Unknown topic '%s'" % topic_)
    abs_path = os.path.abspath(target_dir) if target_dir else ""
    _LOG.debug("Returning absolute path: %s", abs_path)
    return abs_path


def _get_template(topic_: str, name: str) -> str:
    """
    Get the template content for creating a new file of the given topic.

    :param topic_: the topic (research, blog, story, skill)
    :param name: the name to include in the template
    :return: template string
    """
    result = ""
    if topic_ == "blog":
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
        result = hprint.dedent(text)
    elif topic_ == "skill":
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
        result = hprint.dedent(text)
    elif topic_ == "research":
        result = f"# {name}\n\n<Research notes here>\n"
    elif topic_ == "story":
        result = ""
    elif topic_ == "rules":
        result = ""
    else:
        hdbg.dfatal("Unknown topic", topic_)
    return result


def _list_markdown_files(
    dir_: str,
    topic_: str,
    *,
    pattern: str = "",
    full_path: bool = False,
) -> None:
    """
    List markdown files in a directory, optionally filtered by pattern.

    For skills and rules
    - 'list' mode shows names only
    - 'full_path' mode shows full paths

    For other topics, both modes show full paths.

    Pattern matching matches against skill/rule names and filenames.

    :param dir_: the directory to search
    :param topic_: the topic (research, blog, story, skill, rules)
    :param pattern: optional filter pattern
    :param full_path:
        - If True, show full paths
        - If False, show names for skills and rules
    """
    _LOG.debug(
        "Listing markdown files in %s (topic=%s, pattern=%s, full_path=%s)",
        dir_,
        topic_,
        pattern,
        full_path,
    )
    if not dir_:
        _LOG.info("Directory not available for topic '%s'", topic_)
        return
    hdbg.dassert_dir_exists(dir_, "Directory must exist to list files")
    # Search for markdown files: skills use **/SKILL.md pattern, rules use
    # *.rules.md pattern, others use recursive **/*.md search.
    if topic_ == "skill":
        files = glob.glob(os.path.join(dir_, "**/SKILL.md"), recursive=True)
        _LOG.debug("Searching for **/SKILL.md files")
    elif topic_ == "rules":
        files = glob.glob(os.path.join(dir_, "*.rules.md"))
        _LOG.debug("Searching for *.rules.md files")
    else:
        files = glob.glob(os.path.join(dir_, "**/*.md"), recursive=True)
        _LOG.debug("Searching for **/*.md files recursively")
    _LOG.debug("Found %d markdown file(s)", len(files))
    files.sort()
    # Remove duplicates while preserving sort order.
    files = list(dict.fromkeys(files))
    if pattern:
        # Filter files by pattern: match against skill name (directory), rule
        # name (filename without suffix), or filename for other topics.
        pattern_lower = pattern.lower()
        _LOG.debug("Filtering files by pattern: '%s'", pattern)
        if topic_ == "skill":
            files = [
                f
                for f in files
                if pattern_lower in os.path.basename(os.path.dirname(f)).lower()
            ]
        elif topic_ == "rules":
            files = [
                f
                for f in files
                if pattern_lower
                in os.path.basename(f).replace(".rules.md", "").lower()
            ]
        else:
            files = [
                f for f in files if pattern_lower in os.path.basename(f).lower()
            ]
        _LOG.debug("After filtering: %d file(s) match pattern", len(files))
    if files:
        # Print files: use skill/rule names if not showing full paths, otherwise
        # print full paths.
        _LOG.debug("Printing %d file(s), full_path=%s", len(files), full_path)
        for f in files:
            if not full_path:
                if topic_ == "skill":
                    skill_name = os.path.basename(os.path.dirname(f))
                    print(skill_name)
                elif topic_ == "rules":
                    rule_name = os.path.basename(f).replace(".rules.md", "")
                    print(rule_name)
                else:
                    basename = os.path.basename(f)
                    print(basename)
            else:
                print(f)
    else:
        _LOG.info("No markdown files found in %s", dir_)


def _find_file_for_edit(topic_: str, dir_: str, name: str) -> str:
    """
    Find or create a file for editing based on topic and name.

    :param topic_: the topic (research, blog, story, skill, rules)
    :param dir_: the base directory for this topic
    :param name: the name/pattern to find or create
    :return: absolute path to the file
    """
    _LOG.debug(
        "Finding file for edit: topic=%s, name=%s, directory=%s",
        topic_,
        name,
        dir_,
    )
    file_path = ""
    # Find or create file based on topic: skills use directory structure
    # (dir/skill_name/SKILL.md), research uses directory with README.md, blog/story
    # use flat files, rules use *.rules.md pattern.
    if topic_ == "skill":
        # Try to find existing skill by pattern or exact name.
        candidates = glob.glob(os.path.join(dir_, f"*{name}*", "SKILL.md"))
        _LOG.debug(
            "Searching for skill candidates matching pattern '%s': found %d",
            name,
            len(candidates),
        )
        if candidates:
            exact_match = os.path.join(dir_, name, "SKILL.md")
            if os.path.exists(exact_match):
                _LOG.debug("Found exact skill match: %s", exact_match)
                file_path = exact_match
            elif len(candidates) > 1:
                msg = f"Multiple skills match pattern '{name}':\n"
                for candidate in candidates:
                    skill_name = os.path.basename(os.path.dirname(candidate))
                    msg += f"  - {skill_name}\n"
                hdbg.dfatal(msg)
            else:
                _LOG.debug("Found skill candidate: %s", candidates[0])
                file_path = candidates[0]
        else:
            # Create new skill directory and SKILL.md file with template.
            skill_dir = os.path.join(dir_, name)
            file_path = os.path.join(skill_dir, "SKILL.md")
            _LOG.debug("Creating new skill directory and file: %s", file_path)
            hio.create_dir(skill_dir, incremental=True)
            template = _get_template(topic_, name)
            hio.to_file(file_path, template)
            _LOG.info("Created new skill: %s", file_path)
    elif topic_ == "research":
        # Research ideas are stored in directories with README.md files.
        idea_dir = os.path.join(dir_, name)
        file_path = os.path.join(idea_dir, "README.md")
        if not os.path.exists(file_path):
            _LOG.debug(
                "Creating new research idea directory and file: %s", file_path
            )
            hio.create_dir(idea_dir, incremental=True)
            template = _get_template(topic_, name)
            hio.to_file(file_path, template)
            _LOG.info("Created new research idea: %s", file_path)
        else:
            _LOG.debug("Found existing research idea file: %s", file_path)
    elif topic_ == "blog":
        # Blog posts are flat files with optional draft prefix.
        candidates = glob.glob(os.path.join(dir_, f"*{name}*.md"))
        _LOG.debug(
            "Searching for blog candidates matching pattern '%s': found %d",
            name,
            len(candidates),
        )
        if candidates:
            _LOG.debug("Found blog candidate: %s", candidates[0])
            file_path = candidates[0]
        else:
            file_path = os.path.join(dir_, f"draft.{name}.md")
            if not os.path.exists(file_path):
                _LOG.debug("Creating new blog post file: %s", file_path)
                template = _get_template(topic_, name)
                hio.to_file(file_path, template)
                _LOG.info("Created new blog post: %s", file_path)
            else:
                _LOG.debug("Found existing blog post file: %s", file_path)
    elif topic_ == "story":
        # Stories are flat files with any extension.
        candidates = glob.glob(os.path.join(dir_, f"*{name}*.*"))
        _LOG.debug(
            "Searching for story candidates matching pattern '%s': found %d",
            name,
            len(candidates),
        )
        if candidates:
            _LOG.debug("Found story candidate: %s", candidates[0])
            file_path = candidates[0]
        else:
            file_path = os.path.join(dir_, f"{name}.md")
            if not os.path.exists(file_path):
                _LOG.debug("Creating new story file: %s", file_path)
                template = _get_template(topic_, name)
                hio.to_file(file_path, template)
                _LOG.info("Created new story: %s", file_path)
            else:
                _LOG.debug("Found existing story file: %s", file_path)
    elif topic_ == "rules":
        # Rules are flat files with .rules.md suffix.
        candidates = glob.glob(os.path.join(dir_, f"*{name}*.rules.md"))
        _LOG.debug(
            "Searching for rule candidates matching pattern '%s': found %d",
            name,
            len(candidates),
        )
        exact_match = os.path.join(dir_, f"{name}.rules.md")
        if candidates:
            if os.path.exists(exact_match):
                _LOG.debug("Found exact rule match: %s", exact_match)
                file_path = exact_match
            elif len(candidates) > 1:
                msg = f"Multiple rules match pattern '{name}':\n"
                for candidate in candidates:
                    rule_name = os.path.basename(candidate).replace(
                        ".rules.md", ""
                    )
                    msg += f"  - {rule_name}\n"
                hdbg.dfatal(msg)
            else:
                _LOG.debug("Found rule candidate: %s", candidates[0])
                file_path = candidates[0]
        else:
            file_path = exact_match
            _LOG.debug("Creating new rule file: %s", file_path)
            template = _get_template(topic_, name)
            hio.to_file(file_path, template)
            _LOG.info("Created new rule: %s", file_path)
    else:
        hdbg.dfatal("Unknown topic", topic_)
    return file_path


# #############################################################################
# Full list
# #############################################################################


def _action_list(topic_: str, dir_: str, *, pattern: str = "") -> None:
    """
    List markdown files in a directory (concise format).

    TODO(ai_gp): Add example

    For skills: shows skill names only.
    For other topics: shows full file paths.

    :param topic_: the topic (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _list_markdown_files(dir_, topic_, pattern=pattern, full_path=False)


def _action_full_list(topic_: str, dir_: str, *, pattern: str = "") -> None:
    """
    List markdown files in a directory (full paths).

    TODO(ai_gp): Add example

    :param topic_: the topic (research, blog, story, skill)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _list_markdown_files(dir_, topic_, pattern=pattern, full_path=True)


# #############################################################################
# Edit
# #############################################################################


def _action_edit(topic_: str, dir_: str, names: List[str]) -> None:
    """
    Open file(s) for editing (creating if necessary).

    :param topic_: the topic (research, blog, story, skill)
    :param dir_: the base directory for this topic
    :param names: list of file name(s) to edit
    """
    _LOG.debug("Preparing to edit %d file(s) of topic '%s'", len(names), topic_)
    file_paths = [_find_file_for_edit(topic_, dir_, name) for name in names]
    _LOG.debug("Resolved file paths: %s", file_paths)
    files_str = " ".join(f'"{path}"' for path in file_paths)
    _LOG.info("Opening %d file(s) in vim", len(file_paths))
    _LOG.debug("Running vim command: vim %s", files_str)
    os.system(f"vim {files_str}")


# #############################################################################
# Describe
# #############################################################################


def _get_description(file_path: str) -> str:
    """
    Extract the description from the YAML front matter of a markdown file.

    :param file_path: path to the markdown file
    :return: description string, or empty string if not found
    """
    _LOG.debug("Extracting description from: %s", file_path)
    result = ""
    if not os.path.exists(file_path):
        _LOG.debug("File does not exist, returning empty description")
    else:
        # Parse YAML front matter to extract description field.
        content = hio.from_file(file_path)
        lines = content.splitlines()
        # YAML front matter must start with `---` delimiter.
        if not lines or lines[0].strip() != "---":
            _LOG.debug("No YAML front matter found in file")
        else:
            _LOG.debug(
                "Found YAML front matter, searching for description field"
            )
            # Scan lines until closing `---` delimiter or description field found.
            for line in lines[1:]:
                if line.strip() == "---":
                    _LOG.debug(
                        "End of YAML front matter reached without finding description"
                    )
                    break
                if line.startswith("description:"):
                    result = line[len("description:") :].strip()
                    _LOG.debug("Found description: %s", result)
                    break
            else:
                _LOG.debug("Description field not found in front matter")
    return result


def _action_describe(topic_: str, dir_: str, *, pattern: str = "") -> None:
    """
    List markdown files with their description from YAML front matter.

    Like list, but also prints the description line from each file.

    :param topic_: the topic (research, blog, story, skill, rules)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _LOG.debug(
        "Describing markdown files in %s (topic=%s, pattern=%s)",
        dir_,
        topic_,
        pattern,
    )
    if not dir_:
        _LOG.info("Directory not available for topic '%s'", topic_)
        return
    hdbg.dassert_dir_exists(dir_, "Directory must exist to describe files")
    # Search for markdown files using appropriate patterns for each topic.
    if topic_ == "skill":
        files = glob.glob(os.path.join(dir_, "**/SKILL.md"), recursive=True)
    elif topic_ == "rules":
        files = glob.glob(os.path.join(dir_, "*.rules.md"))
    else:
        files = glob.glob(os.path.join(dir_, "**/*.md"), recursive=True)
    files.sort()
    _LOG.debug("Found %d total markdown file(s)", len(files))
    if pattern:
        # Filter files by pattern: match against skill name (directory), rule
        # name (filename without suffix), or filename for other topics.
        pattern_lower = pattern.lower()
        _LOG.debug("Filtering files by pattern: '%s'", pattern)
        if topic_ == "skill":
            files = [
                f
                for f in files
                if pattern_lower in os.path.basename(os.path.dirname(f)).lower()
            ]
        elif topic_ == "rules":
            files = [
                f
                for f in files
                if pattern_lower
                in os.path.basename(f).replace(".rules.md", "").lower()
            ]
        else:
            files = [
                f for f in files if pattern_lower in os.path.basename(f).lower()
            ]
        _LOG.debug("After filtering: %d file(s) match pattern", len(files))
    if files:
        # Collect entries and extract descriptions to compute column alignment.
        _LOG.debug("Extracting descriptions from %d file(s)", len(files))
        entries = []
        for f in files:
            if topic_ == "skill":
                name = os.path.basename(os.path.dirname(f))
            elif topic_ == "rules":
                name = os.path.basename(f).replace(".rules.md", "")
            else:
                name = os.path.basename(f)
            desc = _get_description(f)
            entries.append((name, desc))
        # Format output with dot-padded alignment: compute longest name length,
        # then pad shorter names with dots before description.
        max_name_len = max(len(name) for name, _ in entries)
        min_dots = 4
        _LOG.debug("Printing %d entries with descriptions", len(entries))
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
    _LOG.debug("Printing directory path: %s", dir_)
    print(dir_)


# #############################################################################
# Topics
# #############################################################################


def _action_topics(topic_: str, dir_: str, *, pattern: str = "") -> None:
    """
    List unique prefixes before the first dot from markdown file names.

    For example, skill names like 'blog.add_figures' and 'blog.create_tldr'
    will both produce prefix 'blog'. Equivalent to cut -d'.' -f1 | sort -u.

    :param topic_: the topic (research, blog, story, skill, rules)
    :param dir_: the directory to list
    :param pattern: optional filter pattern
    """
    _LOG.debug(
        "Extracting topic prefixes from %s (topic=%s, pattern=%s)",
        dir_,
        topic_,
        pattern,
    )
    if not dir_:
        _LOG.info("Directory not available for topic '%s'", topic_)
        return
    hdbg.dassert_dir_exists(
        dir_, "Directory must exist to extract topic prefixes"
    )
    # Search for markdown files using appropriate patterns for each topic.
    if topic_ == "skill":
        files = glob.glob(os.path.join(dir_, "**/SKILL.md"), recursive=True)
    elif topic_ == "rules":
        files = glob.glob(os.path.join(dir_, "*.rules.md"))
    else:
        files = glob.glob(os.path.join(dir_, "**/*.md"), recursive=True)
    _LOG.debug("Found %d markdown file(s) total", len(files))
    if pattern:
        # Filter files by pattern: match against skill name (directory), rule
        # name (filename without suffix), or filename for other topics.
        pattern_lower = pattern.lower()
        _LOG.debug("Filtering files by pattern: '%s'", pattern)
        if topic_ == "skill":
            files = [
                f
                for f in files
                if pattern_lower in os.path.basename(os.path.dirname(f)).lower()
            ]
        elif topic_ == "rules":
            files = [
                f
                for f in files
                if pattern_lower
                in os.path.basename(f).replace(".rules.md", "").lower()
            ]
        else:
            files = [
                f for f in files if pattern_lower in os.path.basename(f).lower()
            ]
        _LOG.debug("After filtering: %d file(s) match pattern", len(files))
    # Extract category prefixes (part before the first dot in filename).
    # For example: 'blog.add_figures' -> 'blog', 'testing.reach_coverage' -> 'testing'.
    _LOG.debug("Extracting prefixes from file names")
    prefixes = set()
    for f in files:
        if topic_ == "skill":
            name = os.path.basename(os.path.dirname(f))
        elif topic_ == "rules":
            name = os.path.basename(f).replace(".rules.md", "")
        else:
            name = os.path.basename(f)
        if name.endswith(".md"):
            name = name[:-3]
        prefix = name.split(".")[0]
        prefixes.add(prefix)
    _LOG.debug(
        "Extracted %d unique prefix(es): %s", len(prefixes), sorted(prefixes)
    )
    if prefixes:
        for prefix in sorted(prefixes):
            print(prefix)
    else:
        _LOG.info("No markdown files found in %s", dir_)


def _action_copy(
    topic_: str, dir_: str, source_name: str, dest_name: str
) -> None:
    """
    Copy a directory (for skills) or file (for rules) to a new location.

    For skills, copies the entire skill directory. For rules, copies the file.

    :param topic_: the topic (skill, rules)
    :param dir_: the base directory for this topic
    :param source_name: name of source to copy
    :param dest_name: name of destination
    """
    _LOG.debug(
        "Copying %s from '%s' to '%s' in directory %s",
        topic_,
        source_name,
        dest_name,
        dir_,
    )
    # Copy skill directory or rule file: skills are directories with all contents,
    # rules are single .rules.md files.
    if topic_ == "skill":
        # Copy entire skill directory including all contents.
        source_dir = os.path.join(dir_, source_name)
        dest_dir = os.path.join(dir_, dest_name)
        _LOG.debug("Copying skill directory from %s to %s", source_dir, dest_dir)
        hdbg.dassert_dir_exists(
            source_dir,
            f"Source skill '{source_name}' not found at {source_dir}",
        )
        hdbg.dassert(
            not os.path.exists(dest_dir),
            "Destination skill '%s' already exists at %s",
            dest_name,
            dest_dir,
        )
        _LOG.debug("Executing copytree from %s to %s", source_dir, dest_dir)
        shutil.copytree(source_dir, dest_dir)
        _LOG.info("Copied skill from '%s' to '%s'", source_name, dest_name)
        print(f"Copied skill from '{source_name}' to '{dest_name}'")
        print(f"New skill location: {dest_dir}")
    elif topic_ == "rules":
        # Copy single rule file with .rules.md suffix.
        source_file = os.path.join(dir_, f"{source_name}.rules.md")
        dest_file = os.path.join(dir_, f"{dest_name}.rules.md")
        _LOG.debug("Copying rule file from %s to %s", source_file, dest_file)
        hdbg.dassert(
            os.path.isfile(source_file),
            "Source rule '%s' not found at %s",
            source_name,
            source_file,
        )
        hdbg.dassert(
            not os.path.exists(dest_file),
            "Destination rule '%s' already exists at %s",
            dest_name,
            dest_file,
        )
        _LOG.debug("Executing copy2 from %s to %s", source_file, dest_file)
        shutil.copy2(source_file, dest_file)
        _LOG.info("Copied rule from '%s' to '%s'", source_name, dest_name)
        print(f"Copied rule from '{source_name}' to '{dest_name}'")
        print(f"New rule location: {dest_file}")
    else:
        hdbg.dfatal("Copy action is only supported for skills and rules")
