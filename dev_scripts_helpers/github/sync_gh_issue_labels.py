#!/usr/bin/env python3
"""
Synchronize GitHub issue labels from a YAML configuration file.

Examples

# Basic usage:
> sync_gh_issue_labels.py \
    --yaml ./labels/gh_issues_labels.yml \
    --owner causify-ai \
    --repo tutorials \
    --token *** \
    --backup
"""

import argparse
import logging
import sys
from typing import List

import requests
import yaml

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

        :param name: Label name
        :param description: Label description
        :param color: Label color in hex format
        """
        self.name = name
        self.description = description
        # Remove # prefix if present.
        self.color = color.lstrip("#")

    def __repr__(self):
        return f"Label(name='{self.name}', description='{self.description}', color='{self.color}')"


# #############################################################################
# GitHubClient
# #############################################################################


class GitHubClient:

    def __init__(self, token: str):
        """
        Initialize the client with a personal access token.

        :param token: GitHub personal access token
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_labels(self, owner: str, repo: str) -> List[Label]:
        """
        Get all labels from a repository.

        :param owner: GitHub repository owner/organization
        :param repo: GitHub repository name
        :return: List of Label objects
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/labels"
        labels = []
        page = 1
        per_page = 50
        while True:
            response = requests.get(
                url,
                headers=self.headers,
                params={"page": page, "per_page": per_page},
            )
            response.raise_for_status()
            page_labels = response.json()
            if not page_labels:
                break
            for label_data in page_labels:
                labels.append(
                    Label(
                        name=label_data["name"],
                        description=label_data.get("description", ""),
                        color=label_data["color"],
                    )
                )
            # Check if we've retrieved all pages.
            if len(page_labels) < per_page:
                break
            page += 1
        return labels

    def create_label(self, owner: str, repo: str, label: Label) -> None:
        """
        Create a new label in the repository.

        :param owner: GitHub repository owner/organization
        :param repo: GitHub repository name
        :param label: Label object to create
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/labels"
        data = {
            "name": label.name,
            "description": label.description,
            "color": label.color,
        }
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        _LOG.info("Label created: %s", label)

    def update_label(self, owner: str, repo: str, label: Label) -> None:
        """
        Update an existing label in the repository.

        :param owner: GitHub repository owner/organization
        :param repo: GitHub repository name
        :param label: Label object to update
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/labels/{label.name}"
        data = {
            "name": label.name,
            "description": label.description,
            "color": label.color,
        }
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        _LOG.info("Label updated: %s", label)

    def delete_label(self, owner: str, repo: str, name: str) -> None:
        """
        Delete a label from the repository.

        :param owner: GitHub repository owner/organization
        :param repo: GitHub repository name
        :param name: Label name to delete
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/labels/{name}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        _LOG.info("Label deleted: %s", name)


def load_manifest_to_labels(path: str) -> List[Label]:
    """
    Load label configurations from YAML file.

    :param path: path to YAML file
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
        _LOG.error("Error loading YAML file: %s", str(e))
        sys.exit(1)


def save_labels_to_manifest(labels: List[Label], path: str) -> None:
    """
    Save label configurations to YAML file.

    :param labels: List of Label objects
    :param path: path to save the YAML file to
    """
    try:
        with open(path, "w") as file:
            yaml_data = [
                {
                    "name": label.name,
                    "description": label.description,
                    "color": f"#{label.color}",
                }
                for label in labels
            ]
            yaml.dump(yaml_data, file, default_flow_style=False, sort_keys=False)
    except Exception as e:
        _LOG.error("Error saving YAML file: %s", str(e))
        sys.exit(1)


def sync_labels(
    client: GitHubClient, owner: str, repo: str, labels: List[Label], prune: bool
) -> None:
    """
    Synchronize labels between config and repository.
    """
    # Build maps for efficient lookup.
    label_map = {label.name: label for label in labels}
    current_labels = client.get_labels(owner, repo)
    current_label_map = {label.name: label for label in current_labels}
    # Delete labels if pruning is enabled.
    if prune:
        for current_label in current_labels:
            if current_label.name not in label_map:
                try:
                    client.delete_label(owner, repo, current_label.name)
                except Exception as e:
                    _LOG.error("Error deleting label %s: %s", current_label.name, e)
    # Create or update labels.
    for label in labels:
        current_label = current_label_map.get(label.name)
        try:
            if current_label is None:
                # Label doesn't exist, create it.
                client.create_label(owner, repo, label)
            elif (
                current_label.description != label.description
                or current_label.color != label.color
            ):
                # Label exists but needs update.
                client.update_label(owner, repo, label)
            else:
                # Label exists and is identical.
                _LOG.info("Label not changed: %s", label)
        except Exception as e:
            _LOG.error("Error processing label %s: %s", label.name, e)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--yaml",
        "-y",
        required=True,
        help="Path to YAML file with label definitions",
    )
    parser.add_argument(
        "--owner",
        "-o",
        required=True,
        help="GitHub repository owner/organization",
    )
    parser.add_argument(
        "--repo", "-r", required=True, help="GitHub repository name"
    )
    parser.add_argument(
        "--token", "-t", required=True, help="GitHub personal access token"
    )
    parser.add_argument(
        "--prune",
        "-p",
        action="store_true",
        help="Delete labels that exist in the repo but not in the YAML file",
    )
    parser.add_argument(
        "--dry_run",
        "-d",
        action="store_true",
        help="Print out the labels and exits immediately",
    )
    parser.add_argument(
        "--backup",
        "-b",
        action="store_true",
        help="Backup current labels to YAML file",
    )
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Load labels from YAML file.
    labels = load_manifest_to_labels(args.yaml)
    if args.dry_run:
        for label in labels:
            _LOG.info(label)
        sys.exit(0)
    client = GitHubClient(args.token)
    if args.backup:
        current_labels = client.get_labels(args.owner, args.repo)
        root_dir = hgit.get_client_root(False)
        dst_dir = f"{root_dir}/dev_scripts_helpers/github/labels/backup"
        file_name = f"labels.{args.owner}.{args.repo}.yaml"
        file_path = f"{dst_dir}/{file_name}"
        save_labels_to_manifest(current_labels, file_path)
        _LOG.info("Labels backed up to %s", file_path)
    hsystem.query_yes_no(
        "Are you sure you want to synchronize labels?", abort_on_no=True
    )
    # Sync labels.
    sync_labels(client, args.owner, args.repo, labels, args.prune)
    _LOG.info("Label synchronization completed!")


if __name__ == "__main__":
    _main(_parse())
