#!/usr/bin/env python3
"""
Build a thin virtual environment to run workflows on the dev container.

The environment is built with `pip` by default, or with `uv` using
`--installer uv`.

# Usage Example

- Build the thin environment with `pip`:
> build.py

- Build the thin environment with `uv`:
> build.py --installer uv
"""

import argparse
import logging
import os
import platform
import shutil
import subprocess

import thin_client_utils as tcu

import helpers.repo_config_utils as hrecouti
from helpers import hdbg, hparser, hprint, hserver, hsystem

_LOG = logging.getLogger(__name__)

SCRIPT_PATH = os.path.abspath(__file__)


def _system(cmd: str) -> None:
    print(hprint.frame(cmd))
    hsystem.system(cmd, suppress_output=False)


def _create_venv(installer: str, venv_dir: str) -> None:
    """
    Create the virtual environment with the selected installer.

    :param installer: tool used to build the env (`pip` or `uv`)
    :param venv_dir: dir of the virtual environment
    """
    if installer == "uv":
        # `--seed` installs `pip` in the venv, so that the `uv` env has the
        # same tools as the `pip` one.
        _system(f"uv venv --seed --python python3 {venv_dir}")
    else:
        _system(f"python3 -m venv {venv_dir}")
        # Test activating the environment.
        _system(f"source {venv_dir}/bin/activate")


def _install_requirements(
    installer: str, venv_dir: str, requirements_path: str
) -> None:
    """
    Install the requirements in the virtual environment and show them.

    :param installer: tool used to build the env (`pip` or `uv`)
    :param venv_dir: dir of the virtual environment
    :param requirements_path: file with the packages to install
    """
    if installer == "uv":
        # `uv` targets the venv through its Python, without activating it.
        python_bin = f"{venv_dir}/bin/python"
        _system(f"uv pip install --python {python_bin} -r {requirements_path}")
        _system(f"uv pip list --python {python_bin}")
    else:
        activate_cmd = f"source {venv_dir}/bin/activate"
        _system(f"{activate_cmd} && python3 -m pip install --upgrade pip")
        _system(f"{activate_cmd} && pip3 install -r {requirements_path}")
        # Show the package list.
        _system("pip3 list")


def _main(parser: argparse.ArgumentParser) -> None:
    print(f"##> {SCRIPT_PATH}")
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _, python_version = hsystem.system_to_string("python3 --version")
    _LOG.info("# python=%s", python_version)
    try:
        _, aws_version = hsystem.system_to_string("aws --version")
        _LOG.info("# aws=%s", aws_version)
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "AWS CLI is not installed. Please install it and try again."
        )
    if args.installer == "uv":
        # Fail before deleting the old virtual environment.
        hdbg.dassert_is_not(
            shutil.which("uv"),
            None,
            "uv is not installed: run 'brew install uv' or see "
            "https://docs.astral.sh/uv/",
        )
        _, uv_version = hsystem.system_to_string("uv --version")
        _LOG.info("# uv=%s", uv_version)
    dir_suffix = hrecouti.get_repo_config().get_dir_suffix()
    # Create the virtual environment.
    venv_dir = tcu.get_venv_dir(dir_suffix)
    # Double check that the dir is in home.
    hdbg.dassert(
        venv_dir.startswith(os.environ["HOME"] + "/src/venv"),
        "Invalid venv_dir='%s'",
        venv_dir,
    )
    if os.path.isdir(venv_dir):
        if not args.do_not_confirm:
            # Confirm.
            msg = f"Delete old virtual environment in '{venv_dir}'?"
            hsystem.query_yes_no(msg)
        msg = f"Deleting dir '{venv_dir}' ..."
        _LOG.warning(msg)
        shutil.rmtree(venv_dir)
        msg = f"Deleting dir '{venv_dir}' ... done"
    _LOG.info(
        "Creating virtual environment in %s with %s", venv_dir, args.installer
    )
    _create_venv(args.installer, venv_dir)
    # Install the requirements.
    thin_environ_dir = tcu.get_thin_environment_dir(dir_suffix)
    requirements_path = os.path.join(thin_environ_dir, "requirements.txt")
    tmp_requirements_path = os.path.join(
        thin_environ_dir, "tmp.requirements.txt"
    )
    shutil.copy(requirements_path, tmp_requirements_path)
    if platform.system() == "Darwin" or (
        platform.system() == "Linux" and not hserver.is_dev_csfy()
    ):
        # Pinning down the package version for running locally on Mac and Linux,
        # see HelpersTask377.
        with open(tmp_requirements_path, "a") as f:
            f.write("pyyaml == 5.3.1\n")
    _install_requirements(args.installer, venv_dir, tmp_requirements_path)
    if hserver.is_host_mac():
        # Darwin specific updates.
        _system("brew update")
        _, brew_ver = hsystem.system_to_string("brew --version")
        _LOG.info("# brew version=%s", brew_ver)
        _system("brew install gh")
        _, gh_ver = hsystem.system_to_string("gh --version")
        _LOG.info("# gh version=%s", gh_ver)
        # Uncomment if you want to install dive
        # run_command("brew install dive")
        # dive_ver = run_command("dive --version")
        # _LOG.info("dive version=%s", dive_ver)
    elif hserver.is_external_linux():
        # Linux specific updates.
        # Install GitHub CLI on linux ubuntu system using apt.
        # Installation instructions based on the official GitHub CLI documentation:
        # https://github.com/cli/cli/blob/trunk/docs/install_linux.md
        commands = [
            "type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)",
            "sudo mkdir -p -m 755 /etc/apt/keyrings",
            (
                "out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg "
                "&& cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null"
            ),
            "sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg",
            (
                'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] '
                'https://cli.github.com/packages stable main" | '
                "sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
            ),
            "sudo apt update",
            "sudo apt install gh -y",
        ]
        for command in commands:
            _system(command)
        _, gh_ver = hsystem.system_to_string("gh --version")
        _LOG.info("# gh version=%s", gh_ver)
    _LOG.info("%s successful", SCRIPT_PATH)


def _parse() -> argparse.ArgumentParser:
    # Create the parser.
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--installer",
        action="store",
        choices=["pip", "uv"],
        default="pip",
        help="Tool used to create the virtual environment and install packages",
    )
    parser.add_argument(
        "--do_not_confirm",
        action="store_true",
        help="Do not ask for user confirmation",
        required=False,
    )
    return parser


if __name__ == "__main__":
    # Parse the arguments.
    _main(_parse())
