import logging
import os
import unittest.mock as umock

import dev_scripts_helpers.github.sync_gh_issue_labels as dshgsgila
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_sync_gh_issue_labels1
# #############################################################################


class Test_sync_gh_issue_labels1(hunitest.TestCase):

    def setUp(self) -> None:
        """
        Set up test fixtures.
        """
        super().setUp()
        # Mock system calls.
        self.system_patcher = umock.patch("helpers.hsystem.system")
        self.mock_system = self.system_patcher.start()
        # Mock docker commands.
        self.build_container_patcher = umock.patch(
            "helpers.hdocker.build_container_image"
        )
        self.mock_build_container = self.build_container_patcher.start()
        self.mock_build_container.return_value = "test.img:latest"
        self.docker_base_cmd_patcher = umock.patch(
            "helpers.hdocker.get_docker_base_cmd"
        )
        self.mock_docker_base_cmd = self.docker_base_cmd_patcher.start()
        self.mock_docker_base_cmd.return_value = ["docker", "run"]
        self.docker_exec_patcher = umock.patch(
            "helpers.hdocker.get_docker_executable"
        )
        self.mock_docker_exec = self.docker_exec_patcher.start()
        self.mock_docker_exec.return_value = "docker"
        self.docker_mount_patcher = umock.patch(
            "helpers.hdocker.get_docker_mount_info"
        )
        self.mock_docker_mount = self.docker_mount_patcher.start()
        self.mock_docker_mount.return_value = (
            "/host",
            "/container",
            "/host:/container",
        )
        self.docker_path_patcher = umock.patch(
            "helpers.hdocker.convert_caller_to_callee_docker_path"
        )
        self.mock_docker_path = self.docker_path_patcher.start()
        self.mock_docker_path.side_effect = (
            lambda path, *args, **kwargs: f"/container{path}"
        )
        self.docker_server_patcher = umock.patch(
            "helpers.hserver.is_inside_docker"
        )
        self.mock_docker_server = self.docker_server_patcher.start()
        self.mock_docker_server.return_value = False

    def tearDown(self) -> None:
        """
        Clean up mock patchers.
        """
        self.system_patcher.stop()
        self.build_container_patcher.stop()
        self.docker_base_cmd_patcher.stop()
        self.docker_exec_patcher.stop()
        self.docker_mount_patcher.stop()
        self.docker_path_patcher.stop()
        self.docker_server_patcher.stop()
        super().tearDown()

    def test_docker_command_structure(self) -> None:
        """
        Test building and running a dockerized executable.

        This test verifies that the correct sequence of commands is
        generated for running the dockerized executable.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test_gh_issues_labels.yml")
        # Call tested function.
        dshgsgila._run_dockerized_sync_gh_issue_labels(
            input_file_path,
            "test-org",
            "test-repo",
            "GH_TOKEN",
            dry_run=True,
            no_interactive=True,
            prune=True,
            backup=True,
        )
        actual_cmd = self.mock_system.call_args[0][0]
        _LOG.info("actual_cmd=%s", actual_cmd)
        expected_cmd = (
            r"docker run -e GH_TOKEN -e PYTHONPATH=/container/app --workdir /container "
            r"--mount /host:/container test.img:latest /container/app/dev_scripts_helpers/github/dockerized_sync_gh_issue_labels.py "
            r"--input_file /container/app/dev_scripts_helpers/github/test/outcomes/Test_sync_gh_issue_labels1.test_docker_command_structure/input/test_gh_issues_labels.yml "
            r"--owner test-org --repo test-repo --token_env_var GH_TOKEN --prune --dry_run --backup --no_interactive"
        )
        # Check output.
        self.assert_equal(
            actual_cmd,
            expected_cmd,
            purify_text=True,
            purify_expected_text=True,
            fuzzy_match=True,
            remove_lead_trail_empty_lines=True,
            dedent=True,
        )
