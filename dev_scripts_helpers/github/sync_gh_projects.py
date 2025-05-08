#!/usr/bin/env python3
"""
The script compares a source GitHub Project (the template) with a destination
project and ensures all global fields from the template exist in the
destination.

It does NOT (currently not supported):
- Reorder fields or views
- Create views (view creation is not supported via GitHub API)
- Modify view filters, sort orders, or layout
- Delete extra fields or views
- Detect hidden fields or per-view field visibility

Usage:
    python sync_gh_projects.py \
        --owner "causify-ai" \
        --src-template "[TEMPLATE] Causify Project" \
        --dst-project "Buildmeister"

Options:
- `--dry-run`: Show what changes would be made without applying them.
- `--verbose`: Enable debug logging to see internal command execution.

What it does:
- Lists fields and views from both the source and destination projects
- Adds missing global fields (columns) from source to destination
- Logs a warning for any views missing in the destination (views are not created)
"""

import argparse
import json
import logging
import shlex
import sys
import textwrap
import typing

import helpers.hsystem as hsystem

# TODO(*): Add support for view creation once GitHub exposes `addProjectV2View` mutation.
# TODO(*): Support reordering of fields and views when GitHub adds position-based mutations.
# TODO(*): Implement `--delete-extra` to remove fields/views not in the template.
# TODO(*): Support syncing view filters, groupings, and layout once exposed via GraphQL.
# TODO(*): Handle per-view field visibility when GitHub exposes view-level metadata.

_LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _run_command(cmd: list) -> str:
    """
    Run a shell command.

    :param cmd: command arguments to execute
    :return: standard output of the executed command
    """
    cmd_str = " ".join(cmd)
    _, output = hsystem.system_to_string(
        cmd_str,
        abort_on_error=True,
        dry_run=False,
        log_level=logging.DEBUG,
    )
    out = typing.cast(str, output)
    return out


def _get_projects(owner: str) -> typing.List[typing.Dict[str, typing.Any]]:
    """
    Retrieve up to 100 Projects for the specified owner.

    :return: list of project dicts with 'title', 'id', and 'number' keys
    """
    cmd = [
        "gh",
        "project",
        "list",
        f"--owner={owner}",
        "--closed",
        "--limit=100",
        "--format=json",
    ]
    raw = _run_command(cmd)
    data = json.loads(raw)
    projects: typing.List[typing.Dict[str, typing.Any]]
    if isinstance(data, dict) and "projects" in data:
        projects = typing.cast(
            typing.List[typing.Dict[str, typing.Any]], data["projects"]
        )
    elif isinstance(data, list):
        projects = typing.cast(typing.List[typing.Dict[str, typing.Any]], data)
    else:
        _LOG.error("Unexpected response format from gh project list: %r", data)
        sys.exit(1)
    return projects


def get_project_titles(owner: str) -> typing.Optional[typing.List[str]]:
    """
    Return all project titles under the specified owner.

    :param owner: GitHub organization or user owning the projects
    :return: list of project titles, or None if none found
    """
    # Extract the title field from each project dictionary.
    title = [proj.get("title", "") for proj in _get_projects(owner)]
    return title


def _find_project(
    projects: typing.List[typing.Dict[str, typing.Any]], title: str
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    """
    Return the project dictionary matching the given title.

    :param projects: project dictionaries to search
    :param title: project title to match
    :return: matching project dictionary, or None if not found
    """
    matched_project: typing.Optional[typing.Dict[str, typing.Any]] = None
    for p in projects:
        if not isinstance(p, dict):
            _LOG.warning("Skipping non-dict entry in project list: %r", p)
            continue
        if p.get("title") == title:
            matched_project = p
            break
    return matched_project


def _get_structure(
    project_number: int, owner: str, _dry_run: bool = False
) -> typing.Dict[str, typing.List[typing.Tuple[str, str]]]:
    """
    Retrieve the field and view structure for a GitHub Project via GraphQL.

    :param project_number: numeric ID of the GitHub Project to inspect
    :param owner: organization or user that owns the project
    :param dry_run: if True, skip any side effects (currently unused)
    :return: 'fields' and 'views' keys, each a list of (id, name)
    """
    # Define the GraphQL query to fetch fields and views.
    raw = f"""
    query {{
      organization(login: "{owner}") {{
        projectV2(number: {project_number}) {{
          fields(first: 100) {{
            nodes {{
              ... on ProjectV2FieldCommon {{ id name }}
            }}
          }}
          views(first: 100) {{
            nodes {{ id name }}
          }}
        }}
      }}
    }}
    """
    # Format the query as a single line.
    single_line = " ".join(textwrap.dedent(raw).split())
    # Quote the query string for shell safety.
    escaped = shlex.quote(single_line)
    # Run the query via the GitHub CLI.
    cmd = ["gh", "api", "graphql", "-f", f"query={escaped}"]
    output = _run_command(cmd)
    data = json.loads(output)
    try:
        # Navigate to the project node in the response.
        project = data["data"]["organization"]["projectV2"]
    except (KeyError, TypeError):
        _LOG.error("Failed to retrieve project structure from GraphQL output")
        sys.exit(1)
    # Extract field and view names with IDs.
    fields = [
        (f["id"], f["name"]) for f in project.get("fields", {}).get("nodes", [])
    ]
    views = [
        (v["id"], v["name"]) for v in project.get("views", {}).get("nodes", [])
    ]
    _LOG.info("Project #%s structure:", project_number)
    _LOG.info("Fields: %s", [n for _, n in fields])
    _LOG.info("Views: %s", [n for _, n in views])
    _LOG.warning(
        "This script cannot detect per-view visibility, filters, grouping or ordering, "
        "since GitHubs GraphQL API does not expose them."
    )
    output = {"fields": fields, "views": views}
    return output


def _sync_structure(
    src_num: int, dst_num: int, owner: str, dry_run: bool = False
) -> None:
    """
    Create any fields present in the source but missing in the destination and
    Warn about any views missing in the destination.

    :param src_num: id of the template (source) project
    :param dst_num: id of the destination project
    :param dry_run: If True, only print what would happen
    """
    # Get structure of source and destination projects.
    src_struct = _get_structure(src_num, owner, dry_run)
    dst_struct = _get_structure(dst_num, owner, dry_run)
    # Extract field names from source.
    src_names = [name for fid, name in src_struct["fields"] if fid]
    # Build a map of field names to IDs in the destination.
    dst_map = {name: fid for fid, name in dst_struct["fields"] if fid}
    # Loop over fields to identify missing ones.
    for name in src_names:
        if name not in dst_map:
            if dry_run:
                _LOG.info("[DRY-RUN] Would create field: '%s'", name)
            else:
                _LOG.info("Creating field: '%s'", name)
                # Construct GraphQL mutation to create the field.
                mut = """
                mutation($pid: ID!, $n: String!) {
                addProjectV2Field(input: { projectId: $pid, name: $n }) {
                    projectV2Field { id }
                }
                }
                """
                # Prepare mutation variables.
                variables = json.dumps({"pid": dst_num, "n": name})
                _run_command(
                    [
                        "gh",
                        "api",
                        "graphql",
                        "-f",
                        f"query={mut}",
                        "-f",
                        f"variables={variables}",
                    ]
                )
    # Compare views and log warnings for missing ones.
    src_view_names = [name for vid, name in src_struct["views"] if vid]
    dst_view_names = [name for vid, name in dst_struct["views"] if vid]
    for name in src_view_names:
        if name not in dst_view_names:
            _LOG.warning(
                "View '%s' is missing in destination. "
                "GitHub API does not currently support view creation. Please add manually.",
                name,
            )
    _LOG.info("Structure sync %scomplete.", "(dry-run) " if dry_run else "")


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments for the script.

    :return: configured ArgumentParser instance.
    """
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--owner",
        required=True,
        help="GitHub organization or user owning the projects",
    )
    p.add_argument(
        "--src-template",
        required=True,
        help="Template project title to copy structure from",
    )
    p.add_argument(
        "--dst-project",
        required=True,
        help="Destination project title to sync structure to",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without making any changes",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output (DEBUG level)",
    )
    return p


def main() -> None:
    args = _parse().parse_args()
    # Enable DEBUG logging if verbose is set.
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    # Get all projects under the owner.
    projects = _get_projects(args.owner)
    # Find the source project by title.
    src = _find_project(projects, args.src_template)
    if src is None:
        sys.exit("Template not found")
    # Find the destination project by title.
    dst = _find_project(projects, args.dst_project)
    if dst is None:
        sys.exit("Destination not found")
    _LOG.info(
        "Syncing '%s' ➔ '%s'%s",
        args.src_template,
        args.dst_project,
        " [dry-run]" if args.dry_run else "",
    )
    # Perform the sync.
    _sync_structure(
        src["number"], dst["number"], args.owner, dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
