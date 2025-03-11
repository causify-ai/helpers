#!/usr/bin/env python
"""
Convert a TikZ file to a PNG image using a dockerized version of `pdflatex` and
`imagemagick`.
"""

import argparse
import logging
import os

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    hparser.add_dockerized_script_arg(parser)
    parser.add_argument("-i", "--input", action="store", required=True)
    parser.add_argument("-o", "--output", action="store", required=True)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = ["-density 300", "-quality 10"]
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    run_latex_again = True
    file_out = os.path.basename(args.input).replace(".tex", ".pdf")
    hdocker.run_basic_latex(args.input, cmd_opts, run_latex_again, file_out,
                            force_rebuild=args.dockerized_force_rebuild,
                            use_sudo=args.dockerized_use_sudo)
    # _LOG.debug("cmd_opts: %s", cmd_opts)
    # hdbg.dassert_file_extension(args.input, "tex")
    # hdbg.dassert_file_extension(args.output, "png")
    # # There is a horrible bug in pdflatex that if the input file is not the last
    # # one the output directory is not recognized.
    # cmd = (
    #     "pdflatex"
    #     + " -output-directory=."
    #     + " -interaction=nonstopmode"
    #     + " -halt-on-error"
    #     + " -shell-escape"
    #     + f" {args.input}"
    # )
    # hdocker.run_dockerized_latex(
    #     cmd,
    #     force_rebuild=args.dockerized_force_rebuild,
    #     use_sudo=args.dockerized_use_sudo,
    # )
    # # Get the path of the output file created by Latex.
    # file_out = os.path.basename(args.input).replace(".tex", ".pdf")
    #
    hdocker.run_dockerized_imagemagick(
        file_out,
        args.output,
        # f"-density 300 -quality 10",
        cmd_opts,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    #
    _LOG.info("Output written to '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
