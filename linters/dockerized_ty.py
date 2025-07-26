#!/usr/bin/env python

"""
Dockerized template.

This script is a template for creating a Dockerized script.

> ty check --output-format concise --color never --exclude '**/outcomes/**' --exclude '**/import_check/example/**' .
"""

import argparse
import logging
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hserver as hserver
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    # Create an ArgumentParser instance with the provided docstring.
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Add Docker-specific arguments (e.g., --dockerized_force_rebuild,
    # --dockerized_use_sudo).
    hparser.add_dockerized_script_arg(parser)
    # Add logging verbosity parsing.
    hparser.add_verbosity_arg(parser)
    return parser


def run_dockerized_ty(
    cmd_opts: List[str],
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
    """
    """
    _LOG.debug(hprint.func_signature_to_str())
    container_image = "tmp.ty"
    dockerfile = r"""
    FROM causify/helpers:dev

    RUN sudo bash -c "(source /venv/bin/activate; pip install ty)"
    """
    container_image = hdocker.build_container_image(
        container_image, dockerfile, force_rebuild, use_sudo
    )
    # Convert files to Docker paths.
    is_caller_host = not hserver.is_inside_docker()
    use_sibling_container_for_callee = True
    caller_mount_path, callee_mount_path, mount = hdocker.get_docker_mount_info(
        is_caller_host, use_sibling_container_for_callee
    )
    in_file_path = hdocker.convert_caller_to_callee_docker_path(
        in_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=True,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    out_file_path = hdocker.convert_caller_to_callee_docker_path(
        out_file_path,
        caller_mount_path,
        callee_mount_path,
        check_if_exists=True,
        is_input=False,
        is_caller_host=is_caller_host,
        use_sibling_container_for_callee=use_sibling_container_for_callee,
    )
    #
    cmd_opts_str = " ".join(cmd_opts)
    graphviz_cmd = [
        "dot",
        f"{cmd_opts_str}",
        "-T png",
        "-Gdpi=300",
        f"-o {out_file_path}",
        in_file_path,
    ]
    graphviz_cmd = " ".join(graphviz_cmd)
    #
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            container_image,
            graphviz_cmd,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret

def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = []
    # Start the logger.
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # Run latex.
    hdocexec.run_basic_latex(
        args.input,
        cmd_opts,
        args.run_latex_again,
        args.output,
        force_rebuild=args.dockerized_force_rebuild,
        use_sudo=args.dockerized_use_sudo,
    )
    _LOG.info("Output written to '%s'", args.output)
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # TODO(*): Implement this.
    # pandoc_cmd = ()
    # _LOG.debug("Command: %s", pandoc_cmd)
    # hdocker.run_dockerized_pandoc(
    #    pandoc_cmd,
    #    container_type="pandoc_only",
    #    force_rebuild=args.dockerized_force_rebuild,
    #    use_sudo=args.dockerized_use_sudo,
    # )
    # _LOG.info("Finished converting '%s' to '%s'.", args.docx_file, args.md_file)


if __name__ == "__main__":
    _main(_parse())
