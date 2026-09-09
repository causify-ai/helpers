"""
Import as:

import helpers.lib_tasks.lib_tasks_open_md as hltltaomd
"""

import logging
import os

from invoke import task

import helpers.lib_tasks.lib_tasks_utils as hlitauti

# We want to minimize the dependencies from non-standard Python packages since
# this code needs to run with minimal dependencies and without Docker.
from helpers import hdbg, hgit, hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# open_md
# #############################################################################

# Keep in sync with `dev_scripts_helpers/documentation/open_md.py`.
_OPEN_MD_MODES = ("github", "pandoc", "pdf", "grip", "grip_daemon")
_OPEN_MD_BACKENDS = ("global", "dockerized")


def _get_open_md_script_path() -> str:
    """
    Return the path of the `open_md.py` script.
    """
    helpers_root = hgit.find_helpers_root()
    script_path = os.path.join(
        helpers_root, "dev_scripts_helpers", "documentation", "open_md.py"
    )
    hdbg.dassert_file_exists(script_path)
    return script_path


def _build_open_md_cmd(
    input_file: str,
    mode: str = "pandoc",
    backend: str = "global",
    css: str = "",
    daemon: bool = False,
    skip_open: bool = False,
    dockerized_force_rebuild: bool = False,
    dockerized_use_sudo: bool = False,
) -> str:
    """
    Build the command line to run `open_md.py` with the given options.

    :param input_file: path to the markdown file to render/open
    :param mode: rendering mode (see `_OPEN_MD_MODES`)
    :param backend: execution environment (see `_OPEN_MD_BACKENDS`)
    :param css: (pandoc mode only) path to a custom HTML snippet to inject
        into the output
    :param daemon: watch the input file and re-render on changes
    :param skip_open: don't open the rendered output
    :param dockerized_force_rebuild: (dockerized backend only) force the
        rebuild of the Docker image
    :param dockerized_use_sudo: (dockerized backend only) run Docker with
        sudo
    :return: the command to run
    """
    hdbg.dassert_ne(input_file, "")
    hdbg.dassert_in(mode, _OPEN_MD_MODES)
    hdbg.dassert_in(backend, _OPEN_MD_BACKENDS)
    script_path = _get_open_md_script_path()
    opts = [
        f"--mode {mode}",
        f"--backend {backend}",
    ]
    if css != "":
        opts.append(f"--css {css}")
    if daemon:
        opts.append("--daemon")
    if skip_open:
        opts.append("--skip_open")
    if dockerized_force_rebuild:
        opts.append("--dockerized_force_rebuild")
    if dockerized_use_sudo:
        opts.append("--dockerized_use_sudo")
    cmd = f"{script_path} --input {input_file} " + " ".join(opts)
    return cmd


@task
def open_md(  # type: ignore
    ctx,
    input_file,
    mode="pandoc",
    backend="global",
    css="",
    daemon=False,
    skip_open=False,
    dockerized_force_rebuild=False,
    dockerized_use_sudo=False,
):
    """
    Render and open a markdown file.

    Thin invoke wrapper around
    `dev_scripts_helpers/documentation/open_md.py`, e.g.:

    > i open_md --input xyz.md
    > i open_md --input xyz.md --mode github
    > i open_md --input xyz.md --backend dockerized

    See the script docstring for the full description of the rendering modes
    (github, pandoc, pdf, grip, grip_daemon) and backends (global,
    dockerized).

    :param input_file: path to the markdown file to render/open
    :param mode: rendering mode: github, pandoc, pdf, grip, grip_daemon
    :param backend: execution environment: global, dockerized
    :param css: (pandoc mode only) path to a custom HTML snippet to inject
        into the output, overriding the default GitHub-like style
    :param daemon: watch the input file and re-render on changes (pandoc,
        pdf, grip modes only)
    :param skip_open: don't open the rendered output
    :param dockerized_force_rebuild: (dockerized backend) force the rebuild
        of the Docker image
    :param dockerized_use_sudo: (dockerized backend) run Docker with sudo
    """
    _ = ctx
    hlitauti.report_task()
    cmd = _build_open_md_cmd(
        input_file,
        mode=mode,
        backend=backend,
        css=css,
        daemon=daemon,
        skip_open=skip_open,
        dockerized_force_rebuild=dockerized_force_rebuild,
        dockerized_use_sudo=dockerized_use_sudo,
    )
    hsystem.system(cmd)
