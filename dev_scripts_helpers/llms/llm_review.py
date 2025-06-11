#!/usr/bin/env python3

"""
Review files automatically using LLMs.

The script `dockerized_llm_review.py` is executed within a Docker container to ensure
all dependencies are met. The Docker container is built dynamically if
necessary. The script requires an OpenAI API key to be set in the environment.

Usage example:

# Review specified files.
> llm_review.py --files="dir1/file1.py dir2/file2.md dir3/file3.ipynb dir3/file3.py"
"""

import argparse
import logging
import os
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


def _run_dockerized_llm_review(
    file_paths: List[str],
    guidelines_doc_filename: str,
    reviewer_log: str,
    force_rebuild: bool,
    use_sudo: bool,
    log_level: str,
) -> None:
    """
    Run `dockerized_llm_review.py` in a Docker container.

    The Docker container has all the necessary dependencies.

    :param file_paths: paths to files to review
    :param guidelines_doc_filename: name of the file with the review
        guidelines
    :param reviewer_log: path to the file to save the review to
    :param force_rebuild: whether to rebuild the container image
    :param use_sudo: whether to run the container with sudo
    :param log_level: level of logging, e.g., "DEBUG", "CRITICAL"
    """
    _LOG.debug(hprint.func_signature_to_str())
    #
    hdbg.dassert_in("OPENAI_API_KEY", os.environ)
    # Build the container.
    container_image = "tmp.llm_review"
    dockerfile = r"""
    FROM python:3.12-alpine

    # Install Bash.
    RUN apk add --no-cache bash

    # Set Bash as the default shell.
    SHELL ["/bin/bash", "-c"]

    # Install pip packages.
    RUN pip install --upgrade pip
    RUN pip install --no-cache-dir PyYAML pandas requests openai
    """
    container_image = hdocker.build_container_image(
        container_image,
        dockerfile,
        force_rebuild,
        use_sudo,
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    helpers_root = hgit.find_helpers_root()
    helpers_root_docker = hdocker.convert_caller_to_callee_docker_path(
        helpers_root,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Get the path to the script.
    script = hsystem.find_file_in_repo(
        "dockerized_llm_review.py", root_dir=hgit.find_git_root()
    )
    script_docker = hdocker.convert_caller_to_callee_docker_path(
        script,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    # Get the path to the review guidelines doc.
    review_guidelines_doc = hsystem.find_file_in_repo(
        guidelines_doc_filename, root_dir=hgit.find_git_root()
    )
    review_guidelines_doc_docker = hdocker.convert_caller_to_callee_docker_path(
        review_guidelines_doc,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    for file_path in file_paths:
        # Get the path to the file to review.
        in_file_path_docker = hdocker.convert_caller_to_callee_docker_path(
            file_path,
            caller_mount_path,
            callee_mount_path,
            check_if_exists=True,
            is_input=True,
            is_caller_host=is_caller_host,
            use_sibling_container_for_callee=use_sibling_container_for_callee,
        )
        # Build the command line.
        cmd = f" {script_docker} -i {in_file_path_docker}"
        cmd += f" --guidelines_doc_filename {review_guidelines_doc_docker}"
        cmd += f" --reviewer_log {reviewer_log}"
        cmd += f" -v {log_level}"
        docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
        docker_cmd.extend(
            [
                f"-e PYTHONPATH={helpers_root_docker}",
                f"--workdir {callee_mount_path}",
                f"--mount {mount}",
                container_image,
                cmd,
            ]
        )
        docker_cmd = " ".join(docker_cmd)
        # Run.
        hsystem.system(docker_cmd)
    # Output the generated comments to the user.
    output_from_file = hio.from_file(reviewer_log)
    print(hprint.frame(reviewer_log, char1="/").rstrip("\n"))
    print(output_from_file + "\n")
    print(hprint.line(char="/").rstrip("\n"))


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # File selection.
    parser.add_argument(
        "-f", "--files", nargs="+", type=str, help="Files to process"
    )
    parser.add_argument(
        "-d",
        "--dir_name",
        action="store",
        help="Select all the files in a dir. 'GIT_ROOT' to select git root",
    )
    parser.add_argument(
        "--modified",
        action="store_true",
        help="Select files modified in the current git client",
    )
    parser.add_argument(
        "--last_commit",
        action="store_true",
        help="Select files modified in the previous commit",
    )
    parser.add_argument(
        "--branch",
        action="store_true",
        help="Select files modified in the current branch with respect to master",
    )
    parser.add_argument(
        "--skip_files", nargs="+", type=str, help="Files to skip"
    )
    # Reviewer guidelines file.
    parser.add_argument(
        "--guidelines_doc_filename",
        action="store",
        help="Name of the document with the guidelines for automated reviewing",
        default="all.automated_review_guidelines.reference.md",
    )
    # Run parameters.
    parser.add_argument(
        "--reviewer_log",
        default="./reviewer_warnings.txt",
        help="File for storing the warnings",
    )
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser, log_level="CRITICAL")
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # Get the files to be reviewed.
    file_paths = liutils.get_files_to_check(
        args.files,
        args.skip_files,
        args.dir_name,
        args.modified,
        args.last_commit,
        args.branch,
    )
    _LOG.debug(
        "Reviewing %s files; file_paths=%s",
        len(file_paths),
        " ".join(file_paths),
    )
    _run_dockerized_llm_review(
        file_paths,
        args.guidelines_doc_filename,
        args.reviewer_log,
        args.dockerized_force_rebuild,
        args.dockerized_use_sudo,
        args.log_level,
    )


if __name__ == "__main__":
    _main(_parse())
