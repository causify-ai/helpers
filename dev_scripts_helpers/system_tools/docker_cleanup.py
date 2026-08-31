#!/usr/bin/env python

"""
Reclaim disk space by removing unused Docker / Apple `container` data.

Cleans up, for the selected engine(s):
- Stopped containers
- Unused networks (`docker` only)
- Dangling volumes
- Build cache (`docker`: pruned in place; `apple`: builder container reset)
- Dangling images

Prints `system df` (or `container system df`) before and after all operations,
per engine, and a report of all images sorted by size and by creation date.

Defaults to `--no_dry_run`, so it actually deletes unless `--dry_run` is
passed.

# Usage Example

- Actually reclaim space on all installed/running engines:
  > docker_cleanup.py

- Preview what would be reclaimed on the `docker` engine only:
  > docker_cleanup.py --docker_engine docker --dry_run

- Actually reclaim space on the Apple `container` engine:
  > docker_cleanup.py --docker_engine apple

Import as:

import dev_scripts_helpers.system_tools.docker_cleanup as dsstdocl
"""

import argparse
import json
import logging
import re
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Low-level helpers.
# #############################################################################


def _run(cmd: str) -> str:
    """
    Run a read-only command and return its output.

    Never aborts on error since callers use this for best-effort reporting
    (e.g., a Docker sub-command that is not supported by the Apple `container`
    CLI).

    :param cmd: shell command to run (e.g., `docker system df`)
    :return: stdout of the command, or the error output if the command failed
    """
    _LOG.debug(hprint.to_str("cmd"))
    rc, output = hsystem.system_to_string(cmd, abort_on_error=False)
    if rc != 0:
        _LOG.warning("Command failed with rc=%d: '%s'\n%s", rc, cmd, output)
    return output


# Multiplier for each unit reported by `docker images` / `docker system df`
# (decimal, matching Docker's own SI-style formatting).
_DOCKER_SIZE_UNIT_MULTIPLIERS = {
    "B": 1.0,
    "KB": 1e3,
    "MB": 1e6,
    "GB": 1e9,
    "TB": 1e12,
}


def _parse_docker_size_to_bytes(size_str: str) -> float:
    """
    Convert a Docker human-readable size to bytes.

    :param size_str: size as printed by `docker images`/`docker system df`
        (e.g., `"25.21GB"`, `"0B"`)
    :return: size in bytes
    """
    match = re.match(r"^([\d.]+)\s*([A-Za-z]+)$", size_str.strip())
    # TODO(ai_gp): Use dassert_re_match and update coding.rules.md to explain to use this.
    hdbg.dassert(
        match is not None, "Cannot parse Docker size string '%s'", size_str
    )
    value_str, unit = match.groups()
    unit = unit.upper()
    hdbg.dassert_in(
        unit,
        _DOCKER_SIZE_UNIT_MULTIPLIERS,
        "Unsupported size unit in '%s'",
        size_str,
    )
    size_bytes = float(value_str) * _DOCKER_SIZE_UNIT_MULTIPLIERS[unit]
    return size_bytes


def _format_bytes(num_bytes: float) -> str:
    """
    Format a byte count using the same decimal units as `docker images`.

    :param num_bytes: size in bytes
    :return: human-readable size (e.g., `"25.21GB"`)
    """
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1000:
            formatted = f"{size:.2f}{unit}"
            return formatted
        size /= 1000
    formatted = f"{size:.2f}TB"
    return formatted


# Matches one row of `docker system df` output, e.g.:
#   Images          26        1         25.21GB   13.03GB (51%)
# The row type (e.g., "Local Volumes", "Build Cache") can contain internal
# spaces, so it is separated from the numeric columns via `\s{2,}`.
# TODO(ai_gp): Inline it and add verbose + comments.
_SYSTEM_DF_ROW_RE = re.compile(
    r"^(?P<type>[A-Za-z ]+?)\s{2,}"
    r"(?P<total>\d+)\s+"
    r"(?P<active>\d+)\s+"
    r"(?P<size>\S+)\s+"
    r"(?P<reclaimable>\S+)"
    r"(?:\s+\(\d+%\))?\s*$"
)


def _parse_docker_system_df(output: str) -> Dict[str, Dict[str, str]]:
    """
    Parse `docker system df` tabular output into a dict keyed by row type.

    :param output: raw stdout of `docker system df`
        Example:
        ```
        TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
        Build Cache     91        0         6.317GB   2.541GB
        ```
    :return: dict mapping row type to a dict with keys `total`, `active`,
        `size`, `reclaimable`
        Example:
        ```
        {"Build Cache": {"total": "91", "active": "0", "size": "6.317GB",
                          "reclaimable": "2.541GB"}}
        ```
    """
    result: Dict[str, Dict[str, str]] = {}
    for line in output.splitlines():
        match = _SYSTEM_DF_ROW_RE.match(line)
        if match is None:
            # Skip the header row and any other non-matching line.
            continue
        result[match.group("type").strip()] = {
            "total": match.group("total"),
            "active": match.group("active"),
            "size": match.group("size"),
            "reclaimable": match.group("reclaimable"),
        }
    return result


# #############################################################################
# Reporting.
# #############################################################################


def _report_system_df(engine: str, *, label: str) -> str:
    """
    Print `system df` (or `container system df`) for `engine`.

    :param engine: `"docker"` or `"apple"`
    :param label: short label identifying when this snapshot was taken
        (e.g., `"before"`, `"after"`)
    :return: raw command output, for callers that need to parse it further
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    cmd = f"{cmd_name} system df"
    output = _run(cmd)
    _LOG.info("## Disk usage (%s, engine='%s')\n%s", label, engine, output)
    return output


def _report_active_containers(engine: str) -> None:
    """
    Print the containers that are not touched by pruning.

    Only stopped containers are removed by `container prune`, so this is
    informational context showing what is being preserved.

    :param engine: `"docker"` or `"apple"`
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    if engine == "docker":
        cmd = (
            f'{cmd_name} ps -a --filter "status=running" '
            '--filter "status=paused" --filter "status=restarting"'
        )
    elif engine == "apple":
        _LOG.info(
            "Engine 'apple': no per-status container filter is available: "
            "listing all containers"
        )
        cmd = f"{cmd_name} list --all"
    else:
        raise ValueError(f"Invalid engine='{engine}'")
    output = _run(cmd)
    _LOG.info("## Active containers (not pruned)\n%s", output)


def _list_images_docker() -> List[Dict[str, Any]]:
    """
    List all Docker images with their size and creation date.

    :return: list of dicts with keys `name`, `created`, `size_bytes`
    """
    hdocker.set_docker_engine("docker")
    cmd_name = hdocker.get_docker_command()
    list_cmd = (
        f"{cmd_name} images --format "
        '"{{.ID}} {{.Repository}}:{{.Tag}} {{.Size}}"'
    )
    output = _run(list_cmd)
    images = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=2)
        hdbg.dassert_eq(
            len(parts),
            3,
            "Unexpected `docker images` line format: '%s'",
            line,
        )
        image_id, repo_tag, size_str = parts
        # `docker inspect` is called per image, matching how `docker images`
        # itself does not report the creation timestamp.
        created_cmd = f"{cmd_name} inspect -f '{{{{.Created}}}}' {image_id}"
        created = _run(created_cmd)
        size_bytes = _parse_docker_size_to_bytes(size_str)
        images.append(
            {"name": repo_tag, "created": created, "size_bytes": size_bytes}
        )
    return images


def _list_images_apple() -> List[Dict[str, Any]]:
    """
    List all Apple `container` images with their size and creation date.

    :return: list of dicts with keys `name`, `created`, `size_bytes`
    """
    hdocker.set_docker_engine("apple")
    cmd_name = hdocker.get_docker_command()
    cmd = f"{cmd_name} image list --format json"
    output = _run(cmd)
    images = []
    if output.strip():
        data = json.loads(output)
        for entry in data:
            config = entry.get("configuration", {})
            name = config.get("name", "")
            created = config.get("creationDate", "")
            variants = entry.get("variants", [])
            size_bytes = sum(variant.get("size", 0) for variant in variants)
            images.append(
                {"name": name, "created": created, "size_bytes": size_bytes}
            )
    return images


def _format_images_table(images: List[Dict[str, Any]]) -> str:
    """
    Format a list of images as a human-readable table.

    :param images: list of dicts with keys `name`, `created`, `size_bytes`
    :return: one line per image: `<name> <size> <created>`
    """
    lines = [
        f"{image['name']:<60} {_format_bytes(image['size_bytes']):>10} "
        f"{image['created']}"
        for image in images
    ]
    table = "\n".join(lines)
    return table


def _report_all_images(engine: str) -> None:
    """
    Print all images, sorted by size (descending) and by creation date
    (descending).

    :param engine: `"docker"` or `"apple"`
    """
    if engine == "docker":
        images = _list_images_docker()
    elif engine == "apple":
        images = _list_images_apple()
    else:
        raise ValueError(f"Invalid engine='{engine}'")
    images_by_size = sorted(
        images, key=lambda image: image["size_bytes"], reverse=True
    )
    images_by_date = sorted(
        images, key=lambda image: image["created"], reverse=True
    )
    _LOG.info(
        "## All images (%d), sorted by size (descending)\n%s",
        len(images),
        _format_images_table(images_by_size),
    )
    _LOG.info(
        "## All images (%d), sorted by creation date (descending)\n%s",
        len(images),
        _format_images_table(images_by_date),
    )


# #############################################################################
# Cleanup steps.
# #############################################################################


def _cleanup_stopped_containers(engine: str, *, dry_run: bool) -> None:
    """
    Remove stopped containers.

    :param engine: `"docker"` or `"apple"`
    :param dry_run: if True, only report what would be removed
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    if engine == "docker":
        list_cmd = (
            f'{cmd_name} ps -a --filter "status=exited" '
            '--filter "status=created" --filter "status=dead" '
            '--format "{{.ID}}: {{.Names}} ({{.Status}})"'
        )
        candidates = _run(list_cmd)
        if dry_run:
            _LOG.warning(
                "[DRY_RUN] Would remove stopped containers:\n%s",
                candidates or "(none)",
            )
        else:
            prune_cmd = f"{cmd_name} container prune -f"
            _, output = hsystem.system_to_string(prune_cmd)
            _LOG.info("Removed stopped containers:\n%s", output)
    elif engine == "apple":
        if dry_run:
            _LOG.warning(
                "[DRY_RUN] Would run: '%s prune' (Apple has no per-status "
                "filter, so the stopped-container set cannot be previewed)",
                cmd_name,
            )
        else:
            prune_cmd = f"{cmd_name} prune"
            _, output = hsystem.system_to_string(prune_cmd)
            _LOG.info("Removed stopped containers:\n%s", output)
    else:
        raise ValueError(f"Invalid engine='{engine}'")


def _cleanup_unused_networks(engine: str, *, dry_run: bool) -> None:
    """
    Remove unused networks.

    Not supported by the Apple `container` CLI (no network plugin installed
    by default), so this is a no-op for `engine == "apple"`.

    :param engine: `"docker"` or `"apple"`
    :param dry_run: if True, only report what would be removed
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    if engine == "docker":
        list_cmd = (
            f'{cmd_name} network ls --filter "dangling=true" '
            '--format "{{.ID}}: {{.Name}}"'
        )
        candidates = _run(list_cmd)
        if dry_run:
            _LOG.warning(
                "[DRY_RUN] Would remove unused networks:\n%s",
                candidates or "(none)",
            )
        else:
            prune_cmd = f"{cmd_name} network prune -f"
            _, output = hsystem.system_to_string(prune_cmd)
            _LOG.info("Removed unused networks:\n%s", output)
    elif engine == "apple":
        _LOG.info(
            "Engine 'apple': network prune not supported by apple engine "
            "(no network plugin installed by default): skipping"
        )
    else:
        raise ValueError(f"Invalid engine='{engine}'")


def _cleanup_dangling_volumes(engine: str, *, dry_run: bool) -> None:
    """
    Remove dangling volumes.

    :param engine: `"docker"` or `"apple"`
    :param dry_run: if True, only report what would be removed
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    if engine == "docker":
        list_cmd = f'{cmd_name} volume ls --filter "dangling=true" -q'
        output = _run(list_cmd)
        volume_ids = [
            line.strip() for line in output.splitlines() if line.strip()
        ]
        if not volume_ids:
            _LOG.info("No dangling volumes to remove")
            return
        if dry_run:
            _LOG.warning(
                "[DRY_RUN] Would remove %d dangling volume(s): %s",
                len(volume_ids),
                ", ".join(volume_ids),
            )
        else:
            # Never run `volume rm` with an empty argument list: guarded by
            # the `if not volume_ids: return` check above.
            rm_cmd = f"{cmd_name} volume rm " + " ".join(volume_ids)
            hsystem.system(rm_cmd)
            _LOG.info(
                "Removed %d dangling volume(s): %s",
                len(volume_ids),
                ", ".join(volume_ids),
            )
    elif engine == "apple":
        if dry_run:
            _LOG.warning("[DRY_RUN] Would run: '%s volume prune'", cmd_name)
        else:
            prune_cmd = f"{cmd_name} volume prune"
            _, output = hsystem.system_to_string(prune_cmd)
            _LOG.info("Removed dangling volumes:\n%s", output)
    else:
        raise ValueError(f"Invalid engine='{engine}'")


def _cleanup_build_cache(
    engine: str, *, dry_run: bool, system_df: Dict[str, Dict[str, str]]
) -> None:
    """
    Remove the build cache.

    The two engines store their build cache differently, so the reset
    mechanism differs:
    - `docker`: the cache is state inside the `dockerd` daemon, pruned in
      place via `builder prune`; the daemon itself is untouched
    - `apple`: the cache is the filesystem of a separate `buildkit` VM
      container, so it can only be cleared by deleting that container
      outright; it is restarted right after, so the next `container build`
      does not also pay a cold-start cost on top of the cold cache

    :param engine: `"docker"` or `"apple"`
    :param dry_run: if True, only report what would be removed
    :param system_df: parsed `docker system df` snapshot (from
        `_parse_docker_system_df()`), used to estimate the reclaimable space
        in dry-run mode since Docker has no per-cache-entry listing command
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    if engine == "docker":
        if dry_run:
            reclaimable = system_df.get("Build Cache", {}).get(
                "reclaimable", "unknown"
            )
            _LOG.warning(
                "[DRY_RUN] Would remove build cache: reclaimable=%s",
                reclaimable,
            )
        else:
            prune_cmd = f"{cmd_name} builder prune -a -f"
            _, output = hsystem.system_to_string(prune_cmd)
            _LOG.info("Removed build cache:\n%s", output)
    elif engine == "apple":
        # Unlike Docker's `builder prune`, there is no cache to inspect
        # independently of the builder container itself: check whether the
        # container exists at all first, mirroring how the dangling-volume
        # / dangling-image branches above check for candidates before
        # mutating anything.
        status_output = _run(f"{cmd_name} builder status")
        # A builder that exists reports a header row plus one data row; no
        # builder means only the header (or an error message).
        if len(status_output.strip().splitlines()) <= 1:
            _LOG.info("No builder container found: skipping")
            return
        if dry_run:
            _LOG.warning(
                "[DRY_RUN] Would run: '%s builder stop', '%s builder "
                "delete', '%s builder start' (drops all cached build "
                "layers)",
                cmd_name,
                cmd_name,
                cmd_name,
            )
        else:
            _, stop_output = hsystem.system_to_string(
                f"{cmd_name} builder stop"
            )
            _LOG.info("Stopped builder:\n%s", stop_output)
            _, delete_output = hsystem.system_to_string(
                f"{cmd_name} builder delete"
            )
            _LOG.info(
                "Deleted builder (dropped all cached build layers):\n%s",
                delete_output,
            )
            _, start_output = hsystem.system_to_string(
                f"{cmd_name} builder start"
            )
            _LOG.info("Restarted builder:\n%s", start_output)
    else:
        raise ValueError(f"Invalid engine='{engine}'")


def _cleanup_dangling_images(engine: str, *, dry_run: bool) -> None:
    """
    Remove dangling images.

    :param engine: `"docker"` or `"apple"`
    :param dry_run: if True, only report what would be removed
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    if engine == "docker":
        list_cmd = f'{cmd_name} images --filter "dangling=true" -q'
        output = _run(list_cmd)
        image_ids = [
            line.strip() for line in output.splitlines() if line.strip()
        ]
        if not image_ids:
            _LOG.info("No dangling images to remove")
            return
        if dry_run:
            _LOG.warning(
                "[DRY_RUN] Would remove %d dangling image(s): %s",
                len(image_ids),
                ", ".join(image_ids),
            )
        else:
            # Never run `rmi` with an empty argument list: guarded by the
            # `if not image_ids: return` check above.
            rmi_cmd = f"{cmd_name} rmi -f " + " ".join(image_ids)
            hsystem.system(rmi_cmd)
            _LOG.info(
                "Removed %d dangling image(s): %s",
                len(image_ids),
                ", ".join(image_ids),
            )
    elif engine == "apple":
        # Dangling only, per the script's policy: `--all` is never passed.
        if dry_run:
            _LOG.warning("[DRY_RUN] Would run: '%s image prune'", cmd_name)
        else:
            prune_cmd = f"{cmd_name} image prune"
            _, output = hsystem.system_to_string(prune_cmd)
            _LOG.info("Removed dangling images:\n%s", output)
    else:
        raise ValueError(f"Invalid engine='{engine}'")


# #############################################################################
# Orchestration.
# #############################################################################


def _cleanup_engine(engine: str, *, dry_run: bool) -> None:
    """
    Run all cleanup steps for a single engine.

    :param engine: `"docker"` or `"apple"`
    :param dry_run: if True, only report what would be removed
    """
    hdocker.set_docker_engine(engine)
    # TODO(ai_gp): Use hprint.frame
    _LOG.info("%s", "#" * 80)
    _LOG.info("Engine: '%s'", engine)
    _LOG.info("%s", "#" * 80)
    # Disk usage before any operation.
    before_output = _report_system_df(engine, label="before")
    system_df = (
        _parse_docker_system_df(before_output) if engine == "docker" else {}
    )
    # Containers not touched by pruning (informational only).
    _report_active_containers(engine)
    # Remove stopped containers.
    _cleanup_stopped_containers(engine, dry_run=dry_run)
    # Remove unused networks.
    _cleanup_unused_networks(engine, dry_run=dry_run)
    # Remove dangling volumes.
    _cleanup_dangling_volumes(engine, dry_run=dry_run)
    # Remove build cache.
    _cleanup_build_cache(engine, dry_run=dry_run, system_df=system_df)
    # Remove dangling images.
    _cleanup_dangling_images(engine, dry_run=dry_run)
    # Report all images, sorted by size and by creation date.
    _report_all_images(engine)
    # Disk usage after all operations.
    _report_system_df(engine, label="after")


def _is_engine_available(engine: str) -> bool:
    """
    Check whether `engine`'s CLI is installed and running.

    Logs a warning (not an error) when unavailable, so callers can skip the
    engine instead of crashing.

    :param engine: `"docker"` or `"apple"`
    :return: True if the engine's CLI is installed and its daemon/service is
        running
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    is_available = True
    if not hsystem.check_exec(cmd_name):
        _LOG.warning(
            "Engine '%s': '%s' CLI is not installed: skipping",
            engine,
            cmd_name,
        )
        is_available = False
    elif not hdocker.is_docker_running():
        _LOG.warning(
            "Engine '%s': '%s' is not running: skipping", engine, cmd_name
        )
        is_available = False
    return is_available


def _get_engines(docker_engine: str) -> List[str]:
    """
    Resolve the `--docker_engine` CLI value into a list of engines to
    process.

    :param docker_engine: value of `--docker_engine` (`"docker"`, `"apple"`,
        or `"all"`)
    :return: list of engine names to process, in order
    """
    if docker_engine == "all":
        engines = ["docker", "apple"]
    else:
        engines = [docker_engine]
    return engines


# #############################################################################
# CLI.
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--docker_engine",
        action="store",
        choices=["docker", "apple", "all"],
        default="all",
        help="Container engine(s) to clean up",
    )
    hparser.add_bool_arg(
        parser,
        "dry_run",
        default_value=False,
        help_="Print what would be deleted instead of actually deleting it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.debug(hprint.to_str("args.docker_engine args.dry_run"))
    engines = _get_engines(args.docker_engine)
    for engine in engines:
        if not _is_engine_available(engine):
            continue
        _cleanup_engine(engine, dry_run=args.dry_run)


if __name__ == "__main__":
    _main(_parse())
