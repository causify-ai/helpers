#!/usr/bin/env python3
"""
Synchronize GitHub issue labels from a label inventory manifest file.

Examples

# Basic usage:
> ./dev_scripts_helpers/github/sync_gh_issue_labels.py \
    --input_file ./dev_scripts_helpers/github/labels/gh_issues_labels.yml \
    --owner causify-ai \
    --repo tutorials \
    --token_env_var GITHUB_TOKEN \
    --dry_run \
    --backup
"""

import argparse
import logging
import os
import subprocess
from typing import Dict, List

import yaml

try:
    import github
except ModuleNotFoundError:
    subprocess.call(["sudo", "/venv/bin/pip", "install", "pygithub"])
    import github

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Label
# #############################################################################


class Label:

    def __init__(self, name: str, description: str, color: str):
        """
        Initialize the label with name, description, and color.

        :param name: label name
        :param description: label description
        :param color: label color in hex format
        """
        self._name = name
        self._description = description
        # Remove '#' prefix from hex code if present.
        self._color = color.lstrip("#")

    def __repr__(self):
        return f"label(name='{self.name}', description='{self.description}', color='{self.color}')"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def color(self) -> str:
        return self._color

    def to_dict(self) -> Dict[str, str]:
        """
        Return label as a dictionary.

        :return: label as a dictionary
        """
        return {
            "name": self._name,
            "description": self._description,
            "color": self._color,
        }


def _load_labels(path: str) -> List[Label]:
    """
    Load labels from label inventory manifest file.

    :param path: path to label inventory manifest file
    :return: label objects
    """
    try:
        with open(path, "r") as file:
            yaml_data = yaml.safe_load(file)
            labels = [
                Label(
                    name=item["name"],
                    description=item["description"],
                    color=item["color"],
                )
                for item in yaml_data
            ]
            return labels
    except Exception as e:
        _LOG.error("Error loading label inventory manifest file: %s", str(e))
        raise e


def _save_labels(labels: List[Label], path: str) -> None:
    """
    Save labels to the label inventory manifest file.

    :param labels: label objects
    :param path: path to save the label inventory manifest file to
    """
    try:
        with open(path, "w") as file:
            labels_data = [
                Label(
                    name=label.name,
                    description=label.description if label.description else None,
                    color=label.color,
                ).to_dict()
                for label in labels
            ]
            # Set `default_flow_style=False` to use block style instead of
            # flow style for better readability.
            yaml.dump(
                labels_data, file, default_flow_style=False, sort_keys=False
            )
    except Exception as e:
        _LOG.error("Error saving label inventory manifest file: %s", str(e))
        raise e


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_verbosity_arg(parser)
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
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Load labels from label inventory manifest file.
    labels = _load_labels(args.input_file)
    labels_map = {label.name: label for label in labels}
    token = os.environ.get(args.token_env_var, None)
    hdbg.dassert(token)
    # Initialize GH client.
    client = github.Github(token)
    repo = client.get_repo(f"{args.owner}/{args.repo}")
    # Get current labels from the repo.
    current_labels = repo.get_labels()
    current_labels_map = {label.name: label for label in current_labels}
    # Execute code if not in dry run mode.
    execute = not args.dry_run
    # Save the labels if backup is enabled.
    if args.backup:
        root_dir = hgit.get_client_root(False)
        dst_dir = f"{root_dir}/dev_scripts_helpers/github/labels/backup"
        file_name = f"tmp.labels.{args.owner}.{args.repo}.yaml"
        file_path = f"{dst_dir}/{file_name}"
        if execute:
            _save_labels(current_labels, file_path)
        _LOG.info("Labels backed up to %s", file_path)
    # Confirm label synchronization.
    hsystem.query_yes_no(
        "Are you sure you want to synchronize labels?", abort_on_no=True
    )
    # Delete labels if pruning is enabled.
    if args.prune:
        for current_label in current_labels:
            if current_label.name not in labels_map:
                if execute:
                    current_label.delete()
                _LOG.info("Label deleted: %s", current_label.name)
    # Sync labels.
    # Create or update labels.
    for label in labels:
        current_label = current_labels_map.get(label.name)
        if current_label is None:
            # Label doesn't exist, create it.
            if execute:
                repo.create_label(
                    name=label.name,
                    color=label.color,
                    description=label.description,
                )
            _LOG.info("Label created: %s", label.name)
        elif (
            current_label.description != label.description
            or current_label.color != label.color
        ):
            # Label exists but needs update.
            if execute:
                current_label.edit(
                    name=label.name,
                    color=label.color,
                    description=label.description,
                )
            _LOG.info("Label updated: %s", label.name)
        else:
            # Label exists and is identical.
            _LOG.info("Label not changed: %s", label)
    _LOG.info("Label synchronization completed!")


if __name__ == "__main__":
    _main(_parse())
