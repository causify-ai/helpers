import helpers.hrig as hrig
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti


# #############################################################################
# TestRigScript
# #############################################################################


class TestRigScript(hunitest.TestCase):
    """
    Test rig script functionality through hrig module integration.
    """

    # TODO(ai_gp): Add type hints
    def helper(
        self, args, expected_cmd=None, expected_exit_code=None, side_effect=None
    ):
        """
        Test helper for rig main function.

        :param args: Arguments to pass to hrig.main()
        :param expected_cmd: Expected command string passed to subprocess.run()
        :param expected_exit_code: Expected exit code from hrig.main()
        :param side_effect: Exception to raise from subprocess.run()
        """
        # Run test.
        with hunteuti.capture_system_calls(side_effect=side_effect) as invocations:
            try:
                exit_code = hrig.main(args)
            except SystemExit as e:
                exit_code = e.code
        # Check outputs.
        if expected_cmd is not None:
            self.assertEqual(len(invocations), 1)
            # TODO(ai_gp): Compare with assert_equal as strings.
            self.assertEqual(invocations[0]["function"], "subprocess.run")
            self.assertEqual(invocations[0]["args"], (expected_cmd,))
        if expected_exit_code is not None:
            self.assertEqual(exit_code, expected_exit_code)

    def test1(self) -> None:
        """
        Test search for pattern in current directory.
        """
        # Prepare inputs.
        args = ["TODO"]
        # Prepare outputs.
        expected_cmd = ["rg", "TODO", ".", "-n", "--no-heading", "--color=never"]
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code=0)

    def test2(self) -> None:
        """
        Test search for pattern in specified directory.
        """
        # Prepare inputs.
        args = ["import", "src"]
        # Prepare outputs.
        # TODO(ai_gp): Pass it as a single str and not a list.
        expected_cmd = ["rg", "import", "src", "-n", "--no-heading", "--color=never"]
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test3(self) -> None:
        """
        Test filter by file extension.
        """
        # Prepare inputs.
        args = ["class", ".", "py"]
        # Prepare outputs.
        # TODO(ai_gp): Pass it as a single str and not a list.
        expected_cmd = ["rg", "-g", "*.py", "class", ".", "-n", "--no-heading", "--color=never"]
        expected_exit_code=0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test4(self) -> None:
        """
        Test --help flag.
        """
        # Prepare inputs.
        args = ["--help"]
        expected_exit_code=0
        # Run test.
        self.helper(args, expected_exit_code)

    def test5(self) -> None:
        """
        Test no arguments shows help.
        """
        # Prepare inputs.
        args = []
        # Run test.
        expected_exit_code=0
        self.helper(args, expected_exit_code)

    def test6(self) -> None:
        """
        Test when ripgrep is not installed.
        """
        # Prepare inputs.
        args = ["TODO"]
        expected_exit_code=1
        # Run test.
        self.helper(args, expected_exit_code, side_effect=FileNotFoundError)
