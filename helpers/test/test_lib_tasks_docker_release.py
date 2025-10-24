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
        _LOG.debug("Actual Docker commands:\n%s", actual_cmds)
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
        cp -f devops/docker_build/dockerignore.dev $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.dev $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.prod $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.prod $GIT_ROOT/.dockerignore
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
        reason="Needs to run inside a super module",
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
        cp -f devops/docker_build/dockerignore.prod $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.prod $GIT_ROOT/.dockerignore
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


class Test_docker_tag_push_multi_build_local_image_as_dev1(_DockerFlowTestHelper):
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
        cp -f devops/docker_build/dockerignore.dev $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.prod $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.dev $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.dev $GIT_ROOT/.dockerignore
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
        cp -f devops/docker_build/dockerignore.prod $GIT_ROOT/.dockerignore
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
        self.file_exists_patcher = umock.patch("helpers.hdbg.dassert_file_exists")
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
            "test_task", expected_image_url, environment="prod"
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


# #############################################################################
# Test_docker_tag_push_dev_image_from_ghcr1
# #############################################################################


class Test_docker_tag_push_dev_image_from_ghcr1(_DockerFlowTestHelper):
    """
    Test tagging and pushing dev image from GHCR to multiple registries.
    """

    def set_up_test2(self) -> None:
        """
        Set up test environment with additional mocks for GHCR workflow.
        """
        super().set_up_test()
        # Mock version retrieval from changelog.
        self.changelog_version_patcher = umock.patch(
            "helpers.hversion.get_changelog_version"
        )
        self.mock_changelog_version = self.changelog_version_patcher.start()
        self.mock_changelog_version.return_value = self.test_version
        # Mock repo config for GHCR registry URL and image name.
        self.get_container_registry_url_patcher = umock.patch(
            "helpers.repo_config_utils.RepoConfig.get_container_registry_url"
        )
        self.mock_get_container_registry_url = (
            self.get_container_registry_url_patcher.start()
        )
        self.mock_get_container_registry_url.return_value = "ghcr.io/causify-ai"
        # Add new patchers to cleanup list.
        self.patchers.update(
            {
                "changelog_version": self.changelog_version_patcher,
                "container_registry_url": self.get_container_registry_url_patcher,
            }
        )

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

    def test_normal_execution1(self) -> None:
        """
        Test normal execution without dry_run.

        This test checks:
        - GHCR image pulling
        - Tagging for GHCR and AWS ECR
        - Pushing to both registries
        - Versioned and latest image handling
        """
        # Call tested function.
        hltadore.docker_tag_push_dev_image_from_ghcr(
            self.mock_ctx,
            container_dir_name=".",
            dry_run=False,
        )
        # Verify expected Docker commands were executed.
        expected = r"""
        docker pull ghcr.io/causify-ai/test-image:dev-1.0.0
        docker tag ghcr.io/causify-ai/test-image:dev-1.0.0 ghcr.io/causify-ai/test-image:dev
        docker push ghcr.io/causify-ai/test-image:dev
        docker tag ghcr.io/causify-ai/test-image:dev-1.0.0 test.ecr.path/test-image:dev-1.0.0
        docker push test.ecr.path/test-image:dev-1.0.0
        docker tag ghcr.io/causify-ai/test-image:dev-1.0.0 test.ecr.path/test-image:dev
        docker push test.ecr.path/test-image:dev
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_dry_run1(self) -> None:
        """
        Test dry_run mode execution.

        This test checks:
        - No actual Docker commands are executed when dry_run=True
        - All operations are simulated
        - Function completes without errors
        - Mock calls should include dry_run parameter
        """
        # Call tested function with dry_run enabled.
        hltadore.docker_tag_push_dev_image_from_ghcr(
            self.mock_ctx,
            container_dir_name=".",
            dry_run=True,
        )
        # Verify expected Docker commands were executed.
        expected = r"""
        docker pull ghcr.io/causify-ai/test-image:dev-1.0.0
        docker tag ghcr.io/causify-ai/test-image:dev-1.0.0 ghcr.io/causify-ai/test-image:dev
        docker push ghcr.io/causify-ai/test-image:dev
        docker tag ghcr.io/causify-ai/test-image:dev-1.0.0 test.ecr.path/test-image:dev-1.0.0
        docker push test.ecr.path/test-image:dev-1.0.0
        docker tag ghcr.io/causify-ai/test-image:dev-1.0.0 test.ecr.path/test-image:dev
        docker push test.ecr.path/test-image:dev
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)


# #############################################################################
# Test_docker_build_test_dev_image1
# #############################################################################


class Test_docker_build_test_dev_image1(_DockerFlowTestHelper):
    """
    Test the complete periodic dev image release workflow.
    """

    def set_up_test(self) -> None:
        """
        Set up test environment with additional mocks for the dev image
        workflow.
        """
        super().set_up_test()
        # Mock version operations.
        self.get_changelog_version_patcher = umock.patch(
            "helpers.hversion.get_changelog_version"
        )
        self.mock_get_changelog_version = (
            self.get_changelog_version_patcher.start()
        )
        self.mock_get_changelog_version.return_value = "2.3.0"
        self.bump_version_patcher = umock.patch("helpers.hversion.bump_version")
        self.mock_bump_version = self.bump_version_patcher.start()
        self.mock_bump_version.return_value = "2.4.0"
        # Mock repo config methods.
        self.get_release_team_patcher = umock.patch(
            "helpers.repo_config_utils.RepoConfig.get_release_team"
        )
        self.mock_get_release_team = self.get_release_team_patcher.start()
        self.mock_get_release_team.return_value = "dev_system"
        self.get_container_registry_url_patcher = umock.patch(
            "helpers.repo_config_utils.RepoConfig.get_container_registry_url"
        )
        self.mock_get_container_registry_url = (
            self.get_container_registry_url_patcher.start()
        )
        self.mock_get_container_registry_url.return_value = "ghcr.io/causify-ai"
        # Mock GitHub operations.
        self.gh_get_team_member_names_patcher = umock.patch(
            "helpers.lib_tasks_gh.gh_get_team_member_names"
        )
        self.mock_gh_get_team_member_names = (
            self.gh_get_team_member_names_patcher.start()
        )
        self.mock_gh_get_team_member_names.return_value = ["user1", "user2"]
        self.gh_issue_create_patcher = umock.patch(
            "helpers.lib_tasks_gh.gh_issue_create"
        )
        self.mock_gh_issue_create = self.gh_issue_create_patcher.start()
        self.mock_gh_issue_create.return_value = 12345
        self.gh_create_pr_patcher = umock.patch(
            "helpers.lib_tasks_gh.gh_create_pr"
        )
        self.mock_gh_create_pr = self.gh_create_pr_patcher.start()
        # Mock git operations.
        self.git_branch_create_patcher = umock.patch(
            "helpers.lib_tasks_git.git_branch_create"
        )
        self.mock_git_branch_create = self.git_branch_create_patcher.start()
        self.get_branch_name_patcher = umock.patch("helpers.hgit.get_branch_name")
        self.mock_get_branch_name = self.get_branch_name_patcher.start()
        self.mock_get_branch_name.return_value = "CsfyTask12345_test_branch"
        # Mock file operations.
        self.get_client_root_patcher = umock.patch(
            "helpers.hversion._get_client_root"
        )
        self.mock_get_client_root = self.get_client_root_patcher.start()
        self.mock_get_client_root.return_value = "/test/root"
        self.from_file_patcher = umock.patch("helpers.hio.from_file")
        self.mock_from_file = self.from_file_patcher.start()
        self.mock_from_file.return_value = "# Existing changelog content\n"
        self.to_file_patcher = umock.patch("helpers.hio.to_file")
        self.mock_to_file = self.to_file_patcher.start()
        # Mock file existence check for dassert_file_exists (changelog validation).
        self.file_exists_patcher = umock.patch("helpers.hdbg.dassert_file_exists")
        self.mock_file_exists = self.file_exists_patcher.start()
        # Mock os.path.exists selectively for file staging logic.
        import os

        # Store the original function before patching
        original_exists = os.path.exists
        # Define which files should exist for staging
        staged_files = {
            "/test/root/./devops/docker_build/poetry.lock",
            "/test/root/./devops/docker_build/pip_list.txt",
            "/test/root/./changelog.txt",
        }

        def selective_exists(path):
            # Return True for staged files, use original function for everything else
            if path in staged_files:
                return True
            return original_exists(path)

        self.path_exists_patcher = umock.patch(
            "os.path.exists", side_effect=selective_exists
        )
        self.mock_path_exists = self.path_exists_patcher.start()
        # Mock date operations.
        self.date_patcher = umock.patch("datetime.date")
        self.mock_date = self.date_patcher.start()
        self.mock_date.today.return_value.strftime.return_value = "2025-10-23"
        # Mock Docker image operations.
        self.get_image_patcher = umock.patch("helpers.lib_tasks_docker.get_image")
        self.mock_get_image = self.get_image_patcher.start()
        self.mock_get_image.return_value = (
            "test.ecr.path/test-image:local-testuser-2.4.0"
        )
        # Mock _run_tests to prevent actual test execution.
        self.run_tests_patcher = umock.patch(
            "helpers.lib_tasks_docker_release._run_tests"
        )
        self.mock_run_tests = self.run_tests_patcher.start()
        # Add all new patchers to cleanup list.
        self.patchers.update(
            {
                "get_changelog_version": self.get_changelog_version_patcher,
                "bump_version": self.bump_version_patcher,
                "get_release_team": self.get_release_team_patcher,
                "container_registry_url": self.get_container_registry_url_patcher,
                "gh_get_team_member_names": self.gh_get_team_member_names_patcher,
                "gh_issue_create": self.gh_issue_create_patcher,
                "gh_create_pr": self.gh_create_pr_patcher,
                "git_branch_create": self.git_branch_create_patcher,
                "get_branch_name": self.get_branch_name_patcher,
                "get_client_root": self.get_client_root_patcher,
                "from_file": self.from_file_patcher,
                "to_file": self.to_file_patcher,
                "file_exists": self.file_exists_patcher,
                "path_exists": self.path_exists_patcher,
                "date": self.date_patcher,
                "get_image": self.get_image_patcher,
                "run_tests": self.run_tests_patcher,
            }
        )

    def tear_down_test(self) -> None:
        """
        Clean up test environment by stopping all mocks after each test case,
        including the additional patchers created in this class.
        """
        super().tear_down_test()

    def test_complete_workflow1(self) -> None:
        """
        Test the complete periodic dev image release workflow.

        This test checks the entire automation process:
        - Version bumping from changelog
        - GitHub team member lookup
        - Issue and branch creation
        - Docker image building and testing
        - Changelog entry creation
        - Git operations (staging, committing, pushing)
        - PR creation with proper reviewers
        - GHCR image tagging and pushing
        """
        # Call the tested function.
        issue_id = hltadore.docker_build_test_dev_image(
            self.mock_ctx,
            assignee="",  # Empty to trigger team lookup
            container_dir_name=".",
        )
        # Verify the returned issue ID.
        self.assertEqual(issue_id, 12345)
        # Verify version operations were called.
        self.mock_bump_version.assert_called_once_with("2.3.0", bump_type="minor")
        # Verify GitHub team lookup was performed.
        self.mock_get_release_team.assert_called_once()
        self.mock_gh_get_team_member_names.assert_called_once_with("dev_system")
        # Verify GitHub issue was created with proper assignees.
        self.mock_gh_issue_create.assert_called_once()
        call_args = self.mock_gh_issue_create.call_args
        self.assertIn("assignees", call_args.kwargs)
        self.assertEqual(call_args.kwargs["assignees"], "user1,user2")
        # Verify branch was created from issue.
        self.mock_git_branch_create.assert_called_once_with(
            self.mock_ctx, issue_id=12345
        )
        # Verify PR was created with team members as reviewers.
        self.mock_gh_create_pr.assert_called_once()
        pr_call_args = self.mock_gh_create_pr.call_args
        self.assertIn("reviewer", pr_call_args.kwargs)
        self.assertEqual(pr_call_args.kwargs["reviewer"], "user1,user2")
        # Verify expected Docker and Git commands were executed.
        expected = r"""
        cp -f devops/docker_build/dockerignore.dev /app/.dockerignore
        tar -czh . | DOCKER_BUILDKIT=0 \
        time \
        docker build \
             \
            --build-arg AM_CONTAINER_VERSION=2.4.0 --build-arg INSTALL_DIND=True --build-arg POETRY_MODE=update --build-arg CLEAN_UP_INSTALLATION=True \
            --tag test.ecr.path/test-image:local-testuser-2.4.0 \
            --file devops/docker_build/dev.Dockerfile \
            -
        invoke docker_cmd --stage local --version 2.4.0 --cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull
        cp -f poetry.lock.out ./devops/docker_build/poetry.lock
        cp -f pip_list.txt ./devops/docker_build/pip_list.txt
        docker image ls test.ecr.path/test-image:local-testuser-2.4.0
        git add /test/root/./devops/docker_build/poetry.lock
        git add /test/root/./devops/docker_build/pip_list.txt
        git add /test/root/./changelog.txt
        git commit -m "Poetry output from the v2.4.0 build" --no-verify
        git push origin CsfyTask12345_test_branch
        docker tag test.ecr.path/test-image:local-testuser-2.4.0 ghcr.io/causify-ai/test-image:dev-2.4.0
        docker push ghcr.io/causify-ai/test-image:dev-2.4.0
        """
        self._check_docker_command_output(expected, self.mock_run.call_args_list)

    def test_with_existing_assignee1(self) -> None:
        """
        Test the workflow when assignee is already provided.

        This test checks:
        - GitHub team lookup is skipped when assignee is provided
        - Provided assignee is used for issue and PR creation
        - Rest of workflow proceeds normally
        """
        # Call the tested function with a specific assignee.
        issue_id = hltadore.docker_build_test_dev_image(
            self.mock_ctx,
            assignee="specific_user",
            container_dir_name=".",
        )
        # Verify the returned issue ID.
        self.assertEqual(issue_id, 12345)
        # Verify GitHub issue was created with the provided assignee.
        self.mock_gh_issue_create.assert_called_once()
        call_args = self.mock_gh_issue_create.call_args
        self.assertIn("assignees", call_args.kwargs)
        self.assertEqual(call_args.kwargs["assignees"], "specific_user")
        # Verify PR was created with the provided assignee as reviewer.
        self.mock_gh_create_pr.assert_called_once()
        pr_call_args = self.mock_gh_create_pr.call_args
        self.assertIn("reviewer", pr_call_args.kwargs)
        self.assertEqual(pr_call_args.kwargs["reviewer"], "specific_user")
