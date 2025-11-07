#!/usr/bin/env python
"""
Print a formatted release message for Docker image releases.

This script generates a Slack-formatted message containing the latest
changelog entry from a specified container directory.

Print release message for the root repo:
```bash
> dev_scripts_helpers/docker/print_release_message.py --container_dir_name .
```

Print release message for a submodule:
```bash
> dev_scripts_helpers/docker/print_release_message.py --container_dir_name amp
```
"""

import argparse
import os

import helpers.hdbg as hdbg
import helpers.hversion as hversio


def _format_release_message(changelog_entry: dict) -> str:
    """
    Format the release message for Slack.

    :param changelog_entry: dict with 'version', 'date', and 'changes'
        keys
    :return: formatted release message with header and changelog
    """
    message_parts = [
        "🚀 *The new image has been released:*",
        f"*{changelog_entry['version']}* ({changelog_entry['date']})",
    ]
    # Add changes.
    for change in changelog_entry["changes"]:
        message_parts.append(change)
    return "\n".join(message_parts)


def _print_release_message(container_dir_name: str) -> None:
    """
    Print the release message for the specified container directory.

    :param container_dir_name: directory where changelog.txt is located
        (e.g., "." for root, "amp" for submodule)
    """
    # Verify version can be extracted.
    version = hversio.get_changelog_version(container_dir_name)
    hdbg.dassert(
        version,
        msg=f"Could not extract version from changelog in {container_dir_name}",
    )
    # Get changelog path.
    changelog_path = os.path.join(container_dir_name, "changelog.txt")
    hdbg.dassert_file_exists(
        changelog_path,
        msg=f"Changelog file not found at {changelog_path}",
    )
    # Get the latest changelog entry using the helper.
    changelog_entry = hversio.get_latest_changelog_entry(changelog_path)
    hdbg.dassert(
        changelog_entry["version"],
        msg="Could not extract version from changelog entry",
    )
    # Format and print the message.
    message = _format_release_message(changelog_entry)
    print(message)


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--container_dir_name",
        default=".",
        help="Container directory name where changelog.txt is located (default: '.')",
    )
    return parser.parse_args()


def _main(args: argparse.Namespace) -> None:
    _print_release_message(args.container_dir_name)


if __name__ == "__main__":
    _main(_parse())
