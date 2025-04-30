#!/usr/bin/env python3
"""
Synchronize GitHub issue labels from a label inventory manifest file.

This script builds the container dynamically if necessary and synchronizes GitHub
issue labels using the provided manifest file.

Synchronize labels for the `helpers` repository from a YAML manifest file with a dry run.
```bash
> ./dev_scripts_helpers/github/sync_gh_issue_labels.py \
    --input_file ./dev_scripts_helpers/github/labels/gh_issues_labels.yml \
    --owner causify-ai \
    --repo tutorials \
    --token_env_var GITHUB_TOKEN \
    --dry_run \
    --backup
```
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--input_file",
        required=True,
        help="Path to label inventory manifest file",
    )
    parser.add_argument(
        "--owner",
        required=True,
        help="GitHub repository owner/organization",
    )
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument(
        "--token_env_var",
        required=True,
        help="Name of the environment variable containing the GitHub token",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete labels that exist in the repo but not in the label inventory manifest file",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print out the actions that would be taken without executing them",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup current labels to a label inventory manifest file",
    )
    parser.add_argument(
        "--no_interactive",
        action="store_true",
        help="Do not prompt for confirmation before executing actions",
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _run_dockerized_sync_gh_issue_labels(
    input_file: str,
    owner: str,
    repo: str,
    token_env_var: str,
    *,
    prune: bool = False,
    dry_run: bool = False,
    backup: bool = False,
    no_interactive: bool = False,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run GitHub label synchronization in a Docker container.

    :param input_file: Path to label inventory manifest file
    :param owner: GitHub repository owner/organization
    :param repo: GitHub repository name
    :param token_env_var: Name of the environment variable containing
        the GitHub token
    :param prune: Delete labels that exist in the repo but not in the
        manifest
    :param dry_run: Print actions without executing them
    :param backup: Backup current labels to a manifest file
    :param no_interactive: Do not prompt for confirmation
    :param force_rebuild: If True, rebuild the container image
    :param use_sudo: If True, run the container with sudo
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Build the container image, if needed.
    container_image = "tmp.sync_gh_issue_labels"
    dockerfile = r"""
    FROM python:3.10-slim

    # Install required packages.
    RUN apt-get update && apt-get install -y git && \
        apt-get clean && rm -rf /var/lib/apt/lists/*
    RUN pip install PyGithub PyYAML

    WORKDIR /app
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert file paths to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    input_file = hdocker.convert_caller_to_callee_docker_path(
        input_file,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    helpers_root = hgit.find_helpers_root()
    helpers_root = hdocker.convert_caller_to_callee_docker_path(
        helpers_root,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Build the command.
    git_root = hgit.find_git_root()
    docker_executable = "dockerized_sync_gh_issue_labels.py"
    script = hsystem.find_file_in_repo(docker_executable, root_dir=git_root)
    script = hdocker.convert_caller_to_callee_docker_path(
        script,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    cmd = [
        script,
        f"--input_file {input_file}",
        f"--owner {owner}",
        f"--repo {repo}",
        f"--token_env_var {token_env_var}",
    ]
    if prune:
        cmd.append("--prune")
    if dry_run:
        cmd.append("--dry_run")
    if backup:
        cmd.append("--backup")
    if no_interactive:
        cmd.append("--no_interactive")
    cmd = " ".join(cmd)
    # Build the Docker command.
    docker_executable = hdocker.get_docker_executable(use_sudo)
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"-e {token_env_var}",
            f"-e PYTHONPATH={helpers_root}",
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    hsystem.system(docker_cmd)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    _run_dockerized_sync_gh_issue_labels(
        args.input_file,
        args.owner,
        args.repo,
        args.token_env_var,
        prune=args.prune,
        dry_run=args.dry_run,
        backup=args.backup,
        no_interactive=args.no_interactive,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Label synchronization completed!")


if __name__ == "__main__":
    _main(_parse())
