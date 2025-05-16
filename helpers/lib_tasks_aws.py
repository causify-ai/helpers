"""
Tasks related to `im` project.

Import as:

import helpers.lib_tasks_aws as hlitaaws
"""

import copy
import json
import logging
import os
import re
from typing import Dict

from invoke import task

import helpers.haws as haws
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hs3 as hs3
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.lib_tasks_utils as hlitauti
import helpers.repo_config_utils as hrecouti

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
_AWS_PROFILE = "ck"
_TASK_DEFINITION_LOG_OPTIONS_TEMPLATE = {
    "awslogs-create-group": "true",
    "awslogs-group": "/ecs/{}",
    "awslogs-region": "{}",
    "awslogs-stream-prefix": "ecs",
}
_IMAGE_URL_TEMPLATE = "623860924167.dkr.ecr.{}.amazonaws.com/{}:prod-xyz"


def _get_ecs_task_definition_template() -> Dict:
    """
    Get the ECS task definition template.

    :return: ECS task definition template
    """
    # TODO(heanh): Read the path from repo config.
    s3_path = "s3://causify-shared-configs/preprod/templates/ecs/ecs_task_definition_template.json"
    hs3.dassert_is_s3_path(s3_path)
    task_definition_config = hs3.from_file(s3_path, aws_profile=_AWS_PROFILE)
    task_definition_config = json.loads(task_definition_config)
    return task_definition_config


def _get_efs_mount_config_template() -> Dict:
    """
    Get the EFS mount config template.

    :return: EFS mount config template
    """
    # TODO(heanh): Read the path from repo config.
    s3_path = "s3://causify-shared-configs/preprod/templates/efs/efs_mount_config_template.json"
    hs3.dassert_is_s3_path(s3_path)
    efs_config = hs3.from_file(s3_path, aws_profile=_AWS_PROFILE)
    efs_config = json.loads(efs_config)
    return efs_config


def _set_task_definition_config(
    task_definition_config: Dict, task_definition_name: str, region: str
) -> Dict:
    """
    Update template of ECS task definition with concrete values.

    :param task_definition_config: task definition config template
    :param task_definition_name: name of the task definition
    :param region: region to create the task definition in
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
    image_name = hrecouti.get_repo_config().get_docker_base_image_name()
    task_definition_config["containerDefinitions"][0]["image"] = (
        _IMAGE_URL_TEMPLATE.format(region, image_name)
    )
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
    efs_config = _get_efs_mount_config_template()
    task_definition_config["volumes"] = efs_config[region]["volumes"]
    task_definition_config["containerDefinitions"][0]["mountPoints"] = efs_config[
        region
    ]["mountPoints"]
    return task_definition_config


def _register_task_definition(task_definition_name: str, region: str) -> None:
    """
    Register a new ECS task definition.

    :param task_definition_name: name of the new task definition.
    :param config_file: path to the JSON file containing the task
        definition configuration.
    :param region: region to create the task definition in
    """
    task_definition_config = _get_ecs_task_definition_template()
    client = haws.get_ecs_client(_AWS_PROFILE, region=region)
    # Prevent overwriting existing task definition if it exists.
    if haws.is_task_definition_exists(task_definition_name, region=region):
        _LOG.info(
            "Task definition %s already exists in region %s",
            task_definition_name,
            region,
        )
        return
    #
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


def _update_task_definition(
    task_definition: str, image_tag: str, region: str
) -> None:
    """
    Create the new revision of specified ECS task definition and point Image
    URL specified to the new candidate image.

    :param task_definition: the name of the ECS task definition for
        which an update to container image URL is made, e.g. cmamp-test
    :param image_tag: the hash of the new candidate image, e.g.
        13538588e
    :param region: region to update the task definition in
    """
    old_image_url = haws.get_task_definition_image_url(
        task_definition, region=region
    )
    # Edit container version, e.g. cmamp:prod-12a45 - > cmamp:prod-12b46`
    new_image_url = re.sub("prod-(.+)$", f"prod-{image_tag}", old_image_url)
    haws.update_task_definition(task_definition, new_image_url, region=region)


@task
def aws_create_test_ecs_task_definition(
    ctx,
    issue_id: int = None,
    region: str = hs3.AWS_EUROPE_REGION_1,
) -> None:
    """
    Create a new ECS task definition.

    :param issue_id: issue ID to create the task definition for
    :param region: region to create the task definition in
    """
    _ = ctx
    hlitauti.report_task()
    # Check if the `issue_id` provided is valid.
    hdbg.dassert_is_not(issue_id, None, "issue_id is required")
    is_valid_issue_id = str(issue_id).isdigit()
    hdbg.dassert(is_valid_issue_id, f"issue_id '{issue_id}' must be an integer")
    # Check if the `region` provided is valid.
    valid_regions = hs3.AWS_REGION_MAPPING.keys()
    hdbg.dassert(
        region in valid_regions,
        f"region '{region}' must be one of {valid_regions}",
    )
    # Prepare inputs.
    region = hs3.AWS_REGION_MAPPING[region]
    image_name = hrecouti.get_repo_config().get_docker_base_image_name()
    task_definition_name = f"{image_name}-test-{issue_id}"
    # Register task definition.
    _register_task_definition(task_definition_name, region=region)


@task
def aws_create_prod_ecs_task_definition(
    ctx,
    region: str = hs3.AWS_EUROPE_REGION_1,
) -> None:
    """
    Create a new ECS task definition.

    :param region: region to create the task definition in
    """
    _ = ctx
    hlitauti.report_task()
    hdbg.dassert(
        region in hs3.AWS_REGIONS,
        f"region '{region}' must be one of {hs3.AWS_REGIONS}",
    )
    image_name = hrecouti.get_repo_config().get_docker_base_image_name()
    task_definition_name = f"{image_name}-prod"
    # Register task definition.
    _register_task_definition(task_definition_name, region=region)


# TODO(heanh): Should this be an invoke task?
def aws_update_ecs_task_definition(
    ctx,
    task_definition: str = None,
    image_tag: str = None,
    region: str = hs3.AWS_EUROPE_REGION_1,
) -> None:
    """
    Update an existing ECS task definition.

    :param task_definition: the name of the ECS task definition for
        which an update to container image URL is made, e.g. cmamp-test
    :param image_tag: the hash of the new candidate image, e.g.
        13538588e
    :param region: region to update the task definition in
    """
    _ = ctx
    hlitauti.report_task()
    hdbg.dassert_is_not(task_definition, None, "task_definition is required")
    hdbg.dassert_is_not(image_tag, None, "image_tag is required")
    hdbg.dassert(
        region in hs3.AWS_REGIONS,
        f"region '{region}' must be one of {hs3.AWS_REGIONS}",
    )
    _update_task_definition(task_definition, image_tag, region)
