#!/usr/bin/env python3
"""
The script is designed to synchronize GitHub issue labels from a label
inventory manifest file. It requires certain dependencies to be present (e.g.,
`pygithub`) and thus it is executed as a dockerized executable.

To use this script, you need to provide the input file, GitHub
repository name, owner, token environment variable, and optional flags
for controlling the synchronization behavior.

The command lines are the same as the `dev_scripts_helpers/github/sync_gh_issue_labels.py` script.
"""

import argparse
import logging
import os
from typing import Dict, List

import yaml

# TODO(gp): Use hdbg.WARNING
_WARNING = "\033[33mWARNING\033[0m"


try:
    import github
except ModuleNotFoundError:
    _module = "pygithub"
    print(_WARNING + f": Can't find {_module}: continuing")


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

    # #########################################################################
    # Label loading/saving
    # #########################################################################

    @staticmethod
    def load_labels(path: str) -> List["Label"]:
        """
        Load labels from label inventory manifest file.

        :param path: path to label inventory manifest file
        :return: label objects
        """
        with open(path, "r", encoding="utf-8") as file:
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

    @staticmethod
    def save_labels(labels: List["Label"], path: str) -> None:
        """
        Save labels to the label inventory manifest file.

        :param labels: label objects
        :param path: path to save the label inventory manifest file to
        """
        with open(path, "w", encoding="utf-8") as file:
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
    parser.add_argument(
        "--no_interactive",
        action="store_true",
        help="Do not prompt for confirmation before executing actions",
    )
    return parser


# TODO(sandeep): Split _main() into multiple functions.
def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Load labels from label inventory manifest file.
    labels = Label.load_labels(args.input_file)
    labels_map = {label.name: label for label in labels}
    token = os.environ[args.token_env_var]
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
        git_root_dir = hgit.get_client_root(False)
        file_name = f"tmp.labels.{args.owner}.{args.repo}.yaml"
        file_path = f"{git_root_dir}/{file_name}"
        Label.save_labels(current_labels, file_path)
        _LOG.info("Labels backed up to %s", file_path)
    else:
        _LOG.warning("Skipping saving labels as per user request")
    # Confirm label synchronization.
    if not args.no_interactive:
        hsystem.query_yes_no(
            "Are you sure you want to synchronize labels?", abort_on_no=True
        )
    else:
        _LOG.warning("Running in non-interactive mode, skipping confirmation")
    # Delete labels if pruning is enabled.
    if args.prune:
        for current_label in current_labels:
            if current_label.name not in labels_map:
                if execute:
                    current_label.delete()
                    _LOG.info("Label '%s' deleted", current_label.name)
                else:
                    _LOG.info(
                        "Label '%s' will be deleted without --dry_run",
                        current_label.name,
                    )
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
                _LOG.info("Label '%s' created", label.name)
            else:
                _LOG.info(
                    "Label '%s' will be created without --dry_run", label.name
                )
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
                _LOG.info("Label '%s' updated", label.name)
            else:
                _LOG.warning(
                    "Label '%s' will be updated without --dry_run",
                    label.name,
                )
        else:
            # Label exists and is identical.
            _LOG.info("Label '%s' not changed", label.name)
    _LOG.info("Label synchronization completed!")


if __name__ == "__main__":
    _main(_parse())
