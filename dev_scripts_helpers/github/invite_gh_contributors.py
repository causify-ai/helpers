#!/usr/bin/env python3
"""
Invite GitHub collaborators listed in a Google Sheet/CSV while obeying the
50-invite / 24-hour cap by creating a docker container and running
`dockerized_invite_gh_contributors`

# Invite to the repo `causify-ai/tutorials` the users in the passed Google Sheet:
> invite_gh_contributors.py \
    --drive_url "https://docs.google.com/spreadsheets/d/1Ez5uRvOgvDMkFc9c6mI21kscTKnpiCSh4UkUh_ifLIw
    /edit?gid=0#gid=0" \
    --org_name causify-ai \
    --repo_name tutorials

# Invite to the repo `causify-ai/tutorials` the users in the passed CSV file:
> invite_gh_contributors.py \
    --csv_file "/tmp/github_users.csv" \
    --org_name causify-ai \
    --repo_name tutorials
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Set build-time constants.

REQUIRED_PACKAGES: List[str] = [
    "pygithub",
    "google-api-python-client",
    "oauth2client",
    "gspread",
    "ratelimit",
    "pyyaml",
    "pandas",
    "requests",
]

INNER_SCRIPT_REL = "dockerized_invite_gh_contributors.py"

CONTAINER_IMAGE_BASE = "tmp.invite_gh_contributors"


def _run_dockerized_invite(args: argparse.Namespace) -> None:  # noqa: D401
    """
    Build image and run the inner script in Docker.
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Add required packages.
    packages_line = " " + " ".join(REQUIRED_PACKAGES)
    dockerfile = rf"""
    FROM python:3.12-slim
    RUN pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir{packages_line}
    WORKDIR /app
    ENTRYPOINT ["python"]
    """
    container_image = hdocker.build_container_image(
        CONTAINER_IMAGE_BASE,
        dockerfile,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    # Mount repo and convert paths.
    is_host = not hserver.is_inside_docker()
    sibling = True
    caller_mount, callee_mount, mount_str = hdocker.get_docker_mount_info(
        is_host, sibling
    )
    # Locate inner script.
    inner_script_host = hsystem.find_file_in_repo(
        INNER_SCRIPT_REL, root_dir=hgit.find_git_root()
    )
    inner_script_docker = hdocker.convert_caller_to_callee_docker_path(
        inner_script_host,
        caller_mount,
        callee_mount,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_host,
        use_sibling_container_for_callee=sibling,
    )
    # Resolve helper imports.
    helpers_root_host = hgit.find_helpers_root()
    helpers_root_docker = hdocker.convert_caller_to_callee_docker_path(
        helpers_root_host,
        caller_mount,
        callee_mount,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_host,
        use_sibling_container_for_callee=sibling,
    )
    # Build Flags.
    passthrough: List[str] = []
    for flag, value in vars(args).items():
        if flag.startswith("dockerized_") or flag == "log_level":
            continue
        if value is None or value is False:
            continue
        # Translate path-like args.
        if flag == "csv_file":
            csv_host = os.path.abspath(str(value))
            csv_docker = hdocker.convert_caller_to_callee_docker_path(
                csv_host,
                caller_mount,
                callee_mount,
                check_if_exists=True,
                is_input=True,
                is_caller_host=is_host,
                use_sibling_container_for_callee=sibling,
            )
            passthrough.extend(["--csv_file", csv_docker])
            continue
        # Propagate flags.
        if isinstance(value, bool):
            passthrough.append(f"--{flag}")
        else:
            passthrough.extend([f"--{flag}", str(value)])
    passthrough_str = " ".join(passthrough)
    # Run Docker.
    docker_cmd_parts = hdocker.get_docker_base_cmd(args.dockerized_use_sudo)
    docker_cmd_parts.extend(
        [
            "-e GITHUB_TOKEN",
            f"-e PYTHONPATH={helpers_root_docker}",
            f"--workdir {callee_mount}",
            f"--mount {mount_str}",
            container_image,
            f"{inner_script_docker} {passthrough_str}",
        ]
    )
    docker_cmd = " ".join(docker_cmd_parts)
    _LOG.debug("Docker cmd: %s", docker_cmd)
    hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode="system"
    )


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invite GitHub collaborators from a Google Sheet, respecting limit.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Set `--drive_url` and `--csv_file` to be mutually exclusive.
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--drive_url",
        help="Google Sheet URL containing a 'GitHub user' column",
    )
    input_group.add_argument(
        "--csv_file",
        help="Path to CSV file containing a 'GitHub user' column",
    )
    parser.add_argument(
        "--repo_name", required=True, help="Target repository name (without org)"
    )
    parser.add_argument(
        "--org_name", required=True, help="GitHub organisation name"
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser.parse_args()


def _main(args: argparse.Namespace) -> None:
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert(
        os.getenv("GITHUB_TOKEN"),
        "Environment variable GITHUB_TOKEN must be set",
    )
    _run_dockerized_invite(args)


if __name__ == "__main__":
    _main(_parse())
