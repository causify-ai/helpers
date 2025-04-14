"""
Import as:

import helpers.hjupyter as hjupyte
"""

import logging
import os

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def run_notebook(
    file_name: str,
    scratch_dir: str,
    *,
    pre_cmd: str = "",
) -> None:
    """
    Run jupyter notebook.

    Assert if the notebook doesn't complete successfully.

    :param file_name: path to the notebook to run. If this is a .py
        file, convert to .ipynb first
    :param scratch_dir: temporary dir storing the output
    :param pre_cmd:
    """
    file_name = os.path.abspath(file_name)
    hdbg.dassert_path_exists(file_name)
    hio.create_dir(scratch_dir, incremental=True)
    # Build command line.
    cmd = []
    if pre_cmd:
        cmd.append(f"{pre_cmd} &&")
    # Convert .py file into .ipynb if needed.
    root, ext = os.path.splitext(file_name)
    if ext == ".ipynb":
        notebook_name = file_name
    elif ext == ".py":
        cmd.append(f"jupytext --update --to notebook {file_name};")
        notebook_name = f"{root}.ipynb"
    else:
        raise ValueError(f"Unsupported file format for `file_name`='{file_name}'")
    # Execute notebook.
    cmd.append(f"cd {scratch_dir} &&")
    cmd.append(f"jupyter nbconvert {notebook_name}")
    cmd.append("--execute")
    cmd.append("--to html")
    cmd.append("--ExecutePreprocessor.kernel_name=python")
    # No time-out.
    cmd.append("--ExecutePreprocessor.timeout=-1")
    # Execute.
    cmd_as_str = " ".join(cmd)
    hsystem.system(cmd_as_str, abort_on_error=True, suppress_output=False)


def build_run_notebook_cmd(
    config_builder: str, dst_dir: str, notebook_path: str, *, extra_opts: str = ""
) -> str:
    """
    Construct a command string to run dev_scripts/notebooks/run_notebook.py
    with specified configurations.

    :param config_builder: the configuration builder to use for the
        notebook execution
    :param dst_dir: the destination directory where the notebook results
        will be saved
    :param notebook_path: the path to the notebook that should be
        executed
    :param extra_opts: options for "run_notebook.py", e.g., "--
        publish_notebook"
    """
    # Importing inside func to avoid error while creating dockerized executable.
    # TODO(Shaunak): debug why.
    import helpers.hgit as hgit

    # TODO(Vlad): Factor out common code with the
    # `helpers.lib_tasks_gh.publish_buildmeister_dashboard_to_s3()`.
    run_notebook_script_path = hgit.find_file_in_git_tree("run_notebook.py")
    cmd_run_txt = [
        run_notebook_script_path,
        f"--notebook {notebook_path}",
        f"--config_builder '{config_builder}'",
        f"--dst_dir '{dst_dir}'",
        f"{extra_opts}",
    ]
    cmd_run_txt = " ".join(cmd_run_txt)
    return cmd_run_txt
