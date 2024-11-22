#!/usr/bin/env python
"""
Script to set batch of GitHub secrets/variables from `.json` file in one go.

Simple usage:

> ./dev_scripts_helpers/github/set_secrets_and_variables.py \
     --file 'dev_scripts/github/vars.json' \
     --repo 'cryptomtc/cmamp_test'

The JSON file looks like:
```
{
    "secrets": {
        "GH_ACTION_ACCESS_TOKEN": "***",
        "CK_AWS_ACCESS_KEY_ID": "***",
        "CK_AWS_SECRET_ACCESS_KEY": "***",
        "CK_TELEGRAM_TOKEN": "***",
    }
    "variables": {
        "CK_AWS_DEFAULT_REGION": "eu-north-1",
        "CK_AWS_S3_BUCKET": "ck-data",
    }
}
```
"""

import argparse
import logging
import pprint
import sys

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--file",
        action="store",
        required=True,
        type=str,
        help="Location of `.json` file with desired secrets.",
    )
    parser.add_argument(
        "--repo",
        action="store",
        required=True,
        type=str,
        help="On which repository command will be applied.",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove batch of secrets from GitHub.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print out the secrets and exits immediately.",
    )
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    file_dict = hio.from_json(args.file)
    # Sort secrets.
    if args.dry_run:
        print(pprint.pformat(file_dict))
        sys.exit(0)
    operation = "set" if not args.remove else "remove"
    for config_item in ["secrets", "variables"]:
        # Sort items before setting.
        for key, value in dict(sorted(file_dict[config_item].items())).items():
            # GitHub does not accept empty strings.
            hdbg.dassert_ne(value, "")
            cmd = [
                # E.g.: "secrets" -> gh secret x y.
                f"gh {config_item[:-1]} {operation} {key}",
                f"--repo {args.repo}",
            ]
            if not args.remove:
                cmd.insert(1, f'--body "{value}"')
            cmd = " ".join(cmd)
            rc = hsystem.system(cmd, abort_on_error=False)
            if rc != 0:
                _LOG.warning("cmd='%s' failed: continuing", cmd)
            else:
                _LOG.info("%s %s!", operation, key)
        _LOG.info("All %s are processed!", config_item)


if __name__ == "__main__":
    _main(_parse())
