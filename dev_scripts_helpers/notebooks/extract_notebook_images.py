#!/usr/bin/env python
"""
Run Notebook Image Extraction inside a Docker container.

This script builds the container dynamically if necessary and extracts
images from the specified Jupyter notebook using the
NotebookImageExtractor module.

Run the module like:

- dev_scripts_helpers/notebooks/extract_notebook_images.py -i <input_file_path> -o <output_folder_path>

Example:

```bash
dev_scripts_helpers/notebooks/extract_notebook_images.py -i dev_scripts_helpers/notebooks/test_images.ipynb -o dev_scripts_helpers/notebooks/screenshots
```
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        required=True,
        help="Path to the input Jupyter notebook",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        required=True,
        help="Directory for output images",
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = []
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    hdocker.run_dockerized_notebook_image_extractor(
        args.input,
        args.output,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Extraction completed. Images saved in '%s'", args.output)


if __name__ == "__main__":
    _main(_parse())
