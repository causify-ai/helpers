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
import helpers.hio as hio
import helpers.hdocker as hdocker
import helpers.hsystem as hsystem
import helpers.hserver as hserver
import helpers.hprint as hprint
import helpers.hdockerized_executables as hdocexec
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

_STANDARD_TY_ARGS = (
    "--output-format concise --color never --exclude '**/outcomes/**' --exclude '**/import_check/example/**' | tee ty.log"
)

def _parse() -> argparse.ArgumentParser:
    # Create an ArgumentParser instance with the provided docstring.
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--no_use_standard_ty_args",
        dest="use_standard_ty_args",
        action="store_false",
        default=True,
        help=f"Use the standard ty arguments ({_STANDARD_TY_ARGS})",
    )
    # Add Docker-specific arguments (e.g., --dockerized_force_rebuild,
    # --dockerized_use_sudo).
    hparser.add_dockerized_script_arg(parser)
    # Add logging verbosity parsing.
    hparser.add_verbosity_arg(parser)
    return parser


def _run_dockerized_ty(
    cmd_opts: List[str],
    use_standard_ty_args: bool,
    *,
    mode: str = "system",
    force_rebuild: bool = False,
    use_sudo: bool = False,
) -> str:
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
    # docker run -it --rm --user $(id -u):$(id -g) \
    #   -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN \
    #   ...
    #   --workdir /app --mount
    #   type=bind,source=/Users/saggese/src/umd_msml6101,target=/app \
    #   --entrypoint "" tmp.ty.arm64.c94f3fcd bash -c "/venv/bin/ty check
    #   /app/helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py"
    cmd_opts_out = hdocker.convert_all_paths_from_caller_to_callee_docker_path(
        cmd_opts,
        caller_mount_path,
        callee_mount_path,
        is_caller_host,
        use_sibling_container_for_callee,
    )
    if use_standard_ty_args:
        cmd_opts_out.extend(_STANDARD_TY_ARGS.split())
    cmd_opts_str = " ".join(cmd_opts_out)
    cmd_opts_str = f"bash -c '/venv/bin/ty {cmd_opts_str}'"
    # Build the docker command.
    docker_cmd = hdocker.get_docker_base_cmd(use_sudo)
    docker_cmd.extend(
        [
            f"--workdir {callee_mount_path} --mount {mount}",
            "--entrypoint ''",
            container_image,
            cmd_opts_str,
        ]
    )
    docker_cmd = " ".join(docker_cmd)
    # Run the docker command.
    ret = hdocker.process_docker_cmd(
        docker_cmd, container_image, dockerfile, mode
    )
    return ret


def _main(parser: argparse.ArgumentParser) -> None:
    # Parse everything that can be parsed and returns the rest.
    args, cmd_opts = parser.parse_known_args()
    if not cmd_opts:
        cmd_opts = []
    _LOG.info("cmd_opts=%s", cmd_opts)
    # Start the logger.
    hdbg.init_logger(
        verbosity=args.log_level, use_exec_path=True, force_white=False
    )
    # Run ty.
    # TODO(gp): This approach doesn't work since we need to configure PYTHONPATH.
    # _run_dockerized_ty(
    #     cmd_opts,
    #     args.use_standard_ty_args,
    #     force_rebuild=args.dockerized_force_rebuild,
    #     use_sudo=args.dockerized_use_sudo,
    # )
    # Create a script with instructions to install and run ty.
    if args.use_standard_ty_args:
        cmd_opts.extend(_STANDARD_TY_ARGS.split())
    cmd_opts_str = " ".join(cmd_opts)
    script = f"""
    #!/bin/bash -xe
    sudo bash -c "(source /venv/bin/activate; pip install ty)"
    /venv/bin/ty {cmd_opts_str}
    """
    script = hprint.dedent(script)
    file_name = "tmp.dockerized_ty.sh"
    hio.create_executable_script(file_name, script)
    #
    cmd = f"invoke docker_cmd --cmd='{file_name}'"
    # ty returns an error code if there are linting errors.
    abort_on_error = False
    hsystem.system(cmd, abort_on_error=abort_on_error, suppress_output=False)
    #
    _LOG.info("Output written to 'ty.log'")


if __name__ == "__main__":
    _main(_parse())
