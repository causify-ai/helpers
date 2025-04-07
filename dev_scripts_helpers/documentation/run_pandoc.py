#!/usr/bin/env python

"""
Run pandoc on stdin/file to stdout/file.

- Read value from stdin/file
- Transform it using Pandoc according to different transforms
  (e.g., `convert_md_to_latex`)
- Write the result to stdout/file.

To run in vim:
```
:'<,'>!dev_scripts/documentation/run_pandoc.py -i - -o - -v CRITICAL
```

This script is derived from `dev_scripts/transform_skeleton.py`.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hlatex as hlatex
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_input_output_args(parser)
    parser.add_argument(
        "--action",
        action="store",
        default="convert_md_to_latex",
        help="Action to perform",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Parse files.
    in_file_name, out_file_name = hparser.parse_input_output_args(args)
    # Read file.
    txt = hparser.read_file(in_file_name)
    # Transform.
    txt_tmp = "\n".join(txt)
    if args.action == "convert_md_to_latex":
        txt_out = hlatex.convert_pandoc_md_to_latex(txt_tmp)
    else:
        hdbg.dfatal("Invalid action='%s'", args.action)
    # Write file.
    hparser.write_file(txt_out.split("\n"), out_file_name)


if __name__ == "__main__":
    _main(_parse())
