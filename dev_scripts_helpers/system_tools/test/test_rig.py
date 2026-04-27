import unittest.mock as mock

import helpers.hrig as hrig
import helpers.hunit_test as hunitest


class TestRigScript(hunitest.TestCase):
    """
    Test rig script functionality through hrig module integration.
    """

    def test_rig_search_pattern(self) -> None:
        """
        Test rig script searches for a pattern in current directory.
        """
        args = ["TODO"]
        expected_cmd = ["rg", "TODO", ".", "-n", "--no-heading", "--color=never"]
        with mock.patch("subprocess.run") as mock_run:
            exit_code = hrig.main(args)
            self.assertEqual(exit_code, 0)
            mock_run.assert_called_once_with(expected_cmd)

    def test_rig_search_pattern_with_directory(self) -> None:
        """
        Test rig script searches for a pattern in specified directory.
        """
        args = ["import", "src"]
        expected_cmd = [
            "rg",
            "import",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        with mock.patch("subprocess.run") as mock_run:
            exit_code = hrig.main(args)
            self.assertEqual(exit_code, 0)
            mock_run.assert_called_once_with(expected_cmd)

    def test_rig_search_pattern_with_extension(self) -> None:
        """
        Test rig script filters by file extension.
        """
        args = ["class", ".", "py"]
        expected_cmd = [
            "rg",
            "-g",
            "*.py",
            "class",
            ".",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        with mock.patch("subprocess.run") as mock_run:
            exit_code = hrig.main(args)
            self.assertEqual(exit_code, 0)
            mock_run.assert_called_once_with(expected_cmd)

    def test_rig_todo_default_user(self) -> None:
        """
        Test rig script with --todo flag searches for TODO(ai_gp).
        """
        args = ["--todo"]
        expected_cmd = ["rg", "TODO\\(ai_gp\\)", ".", "-n", "--no-heading", "--color=never"]
        with mock.patch("subprocess.run") as mock_run:
            exit_code = hrig.main(args)
            self.assertEqual(exit_code, 0)
            mock_run.assert_called_once_with(expected_cmd)

    def test_rig_todo_custom_user(self) -> None:
        """
        Test rig script with --todo and custom user.
        """
        args = ["--todo", "gp"]
        expected_cmd = ["rg", "TODO\\(gp\\)", ".", "-n", "--no-heading", "--color=never"]
        with mock.patch("subprocess.run") as mock_run:
            exit_code = hrig.main(args)
            self.assertEqual(exit_code, 0)
            mock_run.assert_called_once_with(expected_cmd)

    def test_rig_todo_with_directory(self) -> None:
        """
        Test rig script with --todo and directory.
        """
        args = ["--todo", "ai_gp", "src"]
        expected_cmd = [
            "rg",
            "TODO\\(ai_gp\\)",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        with mock.patch("subprocess.run") as mock_run:
            exit_code = hrig.main(args)
            self.assertEqual(exit_code, 0)
            mock_run.assert_called_once_with(expected_cmd)

    def test_rig_todo_with_extension(self) -> None:
        """
        Test rig script with --todo and file extension filter.
        """
        args = ["--todo", "gp", "src", "py"]
        expected_cmd = [
            "rg",
            "-g",
            "*.py",
            "TODO\\(gp\\)",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        with mock.patch("subprocess.run") as mock_run:
            exit_code = hrig.main(args)
            self.assertEqual(exit_code, 0)
            mock_run.assert_called_once_with(expected_cmd)

    def test_rig_help_flag(self) -> None:
        """
        Test rig script with --help flag.
        """
        args = ["--help"]
        with mock.patch("subprocess.run"):
            exit_code = hrig.main(args)
        self.assertEqual(exit_code, 0)

    def test_rig_no_args_shows_help(self) -> None:
        """
        Test rig script with no arguments shows help.
        """
        args = []
        with mock.patch("subprocess.run"):
            exit_code = hrig.main(args)
        self.assertEqual(exit_code, 0)

    def test_rig_ripgrep_not_found(self) -> None:
        """
        Test rig script when ripgrep is not installed.
        """
        args = ["TODO"]
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            exit_code = hrig.main(args)
        self.assertEqual(exit_code, 1)
