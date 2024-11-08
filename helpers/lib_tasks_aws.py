"""
Tasks related to `im` project.

Import as:

import helpers.lib_tasks_aws as hlitaaws
"""

import logging
import os
import re

from invoke import task

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hserver as hserver
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


@task
def release_dags_to_airflow(
    ctx,
    files,
    platform,
    dst_airflow_dir=None,
    release_from_branch=False,
    release_test=None,
):
    """
    Copy the DAGs to the shared Airflow directory.

    :param files: string of filenames separated by space, e.g., "a.py
        b.py c.py"
    :param platform: string indicating the platform, e.g., "EC2" or "K8"
    :param dst_airflow_dir: destination directory path in Airflow
    :param release_from_branch: boolean indicating whether to release
        from the current branch or not
    :param release_test: string indicating the test username and release
        test DAGs
    """
    hdbg.dassert(
        hserver.is_inside_docker(), "This is runnable only inside Docker."
    )
    # Make sure we are working from `master`.
    curr_branch = hgit.get_branch_name()
    if not release_from_branch:
        hdbg.dassert_eq(
            curr_branch, "master", msg="You should release from master branch"
        )
    # If no destination Airflow directory (`dst_airflow_dir`) is provided,
    # determine the appropriate directory:
    # - If `release_test` is provided, set the directory to the test-specific
    #   Airflow DAGs location.
    # - If it's not a test release, choose the destination based on the
    #   platform.
    if dst_airflow_dir is None:
        if release_test is not None:
            dst_airflow_dir = "/shared_test/airflow/dags"
        else:
            if platform == "EC2":
                dst_airflow_dir = "/shared_data/airflow_preprod_new/dags"
            elif platform == "K8":
                dst_airflow_dir = "/shared_data/airflow/dags"
            else:
                raise ValueError(f"Unknown platform: {platform}")
    hdbg.dassert_dir_exists(dst_airflow_dir)
    file_paths = files.split()
    test_file_path = []
    # Iterate over each file path in the list.
    for file_path in file_paths:
        # Check the file_path is correct.
        hdbg.dassert_file_exists(file_path)
        # Get the directory and filename
        directory, file_name = os.path.split(file_path)
        if release_test is not None:
            _LOG.info("Creating and uploading test DAG")
            content = hio.from_file(file_path)
            # Replace the line containing "USERNAME = "
            content = re.sub(
                r'USERNAME = ""', f'USERNAME = "{release_test}"', content
            )
            # Change the file name to test.
            file_name = file_name.replace("preprod", "test")
            file_path = os.path.join(directory, file_name)
            test_file_path.append(file_path)
            hio.to_file(file_path, content)
        dest_file = os.path.join(dst_airflow_dir, file_name)
        # If same file already exists, then overwrite.
        if os.path.exists(dest_file):
            _LOG.warning(
                "DAG already exists in destination, Overwriting ... %s", dest_file
            )
            # Steps to overwrite:
            # 1. Change user to root.
            # 2. Add permission to write.
            # 3. Copy file.
            # 4. Remove write permission.
            cmds = [
                f"sudo chown root {dest_file}",
                f"sudo chmod a+w {dest_file}",
                f"cp {file_path} {dest_file}",
                f"sudo chmod a-w {dest_file}",
            ]
        else:
            _LOG.info(
                "DAG doesn't exist in destination, Copying ... %s", dest_file
            )
            cmds = [f"cp {file_path} {dest_file}", f"sudo chmod a-w {dest_file}"]
        cmd = "&&".join(cmds)
        # TODO(sonaal): Instead of running scripts, run individual commands.
        # Append script for each file to a temporary file
        temp_script_path = "./tmp.release_dags.sh"
        hio.create_executable_script(temp_script_path, cmd)
        hsystem.system(f"bash -c {temp_script_path}")
    for test_file in test_file_path:
        hio.delete_file(test_file)
