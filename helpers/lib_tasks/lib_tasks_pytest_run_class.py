"""
Import as:

import helpers.lib_tasks.lib_tasks_pytest_run_class as hltltaprc
"""

import logging

from invoke.tasks import task

import helpers.lib_tasks.lib_tasks_find as hltltafi
import helpers.lib_tasks.lib_tasks_pytest as hltltapy
import helpers.lib_tasks.lib_tasks_utils as hltltaut

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


def _resolve_pytest_class_target(class_name: str, dir_name: str) -> str:
    """Resolve one exact test class to a pytest node id."""
    if not class_name:
        raise ValueError("You need to specify a class name")
    file_names = hltltafi._find_test_files(dir_name)
    matches = hltltafi._find_test_class(
        class_name, file_names, exact_match=True
    )
    if not matches:
        raise ValueError(
            f"Could not find test class '{class_name}' under '{dir_name}'"
        )
    if len(matches) != 1:
        raise ValueError(
            f"Test class '{class_name}' is ambiguous: {matches}"
        )
    return matches[0]


def _build_pytest_run_class_command(class_name: str, dir_name: str = ".") -> str:
    """Build a pytest command targeting exactly one test class."""
    target = _resolve_pytest_class_target(class_name, dir_name)
    return f"pytest {target}"


@task
def pytest_run_class(  # type: ignore
    ctx,
    class_name,
    dir_name=".",
    dry_run=False,
    stage="dev",
    version="",
    skip_pull=False,
):
    """Run exactly one pytest class resolved by its class name.

    :param class_name: exact test class name to execute
    :param dir_name: directory to search for the class
    :param dry_run: print the resolved pytest command without executing it
    :param stage: select a specific stage for the Docker image
    :param version: Docker image version
    :param skip_pull: skip pulling the Docker image before execution
    """
    hltltaut.report_task()
    cmd = _build_pytest_run_class_command(class_name, dir_name)
    _LOG.info("cmd=%s", cmd)
    if dry_run:
        print(cmd)
        return 0
    rc = hltltapy._run_test_cmd(
        ctx,
        stage,
        version,
        cmd,
        coverage=False,
        collect_only=False,
        skip_pull=skip_pull,
        start_coverage_script=False,
    )
    return rc
