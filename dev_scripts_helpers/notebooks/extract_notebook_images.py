#!/usr/bin/env python
"""
Extract images from a Jupyter notebook by running inside a Docker container.

This script builds the container dynamically if necessary and extracts images
from the specified Jupyter notebook using the NotebookImageExtractor module.

Extract images from notebook test_images.ipynb and save them to `screenshots`
directory.
```bash
> dev_scripts_helpers/notebooks/extract_notebook_images.py \
    -i dev_scripts_helpers/notebooks/test_images.ipynb \
    -o dev_scripts_helpers/notebooks/screenshots
```
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--in_notebook_filename",
        required=True,
        type=str,
        help="Input notebook filename",
    )
    parser.add_argument(
        "--out_image_dir",
        required=True,
        type=str,
        help="Output image directory",
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _run_dockerized_extract_notebook_images(
    notebook_path: str,
    output_dir: str,
    *,
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> None:
    """
    Run `NotebookImageExtractor` in a Docker container.

    :param notebook_path: Path to the input Jupyter notebook
    :param output_dir: Directory for output images
    :param force_rebuild: If True, rebuild the container image
    :param use_sudo: If True, run the container with sudo
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Build the container image, if needed.
    container_image = "tmp.extract_notebook_images"
    dockerfile = r"""
    FROM python:3.10-slim

    # Install required system libraries for Chromium and Playwright.
    RUN apt-get update && apt-get install -y \
        libglib2.0-0 \
        libnss3 \
        libnspr4 \
        libdbus-1-3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libexpat1 \
        libatspi2.0-0 \
        libdbus-glib-1-2 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libxkbcommon0 \
        libasound2 \
        libcups2 \
        libpango-1.0-0 \
        libcairo2 \
        && rm -rf /var/lib/apt/lists/*

    # Set the environment variable for Playwright to install browsers in a known
    # location.
    ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

    # Create the directory for Playwright browsers and ensure it's writable.
    RUN mkdir -p /ms-playwright && chmod -R 777 /ms-playwright

    # Install required packages.
    RUN pip install nbconvert nbformat playwright pyyaml

    # Install Playwright browsers.
    RUN python -m playwright install

    WORKDIR /app
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert file paths to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    notebook_path = hdocker.convert_caller_to_callee_docker_path(
        notebook_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    output_dir = hdocker.convert_caller_to_callee_docker_path(
        output_dir,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=False,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    helpers_root = hgit.find_helpers_root()
    helpers_root = hdocker.convert_caller_to_callee_docker_path(
        helpers_root,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Build the command.
    git_root = hgit.find_git_root()
    docker_executable = "dockerized_extract_notebook_images.py"
    script = hsystem.find_file_in_repo(docker_executable, root_dir=git_root)
    script = hdocker.convert_caller_to_callee_docker_path(
        script,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    cmd = [
        script,
        f"--in_notebook_filename {notebook_path}",
        f"--out_image_dir {output_dir}",
    ]
    cmd = " ".join(cmd)
    # Build the Docker command.
    docker_executable = hdocker.get_docker_executable(use_sudo)
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"-e PLAYWRIGHT_BROWSERS_PATH=/ms-playwright",
            f"-e PYTHONPATH={helpers_root}",
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    hsystem.system(docker_cmd)


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    _run_dockerized_extract_notebook_images(
        args.in_notebook_filename,
        args.out_image_dir,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Extraction completed. Images saved in '%s'", args.out_image_dir)


if __name__ == "__main__":
    _main(_parse())
