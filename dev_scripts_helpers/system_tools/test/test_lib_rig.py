from typing import Any, Dict, List, Optional, Type

import pytest

import dev_scripts_helpers.system_tools.lib_rig as dshstliri
import helpers.hgit as hgit
import helpers.hserver as hserver
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti


# #############################################################################
# TestRigScript
# #############################################################################


class TestRigScript(hunitest.TestCase):
    """
    Test rig script functionality through hrig module integration.
    """

    # TODO(gp): Use hunteuti.assert_sys_calls()...
    def _assert_cmd_invocation(
        self,
        sys_calls: List[Dict[str, Any]],
        expected_cmd: str,
    ) -> None:
        """
        Assert that the captured system calls match the expected command.

        :param sys_calls: Captured system calls
        :param expected_cmd: Expected command string
        """
        self.assertEqual(len(sys_calls), 1, "Expected exactly one call")
        self.assertEqual(
            sys_calls[0]["function"],
            "subprocess.run",
            "Expected subprocess.run call",
        )
        actual_cmd = " ".join(sys_calls[0]["args"][0])
        self.assertEqual(actual_cmd, expected_cmd)

    def helper(
        self,
        args: List[str],
        expected_cmd: str,
        expected_exit_code: Optional[int],
        *,
        side_effect: Optional[Type[Exception]] = None,
    ) -> None:
        """
        Test helper for rig main function.

        :param args: Arguments to pass to hrig.main()
        :param expected_cmd: Expected command string or "" to skip command
            verification
        :param expected_exit_code: Expected exit code or None to skip exit code
            verification
        :param side_effect: Exception to raise from subprocess.run()
        """
        # Run test.
        with hunteuti.capture_sys_calls(side_effect=side_effect) as sys_calls:
            try:
                exit_code = dshstliri.main(args)
            except SystemExit as e:
                exit_code = e.code
        # Check command output.
        if expected_cmd != "":
            self._assert_cmd_invocation(sys_calls, expected_cmd)
        # Check exit code.
        if expected_exit_code is not None:
            self.assertEqual(exit_code, expected_exit_code)

    def test1(self) -> None:
        """
        Test search for pattern in current directory.
        """
        # Prepare inputs.
        args = ["TODO"]
        # Prepare outputs.
        expected_cmd = (
            "rg TODO --hidden -n --no-heading --color=never -g !.git ."
        )
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test2(self) -> None:
        """
        Test search for pattern in specified directory.
        """
        # Prepare inputs.
        args = ["import", "src"]
        # Prepare outputs.
        expected_cmd = (
            "rg import --hidden -n --no-heading --color=never -g !.git src"
        )
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test3(self) -> None:
        """
        Test filter by file extension using third positional argument.
        """
        # Prepare inputs.
        args = ["class", ".", "py"]
        # Prepare outputs.
        expected_cmd = (
            "rg class --hidden -n --no-heading --color=never -g !.git -g *.py ."
        )
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test4(self) -> None:
        """
        Test --help flag.
        """
        # Prepare inputs.
        args = ["--help"]
        expected_exit_code = 0
        expected_cmd = ""
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test5(self) -> None:
        """
        Test no arguments shows help.
        """
        # Prepare inputs.
        args = []
        expected_cmd = ""
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test6(self) -> None:
        """
        Test when ripgrep is not installed.
        """
        # Prepare inputs.
        args = ["TODO"]
        expected_exit_code = 1
        side_effect = FileNotFoundError
        # Run test.
        self.helper(
            args,
            "",
            expected_exit_code,
            side_effect=side_effect,
        )

    def test7(self) -> None:
        """
        Test filter by multiple file extensions.
        """
        # Prepare inputs.
        args = ["def", ".", "py,md"]
        # Prepare outputs.
        expected_cmd = "rg def --hidden -n --no-heading --color=never -g !.git -g *.py -g *.md ."
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test8(self) -> None:
        """
        Test filter with spaces in comma-separated extensions.
        """
        # Prepare inputs.
        args = ["import", "src", "py, ipynb, md"]
        # Prepare outputs.
        expected_cmd = "rg import --hidden -n --no-heading --color=never -g !.git -g *.py -g *.ipynb -g *.md src"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
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
        expected_cmd = ""
        expected_exit_code = 0
        # Run test (may return 0 even if no files, since git cmd may not work in test).
        self.helper(args, expected_cmd, expected_exit_code)

    def test11(self) -> None:
        """
        Test --branch flag with pattern.
        """
        # Prepare inputs.
        args = ["TODO", "--branch"]
        # Prepare outputs.
        expected_cmd = ""
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test12(self) -> None:
        """
        Test --all flag with pattern.
        """
        # Prepare inputs.
        args = ["TODO", "--all"]
        # Prepare outputs.
        expected_cmd = ""
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    @pytest.mark.skipif(
        hserver.is_inside_docker(),
        reason="rg version issues",
    )
    def test13(self) -> None:
        """
        Test --last_commit flag with pattern.
        """
        # Prepare inputs.
        args = ["TODO", "--last_commit"]
        # Prepare outputs.
        expected_cmd = ""
        expected_exit_code = 0
        # Run test.
        self.helper(args, expected_cmd, expected_exit_code)

    def test14(self) -> None:
        """
        Test --rg_opts flag to pass additional ripgrep options.
        """
        # Prepare inputs.
        args = ["TODO", ".", "--rg_opts", "-S -i"]
        # Prepare outputs.
        expected_cmd = (
            "rg TODO --hidden -n --no-heading --color=never -g !.git -S -i ."
        )
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test15(self) -> None:
        """
        Test --def flag to search for Python class/def definitions.
        """
        # Prepare inputs.
        args = ["main", "--def"]
        # Prepare outputs.
        expected_cmd = "rg (class|def) main --hidden -n --no-heading --color=never -g !.git -g *.py ."
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    @pytest.mark.skipif(
        hserver.is_inside_docker(),
        reason="rg version issues",
    )
    def test16(self) -> None:
        """
        Test --rule flag to search for Markdown headers in .claude/skills.
        """
        # Prepare inputs.
        args = ["--rule"]
        # Prepare outputs.
        git_root = hgit.find_git_root()
        expected_cmd = f"rg ^# --hidden -n --no-heading --color=never -g !.git -i -g *.md {git_root}/.claude/skills"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    @pytest.mark.skipif(
        hserver.is_inside_docker(),
        reason="rg version issues",
    )
    def test16_rule_with_pattern(self) -> None:
        """
        Test --rule flag with a pattern to match Markdown headers.
        """
        # Prepare inputs.
        args = ["assert_equal", "--rule"]
        # Prepare outputs.
        git_root = hgit.find_git_root()
        expected_cmd = f"rg ^#+.*assert_equal --hidden -n --no-heading --color=never -g !.git -i -g *.md {git_root}/.claude/skills"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    @pytest.mark.skipif(
        hserver.is_inside_docker(),
        reason="rg version issues",
    )
    def test17(self) -> None:
        """
        Test --todo flag.
        """
        # Prepare inputs.
        args = ["--todo"]
        # Prepare outputs.
        expected_cmd = r"rg ^\s*(#|//)\s*TODO\(ai_gp\S*\) --hidden -n --no-heading --color=never -g !.git ."
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test18(self) -> None:
        """
        Test -i flag expands to -S -i for ripgrep (smart-case + ignore-case).
        """
        # Prepare inputs.
        args = ["TODO", "-i"]
        # Prepare outputs.
        expected_cmd = (
            "rg TODO --hidden -n --no-heading --color=never -g !.git -S -i ."
        )
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test19(self) -> None:
        """
        Test -i flag combined with directory and extension arguments.
        """
        # Prepare inputs.
        args = ["import", "src", "js", "-i"]
        # Prepare outputs.
        expected_cmd = "rg import --hidden -n --no-heading --color=never -g !.git -S -i -g *.js src"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test20(self) -> None:
        """
        Test --todo flag with directory and file extension.
        """
        # Prepare inputs.
        args = ["--todo", "ai_gp", ".", "py"]
        # Prepare outputs.
        expected_cmd = r"rg ^\s*(#|//)\s*TODO\(ai_gp\) --hidden -n --no-heading --color=never -g !.git -g *.py ."
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test21(self) -> None:
        """
        Test --todo flag with custom pattern, directory, and extension.
        """
        # Prepare inputs.
        args = ["--todo", "gp_custom", "src", "md"]
        # Prepare outputs.
        expected_cmd = r"rg ^\s*(#|//)\s*TODO\(gp_custom\) --hidden -n --no-heading --color=never -g !.git -g *.md src"
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )

    def test22(self) -> None:
        """
        Test --todo flag with multiple extensions.
        """
        # Prepare inputs.
        args = ["--todo", "ai_gp", ".", "py,md"]
        # Prepare outputs.
        expected_cmd = r"rg ^\s*(#|//)\s*TODO\(ai_gp\) --hidden -n --no-heading --color=never -g !.git -g *.py -g *.md ."
        expected_exit_code = 0
        # Run test.
        self.helper(
            args,
            expected_cmd,
            expected_exit_code,
        )
