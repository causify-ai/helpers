"""
Import as:

import helpers.haws as haws
"""

import logging
import os
from typing import Dict, List, Optional

import boto3
import boto3.session
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient

import helpers.hdbg as hdbg
import helpers.hs3 as hs3
import helpers.hserver as hserver

_LOG = logging.getLogger(__name__)
# #############################################################################
# Utils
# #############################################################################


def get_session(
    aws_profile: str, *, region: Optional[str] = None
) -> boto3.session.Session:
    """
    Return connected Boto3 session.

    :param aws_profile: AWS profile name to use for the session.
    :param region: AWS region, if None get region from AWS credentials.
    :return: Boto3 session object.
    """
    hdbg.dassert_isinstance(aws_profile, str)
    # When deploying jobs via ECS the container obtains credentials based on
    # passed task role specified in the ECS task-definition, refer to:
    # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html
    if aws_profile == "ck" and hserver.is_inside_ecs_container():
        _LOG.info("Fetching credentials from task IAM role")
        session = boto3.session.Session()
    else:
        # We do not need to extract the credential from the file because 
        # the credential is already set and `boto3` know where to find them.
        session = boto3.Session(profile_name=aws_profile)
    return session


def get_service_client(
    aws_profile: str, service_name: str, *, region: Optional[str] = None
) -> BaseClient:
    """
    Return client to work with desired service in the specific region.

    For params look at `get_session()`
    """
    session = get_session(aws_profile, region=region)
    client = session.client(service_name=service_name)
    return client


def get_service_resource(aws_profile: str, service_name: str) -> ServiceResource:
    """
    Return resource to work with desired service in the specific region.
    """
    session = get_session(aws_profile)
    resource = session.resource(service_name=service_name)
    return resource


# #############################################################################
# ECS
# #############################################################################


# TODO(Toma): Deprecate in favor of `get_service_client`.
def get_ecs_client(
    aws_profile: str, *, region: Optional[str] = None
) -> BaseClient:
    """
    Return client to work with Elastic Container Service in the specific
    region.

    For params look at `get_session()`
    """
    session = get_session(aws_profile, region=region)
    client = session.client(service_name="ecs")
    return client


def get_task_definition_image_url(
    task_definition_name: str, environment: str, *, region: Optional[str] = None
) -> str:
    """
    Get ECS task definition by name and return only image URL.

    :param task_definition_name: The name of the ECS task definition,
        e.g., `cmamp-test`.
    :param region: AWS region, if None get region from AWS credentials.
    :param region: look at `get_session()`
    """
    aws_profile = "csfy" if environment == "prod" else "ck"
    service_name = "ecs"
    client = get_service_client(aws_profile, service_name, region=region)
    # Get the last revision of the task definition.
    task_description = client.describe_task_definition(
        taskDefinition=task_definition_name
    )
    task_definition_json = task_description["taskDefinition"]
    image_url = task_definition_json["containerDefinitions"][0]["image"]
    return image_url


def is_task_definition_exists(
    task_definition_name: str, *, region: Optional[str] = None
) -> bool:
    """
    Check if a task definition exists in the specified region.

    :param task_definition_name: the name of the ECS task definition
    :param region: region of the task definition
    :return: whether the task definition exists
    """
    client = get_ecs_client("ck", region=region)
    try:
        client.describe_task_definition(taskDefinition=task_definition_name)
        return True
    except client.exceptions.ClientError as e:
        _LOG.warning(
            "Failed to describe task definition '%s': %s",
            task_definition_name,
            e,
        )
        return False


# TODO(Nikola): Pass a dict config instead, so any part can be updated.
def update_task_definition(
    task_definition_name: str,
    new_image_url: str,
    *,
    region: Optional[str] = None,
    environment: str,
) -> None:
    """
    Create the new revision of specified ECS task definition.

    If region is different then the default one, it is assumed that ECR
    replication is enabled from the default region to the target region.

    :param task_definition_name: The name of the ECS task definition for
        which an update to container image URL is made, e.g., `cmamp-
        test`.
    :param new_image_url: New image URL for task definition. e.g.,
        `***.dkr.ecr.***/cmamp:prod`.
    :param region: AWS region, if None get region from AWS credentials.
    """
    aws_profile = "csfy" if environment == "prod" else "ck"
    client = get_ecs_client(aws_profile, region=region)
    # Get the last revision of the task definition.
    task_description = client.describe_task_definition(
        taskDefinition=task_definition_name
    )
    task_definition_json = task_description["taskDefinition"]
    # Set new image.
    old_image_url = task_definition_json["containerDefinitions"][0]["image"]
    if old_image_url == new_image_url:
        _LOG.info(
            "New image url `%s` is already set for task definition `%s`!",
            new_image_url,
            task_definition_name,
        )
        return
    task_definition_json["containerDefinitions"][0]["image"] = new_image_url
    # Register the new revision with the new image.
    response = client.register_task_definition(
        family=task_definition_name,
        taskRoleArn=task_definition_json.get("taskRoleArn", ""),
        executionRoleArn=task_definition_json["executionRoleArn"],
        networkMode=task_definition_json["networkMode"],
        containerDefinitions=task_definition_json["containerDefinitions"],
        volumes=task_definition_json["volumes"],
        placementConstraints=task_definition_json["placementConstraints"],
        requiresCompatibilities=task_definition_json["requiresCompatibilities"],
        cpu=task_definition_json["cpu"],
        memory=task_definition_json["memory"],
    )
    updated_image_url = response["taskDefinition"]["containerDefinitions"][0][
        "image"
    ]
    # Check if the image URL is updated.
    hdbg.dassert_eq(updated_image_url, new_image_url)
    _LOG.info(
        "The image URL of `%s` task definition is updated to `%s`",
        task_definition_name,
        updated_image_url,
    )


def list_all_objects(
    s3_client: BaseClient, bucket_name: str, prefix: str
) -> List[Dict]:
    """
    List all objects in the specified S3 bucket under the given prefix,
    handling pagination.

    :param s3_client: Instance of boto3 S3 client.
    :param bucket_name: The name of the S3 bucket e.g., `cryptokaizen-data-test`.
    :param prefix: Prefix to filter the S3 objects e.g., `binance/historical_bid_ask/`.
    :return: A list of dictionaries containing metadata about each object. E.g.,
        ```
        [
            {
                'Key': 'binance/historical_bid_ask/S_DEPTH/1000BONK_USDT/2023-05-27/data.tar.gz',
                'LastModified': datetime.datetime(2024, 5, 30, 17, 12, 12, tzinfo=tzlocal()),
                'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
                'Size': 0,
                'StorageClass': 'STANDARD'
            },
            {
                'Key': 'binance/historical_bid_ask/S_DEPTH/1000BONK_USDT/2023-05-28/data.tar.gz',
                'LastModified': datetime.datetime(2024, 5, 30, 17, 12, 12, tzinfo=tzlocal()),
                'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
                'Size': 0,
                'StorageClass': 'STANDARD'
            }
        ]
        ```
    """
    objects = []
    continuation_token = None
    while True:
        # If there's a continuation token, include it in the request to fetch
        # the next page of results.
        if continuation_token:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                ContinuationToken=continuation_token,
            )
        else:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=prefix
            )
        # Extend the objects list with the contents of the current page.
        objects.extend(response.get("Contents", []))
        # Check if there are more pages.
        if response.get("IsTruncated"):
            continuation_token = response.get("NextContinuationToken")
        else:
            break
    return objects
