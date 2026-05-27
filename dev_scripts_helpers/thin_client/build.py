#!/usr/bin/env python3
"""
Build a thin virtual environment used to drive the dev container from the host.

The Python interpreter version is read from `repo_config.yaml`
(`python_info.python_version`) so that the thin env, the dev container, and any
Lambda / IaC layers stay in lock-step. The build defaults to `uv` because it is
much faster, deterministic, and can fetch the pinned interpreter when the host
does not have it; it can also fall back to plain `pip` + `python3 -m venv` when
the user passes `--use_pip`, to keep backward compatibility with the historical
flow.

Import as:

import dev_scripts_helpers.thin_client.build as dshtcbu
"""

import argparse
import logging
import os
import platform
import shutil
import subprocess
from typing import Tuple

import thin_client_utils as tcu

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)

SCRIPT_PATH = os.path.abspath(__file__)


# #############################################################################
# Helpers
# #############################################################################


def _system(cmd: str) -> None:
    """
    Run a shell command, echoing it in a banner first.

    :param cmd: Command to execute
    """
    print(hprint.frame(cmd))
    hsystem.system(cmd, suppress_output=False)


def _is_uv_available() -> bool:
    """
    Return whether the `uv` CLI is on `PATH`.

    :return: `True` when `uv --version` succeeds; `False` otherwise
    """
    # `which uv` keeps the check shell-portable and avoids importing uv.
    rc, _ = hsystem.system_to_string("which uv", abort_on_error=False)
    return rc == 0


def _bootstrap_uv() -> None:
    """
    Install `uv` into the user's site-packages if it is not already on
    `PATH`.

    The thin env exists precisely so that the host can drive the dev
    container, so we bootstrap with the host Python via `pip --user` (with
    `--break-system-packages` to support PEP 668 distributions such as
    Ubuntu 24.04). On a fresh host this is the only network round-trip
    needed before `uv` itself takes over.
    """
    if _is_uv_available():
        _LOG.info("# `uv` already available on PATH; skipping bootstrap")
        return
    _LOG.info("# `uv` not found on PATH; bootstrapping via pip --user")
    # `--break-system-packages` is a no-op on non-PEP-668 systems and
    # required on Ubuntu 24.04 / Debian 12 etc.; pass it unconditionally to
    # avoid host-specific branches.
    _system(
        "python3 -m pip install --user --break-system-packages --upgrade uv"
    )
    if not _is_uv_available():
        # The user-site bin directory is not always on PATH on a fresh
        # host. Surface a clear error rather than letting the next `uv`
        # call die with `command not found`.
        raise RuntimeError(
            "uv was installed but is not on PATH. Add "
            "`$(python3 -m site --user-base)/bin` to PATH and retry, or "
            "rerun with `--use_pip` to skip uv."
        )


def _print_tool_versions() -> Tuple[str, str]:
    """
    Print the host Python and AWS CLI versions to the log.

    :return: Tuple `(python_version, aws_version)` as the strings reported
        by the tools themselves
    """
    _, python_version = hsystem.system_to_string("python3 --version")
    _LOG.info("# python=%s", python_version)
    try:
        _, aws_version = hsystem.system_to_string("aws --version")
        _LOG.info("# aws=%s", aws_version)
    except subprocess.CalledProcessError:
        # The thin env drives `aws` for S3 uploads, backups, etc., so a
        # missing CLI here is a hard fail.
        raise RuntimeError(
            "AWS CLI is not installed. Please install it and try again."
        )
    return python_version, aws_version


def _materialize_requirements(
    requirements_path: str, tmp_requirements_path: str
) -> None:
    """
    Copy the project's pinned thin-env requirements into a temp file so
    that any future host-specific overrides can be appended without
    touching the source file.

    :param requirements_path: Source `requirements.txt` checked into the
        repo
    :param tmp_requirements_path: Destination path written into the
        thin-env dir; preserved on disk for debugging (`tmp.*` prefix)
    """
    shutil.copy(requirements_path, tmp_requirements_path)
    # Historically we appended `pyyaml == 5.3.1` here on Mac and external
    # Linux (HelpersTask377) but that pin is incompatible with Python 3.12
    # and the underlying issue is fixed by `pyyaml >= 6.0.1` in
    # `requirements.txt`. Left as a hook for future host-specific pins.
    _ = platform.system, hserver.is_dev_csfy


def _build_with_uv(
    *, venv_dir: str, python_version: str, requirements_path: str
) -> None:
    """
    Create the thin env and install requirements using `uv`.

    :param venv_dir: Destination directory for the virtual environment
    :param python_version: Pinned major.minor (or major.minor.patch)
        Python version that `uv` should resolve / install
    :param requirements_path: Path to the requirements file to install
    """
    hdbg.dassert_ne(
        python_version, "", "python_version must not be empty"
    )
    _bootstrap_uv()
    _, uv_version = hsystem.system_to_string("uv --version")
    _LOG.info("# uv=%s", uv_version)
    # Ensure an interpreter matching the pin is available; `uv python
    # install` is a no-op when the version is already present.
    _system(f"uv python install {python_version}")
    _system(
        f"uv venv --python {python_version} --seed --clear {venv_dir}"
    )
    # `--no-cache` keeps thin-env rebuilds reproducible (the dev container
    # is the place to benefit from caching); `--strict` makes mismatched
    # wheels fail loudly.
    _system(
        f"uv pip install --python {venv_dir}/bin/python "
        f"--requirements {requirements_path} --strict"
    )
    _system(f"{venv_dir}/bin/python -m pip list")


def _build_with_pip(
    *, venv_dir: str, requirements_path: str
) -> None:
    """
    Create the thin env and install requirements using the historical
    `python3 -m venv` + `pip install` flow.

    This is the explicit `--use_pip` fallback for environments where `uv`
    is not desired (e.g., a host on which the user has not yet authorized
    `--break-system-packages`).

    :param venv_dir: Destination directory for the virtual environment
    :param requirements_path: Path to the requirements file to install
    """
    _system(f"python3 -m venv {venv_dir}")
    activate_cmd = f"source {venv_dir}/bin/activate"
    # Sanity-check that activation works before paying the install cost.
    _system(activate_cmd)
    _system(f"{activate_cmd} && python3 -m pip install --upgrade pip")
    _system(f"{activate_cmd} && pip3 install -r {requirements_path}")
    _system("pip3 list")


def _install_host_tools() -> None:
    """
    Install host-side conveniences (`gh`, etc.) that are not Python
    packages and therefore live outside the venv.
    """
    if hserver.is_host_mac():
        # Darwin specific updates.
        _system("brew update")
        _, brew_ver = hsystem.system_to_string("brew --version")
        _LOG.info("# brew version=%s", brew_ver)
        #
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


# #############################################################################
# Entry point
# #############################################################################


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Drive the thin-env build end-to-end.

    :param parser: Configured argument parser
    """
    print(f"##> {SCRIPT_PATH}")
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    # Print versions so the log preserves what the host looked like.
    _print_tool_versions()
    repo_config = hrecouti.get_repo_config()
    dir_suffix = repo_config.get_dir_suffix()
    python_version = repo_config.get_python_version()
    _LOG.info("# pinned python_version=%s", python_version)
    # Create the virtual environment dir.
    venv_dir = tcu.get_venv_dir(dir_suffix)
    # Double check that the dir is in home.
    hdbg.dassert(
        venv_dir.startswith(os.environ["HOME"] + "/src/venv"),
        "Invalid venv_dir='%s'",
        venv_dir,
    )
    if os.path.isdir(venv_dir):
        if not args.do_not_confirm:
            # Confirm before nuking an existing venv.
            msg = f"Delete old virtual environment in '{venv_dir}'?"
            hsystem.query_yes_no(msg)
        msg = f"Deleting dir '{venv_dir}' ..."
        _LOG.warning(msg)
        shutil.rmtree(venv_dir)
        msg = f"Deleting dir '{venv_dir}' ... done"
    _LOG.info("Creating virtual environment in %s", venv_dir)
    # Materialize the host-specific requirements file.
    thin_environ_dir = tcu.get_thin_environment_dir(dir_suffix)
    requirements_path = os.path.join(thin_environ_dir, "requirements.txt")
    tmp_requirements_path = os.path.join(
        thin_environ_dir, "tmp.requirements.txt"
    )
    _materialize_requirements(requirements_path, tmp_requirements_path)
    # Dispatch on the chosen build tool.
    if args.use_pip:
        _LOG.info("# Building thin env with `pip` (uv disabled)")
        _build_with_pip(
            venv_dir=venv_dir,
            requirements_path=tmp_requirements_path,
        )
    else:
        _LOG.info("# Building thin env with `uv`")
        _build_with_uv(
            venv_dir=venv_dir,
            python_version=python_version,
            requirements_path=tmp_requirements_path,
        )
    # Host-side tools (`gh`, brew, apt).
    _install_host_tools()
    _LOG.info("%s successful", SCRIPT_PATH)


def _parse() -> argparse.ArgumentParser:
    """
    Build the argument parser for the script.

    :return: Configured `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_verbosity_arg(parser)
    parser.add_argument(
        "--do_not_confirm",
        action="store_true",
        help="Do not ask for user confirmation",
        required=False,
    )
    parser.add_argument(
        "--use_pip",
        action="store_true",
        help=(
            "Fall back to the historical `python3 -m venv` + `pip install` "
            "flow instead of using `uv`. Provided for backward compatibility "
            "with hosts where `uv` cannot be bootstrapped."
        ),
        required=False,
    )
    return parser


if __name__ == "__main__":
    # Parse the arguments.
    _main(_parse())
