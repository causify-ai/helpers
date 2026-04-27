import logging
import unittest.mock as mock

import helpers.hrig as hrig
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class Test_build_ripgrep_command(hunitest.TestCase):
    """
    Test ripgrep command building with various parameter combinations.
    """

    def test1(self) -> None:
        """
        Test building command with pattern and directory only.
        """
        # Prepare inputs.
        pattern = "TODO"
        directory = "."
        extension = None
        rg_opts = ["-n", "--no-heading", "--color=never"]
        # Prepare outputs.
        expected = ["rg", "TODO", ".", "-n", "--no-heading", "--color=never"]
        # Run test.
        actual = hrig.build_ripgrep_command(
            pattern=pattern,
            directory=directory,
            extension=extension,
            rg_opts=rg_opts,
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test building command with extension filter.
        """
        # Prepare inputs.
        pattern = "import"
        directory = "src"
        extension = "py"
        rg_opts = ["-n", "--no-heading", "--color=never"]
        # Prepare outputs.
        expected = [
            "rg",
            "-g",
            "*.py",
            "import",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        # Run test.
        actual = hrig.build_ripgrep_command(
            pattern=pattern,
            directory=directory,
            extension=extension,
            rg_opts=rg_opts,
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test building command with additional ripgrep options.
        """
        # Prepare inputs.
        pattern = "class"
        directory = "."
        extension = "js"
        rg_opts = ["-i", "-n"]
        # Prepare outputs.
        expected = ["rg", "-g", "*.js", "class", ".", "-i", "-n"]
        # Run test.
        actual = hrig.build_ripgrep_command(
            pattern=pattern,
            directory=directory,
            extension=extension,
            rg_opts=rg_opts,
        )
        # Check outputs.
        self.assertEqual(actual, expected)


class Test_get_default_rg_opts(hunitest.TestCase):
    """
    Test default ripgrep options.
    """

    def test1(self) -> None:
        """
        Test that default options are correct.
        """
        # Prepare outputs.
        expected = ["-n", "--no-heading", "--color=never"]
        # Run test.
        actual = hrig.get_default_rg_opts()
        # Check outputs.
        self.assertEqual(actual, expected)


class Test_parse_arguments(hunitest.TestCase):
    """
    Test command-line argument parsing.
    """

    def test1(self) -> None:
        """
        Test parsing simple pattern search.
        """
        # Prepare inputs.
        args = ["TODO"]
        # Run test.
        parsed = hrig.parse_arguments(args)
        # Check outputs.
        self.assertEqual(parsed.pattern, "TODO")
        self.assertEqual(parsed.directory, ".")
        self.assertIsNone(parsed.extension)
        self.assertIsNone(parsed.todo)
        self.assertFalse(parsed.help)

    def test2(self) -> None:
        """
        Test parsing with directory and extension.
        """
        # Prepare inputs.
        args = ["import", "src", "py"]
        # Run test.
        parsed = hrig.parse_arguments(args)
        # Check outputs.
        self.assertEqual(parsed.pattern, "import")
        self.assertEqual(parsed.directory, "src")
        self.assertEqual(parsed.extension, "py")
        self.assertIsNone(parsed.todo)

    def test3(self) -> None:
        """
        Test parsing --todo with default user.
        """
        # Prepare inputs.
        args = ["--todo"]
        # Run test.
        parsed = hrig.parse_arguments(args)
        # Check outputs.
        self.assertEqual(parsed.todo, "ai_gp")
        self.assertIsNone(parsed.pattern)

    def test4(self) -> None:
        """
        Test parsing --todo with custom user.
        """
        # Prepare inputs.
        args = ["--todo", "gp"]
        # Run test.
        parsed = hrig.parse_arguments(args)
        # Check outputs.
        self.assertEqual(parsed.todo, "gp")

    def test5(self) -> None:
        """
        Test parsing --todo with user and directory.
        """
        # Prepare inputs.
        args = ["--todo", "ai_gp", "src"]
        # Run test.
        parsed = hrig.parse_arguments(args)
        # Check outputs.
        self.assertEqual(parsed.todo, "ai_gp")
        self.assertEqual(parsed.directory, "src")
        self.assertIsNone(parsed.pattern)

    def test6(self) -> None:
        """
        Test parsing --help flag.
        """
        # Prepare inputs.
        args = ["--help"]
        # Run test.
        parsed = hrig.parse_arguments(args)
        # Check outputs.
        self.assertTrue(parsed.help)

    def test7(self) -> None:
        """
        Test parsing -h flag.
        """
        # Prepare inputs.
        args = ["-h"]
        # Run test.
        parsed = hrig.parse_arguments(args)
        # Check outputs.
        self.assertTrue(parsed.help)


class Test_main(hunitest.TestCase):
    """
    Test main function with various input combinations.
    """

    def helper(self, args, expected_cmd=None):
        """
        Test helper for main function.

        :param args: Command-line arguments
        :param expected_cmd: Expected ripgrep command (if None, just check success)
        """
        with mock.patch("helpers.hrig.subprocess.run") as mock_run:
            hrig.main(args)
            if expected_cmd:
                mock_run.assert_called_once()
                actual_cmd = mock_run.call_args[0][0]
                self.assertEqual(actual_cmd, expected_cmd)

    def test1(self) -> None:
        """
        Test main with simple pattern search.
        """
        # Prepare inputs.
        args = ["TODO"]
        expected = ["rg", "TODO", ".", "-n", "--no-heading", "--color=never"]
        # Run test.
        self.helper(args, expected)

    def test2(self) -> None:
        """
        Test main with pattern, directory, and extension.
        """
        # Prepare inputs.
        args = ["import", "src", "py"]
        expected = [
            "rg",
            "-g",
            "*.py",
            "import",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        # Run test.
        self.helper(args, expected)

    def test3(self) -> None:
        """
        Test main with --todo flag.
        """
        # Prepare inputs.
        args = ["--todo"]
        expected = ["rg", "TODO\\(ai_gp\\)", ".", "-n", "--no-heading", "--color=never"]
        # Run test.
        self.helper(args, expected)

    def test4(self) -> None:
        """
        Test main with --todo and custom user.
        """
        # Prepare inputs.
        args = ["--todo", "gp"]
        expected = ["rg", "TODO\\(gp\\)", ".", "-n", "--no-heading", "--color=never"]
        # Run test.
        self.helper(args, expected)

    def test5(self) -> None:
        """
        Test main with --todo and directory.
        """
        # Prepare inputs.
        args = ["--todo", "ai_gp", "src"]
        expected = [
            "rg",
            "TODO\\(ai_gp\\)",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        # Run test.
        self.helper(args, expected)

    def test6(self) -> None:
        """
        Test main with --todo, user, directory, and extension.
        """
        # Prepare inputs.
        args = ["--todo", "gp", "src", "py"]
        expected = [
            "rg",
            "-g",
            "*.py",
            "TODO\\(gp\\)",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        # Run test.
        self.helper(args, expected)

    def test7(self) -> None:
        """
        Test main with help flag returns 0.
        """
        # Prepare inputs.
        args = ["--help"]
        # Run test.
        with mock.patch("helpers.hrig.subprocess.run"):
            exit_code = hrig.main(args)
        # Check outputs.
        self.assertEqual(exit_code, 0)

    def test8(self) -> None:
        """
        Test main with no arguments shows help returns 0.
        """
        # Prepare inputs.
        args = []
        # Run test.
        with mock.patch("helpers.hrig.subprocess.run"):
            exit_code = hrig.main(args)
        # Check outputs.
        self.assertEqual(exit_code, 0)

    def test9(self) -> None:
        """
        Test main with ripgrep not found returns 1.
        """
        # Prepare inputs.
        args = ["TODO"]
        # Run test.
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            exit_code = hrig.main(args)
        # Check outputs.
        self.assertEqual(exit_code, 1)
