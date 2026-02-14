"""
Import as:

import helpers.hjupyter as hjupyte
"""

import logging
import os
from typing import Dict, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.htimer as htimer

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
        raise ValueError(
            f"Unsupported file format for `file_name`='{file_name}'"
        )
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
    config_builder: str,
    dst_dir: str,
    notebook_path: str,
    *,
    extra_opts: str = "",
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


# #############################################################################


def find_paired_files(
    directory: str,
    *,
    pattern: str = "*.py",
    exclude_pattern: str = None,
) -> tuple:
    """
    Find Python files and paired Jupyter notebooks in a directory.

    :param directory: path to the directory to search
    :param pattern: glob pattern for Python files (default: "*.py")
    :param exclude_pattern: suffix pattern to exclude (e.g., "_utils.py")
    :return: tuple of (python_files, paired_notebooks, unpaired_notebooks)
        - python_files: list of .py files matching pattern
        - paired_notebooks: list of .ipynb files with corresponding .py
        - unpaired_notebooks: list of .ipynb files without corresponding .py
    """
    hdbg.dassert_path_exists(directory)
    # Find Python files matching pattern.
    py_files = hio.listdir(
        directory,
        pattern,
        only_files=True,
        use_relative_paths=False,
        maxdepth=1,
    )
    # Exclude files matching exclude_pattern.
    if exclude_pattern:
        py_files = [f for f in py_files if not f.endswith(exclude_pattern)]
    py_files = sorted(py_files)
    # Find notebook files.
    nb_pattern = pattern.replace(".py", ".ipynb")
    nb_files = hio.listdir(
        directory,
        nb_pattern,
        only_files=True,
        use_relative_paths=False,
        maxdepth=1,
    )
    nb_files = sorted(nb_files)
    # Build set of base names from Python files.
    py_basenames = set()
    for py_file in py_files:
        basename = os.path.basename(py_file)
        basename = os.path.splitext(basename)[0]
        py_basenames.add(basename)
    # Check which notebooks have corresponding .py files.
    paired_notebooks = []
    unpaired_notebooks = []
    for nb_file in nb_files:
        basename = os.path.basename(nb_file)
        basename = os.path.splitext(basename)[0]
        if basename in py_basenames:
            paired_notebooks.append(nb_file)
        else:
            unpaired_notebooks.append(nb_file)
    return py_files, paired_notebooks, unpaired_notebooks


def execute_file_with_docker(
    file_path: str,
    *,
    working_dir: str,
    is_notebook: bool,
) -> Tuple[bool, str, float]:
    """
    Execute a Python file or notebook using docker_cmd.

    :param file_path: path to the file to execute
    :param working_dir: directory to cd into before execution
    :param is_notebook: True if file is a notebook, False if Python script
    :return: tuple of (success, error_message, elapsed_time)
    """
    timer = htimer.Timer()
    success = False
    error_msg = ""
    try:
        if is_notebook:
            # For notebooks, use hjupyter.run_notebook via docker_cmd.
            scratch_dir = os.path.join(working_dir, "tmp.notebook_scratch")
            # Build Python command to run notebook.
            cmd = (
                f'python -c "'
                f"import helpers.hjupyter as hjupyte; "
                f"import helpers.hio as hio; "
                f"hio.create_dir('{scratch_dir}', incremental=True); "
                f"hjupyte.run_notebook('{file_path}', '{scratch_dir}')\""
            )
        else:
            # For Python scripts, execute directly.
            cmd = f"python {file_path}"
        # Build invoke docker_cmd command.
        docker_cmd = f'invoke docker_cmd --cmd "{cmd}"'
        # Execute in the working directory.
        hsystem.system(
            docker_cmd,
            abort_on_error=False,
            suppress_output=False,
        )
        success = True
    except Exception as e:
        error_msg = str(e)
    elapsed = timer.get_elapsed()
    return success, error_msg, elapsed


def execute_file_directly(
    file_path: str,
    *,
    working_dir: str,
    is_notebook: bool,
) -> Tuple[bool, str, float]:
    """
    Execute a Python file or notebook directly (inside container).

    :param file_path: path to the file to execute
    :param working_dir: directory to cd into before execution
    :param is_notebook: True if file is a notebook, False if Python script
    :return: tuple of (success, error_message, elapsed_time)
    """
    timer = htimer.Timer()
    success = False
    error_msg = ""
    try:
        if is_notebook:
            # For notebooks, use hjupyter.run_notebook.
            scratch_dir = os.path.join(working_dir, "tmp.notebook_scratch")
            hio.create_dir(scratch_dir, incremental=True)
            run_notebook(
                file_path,
                scratch_dir,
                pre_cmd=f"cd {working_dir}",
            )
        else:
            # For Python scripts, execute directly.
            cmd = f"cd {working_dir} && python {file_path}"
            hsystem.system(
                cmd,
                abort_on_error=True,
                suppress_output=False,
            )
        success = True
    except Exception as e:
        error_msg = str(e)
    elapsed = timer.get_elapsed()
    return success, error_msg, elapsed


def report_execution_results(
    py_results: Dict[str, Tuple[bool, str, float]],
    nb_results: Dict[str, Tuple[bool, str, float]],
) -> Tuple[int, str]:
    """
    Report execution results and return failure information.

    :param py_results: results from Python file execution
    :param nb_results: results from notebook execution
    :return: tuple of (total_failures, error_message)
    """
    # Collect failures.
    py_failures = [f for f, (success, _, _) in py_results.items() if not success]
    nb_failures = [f for f, (success, _, _) in nb_results.items() if not success]
    # Calculate statistics.
    py_total = len(py_results)
    py_success = py_total - len(py_failures)
    nb_total = len(nb_results)
    nb_success = nb_total - len(nb_failures)
    total_files = py_total + nb_total
    total_success = py_success + nb_success
    total_failures = len(py_failures) + len(nb_failures)
    # Calculate timing statistics.
    py_times = [elapsed for _, _, elapsed in py_results.values()]
    nb_times = [elapsed for _, _, elapsed in nb_results.values()]
    py_total_time = sum(py_times) if py_times else 0.0
    nb_total_time = sum(nb_times) if nb_times else 0.0
    total_time = py_total_time + nb_total_time
    # Report summary.
    _LOG.info("=" * 80)
    _LOG.info("EXECUTION SUMMARY")
    _LOG.info("=" * 80)
    _LOG.info(
        "Python scripts: %d total, %d success, %d failed",
        py_total,
        py_success,
        len(py_failures),
    )
    if py_total > 0:
        _LOG.info("  Total time: %.2f seconds", py_total_time)
        _LOG.info("  Average time: %.2f seconds", py_total_time / py_total)
    _LOG.info(
        "Notebooks: %d total, %d success, %d failed",
        nb_total,
        nb_success,
        len(nb_failures),
    )
    if nb_total > 0:
        _LOG.info("  Total time: %.2f seconds", nb_total_time)
        _LOG.info("  Average time: %.2f seconds", nb_total_time / nb_total)
    _LOG.info("-" * 80)
    _LOG.info(
        "TOTAL: %d files, %d success, %d failed",
        total_files,
        total_success,
        total_failures,
    )
    _LOG.info("Total execution time: %.2f seconds", total_time)
    # Build error message if failures exist.
    error_message = ""
    if total_failures > 0:
        _LOG.error("=" * 80)
        _LOG.error("FAILURES DETECTED")
        _LOG.error("=" * 80)
        if py_failures:
            _LOG.error("Failed Python scripts:")
            for file_path in py_failures:
                basename = os.path.basename(file_path)
                _, error, _ = py_results[file_path]
                _LOG.error("  - %s: %s", basename, error)
        if nb_failures:
            _LOG.error("Failed notebooks:")
            for file_path in nb_failures:
                basename = os.path.basename(file_path)
                _, error, _ = nb_results[file_path]
                _LOG.error("  - %s: %s", basename, error)
        _LOG.error("=" * 80)
        error_message = (
            f"{total_failures} file(s) failed to execute. See log for details."
        )
    return total_failures, error_message
