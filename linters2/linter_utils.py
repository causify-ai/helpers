"""
Import as:

import linters2.linter_utils as llinutil
"""

import logging
import os
import re
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

ROOT_DIR = hgit.get_client_root(False)

_DIRS_TO_EXCLUDE: List[str] = []

_DIRS_TO_EXCLUDE_INIT = ["./import_check/example"]

FILES_TO_EXCLUDE = [
    "__init__.py",
    "conftest.py",
    "repo_config.py",
    "setup.py",
    "tasks.py",
]


# #############################################################################


# TODO(gp): Move in a more general file: probably system_interaction.
def _is_under_dir(file_name: str, dir_name: str) -> bool:
    """
    Return whether a file is under the given directory.
    """
    subdir_names = file_name.split("/")
    return dir_name in subdir_names


def is_under_test_dir(file_name: str) -> bool:
    """
    Return whether a file is under a test directory (which is called "test").
    """
    return _is_under_dir(file_name, "test")


def is_test_input_output_file(file_name: str) -> bool:
    """
    Return whether a file is used as input or output in a unit test.
    """
    ret = is_under_test_dir(file_name)
    ret &= file_name.endswith(".txt")
    ret &= not _is_under_dir(file_name, "tmp.scratch")
    return ret


def _filter_files(
    file_paths: List[str], file_paths_to_skip: List[str]
) -> List[str]:
    """
    Filter the list of files by removing invalid or excluded ones.

    The following files are skipped:
    - Files that do not exist
    - Non-files (directories)
    - Ipynb checkpoints
    - Input and output files in unit tests
    - Files explicitly excluded by the user

    :param file_paths: all the original files to validate and filter
    :param file_paths_to_skip: files to exclude from processing
    :return: files that passed the filters
    """
    file_paths_to_keep: List[str] = []
    for file_path in file_paths:
        # Skip files that do not exist.
        is_valid = os.path.exists(file_path)
        # Skip non-files.
        is_valid &= os.path.isfile(file_path)
        # Skip checkpoints.
        is_valid &= ".ipynb_checkpoints/" not in file_path
        # Skip input and output files used in unit tests.
        is_valid &= not is_test_input_output_file(file_path)
        # Skip files explicitly excluded by user.
        is_valid &= file_path not in file_paths_to_skip
        if is_valid:
            file_paths_to_keep.append(file_path)
        else:
            _LOG.warning("Skipping %s", file_path)
    return file_paths_to_keep


def get_files_to_check(
    files: Optional[List[str]],
    from_file: Optional[str],
    skip_files: Optional[List[str]],
    dir_name: Optional[str],
    modified: bool,
    last_commit: bool,
    branch: bool,
) -> List[str]:
    """
    Get the files to be processed by Linter/Reviewer.

    :param files: specific files to process
    :param skip_files: specific files to skip and not process
    :param dir_name: name of the dir where all files should be processed
    :param modified: process the files modified in the current git
        client
    :param last_commit: process the files modified in the previous
        commit
    :param branch: process the files modified in the current branch
        w.r.t. master
    :return: paths of the files to process
    """
    file_paths: List[str] = []
    if files:
        # Get the files that were explicitly specified.
        file_paths = files
    elif from_file:
        # Get the files from a file.
        file_paths_str = hio.from_file(from_file)
        file_paths_str = file_paths_str.replace("\n", " ")
        file_paths = file_paths_str.split(" ")
        _LOG.info("Read %d files from '%s'", len(file_paths), from_file)
        hdbg.dassert_list_of_strings(file_paths)
    elif modified:
        # Get all the modified files in the git client.
        file_paths = hgit.get_modified_files()
    elif last_commit:
        # Get all the files modified in the previous commit.
        file_paths = hgit.get_previous_committed_files()
    elif branch:
        # Get all the files modified in the branch.
        file_paths = hgit.get_modified_files_in_branch(dst_branch="master")
    elif dir_name:
        # Get the files in a specified dir.
        if dir_name == "$GIT_ROOT":
            dir_name = hgit.get_client_root(super_module=True)
        dir_name = os.path.abspath(dir_name)
        _LOG.info("Looking for all files in '%s'", dir_name)
        hdbg.dassert_path_exists(dir_name)
        cmd = f"find {dir_name} -name '*' -type f"
        _, output = hsystem.system_to_string(cmd)
        file_paths = output.split("\n")
    file_paths_to_skip: List[str] = []
    if skip_files:
        # Get the files to skip.
        file_paths_to_skip = skip_files
    # Remove files that should not be processed.
    file_paths = _filter_files(file_paths, file_paths_to_skip)
    if len(file_paths) < 1:
        _LOG.warning("No files that can be processed were found")
    return file_paths


# TODO(gp): This seems obsolete given the code in linters2/lint.py
def get_python_files_to_lint(dir_name: str) -> List[str]:
    """
    Get Python files for linter excluding jupytext and test Python files.

    :param dir_name: directory name to get Python files from
    :return: list of Python files to lint in a specified dir
    """
    # Get all Python files.
    hdbg.dassert_dir_exists(dir_name)
    pattern = "*"
    only_files = True
    use_relative_paths = False
    files = hio.listdir(dir_name, pattern, only_files, use_relative_paths)
    _LOG.debug("all files=%s", len(files))
    # Exclude paired jupytext Python files.
    files_not_jupytext = hio.keep_python_files(
        files, exclude_paired_jupytext=True
    )
    _LOG.debug("all Python files w/o jupytext files=%s", len(files_not_jupytext))
    # TODO(Dan): Consider verifying if a file is under a subdir in _is_under_dir().
    # Remove dirs to exclude.
    files_wo_excluded_dirs = [
        f
        for f in files_not_jupytext
        if not any(
            os.path.commonprefix([f, dir_]) == dir_ for dir_ in _DIRS_TO_EXCLUDE
        )
        and ".Trash" not in f
    ]
    _LOG.debug(
        "after removing dirs to exclude: files=%s",
        len(files_wo_excluded_dirs),
    )
    # Remove files to exclude.
    files_wo_excluded = [
        f
        for f in files_wo_excluded_dirs
        if os.path.basename(f) not in FILES_TO_EXCLUDE
    ]
    _LOG.debug(
        "after removing files to exclude: files=%s", len(files_wo_excluded)
    )
    # Remove files under `test`.
    not_test_files = [
        file for file in files_wo_excluded if not is_under_test_dir(file)
    ]
    _LOG.debug("after removing test: files=%s", len(not_test_files))
    return not_test_files


# TODO(ai_gp): should this be moved to helpers/hio.py?
def write_file_back(
    file_name: str, txt_old: List[str], txt_new: List[str]
) -> None:
    """
    Write new text to file only if it differs from the old text.

    :param file_name: Path to the file to write to
    :param txt_old: Original text as a list of strings
    :param txt_new: New text as a list of strings
    """
    # Process old text.
    hdbg.dassert_list_of_strings(txt_old)
    txt_as_str = "\n".join(txt_old)
    # Process new text.
    hdbg.dassert_list_of_strings(txt_new)
    txt_new_as_str = "\n".join(txt_new)
    # Write file back, if needed.
    if txt_as_str != txt_new_as_str:
        hio.to_file(file_name, txt_new_as_str)


# TODO(ai_gp): should this be moved to helpers/hsystem.py?
def tee(
    cmd: str, executable: str, abort_on_error: bool
) -> Tuple[int, List[str]]:
    """
    Execute command and return its exit code and output lines.

    Captures output, removes empty lines, and optionally aborts on error.

    :param cmd: Command string to execute
    :param executable: Executable to use for running the command
    :param abort_on_error: Whether to abort execution if command fails
    :return: Tuple of (exit code, list of non-empty output lines)
    """
    _LOG.debug("cmd=%s executable=%s", cmd, executable)
    rc, output = hsystem.system_to_string(cmd, abort_on_error=abort_on_error)
    hdbg.dassert_isinstance(output, str)
    output1 = output.split("\n")
    _LOG.debug("output1= (%d)\n'%s'", len(output1), "\n".join(output1))
    #
    output2 = hprint.remove_empty_lines(output1)
    _LOG.debug("output2= (%d)\n'%s'", len(output2), "\n".join(output2))
    hdbg.dassert_list_of_strings(output2)
    return rc, output2


# TODO(gp): Some of these functions can be centralized in helpers.
def is_under_tmp_scratch_dir(file_name: str) -> bool:
    """
    Return whether a file is under the temporary scratch directory.
    """
    return _is_under_dir(file_name, "tmp.scratch")


def is_test_code(file_name: str) -> bool:
    """
    Return whether a file contains unit test code.
    """
    ret = is_under_test_dir(file_name)
    ret &= os.path.basename(file_name).startswith("test_")
    ret &= file_name.endswith(".py")
    return ret


def is_py_file(file_name: str) -> bool:
    """
    Return whether a file is a python file.
    """
    return file_name.endswith(".py")


def is_ipynb_file(file_name: str) -> bool:
    """
    Return whether a file is a jupyter notebook file.
    """
    return file_name.endswith(".ipynb")


def from_python_to_ipynb_file(file_name: str) -> str:
    """
    Convert Python file path to its paired Jupyter notebook path.

    :param file_name: Path to a .py file
    :return: Corresponding .ipynb file path
    """
    hdbg.dassert(
        is_py_file(file_name),
        "File '%s' must be a Python file to convert to notebook",
        file_name,
    )
    ret = file_name.replace(".py", ".ipynb")
    return ret


def from_ipynb_to_python_file(file_name: str) -> str:
    """
    Convert Jupyter notebook path to its paired Python file path.

    :param file_name: Path to a .ipynb file
    :return: Corresponding .py file path
    """
    hdbg.dassert(
        is_ipynb_file(file_name),
        "File '%s' must be a Jupyter notebook to convert to Python",
        file_name,
    )
    ret = file_name.replace(".ipynb", ".py")
    return ret


def is_paired_jupytext_file(file_name: str) -> bool:
    """
    Return whether a py or ipynb file is a paired jupytext file.
    """
    is_paired = (
        is_py_file(file_name)
        and os.path.exists(from_python_to_ipynb_file(file_name))
        or (
            is_ipynb_file(file_name)
            and os.path.exists(from_ipynb_to_python_file(file_name))
        )
    )
    return is_paired


def is_init_py(file_name: str) -> bool:
    """
    Check if the file is a Python package initialization file.

    :param file_name: Path to the file to check
    :return: True if the file is named __init__.py
    """
    return os.path.basename(file_name) == "__init__.py"


def is_separator(line: str) -> bool:
    """
    Check if the line matches a separator line.

    :return: True if it matches a separator line
    """
    return (
        line
        == "# #############################################################################"
    )


def is_shebang(line: str) -> bool:
    """
    Check if the line is a shebang (starts with #!).

    :return: True if it is a shebang (starts with #!)
    """
    return line.startswith("#!")


def is_comment(line: str) -> bool:
    """
    Check if the line is a comment (starts with # but is not a shebang).

    :param line: the line to check
    :return: True if it is a comment
    """
    line = line.strip()
    return line.startswith("#") and not line.startswith("#!")


def parse_comment(
    line: str, regex: str = r"(^\s*)#\s*(.*)\s*"
) -> Optional[re.Match]:
    """
    Parse a line and return a regex match for the comment part.

    Separator lines and shebangs are skipped and return None.

    :param line: The line to parse
    :param regex: Regular expression to match comment syntax
    :return: Regex match object if comment found, None for separators or shebangs
    """
    if is_separator(line) or is_shebang(line):
        return None
    return re.search(regex, line)


def is_executable(file_name: str) -> bool:
    """
    Check if the file has x+ permission.

    :return: True if file has x+ permission
    """
    return os.access(file_name, os.X_OK)


def is_text_file(file_name: str) -> bool:
    """
    Check whether the file has extension of a text file.

    :return: True if text file
    """
    for extension in [".csv", ".json", ".tsv", ".txt"]:
        if file_name.endswith(extension):
            return True
    return False


# #############################################################################


def get_dirs_with_missing_init(
    dir_name: str, exclude_unimported_dirs: bool
) -> List[str]:
    """
    Get dirs with the missing `__init__.py` file.

    A dir is required to have the `__init__.py` file if it has
    `.py` files underneath it (on any level).

    :param dir_name: path to the head dir to start the check from
      - the check will cover `dir_name` and all the dirs underneath it
    :param exclude_unimported_dirs: if True, exclude dirs that contain files
        that are usually not imported (trash, temporary cache,
        unit tests and notebooks)
    :return: names of the dirs with the missing `__init__.py` file
    """
    dirs_missing_init: List[str] = []
    for root, _, files in os.walk(dir_name):
        if root in _DIRS_TO_EXCLUDE_INIT:
            continue
        if exclude_unimported_dirs and (
            "test" in root.split("/")
            or "notebooks" in root.split("/")
            or ".Trash" in root
            or "/tmp." in root
            or ".ipynb_checkpoints" in root
        ):
            continue
        pattern = "*.py"
        only_files = True
        use_relative_paths = False
        py_files = hio.listdir(root, pattern, only_files, use_relative_paths)
        if len(py_files) != 0 and "__init__.py" not in files:
            # A dir is not a module but has Python files underneath it.
            dirs_missing_init.append(root)
    dirs_missing_init = sorted(dirs_missing_init)
    return dirs_missing_init


def filter_files_by_type(
    file_paths: List[str],
    keep_python_files: bool,
    keep_jupyter_files: bool,
    keep_markdown_files: bool,
    *,
    skip_dassert_exists: bool = False,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Filter files by type (Python, Jupyter, Markdown).

    If no type filters are provided (all False), returns all files grouped
    by detected type.

    :param file_paths: files to filter
    :param keep_python_files: include Python files
    :param keep_jupyter_files: include Jupyter notebooks
    :param keep_markdown_files: include Markdown files
    :param skip_dassert_exists: skip file existence checks
    :return: tuple of (python_files, jupyter_files, markdown_files)
    """
    python_files = []
    jupyter_files = []
    markdown_files = []
    # Categorize all files by type.
    for f in file_paths:
        if is_ipynb_file(f):
            paired_python_file = from_ipynb_to_python_file(f)
            if not skip_dassert_exists:
                hdbg.dassert_file_exists(
                    paired_python_file,
                    "Paired Jupyter notebook file '%s' not found for Python file '%s'",
                    f,
                    paired_python_file,
                )
            jupyter_files.append(f)
        elif is_py_file(f):
            if not is_paired_jupytext_file(f):
                python_files.append(f)
        elif f.endswith(".md"):
            markdown_files.append(f)
        else:
            _LOG.warning("File type for '%s' not recognized", f)
    # Select files based on types.
    if not keep_python_files:
        python_files = []
    if not keep_jupyter_files:
        jupyter_files = []
    if not keep_markdown_files:
        markdown_files = []
    return python_files, jupyter_files, markdown_files
