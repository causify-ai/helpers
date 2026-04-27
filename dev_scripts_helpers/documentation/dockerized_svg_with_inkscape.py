#!/usr/bin/env python
"""
Convert SVG to various formats using inkscape in a Docker container.

This script builds the container dynamically if necessary and converts SVG
files to various output formats (PNG, PDF, PS, EPS, SVG, EMF, WMF) using
inkscape.
"""

import argparse
import logging

import helpers.hdbg as hdbg
import dev_scripts_helpers.hdockerized_cli_utils as dshhclut
import helpers.hparser as hparser
import dev_scripts_helpers.documentation.lib_svg as dshdlisv

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        required=True,
        help="Path to input SVG file",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        required=True,
        help="Path to output file",
    )
    parser.add_argument(
        "--output_format",
        action="store",
        default="png",
        choices=["png", "pdf", "ps", "eps", "svg", "emf", "wmf"],
        help="Output format (default: png)",
    )
    hparser.add_dockerized_script_arg(parser)
    dshhclut.add_open_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    dshdlisv.run_dockerized_svg_with_inkscape(
        args.input,
        args.output,
        output_format=args.output_format,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)
    if args.open:
        dshhclut.open_file_on_macos(args.output)


if __name__ == "__main__":
    _main(_parse())
