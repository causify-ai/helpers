"""
Import as:

import helpers.hnotebook as hnotebo
"""

import logging

from typing import Any, Optional, cast


def config_notebook(sns_set: bool = True) -> None:
    """
    Configure the notebook for plotting.
    """
    import helpers.hmodule as hmodule

    # Matplotlib.
    module = "matplotlib"
    if hmodule.has_module(module):
        # Matplotlib.
        import matplotlib.pyplot as plt

        # plt.rcParams
        plt.rcParams["figure.figsize"] = (20, 5)
        plt.rcParams["legend.fontsize"] = 14
        plt.rcParams["font.size"] = 14
        plt.rcParams["image.cmap"] = "rainbow"
        if False:
            # Tweak the size of the plots to make it more readable when embedded in
            # documents or presentations.
            # font = {'family' : 'normal',
            #         #'weight' : 'bold',
            #         'size'   : 32}
            # matplotlib.rc('font', **font)
            scale = 3
            small_size = 8 * scale
            medium_size = 10 * scale
            bigger_size = 12 * scale
            # Default text sizes.
            plt.rc("font", size=small_size)
            # Fontsize of the axes title.
            plt.rc("axes", titlesize=small_size)
            # Fontsize of the x and y labels.
            plt.rc("axes", labelsize=medium_size)
            # Fontsize of the tick labels.
            plt.rc("xtick", labelsize=small_size)
            # Fontsize of the tick labels.
            plt.rc("ytick", labelsize=small_size)
            # Legend fontsize.
            plt.rc("legend", fontsize=small_size)
            # Fontsize of the figure title.
            plt.rc("figure", titlesize=bigger_size)
    else:
        print(f"No module '{module}'")
    # Seaborn.
    module = "seaborn"
    if hmodule.has_module(module):
        import seaborn as sns

        if sns_set:
            sns.set()
    else:
        print(f"No module '{module}'")
    # Pandas.
    module = "pandas"
    if hmodule.has_module(module):
        import pandas as pd

        pd.set_option("display.max_rows", 500)
        pd.set_option("display.max_columns", 500)
        pd.set_option("display.width", 1000)
    else:
        print(f"No module '{module}'")
    # Warnings.
    import helpers.hwarnings as hwarnin

    # Force the linter to keep this import.
    _ = hwarnin


# #############################################################################
# Logger Configuration
# #############################################################################

# Notebook util libraries can use the following idiom to control the logging so
# that it works well both in a notebook and in code.
#
# In the notebook add:
# ```
# import <tutorial>_utils as tutils
#
# _LOG = logging.getLogger(__name__)
# tutils.init_loggers(_LOG)
# ```
#
# Define `init_loggers()` in the paired `*_utils.py` file:
# ```
# import helpers.hnotebook as hnotebo
#
# def init_logger(notebook_log: logging.Logger) -> None:
#     global _LOG
#     hnotebo.init_loggers(notebook_log, utils_log=_LOG)
# ```


def _info_print(msg: str, *args) -> None:
    """
    Print a message with optional formatting arguments.

    Formats the message using printf-style formatting if additional arguments
    are provided, then prints it.

    :param msg: Message template to print
    :param args: Optional positional arguments for message formatting
    """
    if args:
        msg = msg % args
    print(msg)


def set_logger_to_print(log: logging.Logger) -> None:
    """
    Replace logger's `info()` method with `print()` function.

    Modifies the logger in-place to output messages via print instead of the
    standard logging mechanism, useful for notebook environments.

    :param log: Logger object to modify
    """
    log.info = _info_print


def _set_all_loggers_to_print() -> None:
    """
    Replace all registered loggers' `info()` methods with `print()` function.

    Iterates through all logger instances in the logging hierarchy and replaces
    their `info()` method with the `_info_print()` function for notebook output.
    """
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        set_logger_to_print(logger)


def get_link_to_code(obj: Any, *, use_master: bool = False) -> str:
    """
    Print and return a GitHub link to the source code of a Python object.

    Resolve the source file and starting line number of `obj` (e.g., a
    function, method, class, or module) via introspection, then build the
    corresponding GitHub URL using the same logic as
    `dev_scripts_helpers/github/to_github.py`.

    :param obj: Python object to link to (e.g., function, method, class,
        module)
    :param use_master: use `master` branch instead of the current branch
        - Default: `False`
    :return: GitHub URL pointing to the object's file and line number, e.g.,
        `https://github.com/<org>/<repo>/blob/<branch>/<path>#L<line>`
    """
    import inspect
    import os

    import helpers.hdbg as hdbg
    import helpers.hsystem as hsystem

    # Resolve the source file and starting line number of the object.
    file_path = None
    start_line = 0
    try:
        file_path = inspect.getsourcefile(obj)
        _, start_line = inspect.getsourcelines(obj)
    except (TypeError, OSError) as e:
        hdbg.dfatal(f"Cannot resolve source for object '{obj}': {e}")
    hdbg.dassert_is_not(
        file_path, None, "Cannot find source file for object '%s'", file_path
    )
    # Narrow the type for the type checker: `dfatal()` above always raises.
    file_path = cast(str, file_path)
    # Get the git root directory.
    git_root_cmd = "git rev-parse --show-toplevel"
    _, git_root = hsystem.system_to_string(git_root_cmd)
    git_root = git_root.strip()
    # Compute the path relative to the git root.
    abs_file_path = os.path.abspath(file_path)
    hdbg.dassert(
        abs_file_path.startswith(git_root),
        "File '%s' is not inside git repo '%s'",
        abs_file_path,
        git_root,
    )
    relative_path = os.path.relpath(abs_file_path, git_root)
    # Get the repository URL and convert it from SSH to HTTPS.
    repo_url_cmd = "git remote get-url origin"
    _, repo_url = hsystem.system_to_string(repo_url_cmd)
    repo_url = repo_url.strip()
    if repo_url.startswith("git@github.com:"):
        repo_url = repo_url.replace("git@github.com:", "https://github.com/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    # Get the branch name.
    if use_master:
        branch_name = "master"
    else:
        branch_name_cmd = "git branch --show-current"
        _, branch_name = hsystem.system_to_string(branch_name_cmd)
        branch_name = branch_name.strip()
    # Build the GitHub URL, anchored to the object's starting line.
    github_url = f"{repo_url}/blob/{branch_name}/{relative_path}#L{start_line}"
    return github_url


def init_loggers(
    notebook_log: logging.Logger,
    *,
    utils_log: Optional[logging.Logger] = None,
    set_all_loggers_to_print: bool = False,
) -> None:
    """
    Initialize loggers for notebook use with sensible defaults.

    Configures notebook environment (matplotlib, seaborn, pandas), sets up
    debug logging, and redirects specified loggers to print output for
    interactive notebook use.

    :param notebook_log: Logger instance from the notebook's `__main__`
    :param utils_log: Optional logger from paired `*_utils.py` module
        - Default: `None` (skipped)
    :param set_all_loggers_to_print: Whether to redirect all loggers to print
        - If True, all registered loggers' `info()` methods will output via print
        - Default: `False`
    """
    # Configure the notebook environment.
    config_notebook()
    # Initialize the logger to INFO level.
    import helpers.hdbg as hdbg

    hdbg.init_logger(verbosity=logging.INFO, use_exec_path=False)
    # Redirect notebook logger to print.
    set_logger_to_print(notebook_log)
    # Redirect utils logger to print if provided.
    if utils_log is not None:
        set_logger_to_print(utils_log)
    # Redirect all module loggers to print if requested.
    if set_all_loggers_to_print:
        _set_all_loggers_to_print()
