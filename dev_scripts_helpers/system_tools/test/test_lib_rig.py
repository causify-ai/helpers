from typing import List, Optional, Type

import dev_scripts_helpers.system_tools.lib_rig as dshstliri
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti


# #############################################################################
# TestRigScript
# #############################################################################


class TestRigScript(hunitest.TestCase):
    """
    Test rig script functionality through hrig module integration.
    """

    def helper(
        self,
        args: List[str],
        *,
        expected_cmd: Optional[str] = None,
        expected_exit_code: Optional[int] = None,
        side_effect: Optional[Type[Exception]] = None,
    ) -> None:
        """
        Test helper for rig main function.

        :param args: Arguments to pass to hrig.main()
        :param expected_cmd: Expected command string passed to subprocess.run()
        :param expected_exit_code: Expected exit code from hrig.main()
        :param side_effect: Exception to raise from subprocess.run()
        """
        # Run test.
        with hunteuti.capture_system_calls(
            side_effect=side_effect
        ) as invocations:
            try:
                exit_code = dshstliri.main(args)
            except SystemExit as e:
                exit_code = e.code
        # Check outputs.
        if expected_cmd is not None:
            self.assertEqual(len(invocations), 1)
            self.assertEqual(invocations[0]["function"], "subprocess.run")
            actual_cmd = " ".join(invocations[0]["args"][0])
            self.assertEqual(actual_cmd, expected_cmd)
        if expected_exit_code is not None:
            self.assertEqual(exit_code, expected_exit_code)

    def test1(self) -> None:
        """
        Test search for pattern in current directory.
        """
        # Prepare inputs.
        args = ["TODO"]
        # Prepare outputs.
        expected_cmd = "rg TODO . -n --no-heading --color=never"
        # Run test.
        self.helper(args, expected_cmd=expected_cmd, expected_exit_code=0)

    def test2(self) -> None:
        """
        Test search for pattern in specified directory.
        """
        # Prepare inputs.
        args = ["import", "src"]
        # Prepare outputs.
        expected_cmd = "rg import src -n --no-heading --color=never"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd=expected_cmd,
            expected_exit_code=expected_exit_code,
        )

    def test3(self) -> None:
        """
        Test filter by file extension using third positional argument.
        """
        # Prepare inputs.
        args = ["class", ".", "py"]
        # Prepare outputs.
        expected_cmd = "rg -g *.py class . -n --no-heading --color=never"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd=expected_cmd,
            expected_exit_code=expected_exit_code,
        )

    def test4(self) -> None:
        """
        Test --help flag.
        """
        # Prepare inputs.
        args = ["--help"]
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_exit_code=expected_exit_code)

    def test5(self) -> None:
        """
        Test no arguments shows help.
        """
        # Prepare inputs.
        args = []
        # Run test.
        expected_exit_code = 0
        self.helper(args, expected_exit_code=expected_exit_code)

    def test6(self) -> None:
        """
        Test when ripgrep is not installed.
        """
        # Prepare inputs.
        args = ["TODO"]
        expected_exit_code = 1
        # Run test.
        self.helper(
            args,
            expected_exit_code=expected_exit_code,
            side_effect=FileNotFoundError,
        )

    def test7(self) -> None:
        """
        Test filter by multiple file extensions.
        """
        # Prepare inputs.
        args = ["def", ".", "py,md"]
        # Prepare outputs.
        expected_cmd = "rg -g *.py -g *.md def . -n --no-heading --color=never"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd=expected_cmd,
            expected_exit_code=expected_exit_code,
        )

    def test8(self) -> None:
        """
        Test filter with spaces in comma-separated extensions.
        """
        # Prepare inputs.
        args = ["import", "src", "py, ipynb, md"]
        # Prepare outputs.
        expected_cmd = "rg -g *.py -g *.ipynb -g *.md import src -n --no-heading --color=never"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd=expected_cmd,
            expected_exit_code=expected_exit_code,
        )

    def test9(self) -> None:
        """
        Test that extensions starting with dot raise assertion error.
        """
        # Prepare inputs.
        args = ["def", ".", ".py"]
        # Run test and expect assertion error.
        with self.assertRaises(AssertionError):
            dshstliri.main(args)

    def test10(self) -> None:
        """
        Test --modified flag with pattern.
        """
        # This test verifies that --modified flag is parsed correctly,
        # though we can't test the actual git integration without a real repo.
        args = ["TODO", "--modified"]
        expected_exit_code = 0
        # Run test (may return 0 even if no files, since git cmd may not work in test)
        self.helper(args, expected_exit_code=expected_exit_code)

    def test11(self) -> None:
        """
        Test --branch flag with pattern.
        """
        args = ["TODO", "--branch"]
        expected_exit_code = 0
        self.helper(args, expected_exit_code=expected_exit_code)

    def test12(self) -> None:
        """
        Test --all flag with pattern.
        """
        args = ["TODO", "--all"]
        expected_exit_code = 0
        self.helper(args, expected_exit_code=expected_exit_code)

    def test13(self) -> None:
        """
        Test --last-commit flag with pattern.
        """
        args = ["TODO", "--last-commit"]
        expected_exit_code = 0
        self.helper(args, expected_exit_code=expected_exit_code)
