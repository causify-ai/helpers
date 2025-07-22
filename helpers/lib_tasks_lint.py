"""
Import as:

import helpers.lib_tasks_lint as hlitalin
"""

import datetime
import filecmp
import logging
import os

from invoke import task

# We want to minimize the dependencies from non-standard Python packages since
# this code needs to run with minimal dependencies and without Docker.
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.lib_tasks_docker as hlitadoc
import helpers.lib_tasks_utils as hlitauti

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


# #############################################################################
# Linter.
# #############################################################################


@task
def lint_check_python_files_in_docker(  # type: ignore
    ctx,
    python_compile=True,
    python_execute=True,
    modified=False,
    branch=False,
    last_commit=False,
    all_=False,
    files="",
):
    """
    Compile and execute Python files checking for errors.

    This is supposed to be run inside Docker.

    The params have the same meaning as in `_get_files_to_process()`.
    """
    hlitauti.report_task()
    _ = ctx
    # We allow to filter through the user specified `files`.
    mutually_exclusive = False
    remove_dirs = True
    file_list = hlitauti._get_files_to_process(
        modified,
        branch,
        last_commit,
        all_,
        files,
        mutually_exclusive,
        remove_dirs,
    )
    _LOG.debug("Found %d files:\n%s", len(file_list), "\n".join(file_list))
    # Filter keeping only Python files.
    _LOG.debug("Filtering for Python files")
    exclude_paired_jupytext = True
    file_list = hio.keep_python_files(file_list, exclude_paired_jupytext)
    _LOG.debug("file_list=%s", "\n".join(file_list))
    _LOG.info("Need to process %d files", len(file_list))
    if not file_list:
        _LOG.warning("No files were selected")
    # Scan all the files.
    failed_filenames = []
    for file_name in file_list:
        _LOG.info("Processing '%s'", file_name)
        if python_compile:
            import compileall

            success = compileall.compile_file(file_name, force=True, quiet=1)
            _LOG.debug("file_name='%s' -> python_compile=%s", file_name, success)
            if not success:
                msg = f"'{file_name}' doesn't compile correctly"
                _LOG.error(msg)
                failed_filenames.append(file_name)
        # TODO(gp): Add also `python -c "import ..."`, if not equivalent to `compileall`.
        if python_execute:
            cmd = f"python {file_name}"
            rc = hsystem.system(cmd, abort_on_error=False, suppress_output=False)
            _LOG.debug("file_name='%s' -> python_compile=%s", file_name, rc)
            if rc != 0:
                msg = f"'{file_name}' doesn't execute correctly"
                _LOG.error(msg)
                failed_filenames.append(file_name)
    hprint.log_frame(
        _LOG,
        f"failed_filenames={len(failed_filenames)}",
        verbosity=logging.INFO,
    )
    _LOG.info("\n".join(failed_filenames))
    error = len(failed_filenames) > 0
    return error


@task
def lint_check_python_files(  # type: ignore
    ctx,
    python_compile=True,
    python_execute=True,
    modified=False,
    branch=False,
    last_commit=False,
    all_=False,
    files="",
):
    """
    Compile and execute Python files checking for errors.

    The params have the same meaning as in `_get_files_to_process()`.
    """
    _ = (
        python_compile,
        python_execute,
        modified,
        branch,
        last_commit,
        all_,
        files,
    )
    # Execute the same command line but inside the container. E.g.,
    # /Users/saggese/src/venv/amp.client_venv/bin/invoke lint_docker_check_python_files --branch
    cmd_line = hdbg.get_command_line()
    # Replace the full path of invoke with just `invoke`.
    cmd_line = cmd_line.split()
    cmd_line = ["/venv/bin/invoke lint_check_python_files_in_docker"] + cmd_line[
        2:
    ]
    docker_cmd_ = " ".join(cmd_line)
    cmd = f'invoke docker_cmd --cmd="{docker_cmd_}"'
    hlitauti.run(ctx, cmd)


@task
def lint_detect_cycles(  # type: ignore
    ctx,
    dir_name=".",
    stage="prod",
    version="",
    out_file_name="lint_detect_cycles.output.txt",
    debug_tool=False,
):
    """
    Detect cyclic imports in the directory files.

    For param descriptions, see `lint()`.

    :param dir_name: the name of the dir to detect cyclic imports in
        - By default, the check will be carried out in the dir from where
          the task is run
    :param debug_tool: print the output of the cycle detector
    """
    hlitauti.report_task()
    # Remove the log file.
    if os.path.exists(out_file_name):
        cmd = f"rm {out_file_name}"
        hlitauti.run(ctx, cmd)
    # Prepare the command line.
    docker_cmd_opts = [dir_name]
    if debug_tool:
        docker_cmd_opts.append("-v DEBUG")
    docker_cmd_ = (
        "$(find -wholename '*import_check/detect_import_cycles.py') "
        + hlitauti._to_single_line_cmd(docker_cmd_opts)
    )
    # Execute command line.
    base_image = ""
    cmd = _get_lint_docker_cmd(base_image, docker_cmd_, stage, version)
    # Use `PIPESTATUS` otherwise the exit status of the pipe is always 0
    # because writing to a file succeeds.
    cmd = f"({cmd}) 2>&1 | tee -a {out_file_name}; exit $PIPESTATUS"
    # Run.
    hlitauti.run(ctx, cmd)


# pylint: disable=line-too-long
@task
def lint(  # type: ignore
    ctx,
    base_image="",
    stage="prod",
    version="",
    files="",
    from_file="",
    skip_files="",
    dir_name="",
    modified=False,
    last_commit=False,
    branch=False,
    # It needs to be a string to allow the user to specify "serial".
    num_threads="serial",
    only_format=False,
    only_check=False,
):
    """
    Lint files.

    ```
    # To lint specific files:
    > i lint --files="dir1/file1.py dir2/file2.md"

    # To lint the files changed in the last commit, excluding specific files:
    > i lint --last-commit --skip-files="dir1/file1.py dir2/file2.md"

    # To lint all the files in the current dir using only formatting actions:
    > i lint --dir-name . --only-format

    # To lint the files modified in the current git client:
    > i lint --modified

    # To exclude certain paths from linting:
    > i lint --files="$(find . -name '*.py' -not -path './compute/*' -not -path './amp/*')"
    ```

    :param stage: the image stage to use (e.g., "prod", "dev", "local")
    :param version: the version of the container to use
    :param files: specific files to lint (e.g. "dir1/file1.py dir2/file2.md")
    :param from_file: specific file storing files to lint
    :param skip_files: specific files to skip during linting (e.g. "dir1/file1.py dir2/file2.md")
    :param dir_name: name of the dir where all files should be linted
    :param modified: lint the files modified in the current git client
    :param last_commit: lint the files modified in the previous commit
    :param branch: lint the files modified in the current branch w.r.t. master
    :param num_threads: number of threads to use ("serial", -1, 0, 1, 2, ...)
    :param only_format: run only the modifying actions of Linter (e.g., black)
    :param only_check: run only the non-modifying actions of Linter (e.g., pylint)
    """
    # Check if the user is in a repo root.
    hdbg.dassert(
        hgit.is_cwd_git_repo(),
        msg="Linter should run from repo root",
    )
    hlitauti.report_task()
    # Prepare the command line.
    lint_cmd_opts = []
    # Add the file selection argument.
    hdbg.dassert_eq(
        int(len(files) > 0)
        + int(len(from_file) > 0)
        + int(len(dir_name) > 0)
        + int(modified)
        + int(last_commit)
        + int(branch),
        1,
        msg="Specify exactly one among --files, --from_file, --dir-name, --modified, --last-commit, --branch",
    )
    if len(files) > 0:
        lint_cmd_opts.append(f"--files {files}")
    elif len(from_file) > 0:
        lint_cmd_opts.append(f"--from_file {from_file}")
    elif len(dir_name) > 0:
        lint_cmd_opts.append(f"--dir_name {dir_name}")
    elif modified:
        lint_cmd_opts.append("--modified")
    elif last_commit:
        lint_cmd_opts.append("--last_commit")
    elif branch:
        lint_cmd_opts.append("--branch")
    else:
        raise ValueError("No file selection arguments are specified")
    if len(skip_files) > 0:
        lint_cmd_opts.append(f"--skip_files {skip_files}")
    #
    lint_cmd_opts.append(f"--num_threads {num_threads}")
    # Add the action selection argument, if needed.
    hdbg.dassert_lte(
        int(only_format) + int(only_check),
        1,
        msg="Specify only one among --only-format, --only-check",
    )
    if only_format:
        lint_cmd_opts.append("--only_format")
    elif only_check:
        lint_cmd_opts.append("--only_check")
    else:
        _LOG.info("All Linter actions selected")
    # Compose the command line.
    if hserver.is_host_mac():
        find_cmd = "$(find . -path '*linters/base.py')"
    else:
        find_cmd = "$(find -wholename '*linters/base.py')"
    lint_cmd_ = find_cmd + " " + hlitauti._to_single_line_cmd(lint_cmd_opts)
    docker_cmd_ = _get_lint_docker_cmd(
        base_image, lint_cmd_, stage=stage, version=version
    )
    # Run.
    hlitauti.run(ctx, docker_cmd_)


@task
def lint_check_if_it_was_run(ctx):  # type: ignore
    """
    Check if the linter was run in the current branch.

    - abort the task with error if the files were modified
    """
    hlitauti.report_task()
    # Check if the files were modified.
    hgit.is_client_clean(abort_if_not_clean=True)


@task
def lint_create_branch(ctx, dry_run=False):  # type: ignore
    """
    Create the branch for linting in the current dir.

    The dir needs to be specified to ensure the set-up is correct.
    """
    hlitauti.report_task()
    #
    date = datetime.datetime.now().date()
    date_as_str = date.strftime("%Y%m%d")
    branch_name = f"AmpTask1955_Lint_{date_as_str}"
    # query_yes_no("Are you sure you want to create the branch '{branch_name}'")
    _LOG.info("Creating branch '%s'", branch_name)
    cmd = f"invoke git_branch_create -b '{branch_name}'"
    hlitauti.run(ctx, cmd, dry_run=dry_run)


def _get_lint_docker_cmd(
    base_image: str,
    docker_cmd_: str,
    stage: str,
    version: str,
    *,
    use_entrypoint: bool = True,
) -> str:
    """
    Create a command to run in Linter service.

    :param docker_cmd_: command to run
    :param stage: the image stage to use
    :return: the full command to run
    """
    if base_image == "":
        base_path = os.environ["CSFY_ECR_BASE_PATH"]
        # Get an image to run the linter on.
        linter_image = f"{base_path}/helpers"
    else:
        linter_image = base_image
    _LOG.debug(hprint.to_str("linter_image"))
    # Execute command line.
    cmd: str = hlitadoc._get_docker_compose_cmd(
        linter_image,
        stage,
        version,
        docker_cmd_,
        use_entrypoint=use_entrypoint,
    )
    return cmd


@task
def lint_sync_code(ctx, git_client_name="helpers1", revert_to_original=False):  # type: ignore
    """
    Sync code needed to run linter / ai_review from a Git client to the current one.

    :param git_client_name: the name of the Git client to sync from. It can be
        something like "helpers1" and it will be used from "$HOME/src" or can
        be a full path.
    :param revert_to_original: if `True`, revert the changes to the original
    """
    _ = ctx
    hlitauti.report_task()
    # Copy the code from the src Git client to the current one.
    src_git_dir = hgit.resolve_git_client_dir(git_client_name)
    #
    files_to_copy = [
        # "hgit.py",
        # "hmarkdown.py",
        "llm_prompts.py",
        "llm_transform.py",
        "inject_todos.py",
        "all.coding_style_guidelines.reference.md",
    ]
    # Revert the files in the current git client to the original code.
    if revert_to_original:
        _LOG.debug("Reverting to original code ...")
        for file_name in files_to_copy:
            _LOG.debug("Reverting %s to original code", file_name)
            src_file_path = hgit.find_file(file_name, dir_path=src_git_dir)
            git_root_dir = hgit.find_git_root(src_git_dir)
            src_file_path = os.path.relpath(src_file_path, git_root_dir)
            cmd = "git checkout -- " + src_file_path
            hsystem.system(cmd)
        _LOG.info("Done")
        return
    # Get the path to the helpers repo.
    src_helpers_dir = hgit.find_helpers_root(src_git_dir)
    hdbg.dassert_ne(src_helpers_dir, "")
    hdbg.dassert_dir_exists(src_helpers_dir)
    #
    dst_helpers_dir = hgit.find_helpers_root()
    hdbg.dassert_dir_exists(dst_helpers_dir)
    _LOG.debug(hprint.to_str("src_helpers_dir dst_helpers_dir"))
    #
    _LOG.info(
        "Copying files from '%s' to '%s' ...", src_helpers_dir, dst_helpers_dir
    )
    # Find the files to copy.
    for file_name in files_to_copy:
        _LOG.debug(hprint.to_str("file_name"))
        # Get the path to the file in the src Git client.
        src_file_path = hgit.find_file(file_name, dir_path=src_git_dir)
        src_file_path = os.path.abspath(os.path.join(src_git_dir, src_file_path))
        _LOG.debug(hprint.to_str("src_file_path"))
        hdbg.dassert_file_exists(src_file_path)
        # Get the path to the file in the dst Git client.
        dst_file_path = hgit.project_file_name_in_git_client(
            src_file_path, src_helpers_dir, dst_helpers_dir
        )
        _LOG.debug(hprint.to_str("dst_file_path"))
        # Copy the file.
        _LOG.debug(hprint.to_str("src_file_path dst_file_path"))
        dir_name = os.path.dirname(dst_file_path)
        # Check that the files are different.
        if os.path.exists(src_file_path) and os.path.isdir(dst_file_path):
            if filecmp.cmp(src_file_path, dst_file_path, shallow=False):
                _LOG.info(
                    "File '%s' is identical to '%s', skipping",
                    src_file_path,
                    dst_file_path,
                )
                continue
        # Copy the file.
        hio.create_dir(dir_name, incremental=True)
        cmd = f"cp -f {src_file_path} {dst_file_path}"
        _LOG.debug(hprint.to_str("cmd"))
        _LOG.info("Copying file '%s' to '%s' ...", src_file_path, dst_file_path)
        hsystem.system(cmd)
    _LOG.info("Done")
