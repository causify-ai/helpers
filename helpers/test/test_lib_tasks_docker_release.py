import logging
import os
import unittest.mock as umock
from typing import Generator, List

import boto3
import moto
import pytest

import helpers.hgit as hgit
import helpers.hunit_test as hunitest
import helpers.lib_tasks_docker as hlitadoc
import helpers.lib_tasks_docker_release as hltadore
import helpers.test.test_lib_tasks as httestlib

_LOG = logging.getLogger(__name__)


def _extract_commands_from_call(calls: List[umock._Call]) -> List[str]:
    """
    Extract command strings from a list of mock call arguments.

    Example:
        calls = [
            (
                # args tuple: (context, command)
                (mock_ctx, "docker build --no-cache image1"),
                # kwargs dictionary
                {"pty": True}
            )
        ]
        After extraction:
        ["docker build --no-cache image1"]

    :param calls: list of mock call objects containing (args, kwargs)
    :return: list of command strings
    """
    # Each mock call is a (args, kwargs) tuple, extract the command string
    # from args[1] in each call.
    call_list = [args_[1] for args_, kwargs_ in calls]
    return call_list


# #############################################################################
# _DockerFlowTestHelper
# #############################################################################


class _DockerFlowTestHelper(hunitest.TestCase):
    """
    Helper test class to perform common setup, teardown logic and assertion
    checks for Docker flow tests.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        self.set_up_test()
        yield
        self.tear_down_test()

    def set_up_test(self) -> None:
        # Mock system calls.
        self.system_patcher = umock.patch("helpers.hsystem.system")
        self.mock_system = self.system_patcher.start()
        # Mock run.
        self.run_patcher = umock.patch("helpers.lib_tasks_utils.run")
        self.mock_run = self.run_patcher.start()
        # Mock version validation.
        self.version_patcher = umock.patch(
            "helpers.lib_tasks_docker.dassert_is_subsequent_version"
        )
        self.mock_version = self.version_patcher.start()
        # Mock docker login.
        self.docker_login_patcher = umock.patch(
            "helpers.lib_tasks_docker.docker_login"
        )
        self.mock_docker_login = self.docker_login_patcher.start()
        # Mock environment variable.
        self.env_patcher = umock.patch.dict(
            "os.environ", {"CSFY_ECR_BASE_PATH": "test.ecr.path"}
        )
        self.get_default_param_patcher = umock.patch(
            "helpers.lib_tasks_utils.get_default_param",
            side_effect=lambda param: {
                "CSFY_ECR_BASE_PATH": "test.ecr.path",
                "BASE_IMAGE": "test-image",
            }.get(param, ""),
        )
        self.mock_get_default_param = self.get_default_param_patcher.start()
        self.env_patcher.start()
        self.get_docker_base_image_name_patcher = umock.patch(
            "helpers.repo_config_utils.RepoConfig.get_docker_base_image_name"
        )
        self.mock_get_docker_base_image_name = (
            self.get_docker_base_image_name_patcher.start()
        )
        #
        self.patchers = {
            "system": self.system_patcher,
            "run": self.run_patcher,
            "version": self.version_patcher,
            "docker_login": self.docker_login_patcher,
            "env": self.env_patcher,
            "docker_base_image_name": self.get_docker_base_image_name_patcher,
            "default_param": self.get_default_param_patcher,
        }
        # Test inputs.
        self.mock_ctx = httestlib._build_mock_context_returning_ok()
        self.test_version = "1.0.0"
        self.test_base_image = "test-registry.com/test-image"
        self.test_multi_arch = "linux/amd64,linux/arm64"
        self.mock_get_docker_base_image_name.return_value = "test-image"

    def tear_down_test(self) -> None:
        """
        Clean up test environment by stopping all mocks after each test case.
        """
        for patcher in self.patchers.values():
            patcher.stop()

    def _check_docker_command_output(
        self, expected: str, call_args_list: List[umock._Call]
    ) -> None:
        """
        Verify that the sequence of Docker commands from mock calls matches the
        expected string.

        :param expected: expected command string
        :param call_args_list: list of mock call objects
        """
        actual_cmds = _extract_commands_from_call(call_args_list)
        actual_cmds = "\n".join(actual_cmds)
        self.assert_equal(
            actual_cmds,
            expected,
            purify_text=True,
            purify_expected_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )


# #############################################################################
# Test_docker_build_local_image1
# #############################################################################


class Test_docker_build_local_image1(_DockerFlowTestHelper):
    """
    Test building a local Docker image.
    """

    def test_single_arch1(self) -> None:
        """
        Test building with single architecture.

        This test checks:
        - Single architecture build
        - No-cache build options
        - Custom build arguments
        - Local user-specific tagging
        """
        # Call tested function.
        hltadore.docker_build_local_image(
            self.mock_ctx,
            self.test_version,
            cache=False,
            base_image=self.test_base_image,
            poetry_mode="update",
        )
        # The output is a list of strings, each representing a command.
        expected = r"""
        cp -f devops/docker_build/dockerignore.dev .dockerignore
        tar -czh . | DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --build-arg AM_CONTAINER_VERSION=1.0.0 --build-arg INSTALL_DIND=True --build-arg POETRY_MODE=update --build-arg CLEAN_UP_INSTALLATION=True \
            --tag test-registry.com/test-image:local-$USER_NAME-1.0.0 \
            --file devops/docker_build/dev.Dockerfile \
            -
        invoke docker_cmd --stage local --version 1.0.0 --cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull
        cp -f poetry.lock.out ./devops/docker_build/poetry.lock
        cp -f pip_list.txt ./devops/docker_build/pip_list.txt
        docker image ls test-registry.com/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_multi_arch1(self) -> None:
        """
        Test building with multiple architectures.

        This test checks:
        - Multi-architecture build (amd64, arm64)
        - Buildx driver setup
        - Platform-specific build options
        - Image pushing to registry
        """
        # Call tested function.
        hltadore.docker_build_local_image(
            self.mock_ctx,
            self.test_version,
            cache=False,
            base_image=self.test_base_image,
            poetry_mode="update",
            multi_arch=self.test_multi_arch,
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.dev .dockerignore
        docker buildx create \
            --name multiarch_builder \
            --driver docker-container \
            --bootstrap \
            && \
            docker buildx use multiarch_builder
        tar -czh . | DOCKER_BUILDKIT=0 \
            time \
            docker buildx build \
            --no-cache \
            --push \
            --platform linux/amd64,linux/arm64 \
            --build-arg AM_CONTAINER_VERSION=1.0.0 --build-arg INSTALL_DIND=True --build-arg POETRY_MODE=update --build-arg CLEAN_UP_INSTALLATION=True \
            --tag test-registry.com/test-image:local-$USER_NAME-1.0.0 \
            --file devops/docker_build/dev.Dockerfile \
            -
        docker pull test-registry.com/test-image:local-$USER_NAME-1.0.0
        invoke docker_cmd --stage local --version 1.0.0 --cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull
        cp -f poetry.lock.out ./devops/docker_build/poetry.lock
        cp -f pip_list.txt ./devops/docker_build/pip_list.txt
        docker image ls test-registry.com/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_build_prod_image1
# #############################################################################


class Test_docker_build_prod_image1(_DockerFlowTestHelper):
    """
    Test building a prod Docker image.
    """

    def test_single_arch_prod_image1(self) -> None:
        """
        Test building with single architecture.

        This test checks:
        - Production build workflow
        - Single architecture build
        - Build arguments for prod environment
        - Prod image versioning
        - Default and versioned tagging
        """
        # Call tested function.
        hltadore.docker_build_prod_image(
            self.mock_ctx,
            self.test_version,
            base_image=self.test_base_image,
            cache=False,
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --tag test-registry.com/test-image:prod-1.0.0 \
            --file /app/devops/docker_build/prod.Dockerfile \
            --build-arg VERSION=1.0.0 \
            --build-arg ECR_BASE_PATH=test.ecr.path \
            --build-arg IMAGE_NAME=test-image \
            /app
        docker tag test-registry.com/test-image:prod-1.0.0 test-registry.com/test-image:prod
        docker image ls test-registry.com/test-image:prod
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_multi_arch_prod_image1(self) -> None:
        """
        Test building with multiple architectures.

        This test checks:
        - Multi-architecture production build
        - Buildx setup for multi-platform builds
        - Push to registry during build
        - Production build arguments
        - Multi-arch specific options
        """
        # Call tested function.
        hltadore.docker_build_multi_arch_prod_image(
            self.mock_ctx,
            self.test_version,
            base_image=self.test_base_image,
            cache=False,
            multi_arch=self.test_multi_arch,
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        docker buildx create \
            --name multiarch_builder \
            --driver docker-container \
            --bootstrap \
            && \
            docker buildx use multiarch_builder
        tar -czh . | DOCKER_BUILDKIT=0 \
            time \
            docker buildx build \
            --no-cache \
            --push \
            --platform linux/amd64,linux/arm64 \
            --build-arg VERSION=1.0.0 --build-arg ECR_BASE_PATH=test.ecr.path \
            --tag test-registry.com/test-image:prod-1.0.0 \
            --file devops/docker_build/prod.Dockerfile \
            -
        docker pull test-registry.com/test-image:prod-1.0.0
        docker image ls test-registry.com/test-image:prod-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    @pytest.mark.skipif(
        not hgit.is_in_helpers_as_supermodule(),
        # TODO(gp): Is the assertion too strict?
        reason="Needs to run insde a super module",
    )
    def test_candidate_tag1(self) -> None:
        """
        Test building with candidate mode using tag.

        This test checks:
        - Production build using candidate mode
        - Custom tag specification
        - Build arguments
        - Non-default image tagging
        """
        test_tag = "test_tag"
        # Call tested function.
        hltadore.docker_build_prod_image(
            self.mock_ctx,
            self.test_version,
            base_image=self.test_base_image,
            cache=False,
            candidate=True,
            tag=test_tag,
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --tag test-registry.com/test-image:prod-test_tag \
            --file /app/devops/docker_build/prod.Dockerfile \
            --build-arg VERSION=1.0.0 \
            --build-arg ECR_BASE_PATH=test.ecr.path \
            --build-arg IMAGE_NAME=test-image \
            /app
        docker image ls test-registry.com/test-image:prod-test_tag
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_candidate_user_tag1(self) -> None:
        """
        Test building with candidate mode using user tag.

        This test checks:
        - Production build using candidate mode
        - Combined user and custom tag parameters
        - Custom tag format (prod-user-tag)
        - Build arguments
        """
        test_user_tag = "test_user"
        test_tag = "test_tag"
        # Call tested function.
        hltadore.docker_build_prod_image(
            self.mock_ctx,
            self.test_version,
            base_image=self.test_base_image,
            cache=False,
            candidate=True,
            user_tag=test_user_tag,
            tag=test_tag,
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --tag test-registry.com/test-image:prod-test_user-test_tag \
            --file /app/devops/docker_build/prod.Dockerfile \
            --build-arg VERSION=1.0.0 \
            --build-arg ECR_BASE_PATH=test.ecr.path \
            --build-arg IMAGE_NAME=test-image \
            /app
        docker image ls test-registry.com/test-image:prod-test_user-test_tag
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_tag_push_multi_arch_prod_image1
# #############################################################################


class Test_docker_tag_push_multi_arch_prod_image1(_DockerFlowTestHelper):
    """
    Test tagging and pushing a multi-architecture Docker image.
    """

    def test_aws_ecr1(self) -> None:
        """
        Test pushing to AWS ECR.

        This test checks:
        - Multi-arch image tagging
        - AWS ECR target registry
        - Production image versioning
        """
        # Call tested function.
        target_registry = "aws_ecr.ck"
        hltadore.docker_tag_push_multi_arch_prod_image(
            self.mock_ctx,
            self.test_version,
            target_registry=target_registry,
        )
        expected = r"""
        docker buildx imagetools create -t test.ecr.path/test-image:prod test.ecr.path/test-image:prod-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_dockerhub1(self) -> None:
        """
        Test pushing to DockerHub from AWS ECR.

        This test checks:
        - Multi-arch image tagging
        - DockerHub registry (differs from AWS ECR test)
        - Version and latest tagging
        - Cross-registry image copying
        """
        # Call tested function.
        target_registry = "dockerhub.causify"
        hltadore.docker_tag_push_multi_arch_prod_image(
            self.mock_ctx,
            self.test_version,
            target_registry=target_registry,
        )
        expected = r"""
        docker buildx imagetools create -t causify/test-image:prod-1.0.0 test.ecr.path/test-image:prod-1.0.0
        docker buildx imagetools create -t causify/test-image:prod test.ecr.path/test-image:prod-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_tag_push_multi_build_local_image_as_dev1
# #############################################################################


class Test_docker_tag_push_multi_build_local_image_as_dev1(
    _DockerFlowTestHelper
):
    """
    Test tagging and pushing a multi-arch local Docker image as dev.
    """

    def test_aws_ecr1(self) -> None:
        """
        Test pushing to AWS ECR.

        This test checks:
        - Multi-arch image tagging
        - AWS ECR target registry
        - Dev image versioning
        - Default and versioned tagging
        """
        # Call tested function.
        target_registry = "aws_ecr.ck"
        hltadore.docker_tag_push_multi_build_local_image_as_dev(
            self.mock_ctx,
            self.test_version,
            target_registry=target_registry,
        )
        expected = r"""
        docker buildx imagetools create -t test.ecr.path/test-image:dev-1.0.0 test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t test.ecr.path/test-image:dev test.ecr.path/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_dockerhub1(self) -> None:
        """
        Test pushing to DockerHub from AWS ECR.

        This test checks:
        - Multi-arch image tagging
        - DockerHub registry (differs from AWS ECR test)
        - Version and latest tagging
        - Cross-registry image copying
        """
        # Call tested function.
        target_registry = "dockerhub.causify"
        hltadore.docker_tag_push_multi_build_local_image_as_dev(
            self.mock_ctx,
            self.test_version,
            target_registry=target_registry,
        )
        expected = r"""
        docker buildx imagetools create -t causify/test-image:dev-1.0.0 test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t causify/test-image:dev test.ecr.path/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_release_dev_image1
# #############################################################################


class Test_docker_release_dev_image1(_DockerFlowTestHelper):
    """
    Test releasing a dev Docker image.
    """

    def test_aws_ecr1(self) -> None:
        """
        Test releasing the dev image to AWS ECR.

        This test checks:
          - Build workflow
          - No-cache build options
          - Dev image versioning
          - Default and versioned tagging
          - Registry target selection
          - Architecture support
          - Tagging and versioning
        """
        # Call tested function.
        hltadore.docker_release_dev_image(
            self.mock_ctx,
            self.test_version,
            cache=False,
            skip_tests=True,
            fast_tests=False,
            slow_tests=False,
            superslow_tests=False,
            qa_tests=False,
            push_to_repo=True,
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.dev .dockerignore
        tar -czh . | DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --build-arg AM_CONTAINER_VERSION=1.0.0 --build-arg INSTALL_DIND=True --build-arg POETRY_MODE=update --build-arg CLEAN_UP_INSTALLATION=True \
            --tag test.ecr.path/test-image:local-$USER_NAME-1.0.0 \
            --file devops/docker_build/dev.Dockerfile \
            -
        invoke docker_cmd --stage local --version 1.0.0 --cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull
        cp -f poetry.lock.out ./devops/docker_build/poetry.lock
        cp -f pip_list.txt ./devops/docker_build/pip_list.txt
        docker image ls test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker tag test.ecr.path/test-image:local-$USER_NAME-1.0.0 test.ecr.path/test-image:dev-1.0.0
        docker tag test.ecr.path/test-image:local-$USER_NAME-1.0.0 test.ecr.path/test-image:dev
        docker push test.ecr.path/test-image:dev-1.0.0
        docker push test.ecr.path/test-image:dev
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_release_prod_image1
# #############################################################################


class Test_docker_release_prod_image1(_DockerFlowTestHelper):
    """
    Test releasing a prod Docker image.
    """

    def test_aws_ecr1(self) -> None:
        """
        Test releasing the prod image to AWS ECR.

        This test checks:
          - Build workflow
          - No-cache build options
          - Prod image versioning
          - Default and versioned tagging
          - Registry target selection
          - Architecture support
          - Tagging and versioning
        """
        # Call tested function.
        hltadore.docker_release_prod_image(
            self.mock_ctx,
            self.test_version,
            cache=False,
            skip_tests=True,
            fast_tests=False,
            slow_tests=False,
            superslow_tests=False,
            qa_tests=False,
            push_to_repo=True,
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --tag test.ecr.path/test-image:prod-1.0.0 \
            --file /app/devops/docker_build/prod.Dockerfile \
            --build-arg VERSION=1.0.0 \
            --build-arg ECR_BASE_PATH=test.ecr.path \
            --build-arg IMAGE_NAME=test-image \
            /app
        docker tag test.ecr.path/test-image:prod-1.0.0 test.ecr.path/test-image:prod
        docker image ls test.ecr.path/test-image:prod
        docker push test.ecr.path/test-image:prod-1.0.0
        docker push test.ecr.path/test-image:prod
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_release_multi_build_dev_image1
# #############################################################################


class Test_docker_release_multi_build_dev_image1(_DockerFlowTestHelper):
    """
    Test releasing a multi-arch dev Docker image.
    """

    def test_single_registry1(self) -> None:
        """
        Test releasing to a single registry.

        This test checks:
        - Multi-arch build setup
        - Build and push workflow
        - Dev image tagging
        - Test skipping options
        - Single registry target
        """
        # Call tested function.
        hltadore.docker_release_multi_build_dev_image(
            self.mock_ctx,
            self.test_version,
            cache=False,
            skip_tests=True,
            fast_tests=False,
            slow_tests=False,
            superslow_tests=False,
            qa_tests=False,
            target_registries="aws_ecr.ck",
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.dev .dockerignore
        docker buildx create \
            --name multiarch_builder \
            --driver docker-container \
            --bootstrap \
            && \
            docker buildx use multiarch_builder
        tar -czh . | DOCKER_BUILDKIT=0 \
            time \
            docker buildx build \
            --no-cache \
            --push \
            --platform linux/amd64,linux/arm64 \
            --build-arg AM_CONTAINER_VERSION=1.0.0 --build-arg INSTALL_DIND=True --build-arg POETRY_MODE=update --build-arg CLEAN_UP_INSTALLATION=True \
            --tag test.ecr.path/test-image:local-$USER_NAME-1.0.0 \
            --file devops/docker_build/dev.Dockerfile \
            -
        docker pull test.ecr.path/test-image:local-$USER_NAME-1.0.0
        invoke docker_cmd --stage local --version 1.0.0 --cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull
        cp -f poetry.lock.out ./devops/docker_build/poetry.lock
        cp -f pip_list.txt ./devops/docker_build/pip_list.txt
        docker image ls test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t test.ecr.path/test-image:dev-1.0.0 test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t test.ecr.path/test-image:dev test.ecr.path/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_multiple_registries1(self) -> None:
        """
        Test releasing to multiple registries.

        This test checks:
        - Multi-arch build workflow
        - Multiple registry targets (AWS ECR and DockerHub)
        - Parallel image tagging
        - Image retagging for different registries
        """
        # Call tested function.
        hltadore.docker_release_multi_build_dev_image(
            self.mock_ctx,
            self.test_version,
            cache=False,
            skip_tests=True,
            fast_tests=False,
            slow_tests=False,
            superslow_tests=False,
            qa_tests=False,
            target_registries="aws_ecr.ck,dockerhub.causify",
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.dev .dockerignore
        docker buildx create \
            --name multiarch_builder \
            --driver docker-container \
            --bootstrap \
            && \
            docker buildx use multiarch_builder
        tar -czh . | DOCKER_BUILDKIT=0 \
            time \
            docker buildx build \
            --no-cache \
            --push \
            --platform linux/amd64,linux/arm64 \
            --build-arg AM_CONTAINER_VERSION=1.0.0 --build-arg INSTALL_DIND=True --build-arg POETRY_MODE=update --build-arg CLEAN_UP_INSTALLATION=True \
            --tag test.ecr.path/test-image:local-$USER_NAME-1.0.0 \
            --file devops/docker_build/dev.Dockerfile \
            -
        docker pull test.ecr.path/test-image:local-$USER_NAME-1.0.0
        invoke docker_cmd --stage local --version 1.0.0 --cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull
        cp -f poetry.lock.out ./devops/docker_build/poetry.lock
        cp -f pip_list.txt ./devops/docker_build/pip_list.txt
        docker image ls test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t test.ecr.path/test-image:dev-1.0.0 test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t test.ecr.path/test-image:dev test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t causify/test-image:dev-1.0.0 test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t causify/test-image:dev test.ecr.path/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_rollback_dev_image1
# #############################################################################


class Test_docker_rollback_dev_image1(_DockerFlowTestHelper):
    """
    Test rolling back a dev Docker image.
    """

    def test_aws_ecr1(self) -> None:
        """
        Test rolling back and pushing to AWS ECR.

        This test checks:
        - Dev image rollback workflow
        - Version-specific image pull
        - Retagging as latest
        - Repository pushing
        """
        # Call tested function.
        hltadore.docker_rollback_dev_image(
            self.mock_ctx,
            self.test_version,
            push_to_repo=True,
        )
        expected = r"""
        docker pull test.ecr.path/test-image:dev-1.0.0
        docker tag test.ecr.path/test-image:dev-1.0.0 test.ecr.path/test-image:dev
        docker push test.ecr.path/test-image:dev-1.0.0
        docker push test.ecr.path/test-image:dev
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_rollback_prod_image1
# #############################################################################


class Test_docker_rollback_prod_image1(_DockerFlowTestHelper):
    """
    Test rolling back a prod Docker image.
    """

    def test_aws_ecr1(self) -> None:
        """
        Test rolling back and pushing to AWS ECR.

        This test checks:
        - Production image rollback workflow
        - Version-specific image pull
        - Retagging as latest production
        - Repository pushing
        """
        # Call tested function.
        hltadore.docker_rollback_prod_image(
            self.mock_ctx,
            self.test_version,
            push_to_repo=True,
        )
        expected = r"""
        docker pull test.ecr.path/test-image:prod-1.0.0
        docker tag test.ecr.path/test-image:prod-1.0.0 test.ecr.path/test-image:prod
        docker push test.ecr.path/test-image:prod-1.0.0
        docker push test.ecr.path/test-image:prod
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_push_prod_candidate_image1
# #############################################################################


class Test_docker_push_prod_candidate_image1(_DockerFlowTestHelper):
    """
    Test pushing a prod candidate Docker image.
    """

    def test_aws_ecr1(self) -> None:
        """
        Test pushing to AWS ECR.

        This test checks:
        - Candidate image pushing
        - AWS ECR target registry
        - Hash-based image tagging
        """
        # Call tested function.
        candidate = "4759b3685f903e6c669096e960b248ec31c63b69"
        hltadore.docker_push_prod_candidate_image(
            self.mock_ctx,
            candidate=candidate,
        )
        expected = r"""
        docker push test.ecr.path/test-image:prod-4759b3685f903e6c669096e960b248ec31c63b69
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_release_multi_arch_prod_image1
# #############################################################################


class Test_docker_release_multi_arch_prod_image1(_DockerFlowTestHelper):
    """
    Test releasing a multi-arch prod Docker image.
    """

    def test_multiple_registries1(self) -> None:
        """
        Test releasing to AWS ECR and DockerHub.

        This test checks:
        - Multi-arch build workflow
        - AWS ECR and DockerHub target registries
        - Test skipping options
        - Image tagging and pushing
        """
        # Call tested function.
        hltadore.docker_release_multi_arch_prod_image(
            self.mock_ctx,
            self.test_version,
            cache=False,
            skip_tests=True,
            fast_tests=False,
            slow_tests=False,
            superslow_tests=False,
            qa_tests=False,
            docker_registry=["aws_ecr.ck", "dockerhub.causify"],
        )
        expected = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        docker buildx create \
            --name multiarch_builder \
            --driver docker-container \
            --bootstrap \
            && \
            docker buildx use multiarch_builder
        tar -czh . | DOCKER_BUILDKIT=0 \
            time \
            docker buildx build \
            --no-cache \
            --push \
            --platform linux/amd64,linux/arm64 \
            --build-arg VERSION=1.0.0 --build-arg ECR_BASE_PATH=test.ecr.path \
            --tag test.ecr.path/test-image:prod-1.0.0 \
            --file devops/docker_build/prod.Dockerfile \
            -
        docker pull test.ecr.path/test-image:prod-1.0.0
        docker image ls test.ecr.path/test-image:prod-1.0.0
        docker buildx imagetools create -t test.ecr.path/test-image:prod test.ecr.path/test-image:prod-1.0.0
        docker buildx imagetools create -t causify/test-image:prod-1.0.0 test.ecr.path/test-image:prod-1.0.0
        docker buildx imagetools create -t causify/test-image:prod test.ecr.path/test-image:prod-1.0.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_create_candidate_image1
# #############################################################################


class Test_docker_create_candidate_image1(_DockerFlowTestHelper):
    """
    Test creating a candidate Docker image.
    """

    def set_up_test2(self) -> None:
        """
        Set up test environment with additional mocks specific to this test
        class.
        """
        self.set_up_test()
        # Mock git hash.
        self.git_hash_patcher = umock.patch(
            "helpers.hgit.get_head_hash",
            return_value="4759b3685f903e6c669096e960b248ec31c63b69",
        )
        self.mock_git_hash = self.git_hash_patcher.start()
        self.patchers["git_hash"] = self.git_hash_patcher
        # Mock workspace size check.
        self.workspace_check_patcher = umock.patch(
            "helpers.lib_tasks_docker_release._check_workspace_dir_sizes"
        )
        self.mock_workspace_check = self.workspace_check_patcher.start()
        self.patchers["workspace_check"] = self.workspace_check_patcher
        # Mock file existence check to handle both paths.
        self.file_exists_patcher = umock.patch(
            "helpers.hdbg.dassert_file_exists"
        )
        self.mock_file_exists = self.file_exists_patcher.start()
        self.patchers["file_exists"] = self.file_exists_patcher
        # Mock `docker_build_prod_image()`.
        self.build_prod_patcher = umock.patch(
            "helpers.lib_tasks_docker_release.docker_build_prod_image"
        )
        self.mock_build_prod = self.build_prod_patcher.start()
        self.patchers["build_prod"] = self.build_prod_patcher
        # Mock `docker_push_prod_candidate_image()`.
        self.push_prod_patcher = umock.patch(
            "helpers.lib_tasks_docker_release.docker_push_prod_candidate_image"
        )
        self.mock_push_prod = self.push_prod_patcher.start()
        self.patchers["push_prod"] = self.push_prod_patcher

    def tear_down_test2(self) -> None:
        """
        Clean up test environment.
        """
        self.tear_down_test()

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        """
        Set up and tear down test environment for each test.
        """
        self.set_up_test2()
        yield
        self.tear_down_test2()

    def test_aws_ecr1(self) -> None:
        """
        Test creating and pushing to AWS ECR.

        This test checks:
        - Task definition update with correct parameters
        - Proper command construction for aws_update_task_definition.py
        """
        # Call tested function.
        hltadore.docker_create_candidate_image(
            self.mock_ctx,
            user_tag="test_user",
        )
        # Verify the mocks were called with correct parameters.
        self.mock_build_prod.assert_called_once_with(
            self.mock_ctx,
            container_dir_name=".",
            version=hlitadoc._IMAGE_VERSION_FROM_CHANGELOG,
            candidate=True,
            tag="test_user-4759b3685f903e6c669096e960b248ec31c63b69",
        )
        self.mock_push_prod.assert_called_once_with(
            self.mock_ctx,
            "test_user-4759b3685f903e6c669096e960b248ec31c63b69",
        )


# #############################################################################
# Test_docker_update_prod_task_definition1
# #############################################################################


class Test_docker_update_prod_task_definition1(_DockerFlowTestHelper):
    """
    Test updating a prod task definition to the desired version.
    """

    @pytest.fixture(autouse=True)
    def aws_credentials(self) -> None:
        """
        Mocked AWS credentials for moto.
        """
        os.environ["DOCKER_MOCK_AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["DOCKER_MOCK_AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["DOCKER_MOCK_AWS_SECURITY_TOKEN"] = "testing"
        os.environ["DOCKER_MOCK_AWS_SESSION_TOKEN"] = "testing"
        os.environ["DOCKER_MOCK_AWS_DEFAULT_REGION"] = "us-east-1"

    def set_up_test2(self) -> None:
        """
        Set up test environment with additional mocks specific to this test
        class.
        """
        self.set_up_test()
        # Mock AWS and S3 functionality.
        self.aws_patcher = umock.patch(
            "helpers.haws.get_task_definition_image_url"
        )
        self.mock_aws = self.aws_patcher.start()
        self.mock_aws.return_value = (
            "test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69"
        )
        self.patchers["aws"] = self.aws_patcher
        self.s3_patcher = umock.patch("helpers.hs3.get_s3fs")
        self.mock_s3 = self.s3_patcher.start()
        self.mock_s3.return_value.cat.return_value = b"test_content"
        self.patchers["s3"] = self.s3_patcher
        # Mock file operations.
        self.file_patcher = umock.patch(
            "helpers.hs3.from_file", return_value="test_content"
        )
        self.mock_file = self.file_patcher.start()
        self.patchers["file"] = self.file_patcher
        # Mock listdir to return test DAG files.
        self.listdir_patcher = umock.patch(
            "helpers.hs3.listdir",
            return_value=["/app/im_v2/airflow/dags/test_dag.py"],
        )
        self.mock_listdir = self.listdir_patcher.start()
        self.patchers["listdir"] = self.listdir_patcher

    def tear_down_test2(self) -> None:
        """
        Clean up test environment.
        """
        # Clean up environment variables.
        for key in [
            "DOCKER_MOCK_AWS_ACCESS_KEY_ID",
            "DOCKER_MOCK_AWS_SECRET_ACCESS_KEY",
            "DOCKER_MOCK_AWS_SECURITY_TOKEN",
            "DOCKER_MOCK_AWS_SESSION_TOKEN",
            "DOCKER_MOCK_AWS_DEFAULT_REGION",
        ]:
            if key in os.environ:
                del os.environ[key]
        # Call parent teardown.
        self.tear_down_test()

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        """
        Set up and tear down test environment for each test.
        """
        self.set_up_test2()
        yield
        self.tear_down_test2()

    @moto.mock_aws
    @umock.patch("helpers.haws.update_task_definition")
    @umock.patch("helpers.haws.get_ecs_client")
    def test_promotion_to_prod(
        self,
        mock_get_ecs_client: umock.Mock,
        mock_update_task_definition: umock.Mock,
    ) -> None:
        """
        Test the promotion of a preprod Docker image and DAGs to production.

        This test checks:
        - Task definition update workflow
        - Preprod to prod image conversion.
        - DAG file synchronization
        - Image tagging and pushing
        """
        # Mock AWS ECS client using moto and register a task definition.
        region = "us-east-1"
        mock_ecs_client = boto3.client("ecs", region_name=region)
        mock_ecs_client.register_task_definition(
            family="test_task",
            containerDefinitions=[
                {
                    "name": "test-container",
                    "image": "test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69",
                }
            ],
            executionRoleArn="__mock__",
            networkMode="bridge",
            requiresCompatibilities=["EC2"],
            cpu="256",
            memory="512",
        )
        mock_get_ecs_client.return_value = mock_ecs_client
        # Add mock client to patchers for cleanup.
        self.ecs_client_patcher = umock.patch(
            "boto3.client", return_value=mock_ecs_client
        )
        self.mock_ecs_client = self.ecs_client_patcher.start()
        self.patchers["ecs_client_test1"] = self.ecs_client_patcher
        # Call tested function.
        hltadore.docker_update_prod_task_definition(
            self.mock_ctx,
            version=self.test_version,
            preprod_tag="4759b3685f903e6c669096e960b248ec31c63b69",
            airflow_dags_s3_path="s3://test-bucket/dags/",
            task_definition="test_task",
        )
        expected = r"""
        docker pull test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69
        docker tag test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69 test.ecr.path/test-image:prod-1.0.0
        docker tag test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69 test.ecr.path/test-image:prod
        docker rmi test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69
        docker push test.ecr.path/test-image:prod-1.0.0
        docker push test.ecr.path/test-image:prod
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)
        # Check whether `update_task_definition` was called with the expected arguments.
        expected_image_url = "test.ecr.path/test-image:prod-1.0.0"
        mock_update_task_definition.assert_called_once_with(
            "test_task", expected_image_url
        )

    @moto.mock_aws
    @umock.patch("helpers.haws.get_ecs_client")
    def test_promotion_to_prod_exception_handling(
        self, mock_get_ecs_client: umock.Mock
    ) -> None:
        """
        Test exception handling and rollback behavior when updating prod task
        definition.

        This test checks:
        - Exception handling during task definition update
        - Rollback of task definition to original image
        - Rollback of S3 DAG files
        - Proper error propagation
        """
        # Mock AWS ECS client using moto and register a task definition.
        region = "us-east-1"
        mock_ecs_client = boto3.client("ecs", region_name=region)
        mock_ecs_client.register_task_definition(
            family="test_task",
            containerDefinitions=[
                {
                    "name": "test-container",
                    "image": "test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69",
                }
            ],
            executionRoleArn="__mock__",
            networkMode="bridge",
            requiresCompatibilities=["EC2"],
            cpu="256",
            memory="512",
        )
        mock_get_ecs_client.return_value = mock_ecs_client
        # Add mock client to patchers for cleanup.
        self.ecs_client_patcher = umock.patch(
            "boto3.client", return_value=mock_ecs_client
        )
        self.mock_ecs_client = self.ecs_client_patcher.start()
        self.patchers["ecs_client_test2"] = self.ecs_client_patcher
        # Mock S3 bucket operations to simulate a failure.
        self.mock_s3.return_value.put.side_effect = Exception("S3 upload failed")
        # Call tested function and verify exception is raised.
        with self.assertRaises(Exception) as cm:
            hltadore.docker_update_prod_task_definition(
                self.mock_ctx,
                version=self.test_version,
                preprod_tag="4759b3685f903e6c669096e960b248ec31c63b69",
                airflow_dags_s3_path="s3://test-bucket/dags/",
                task_definition="test_task",
            )
        # Check the error message.
        self.assertIn("S3 upload failed", str(cm.exception))
        # Check whether rollback commands were executed.
        expected = r"""
        docker pull test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69
        docker tag test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69 test.ecr.path/test-image:prod-1.0.0
        docker tag test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69 test.ecr.path/test-image:prod
        docker rmi test.ecr.path/test-image:4759b3685f903e6c669096e960b248ec31c63b69
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)
        # Check whether task definition was rolled back.
        self.mock_aws.assert_called_with("test_task")
