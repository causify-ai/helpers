import logging
import unittest.mock as umock
from typing import Generator, List

import pytest

import helpers.hunit_test as hunitest
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
        self.patchers = [
            self.system_patcher,
            self.run_patcher,
            self.version_patcher,
            self.docker_login_patcher,
            self.env_patcher,
            self.get_docker_base_image_name_patcher,
            self.get_default_param_patcher,
        ]
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
        for patcher in self.patchers:
            patcher.stop()

    def _check_docker_command_output(
        self, exp: str, call_args_list: List[umock._Call]
    ) -> None:
        """
        Verify that the sequence of Docker commands from mock calls matches the
        expected string.

        :param exp: expected command string
        :param call_args_list: list of mock call objects
        """
        actual_cmds = _extract_commands_from_call(call_args_list)
        actual_cmds = "\n".join(actual_cmds)
        self.assert_equal(
            actual_cmds,
            exp,
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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)

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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)

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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)

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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)

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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
        docker buildx imagetools create -t test.ecr.path/test-image:prod test.ecr.path/test-image:prod-1.0.0
        """
        self._check_docker_command_output(exp, self.mock_run.call_args_list)

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
        exp = r"""
        docker buildx imagetools create -t causify/test-image:prod-1.0.0 test.ecr.path/test-image:prod-1.0.0
        docker buildx imagetools create -t causify/test-image:prod test.ecr.path/test-image:prod-1.0.0
        """
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
        docker buildx imagetools create -t test.ecr.path/test-image:dev-1.0.0 test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t test.ecr.path/test-image:dev test.ecr.path/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(exp, self.mock_run.call_args_list)

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
        exp = r"""
        docker buildx imagetools create -t causify/test-image:dev-1.0.0 test.ecr.path/test-image:local-$USER_NAME-1.0.0
        docker buildx imagetools create -t causify/test-image:dev test.ecr.path/test-image:local-$USER_NAME-1.0.0
        """
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)

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
        exp = r"""
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
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
        docker pull test.ecr.path/test-image:dev-1.0.0
        docker tag test.ecr.path/test-image:dev-1.0.0 test.ecr.path/test-image:dev
        docker push test.ecr.path/test-image:dev-1.0.0
        docker push test.ecr.path/test-image:dev
        """
        self._check_docker_command_output(exp, self.mock_run.call_args_list)


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
        exp = r"""
        docker pull test.ecr.path/test-image:prod-1.0.0
        docker tag test.ecr.path/test-image:prod-1.0.0 test.ecr.path/test-image:prod
        docker push test.ecr.path/test-image:prod-1.0.0
        docker push test.ecr.path/test-image:prod
        """
        self._check_docker_command_output(exp, self.mock_run.call_args_list)
