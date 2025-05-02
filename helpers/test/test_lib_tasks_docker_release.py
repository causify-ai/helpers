import logging
import unittest.mock as umock
from typing import List

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
# TestDockerBuildLocalImage1
# #############################################################################


class TestDockerBuildLocalImage1(hunitest.TestCase):

    def setUp(self) -> None:
        """
        Set up test environment and initialize all necessary mocks.
        """
        super().setUp()
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

    def tearDown(self) -> None:
        """
        Clean up test environment by stopping all mocks after each test case.
        """
        self.system_patcher.stop()
        self.run_patcher.stop()
        self.version_patcher.stop()
        self.docker_login_patcher.stop()
        super().tearDown()

    def test_docker_build_single_arch(self) -> None:
        """
        Test building a local Docker image with single architecture.

        This test verifies that the correct sequence of commands is
        generated for building a local Docker image with single
        architecture.
        """
        # Prepare inputs.
        mock_ctx = httestlib._build_mock_context_returning_ok()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        # Call tested function.
        hltadore.docker_build_local_image(
            mock_ctx,
            test_version,
            cache=False,
            base_image=test_base_image,
            poetry_mode="update",
        )
        actual_cmds = _extract_commands_from_call(self.mock_run.call_args_list)
        actual_cmds = "\n".join(actual_cmds)
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
        # Check output.
        self.assert_equal(
            actual_cmds,
            exp,
            purify_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )

    def test_docker_build_multi_arch(self) -> None:
        """
        Test building a local Docker image with multiple architectures.

        This test verifies that the correct sequence of commands is
        generated for building a local Docker image with multiple
        architectures.
        """
        # Prepare inputs.
        mock_ctx = httestlib._build_mock_context_returning_ok()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        test_multi_arch = "linux/amd64,linux/arm64"
        # Call tested function.
        hltadore.docker_build_local_image(
            mock_ctx,
            test_version,
            cache=False,
            base_image=test_base_image,
            poetry_mode="update",
            multi_arch=test_multi_arch,
        )
        actual_cmds = _extract_commands_from_call(self.mock_run.call_args_list)
        actual_cmds = "\n".join(actual_cmds)
        # The output is a list of strings, each representing a command.
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
        # Check output.
        self.assert_equal(
            actual_cmds,
            exp,
            purify_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )


# #############################################################################
# TestDockerBuildProdImage1
# #############################################################################


class TestDockerBuildProdImage1(hunitest.TestCase):

    def setUp(self) -> None:
        """
        Set up test environment and initialize all necessary mocks.
        """
        super().setUp()
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
            "os.environ", {"CSFY_ECR_BASE_PATH": "dummy.ecr.path"}
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        """
        Clean up test environment by stopping all mocks after each test case.
        """
        self.system_patcher.stop()
        self.run_patcher.stop()
        self.version_patcher.stop()
        self.docker_login_patcher.stop()
        self.env_patcher.stop()
        super().tearDown()

    def test_docker_build_prod_image(self) -> None:
        """
        Test building a prod Docker image with single architecture.

        This test verifies that the correct sequence of commands is
        generated for building a prod Docker image.
        """
        # Prepare inputs.
        mock_ctx = httestlib._build_mock_context_returning_ok()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        # Call tested function.
        hltadore.docker_build_prod_image(
            mock_ctx,
            test_version,
            base_image=test_base_image,
            cache=False,
        )
        actual_cmds = _extract_commands_from_call(self.mock_run.call_args_list)
        actual_cmds = "\n".join(actual_cmds)
        # The output is a list of strings, each representing a command.
        exp = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --tag test-registry.com/test-image:prod-1.0.0 \
            --file /app/devops/docker_build/prod.Dockerfile \
            --build-arg VERSION=1.0.0 \
            --build-arg ECR_BASE_PATH=dummy.ecr.path \
            .
        docker tag test-registry.com/test-image:prod-1.0.0 test-registry.com/test-image:prod
        docker image ls test-registry.com/test-image:prod
        """
        # Check output.
        self.assert_equal(
            actual_cmds,
            exp,
            purify_text=True,
            purify_expected_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )

    def test_docker_build_multi_arch_prod_image(self) -> None:
        """
        Test building a prod Docker image with multiple architectures.

        This test verifies that the correct sequence of commands is
        generated for building a multi-arch prod Docker image.
        """
        # Prepare inputs.
        mock_ctx = httestlib._build_mock_context_returning_ok()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        test_multi_arch = "linux/amd64,linux/arm64"
        # Call tested function.
        hltadore.docker_build_multi_arch_prod_image(
            mock_ctx,
            test_version,
            base_image=test_base_image,
            cache=False,
            multi_arch=test_multi_arch,
        )
        actual_cmds = _extract_commands_from_call(self.mock_run.call_args_list)
        actual_cmds = "\n".join(actual_cmds)
        # The output is a list of strings, each representing a command.
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
            --build-arg VERSION=1.0.0 --build-arg ECR_BASE_PATH=dummy.ecr.path \
            --tag test-registry.com/test-image:prod-1.0.0 \
            --file devops/docker_build/prod.Dockerfile \
            -
        docker pull test-registry.com/test-image:prod-1.0.0
        docker image ls test-registry.com/test-image:prod-1.0.0
        """
        # Check output.
        self.assert_equal(
            actual_cmds,
            exp,
            purify_text=True,
            purify_expected_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )

    def test_docker_build_prod_image_with_candidate_tag(self) -> None:
        """
        Test building a prod Docker image with candidate mode using tag.

        This test verifies that the correct sequence of commands is
        generated for building a prod image with candidate mode using
        tag.
        """
        # Prepare inputs.
        mock_ctx = httestlib._build_mock_context_returning_ok()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        test_tag = "test_tag"
        # Call tested function.
        hltadore.docker_build_prod_image(
            mock_ctx,
            test_version,
            base_image=test_base_image,
            cache=False,
            candidate=True,
            tag=test_tag,
        )
        actual_cmds = _extract_commands_from_call(self.mock_run.call_args_list)
        actual_cmds = "\n".join(actual_cmds)
        # The output is a list of strings, each representing a command.
        exp = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --tag test-registry.com/test-image:prod-test_tag \
            --file /app/devops/docker_build/prod.Dockerfile \
            --build-arg VERSION=1.0.0 \
            --build-arg ECR_BASE_PATH=dummy.ecr.path \
            .
        docker image ls test-registry.com/test-image:prod-test_tag
        """
        # Check output.
        self.assert_equal(
            actual_cmds,
            exp,
            purify_text=True,
            purify_expected_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )

    def test_docker_build_prod_image_with_candidate_user_tag(self) -> None:
        """
        Test building a prod Docker image with candidate mode using user tag.

        This test verifies that the correct sequence of commands is
        generated for building a prod image with candidate mode using
        user tag and tag.
        """
        # Prepare inputs.
        mock_ctx = httestlib._build_mock_context_returning_ok()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        test_user_tag = "testuser"
        test_tag = "test_tag"
        # Call tested function.
        hltadore.docker_build_prod_image(
            mock_ctx,
            test_version,
            base_image=test_base_image,
            cache=False,
            candidate=True,
            user_tag=test_user_tag,
            tag=test_tag,
        )
        actual_cmds = _extract_commands_from_call(self.mock_run.call_args_list)
        actual_cmds = "\n".join(actual_cmds)
        # The output is a list of strings, each representing a command.
        exp = r"""
        cp -f devops/docker_build/dockerignore.prod .dockerignore
        DOCKER_BUILDKIT=0 \
        time \
        docker build \
            --no-cache \
            --tag test-registry.com/test-image:prod-testuser-test_tag \
            --file /app/devops/docker_build/prod.Dockerfile \
            --build-arg VERSION=1.0.0 \
            --build-arg ECR_BASE_PATH=dummy.ecr.path \
            .
        docker image ls test-registry.com/test-image:prod-testuser-test_tag
        """
        # Check output.
        self.assert_equal(
            actual_cmds,
            exp,
            purify_text=True,
            purify_expected_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )
