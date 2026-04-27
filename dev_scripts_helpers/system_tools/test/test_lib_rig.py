import unittest.mock as mock

import helpers.hrig as hrig
import helpers.hunit_test as hunitest


# #############################################################################
# TestRigScript
# #############################################################################


class TestRigScript(hunitest.TestCase):
    """
    Test rig script functionality through hrig module integration.
    """

    def helper(self, args, expected_cmd=None, side_effect=None):
        """
        Test helper for rig main function.

        :param args: Arguments to pass to hrig.main()
        :param expected_cmd: Expected command passed to subprocess.run()
        :param side_effect: Exception to raise from subprocess.run()
        """
        # Run test.
        with mock.patch("subprocess.run", side_effect=side_effect) as mock_run:
            try:
                exit_code = hrig.main(args)
            except SystemExit as e:
                exit_code = e.code
        # Check outputs.
        if expected_cmd is not None:
            mock_run.assert_called_once_with(expected_cmd)
        return exit_code

    def test1(self) -> None:
        """
        Test search for pattern in current directory.
        """
        # Prepare inputs.
        args = ["TODO"]
        # Prepare outputs.
        expected_cmd = ["rg", "TODO", ".", "-n", "--no-heading", "--color=never"]
        # Run test.
        exit_code = self.helper(args, expected_cmd)
        # Check outputs.
        self.assertEqual(exit_code, 0)

    def test2(self) -> None:
        """
        Test search for pattern in specified directory.
        """
        # Prepare inputs.
        args = ["import", "src"]
        # Prepare outputs.
        expected_cmd = [
            "rg",
            "import",
            "src",
            "-n",
            "--no-heading",
            "--color=never",
        ]
        # Run test.
        exit_code = self.helper(args, expected_cmd)
        # Check outputs.
        self.assertEqual(exit_code, 0)

    def test3(self) -> None:
        """
        Test filter by file extension.
        """
        # Prepare inputs.
        args = ["class", ".", "py"]
        # Prepare outputs.
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
        # Run test.
        exit_code = self.helper(args, expected_cmd)
        # Check outputs.
        self.assertEqual(exit_code, 0)

    def test4(self) -> None:
        """
        Test --help flag.
        """
        # Prepare inputs.
        args = ["--help"]
        # Run test.
        exit_code = self.helper(args)
        # Check outputs.
        self.assertEqual(exit_code, 0)

    def test5(self) -> None:
        """
        Test no arguments shows help.
        """
        # Prepare inputs.
        args = []
        # Run test.
        exit_code = self.helper(args)
        # Check outputs.
        self.assertEqual(exit_code, 0)

    def test6(self) -> None:
        """
        Test when ripgrep is not installed.
        """
        # Prepare inputs.
        args = ["TODO"]
        # Run test.
        exit_code = self.helper(args, side_effect=FileNotFoundError)
        # Check outputs.
        self.assertEqual(exit_code, 1)
