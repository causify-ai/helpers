"""
Tasks related to `im` project.

Import as:

import helpers.lib_tasks_aws as hlitaaws
"""

import logging
import os
import re
import copy
import json
from typing import Dict

from invoke import task

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.lib_tasks_utils as hlitauti
import helpers.haws as haws
import helpers.hs3 as hs3

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
                dst_airflow_dir = "/shared_k8s/airflow/dags"
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

# #############################################################################
# ECS Task Definition
# #############################################################################

# Decide where to get these values from.
_AWS_PROFILE = ""
_TASK_DEFINITION_PREFIX = ""
_TASK_DEFINITION_JSON_TEMPLATE_PATH = ""
_TASK_DEFINITION_LOG_OPTIONS_TEMPLATE = {}
_IMAGE_URL_TEMPLATE = ""
_EFS_CONFIG = {}

def _set_task_definition_config(
    task_definition_config: Dict, task_definition_name: str, region: str
) -> Dict:
    """
    Update template of ECS task definition with concrete values:

    :return: full formed task definition config dictionary
    """
    # Replace placeholder values inside container definition
    # from the template with concrete values.
    # We use single container inside our task definition and
    # the convention is to set the same name as the task
    # definition itself
    task_definition_config["containerDefinitions"][0][
        "name"
    ] = task_definition_name
    # Set placeholder image URL.
    task_definition_config["containerDefinitions"][0][
        "image"
    ] = _IMAGE_URL_TEMPLATE.format(region)
    # Set log configuration options.
    log_config_opts = copy.deepcopy(_TASK_DEFINITION_LOG_OPTIONS_TEMPLATE)
    log_config_opts["awslogs-group"] = log_config_opts["awslogs-group"].format(
        task_definition_name
    )
    log_config_opts["awslogs-region"] = region
    task_definition_config["containerDefinitions"][0]["logConfiguration"][
        "options"
    ] = log_config_opts
    # Set environment variable "CSFY_AWS_DEFAULT_REGION".
    task_definition_config["containerDefinitions"][0]["environment"][1][
        "value"
    ] = region
    # Configure access to EFS
    task_definition_config["volumes"] = _EFS_CONFIG[region]["volumes"]
    task_definition_config["containerDefinitions"][0][
        "mountPoints"
    ] = _EFS_CONFIG[region]["mountPoints"]
    return task_definition_config


def _register_task_definition(task_definition_name: str, region: str) -> None:
    """
    Register a new ECS task definition.

    :param task_definition_name: The name of the new task definition.
    :param config_file: Path to the JSON file containing the task
        definition configuration.
    :param region: Optional AWS region. If not provided, the default
        region from the AWS profile will be used.
    """
    # Check if the template file exists.
    hdbg.dassert_file_exists(_TASK_DEFINITION_JSON_TEMPLATE_PATH)
    with open(_TASK_DEFINITION_JSON_TEMPLATE_PATH, "r") as f:
        task_definition_config = json.load(f)
    client = haws.get_ecs_client(_AWS_PROFILE, region=region)
    task_definition_config = _set_task_definition_config(
        task_definition_config, task_definition_name, region
    )
    client.register_task_definition(
        family=task_definition_name,
        taskRoleArn=task_definition_config.get("taskRoleArn", ""),
        executionRoleArn=task_definition_config["executionRoleArn"],
        networkMode=task_definition_config["networkMode"],
        containerDefinitions=task_definition_config["containerDefinitions"],
        volumes=task_definition_config.get("volumes", []),
        placementConstraints=task_definition_config.get(
            "placementConstraints", []
        ),
        requiresCompatibilities=task_definition_config["requiresCompatibilities"],
        cpu=task_definition_config["cpu"],
        memory=task_definition_config["memory"],
    )
    _LOG.info(
        "Registered new task definition: %s in region %s",
        task_definition_name,
        region,
    )

@task
def aws_create_ecs_task_definition(ctx, issue_id: int = None) -> None:
    """
    Create a new ECS task definition.

    :param issue_id: issue ID to create the task definition for
    """
    hlitauti.report_task()
    hdbg.dassert_is_not(issue_id, None, "issue_id is required")
    is_valid_issue_id = str(issue_id).isdigit()
    hdbg.dassert(is_valid_issue_id, f"issue_id '{issue_id}' must be an integer")
    _LOG.debug("Creating task definition for issue '%s'", issue_id)
    task_definition_name = f"{_TASK_DEFINITION_PREFIX}-{issue_id}"
    for region in hs3.AWS_REGIONS:
        _register_task_definition(task_definition_name, region=region)
    # helpers_root = hgit.find_helpers_root()
    # exec_name = f"{helpers_root}/dev_scripts_helpers/aws/aws_create_test_task_definition.py"
    # cmd = f'invoke docker_cmd -c "{exec_name} -issue_id {issue_id}"'
    # hlitauti.run(ctx, cmd)
 