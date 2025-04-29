import logging
import re
import unittest.mock as umock

import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.lib_tasks_docker_release as hltadore

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestDockerBuildLocalImage1
# #############################################################################


class TestDockerBuildLocalImage1(hunitest.TestCase):

    def setUp(self) -> None:
        """
        Set up test environment and initialize all necessary mocks.
        """
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
        self.user = hsystem.get_user_name()

    def tearDown(self) -> None:
        """
        Clean up test environment by stopping all mocks after each test case.
        """
        self.system_patcher.stop()
        self.run_patcher.stop()
        self.version_patcher.stop()
        self.docker_login_patcher.stop()

    def test_docker_build_single_arch(self) -> None:
        """
        Test building a local Docker image with single architecture.

        This test verifies that the correct sequence of commands is
        generated for building a local Docker image with single
        architecture.
        """
        # Prepare inputs.
        mock_ctx = umock.MagicMock()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        test_multi_arch = ""
        # Call tested function.
        hltadore.docker_build_local_image.body(
            ctx=mock_ctx,
            version=test_version,
            base_image=test_base_image,
            multi_arch=test_multi_arch,
            poetry_mode="update",
            cache=False,
        )
        # Extract the command arguments from the call.
        actual_cmds = [call[0][1] for call in self.mock_run.call_args_list]
        # Check output.
        expected_cmds = [
            "cp -f devops/docker_build/dockerignore.dev .dockerignore",
            "tar -czh . | DOCKER_BUILDKIT=0 time docker build "
            " --no-cache "
            " --build-arg AM_CONTAINER_VERSION=1.0.0 "
            " --build-arg INSTALL_DIND=True "
            " --build-arg POETRY_MODE=update "
            " --build-arg CLEAN_UP_INSTALLATION=True "
            f" --tag {test_base_image}:local-{self.user}-1.0.0 "
            " --file devops/docker_build/dev.Dockerfile -",
            "invoke docker_cmd  "
            "--stage local "
            f"--version {test_version} "
            f"--cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull",
            "cp -f poetry.lock.out ./devops/docker_build/poetry.lock",
            "cp -f pip_list.txt ./devops/docker_build/pip_list.txt",
            f"docker image ls {test_base_image}:local-{self.user}-1.0.0",
        ]
        # Normalize both expected and actual commands.
        expected = [self._normalize_command(cmd) for cmd in expected_cmds]
        actual = [self._normalize_command(cmd) for cmd in actual_cmds]
        self.assertEqual(
            expected,
            actual,
            f"Expected commands: {expected}\nActual commands: {actual}",
        )

    def test_docker_build_multi_arch(self) -> None:
        """
        Test building a local Docker image with multiple architectures.

        This test verifies that the correct sequence of commands is
        generated for building a local Docker image with multiple
        architectures.
        """
        # Prepare inputs.
        mock_ctx = umock.MagicMock()
        test_version = "1.0.0"
        test_base_image = "test-registry.com/test-image"
        test_multi_arch = "linux/amd64,linux/arm64"
        # Call tested function.
        hltadore.docker_build_local_image.body(
            ctx=mock_ctx,
            version=test_version,
            base_image=test_base_image,
            multi_arch=test_multi_arch,
            poetry_mode="update",
            cache=False,
        )
        # Extract the command arguments from the call.
        actual_cmds = [call[0][1] for call in self.mock_run.call_args_list]
        # Check output.
        expected_cmds = [
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
            f"docker pull {test_base_image}:local-{self.user}-1.0.0",
            "invoke docker_cmd  "
            "--stage local "
            f"--version {test_version} "
            f"--cmd 'cp -f /install/poetry.lock.out /install/pip_list.txt .' --skip-pull",
            "cp -f poetry.lock.out ./devops/docker_build/poetry.lock",
            "cp -f pip_list.txt ./devops/docker_build/pip_list.txt",
            f"docker image ls {test_base_image}:local-{self.user}-1.0.0",
        ]
        # Normalize both expected and actual commands.
        expected = [self._normalize_command(cmd) for cmd in expected_cmds]
        actual = [self._normalize_command(cmd) for cmd in actual_cmds]
        self.assertEqual(
            expected,
            actual,
            f"Expected commands: {expected}\nActual commands: {actual}",
        )

    def _normalize_command(self, cmd: str) -> str:
        """
        Normalize a command string by removing whitespace and line
        continuations.

        :param cmd: command string to normalize
        :return: normalized command string
        """
        # Replace line continuation backslashes with spaces.
        cmd = re.sub(r"\\\s*\n\s*", " ", cmd)
        # Remove all extra whitespaces.
        cmd = re.sub(r"\s+", " ", cmd)
        # Remove spaces around special characters.
        chars_to_normalize = ["=", ",", "|"]
        escaped_chars = "".join(re.escape(ch) for ch in chars_to_normalize)
        cmd = re.sub(rf"\s*([{escaped_chars}])\s*", r"\1", cmd)
        # Remove leading/trailing whitespace.
        cmd = cmd.strip()
        return cmd
