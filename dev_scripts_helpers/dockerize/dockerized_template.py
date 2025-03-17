#!/usr/bin/env python

"""
Convert Docx file to Markdown.

- Download a Google Doc as a docx document

- Run this command in the same directory as the Markdown file:
> FILE_NAME="tmp"; ls $FILE_NAME
> dev_scripts/convert_docx_to_markdown.py --docx_file $FILE_NAME.docx --md_file $FILE_NAME.md
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _build_container() -> str:
    container_name = "convert_docx_to_markdown"
    txt = r"""
    FROM ubuntu:latest

    RUN apt-get update && \
        apt-get -y upgrade

    RUN apt-get install -y curl pandoc && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/*
    """
    txt = hprint.dedent()
    force_rebuild = False
    use_sudo = False
    container_name = hdocker.build_container_image(container_name, txt,
                                                   force_rebuild, use_sudo)
    return container_name


def _convert_docx_to_markdown(
    docx_file: str, md_file: str, md_file_figs: str
) -> None:
    """
    Convert Docx file to Markdown.

    :param docx_file: path to the Docx file
    :param md_file: path to the Markdown file
    :param md_file_figs: the folder containing the figures for Markdown
        file
    """
    _LOG.info("Converting Docx to Markdown...")
    hdbg.dassert_file_exists(docx_file)
    # Create the Markdown file.
    hsystem.system(f"touch {md_file}")
    docker_container_name = _build_container()
    # Run Docker container.
    cmd = f"rm -rf {md_file_figs}"
    hsystem.system(cmd)
    # Convert from Docx to Markdown.
    cmd = f"pandoc --extract-media {md_file_figs} -f docx -t markdown_strict -{md_file} {docx_file}"
    hdocker.run_container(docker_container_name, cmd)


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--docx_file",
        action="store",
        required=True,
        type=str,
        help="The Docx file that needs to be converted to Markdown",
    )
    parser.add_argument(
        "--md_file",
        action="store",
        required=True,
        type=str,
        help="The output Markdown file",
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    docx_file = args.docx_file
    md_file = args.md_file
    # The folder for the figures.
    md_file_figs = md_file.replace(".md", "_figs")
    _convert_docx_to_markdown(docx_file, md_file, md_file_figs)
    _LOG.info("Finished converting '%s' to '%s'.", docx_file, md_file)


if __name__ == "__main__":
    _main(_parse())
