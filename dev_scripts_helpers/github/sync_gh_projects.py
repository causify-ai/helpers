#!/usr/bin/env python3
"""
Synchronize the structure (fields and views) of a GitHub Projects Beta board
from a template project to a destination project, without touching title or
content.

Example:
    ./sync_gh_project_structure.py \
      --src-template "[TEMPLATE] Causify Project" \
      --dst-project "Buildmeister"

Helper: get_project_titles() returns all project titles for quick lookup.
"""

import argparse
import json
import logging
import subprocess
import sys

DEFAULT_OWNER = "causify-ai"
_LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _run_command(cmd: list) -> str:
    """
    Run a command and return its stdout or exit on error.
    """
    _LOG.debug("Running command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        _LOG.error(
            "Error running command:\n%s\n%s", " ".join(cmd), result.stderr.strip()
        )
        sys.exit(1)
    return result.stdout


def _get_projects() -> list:
    """
    Retrieve up to 100 Projects Beta boards for DEFAULT_OWNER (including
    closed).

    Returns list of dicts with 'title', 'id', and 'number'.
    """
    cmd = [
        "gh",
        "project",
        "list",
        "--owner",
        DEFAULT_OWNER,
        "--closed",
        "--limit",
        "100",
        "--format",
        "json",
    ]
    data = json.loads(_run_command(cmd))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "projects" in data:
        return data["projects"]
    _LOG.error("Unexpected response from gh project list: %r", data)
    sys.exit(1)


def get_project_titles() -> list:
    """
    Return all project titles under DEFAULT_OWNER for user reference.
    """
    return [proj.get("title", "") for proj in _get_projects()]


def _find_project(projects: list, title: str) -> dict:
    """
    Return the project dict whose title matches exactly, else None.
    """
    for p in projects:
        if p.get("title") == title:
            return p
    return None


def _get_structure(project_number: int) -> dict:
    """
    Use GitHub CLI to fetch fields and views for a ProjectV2 by number.

    Returns: {'fields': [(id,name), ...], 'views': [(id,name), ...]}
    """
    cmd = [
        "gh",
        "project",
        "view",
        str(project_number),
        "--owner",
        DEFAULT_OWNER,
        "--format",
        "json",
    ]
    output = _run_command(cmd)
    data = json.loads(output)
    fields = []
    views = []
    if "fields" in data:
        for f in data["fields"]:
            if isinstance(f, dict):
                fields.append((f.get("id"), f.get("name", "")))
            else:
                fields.append((None, f))
    if "views" in data:
        for v in data["views"]:
            if isinstance(v, dict):
                views.append((v.get("id"), v.get("name", "")))
            else:
                views.append((None, v))
    return {"fields": fields, "views": views}


def _sync_structure(src_num: int, dst_num: int) -> None:
    """
    Sync the fields and views order and presence from src → dst.
    """
    src_struct = _get_structure(src_num)
    dst_struct = _get_structure(dst_num)
    src_fields = [(fid, name) for fid, name in src_struct["fields"] if fid]
    src_names = [name for _, name in src_fields]
    dst_map = {name: fid for fid, name in dst_struct["fields"] if fid}
    # Create missing fields.
    for name in src_names:
        if name not in dst_map:
            _LOG.info("Creating field '%s'", name)
            mut = """
            mutation($pid: ID!, $n: String!) {
              addProjectV2Field(input: { projectId: $pid, name: $n }) {
                projectV2Field { id }
              }
            }
            """
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
    # Reorder fields using the correct GitHub mutation.
    dst_struct = _get_structure(dst_num)
    dst_map = {name: fid for fid, name in dst_struct["fields"] if fid}
    prev = None
    for name in src_names:
        fid = dst_map.get(name)
        if not fid:
            continue
        _LOG.info("Moving field '%s' after '%s'", name, prev)
        mv = """
        mutation($input: UpdateProjectV2FieldConfigurationPositionInput!) {
          updateProjectV2FieldConfigurationPosition(input: $input) {
            projectV2FieldConfiguration { id }
          }
        }
        """
        variables = json.dumps(
            {
                "input": {
                    "projectId": dst_num,
                    "fieldConfigurationId": fid,
                    "afterId": prev,
                }
            }
        )
        _run_command(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={mv}",
                "-f",
                f"variables={variables}",
            ]
        )
        prev = fid
    # Note: View reordering via API is not supported; we still filter and create.
    src_view_names = [name for vid, name in src_struct["views"] if vid]
    dst_map = {name: vid for vid, name in dst_struct["views"] if vid}
    # Create missing views.
    for name in src_view_names:
        if name not in dst_map:
            _LOG.info("Creating view '%s'", name)
            mut = """
            mutation($pid: ID!, $n: String!) {
              addProjectV2View(input: { projectId: $pid, name: $n }) {
                projectV2View { id }
              }
            }
            """
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
    # Reordering views is not available via GraphQL.
    _LOG.info("Structure sync complete.")


def _parse() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
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
    return p


def main():
    args = _parse().parse_args()
    projects = _get_projects()
    src = _find_project(projects, args.src_template) or sys.exit(
        "Template not found"
    )
    dst = _find_project(projects, args.dst_project) or sys.exit(
        "Destination not found"
    )
    _LOG.info("Syncing %r ➔ %r", args.src_template, args.dst_project)
    _sync_structure(src["number"], dst["number"])


if __name__ == "__main__":
    main()
