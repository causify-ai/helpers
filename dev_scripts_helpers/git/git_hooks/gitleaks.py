#!/usr/bin/env python

"""
Run gitleaks checks to detect leaked secrets in staged files.

This script runs gitleaks security checks using Docker to scan for potential
secrets in the git repository. It uses the gitleaks configuration from
dev_scripts_helpers/git/gitleaks/gitleaks-rules.toml.

Examples:
    # Run gitleaks check on staged files
    > python dev_scripts_helpers/git/git_hooks/gitleaks.py

    # Run gitleaks check without aborting on error
    > python dev_scripts_helpers/git/git_hooks/gitleaks.py --no-abort-on-error

Import as:

import dev_scripts_helpers.git.git_hooks.gitleaks as dshgghogi
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hparser as hparser

import dev_scripts_helpers.git.git_hooks.utils as dshgghout

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--abort-on-error",
        action="store_true",
        default=True,
        help="Abort execution if gitleaks check fails (default: True)",
    )
    parser.add_argument(
        "--no-abort-on-error",
        action="store_false",
        dest="abort_on_error",
        help="Do not abort execution if gitleaks check fails",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Running gitleaks security check")
    # Run the gitleaks check from utils.
    dshgghout.check_gitleaks(abort_on_error=args.abort_on_error)
    _LOG.info("Gitleaks check completed successfully")


if __name__ == "__main__":
    _main(_parse())
