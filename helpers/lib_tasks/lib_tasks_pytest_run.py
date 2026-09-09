"""
Import as:

import helpers.lib_tasks.lib_tasks_pytest_run as hltltpyru
"""

import logging
import shlex

from invoke.tasks import task

import helpers.lib_tasks.lib_tasks_find as hltltafi
import helpers.lib_tasks.lib_tasks_utils as hltltaut

_LOG = logging.getLogger(__name__)


# #############################################################################
# Run a pytest class.
# #############################################################################


def _resolve_pytest_class_target(
    class_name: str, search_root: str, run_file: bool
) -> str:
    """
    Resolve an exact test class to one pytest target.
    """
    if not class_name:
        raise ValueError("You need to specify a class name")
    file_names = hltltafi._find_test_files(search_root)
    targets = hltltafi._find_test_class(class_name, file_names, exact_match=True)
    if not targets:
        raise ValueError(
            f"Could not find test class '{class_name}' under '{search_root}'"
        )
    if len(targets) > 1:
        target_list = "\n".join(targets)
        raise ValueError(
            f"Test class '{class_name}' is ambiguous; found "
            f"{len(targets)} matches:\n{target_list}"
        )
    target = targets[0]
    if run_file:
        target = target.rsplit("::", 1)[0]
    return target


def _build_pytest_run_class_command(
    class_name: str, search_root: str = ".", run_file: bool = False
) -> str:
    """
    Build a safely quoted command for one test class or its file.
    """
    target = _resolve_pytest_class_target(class_name, search_root, run_file)
    return f"pytest {shlex.quote(target)}"


@task
def pytest_run_class(
    ctx,
    class_name,
    run_file=False,
    preview=False,
    search_root=".",
):  # type: ignore
    """Run an exactly named pytest class or its containing file.

    E.g.:
    ```bash
    > invoke pytest_run_class -c TestExample
    > invoke pytest_run_class -c TestExample --run-file
    > invoke pytest_run_class -c TestExample --search-root src --preview
    ```

    :param class_name: exact test class name to run
    :param run_file: run the whole containing file instead of only the class
    :param preview: print the command without executing it
    :param search_root: directory in which to search for test files
    """
    hltltaut.report_task()
    cmd = _build_pytest_run_class_command(
        class_name, search_root=search_root, run_file=run_file
    )
    if preview:
        _LOG.info("Preview: %s", cmd)
        return 0
    result = ctx.run(cmd, echo=True, warn=False)
    return result.return_code
