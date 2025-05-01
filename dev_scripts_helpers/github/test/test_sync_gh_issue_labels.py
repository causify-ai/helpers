import os
import tempfile
import unittest
from typing import List
from unittest.mock import DEFAULT, patch

import dev_scripts_helpers.github.dockerized_sync_gh_issue_labels as dshgdsgil
import dev_scripts_helpers.github.sync_gh_issue_labels as dshgsgila


# #############################################################################
# TestLabelModel
# #############################################################################


class TestLabelModel(unittest.TestCase):
    """
    Validate the `Label` data model.
    """

    def setUp(self) -> None:
        """
        Prepare a shared label inventory.
        """
        super().setUp()
        self._labels: List[dshgdsgil.Label] = [
            dshgdsgil.Label("bug", "Something is broken", "#d73a4a"),
            dshgdsgil.Label("todo", None, "#ABCDEF"),
        ]

    def test_color_prefix_stripped(self) -> None:
        """
        Ensure the leading " # " is removed from colours.
        """
        self.assertEqual(self._labels[0].color, "d73a4a")
        self.assertEqual(self._labels[1].color, "ABCDEF")

    def test_save_load_roundtrip(self) -> None:
        """
        Ensure round-trip save ↔ load returns identical label data.
        """
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp:
            path = tmp.name
        try:
            dshgdsgil.Label.save_labels(self._labels, path)
            loaded = dshgdsgil.Label.load_labels(path)
            self.assertEqual(
                [lbl.to_dict() for lbl in loaded],
                [lbl.to_dict() for lbl in self._labels],
            )
        finally:
            os.unlink(path)


# #############################################################################
# TestDockerCommand
# #############################################################################


class TestDockerCommand(unittest.TestCase):
    """
    Verify that the wrapper builds the expected Docker command.
    """

    def setUp(self) -> None:
        """
        Set up test fixtures.
        """
        super().setUp()
        # Define all mock return values in one place.
        self.mock_values = {
            "helpers.hdocker.build_container_image": lambda *args, **kwargs: "test.img:latest",
            "helpers.hdocker.get_docker_base_cmd": lambda *args, **kwargs: [
                "docker",
                "run",
            ],
            "helpers.hdocker.get_docker_executable": lambda *args, **kwargs: "docker",
            "helpers.hdocker.get_docker_mount_info": lambda *args, **kwargs: (
                "/host",
                "/container",
                "/host:/container",
            ),
            "helpers.hdocker.convert_caller_to_callee_docker_path": lambda path, *args, **kwargs: f"/container/{path}",
            "helpers.hserver.is_inside_docker": lambda *args, **kwargs: False,
            "helpers.hgit.find_helpers_root": lambda *args, **kwargs: "/abs/helpers",
            "helpers.hgit.find_git_root": lambda *args, **kwargs: "/gitroot",
            "helpers.hsystem.find_file_in_repo": lambda *args, **kwargs: "/gitroot/dockerized_sync_gh_issue_labels.py",
        }

    def test_docker_command_structure(self) -> None:
        """
        Verify the complete Docker command structure and sequence.
        """
        # Create a test input file.
        with tempfile.NamedTemporaryFile(suffix=".yml") as tmp:
            # Set up all mocks using context manager.
            with patch.multiple(
                "helpers.hsystem",
                system=DEFAULT,
                find_file_in_repo=self.mock_values[
                    "helpers.hsystem.find_file_in_repo"
                ],
            ) as system_mocks, patch.multiple(
                "helpers.hdocker",
                build_container_image=self.mock_values[
                    "helpers.hdocker.build_container_image"
                ],
                get_docker_base_cmd=self.mock_values[
                    "helpers.hdocker.get_docker_base_cmd"
                ],
                get_docker_executable=self.mock_values[
                    "helpers.hdocker.get_docker_executable"
                ],
                get_docker_mount_info=self.mock_values[
                    "helpers.hdocker.get_docker_mount_info"
                ],
                convert_caller_to_callee_docker_path=self.mock_values[
                    "helpers.hdocker.convert_caller_to_callee_docker_path"
                ],
            ), patch.multiple(
                "helpers.hserver",
                is_inside_docker=self.mock_values[
                    "helpers.hserver.is_inside_docker"
                ],
            ), patch.multiple(
                "helpers.hgit",
                find_helpers_root=self.mock_values[
                    "helpers.hgit.find_helpers_root"
                ],
                find_git_root=self.mock_values["helpers.hgit.find_git_root"],
            ):
                # Run the sync command with various flags.
                dshgsgila._run_dockerized_sync_gh_issue_labels(
                    input_file=tmp.name,
                    owner="test-org",
                    repo="test-repo",
                    token_env_var="GH_TOKEN",
                    dry_run=True,
                    no_interactive=True,
                    prune=True,
                    backup=True,
                )
                # Get the executed command.
                executed_cmd: str = system_mocks["system"].call_args[0][0]
                # Define the expected command parts in sequence.
                expected_parts = [
                    # Base Docker command.
                    "docker run",
                    # Docker environment and mount settings.
                    "-e GH_TOKEN",
                    "-e PYTHONPATH=/container//abs/helpers",
                    "--workdir /container",
                    "--mount /host:/container",
                    # Image specification.
                    "test.img:latest",
                    # Script path and arguments.
                    "/container//gitroot/dockerized_sync_gh_issue_labels.py",
                    f"--input_file /container/{tmp.name}",
                    "--owner test-org",
                    "--repo test-repo",
                    "--token_env_var GH_TOKEN",
                ]
                # Optional flags can appear in any order.
                optional_flags = [
                    "--prune",
                    "--dry_run",
                    "--backup",
                    "--no_interactive",
                ]
                # Verify command starts with expected sequence.
                cmd_parts = executed_cmd.split()
                current_idx = 0
                for expected in expected_parts:
                    # Find the next occurrence of the expected part.
                    found = False
                    expected_tokens = expected.split()
                    for i in range(
                        current_idx, len(cmd_parts) - len(expected_tokens) + 1
                    ):
                        if (
                            cmd_parts[i : i + len(expected_tokens)]
                            == expected_tokens
                        ):
                            current_idx = i + len(expected_tokens)
                            found = True
                            break
                    self.assertTrue(
                        found,
                        f"Expected command part '{expected}' not found in correct "
                        f"sequence in '{executed_cmd}'",
                    )
                # Verify all optional flags are present (order doesn't matter).
                remaining_cmd = " ".join(cmd_parts[current_idx:])
                for flag in optional_flags:
                    self.assertIn(
                        flag,
                        remaining_cmd,
                        f"Expected flag '{flag}' not found in command",
                    )
                # Verify no unexpected arguments are present.
                unexpected_args = [
                    "--force",
                    "--skip",
                    "--unknown",
                ]
                for arg in unexpected_args:
                    self.assertNotIn(
                        arg,
                        executed_cmd,
                        f"Unexpected argument '{arg}' found in command",
                    )
