#!/usr/bin/env python

"""
Convert Docx file to markdown using Dockerized `pandoc` and save the figs in a
directory.

# Usage:

1) Download a Google Doc as a docx document

2) Run this command in the same directory as the Markdown file:

> IN_FILE_NAME="/Users/saggese/Downloads/Blank.docx"; ls $FILE_NAME
> OUT_FILE_NAME="paper/paper.md"
> convert_docx_to_markdown.py --docx_file $IN_FILE_NAME --md_file $OUT_FILE_NAME
"""

import argparse
import logging
import os
import shutil

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _move_media(md_file_figs: str) -> None:
    """
    Move the media if it exists.
    """
    _LOG.info("Moving media...")
    media_dir = os.path.join(md_file_figs, "media")
    if os.path.isdir(media_dir):
        # Move all the files in 'media' to 'md_file_figs'.
        for file_name in os.listdir(media_dir):
            file_path = os.path.join(media_dir, file_name)
            shutil.move(file_path, md_file_figs)
        # Remove the 'media' directory.
        shutil.rmtree(media_dir)
    else:
        _LOG.info("No media directory found.")


def _clean_up_artifacts(md_file: str, md_file_figs: str) -> None:
    """
    Remove the artifacts.

    :param md_file: path to the Markdown file
    :param md_file_figs: path to the folder containing the artifacts
    """
    _LOG.info("Cleaning up artifacts...")
    # TODO(gp): Use f-strings to avoid the linter error.
    perl_regex_replacements = [
        # # \# Running PyCharm remotely -> # Running PyCharm remotely.
        rf"perl -pi -e 's:# (\\#)+ :# :g' {md_file}",
        # \#\# Docker image"  -> ## Docker image.
        rf"perl -pi -e 's:\\#:#:g' {md_file}",
        # **## amp / cmamp container** -> ## amp / cmamp container.
        rf"perl -pi -e 's:\*\*#(.*?)\*\*:#$1:g' {md_file}",
        # -  Typically instructions include information about which packages and
        #    > their versions to install, e.g. list of python packages and their
        #    > corresponding versions
        rf"perl -pi -e 's:^(\s+)> :$1:g' {md_file}",
        # >
        # > botocore==1.24.37
        # >
        rf"perl -pi -e 's:^>: :g' {md_file}",
        # Remove the \ before - $ | " _ [ ].
        rf"perl -pi -e 's:\\([-\$|\"\_\]\[\.]):$1:g' {md_file}",
        # \' -> '.
        rf'perl -pi -e "s:\\\':\':g" {md_file}',
        # \` -> `.
        rf"perl -pi -e 's:\\\`:\`:g' {md_file}",
        # \* -> *.
        rf"perl -pi -e 's:\\\*:\*:g' {md_file}",
        # “ -> ".
        rf"perl -pi -e 's:“:\":g' {md_file}",
        # ” -> ".
        rf"perl -pi -e 's:”:\":g' {md_file}",
        # Remove trailing \.
        rf"perl -pi -e 's:\\$::g' {md_file}",
        # Remove ========= and --------.
        rf"perl -pi -e 's:======+::g' {md_file}",
        rf"perl -pi -e 's:------+::g' {md_file}",
        # Translate HTML elements.
        rf"perl -pi -e 's:\&gt;:\>:g' {md_file}",
        rf"perl -pi -e 's:\<\!\-\-.*\-\-\>::g' {md_file}",
        # Fix image links.
        rf"perl -pi -e 's:{md_file_figs}/media/:{md_file_figs}/:g' {md_file}",
        # Remove underling like
        # [<u>Uber: Faster Together: Uber Engineering’s iOS
        #  Monorepo</u>](https://www.uber.com/blog/ios-monorepo/)
        rf"perl -pi -e 's/<\/?u>//g' {md_file}",
    ]
    # Run the commands.
    for clean_cmd in perl_regex_replacements:
        hsystem.system(clean_cmd, suppress_output=False)


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
        help="The Docx file to convert to Markdown",
    )
    parser.add_argument(
        "--md_file",
        action="store",
        required=True,
        type=str,
        help="The output Markdown file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    docx_file = args.docx_file
    md_file = args.md_file
    # Create the folder for the figures.
    md_file_figs = md_file.replace(".md", "_figs")
    hio.create_dir(md_file_figs, incremental=False)
    # Convert from Docx to Markdown.
    cmd = (
        f"pandoc {docx_file} --extract-media {md_file_figs} "
        f"-f docx -t markdown_strict --output {md_file}"
    )
    container_type = "pandoc_only"
    hdocker.run_dockerized_pandoc(cmd, container_type)
    _move_media(md_file_figs)
    _clean_up_artifacts(md_file, md_file_figs)
    _LOG.info("Finished converting '%s' to '%s'.", docx_file, md_file)


if __name__ == "__main__":
    _main(_parse())
