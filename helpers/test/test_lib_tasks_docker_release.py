import logging
import re
import unittest.mock as umock
from typing import List, Tuple

import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.lib_tasks_docker_release as hltadore
import helpers.test.test_lib_tasks as httestlib

_LOG = logging.getLogger(__name__)


def _normalize_command(cmd: str) -> str:
    """
    Normalize a command string by removing line continuations and spaces around
    special characters.

    :param cmd: command string to normalize
    :return: normalized command string
    """
    cmd = re.sub(r"\\\s*\n\s*", " ", cmd)
    chars_to_normalize = ["=", ",", "|"]
    escaped_chars = "".join(re.escape(ch) for ch in chars_to_normalize)
    cmd = re.sub(rf"\s*([{escaped_chars}])\s*", r"\1", cmd)
    return cmd


def _convert_commands_to_strings(
    actual_cmds: List[str], expected_cmds: List[str]
) -> Tuple[str, str]:
    """
    Convert a list of commands to strings and normalize them.

    :param actual_cmds: list of actual command strings
    :param expected_cmds: list of expected command strings
    :return: normalized actual commands string and normalized expected
        commands string
    """
    # Normalize each command in both lists.
    actual_normalized = [_normalize_command(cmd) for cmd in actual_cmds]
    expected_normalized = [_normalize_command(cmd) for cmd in expected_cmds]
    # Convert to strings.
    actual_str = "\n".join(actual_normalized)
    expected_str = "\n".join(expected_normalized)
    return actual_str, expected_str


def _extract_commands_from_call(calls: List[umock._Call]) -> List[str]:
    """
    Extract command strings from a list of mock call arguments.

    :param calls: list of mock call objects containing (args, kwargs)
    :return: list of command strings
    """
    # Each mock call is a (args, kwargs) tuple, extract the command string
    # from args[1] in each call.
    call_list = [call[0][1] for call in calls]
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
        #
        self.user = hsystem.get_user_name()

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
        # Call tested function .
        hltadore.docker_build_local_image(
            mock_ctx,
            test_version,
            cache=False,
            base_image=test_base_image,
            poetry_mode="update",
        )
        actual_cmds = _extract_commands_from_call(self.mock_run.call_args_list)
        # Check build image commands.
        build_cmds = actual_cmds[:2]
        expected_build_cmds = [
            "cp -f devops/docker_build/dockerignore.dev .dockerignore",
            "tar -czh . | DOCKER_BUILDKIT=0 time docker build "
            " --no-cache "
            " --build-arg AM_CONTAINER_VERSION=1.0.0 "
            " --build-arg INSTALL_DIND=True "
            " --build-arg POETRY_MODE=update "
            " --build-arg CLEAN_UP_INSTALLATION=True "
            f" --tag {test_base_image}:local-{self.user}-1.0.0 "
            " --file devops/docker_build/dev.Dockerfile -",
        ]
        actual_build, expected_build = _convert_commands_to_strings(
            build_cmds, expected_build_cmds
        )
        self.assert_equal(
            actual_build,
            expected_build,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )
        # Check poetry file commands.
        poetry_cmds = actual_cmds[2:5]
        expected_poetry_cmds = [
            "invoke docker_cmd  "
            "--stage local "
            f"--version {test_version} "
            f"--cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull",
            "cp -f poetry.lock.out ./devops/docker_build/poetry.lock",
            "cp -f pip_list.txt ./devops/docker_build/pip_list.txt",
        ]
        actual_poetry, expected_poetry = _convert_commands_to_strings(
            poetry_cmds, expected_poetry_cmds
        )
        self.assert_equal(
            actual_poetry,
            expected_poetry,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )
        # Check list images command.
        actual_list_cmd = actual_cmds[5]
        expected_list_cmd = (
            f"docker image ls {test_base_image}:local-{self.user}-1.0.0"
        )
        actual_list, expected_list = _convert_commands_to_strings(
            actual_list_cmd, expected_list_cmd
        )
        self.assert_equal(
            actual_list,
            expected_list,
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
        # Check buildx setup and build commands.
        actual_build_cmds = actual_cmds[:3]
        expected_build_cmds = [
            "cp -f devops/docker_build/dockerignore.dev .dockerignore",
            "docker buildx create --name multiarch_builder --driver docker-container --bootstrap && docker buildx use multiarch_builder",
            "tar -czh . | DOCKER_BUILDKIT=0 time docker buildx build "
            " --no-cache "
            " --push --platform linux/amd64,linux/arm64 "
            " --build-arg AM_CONTAINER_VERSION=1.0.0 "
            " --build-arg INSTALL_DIND=True "
            " --build-arg POETRY_MODE=update "
            " --build-arg CLEAN_UP_INSTALLATION=True "
            f" --tag {test_base_image}:local-{self.user}-1.0.0 "
            " --file devops/docker_build/dev.Dockerfile -",
        ]
        actual_build, expected_build = _convert_commands_to_strings(
            actual_build_cmds, expected_build_cmds
        )
        self.assert_equal(
            actual_build,
            expected_build,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )
        # Check pull and poetry file commands.
        actual_poetry_cmds = actual_cmds[3:7]
        expected_poetry_cmds = [
            f"docker pull {test_base_image}:local-{self.user}-1.0.0",
            "invoke docker_cmd  "
            "--stage local "
            f"--version {test_version} "
            f"--cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull",
            "cp -f poetry.lock.out ./devops/docker_build/poetry.lock",
            "cp -f pip_list.txt ./devops/docker_build/pip_list.txt",
        ]
        actual_poetry, expected_poetry = _convert_commands_to_strings(
            actual_poetry_cmds, expected_poetry_cmds
        )
        self.assert_equal(
            actual_poetry,
            expected_poetry,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )
        # Check list images command.
        actual_list_cmd = actual_cmds[7]
        expected_list_cmd = (
            f"docker image ls {test_base_image}:local-{self.user}-1.0.0"
        )
        actual_list, expected_list = _convert_commands_to_strings(
            actual_list_cmd, expected_list_cmd
        )
        self.assert_equal(
            actual_list,
            expected_list,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )
