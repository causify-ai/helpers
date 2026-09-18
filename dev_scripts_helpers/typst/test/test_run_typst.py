# TODO(ai_gp): Add logging setup to match template - missing import logging and
# _LOG = logging.getLogger(__name__) (testing.rules.md:## Unit Test Code
# Structure)
import os
from typing import List
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.lib_typst as dshdlity
import dev_scripts_helpers.typst.run_typst as dshtruty


# #############################################################################
# Test__report_compile_warnings
# #############################################################################


class Test__report_compile_warnings(hunitest.TestCase):
    """
    Test the `_report_compile_warnings()` function.
    """

    def helper(self, output: str, expected: List[str]) -> None:
        """
        Test helper for `_report_compile_warnings()`.

        :param output:`typst compile` output to scan
        :param expected: warning lines expected to be extracted
        """
        # Run test.
        actual = dshtruty._report_compile_warnings(output)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that `warning:` diagnostic lines are extracted.
        """
        # Prepare inputs.
        output = "\n".join(
            [
                "warning: unnecessary parentheses",
                "  ┌─ test.typ:1:8",
                "compiling test.typ",
                "warning: unknown variable: text",
                "written test.pdf",
            ]
        )
        # Prepare outputs.
        expected = [
            "warning: unnecessary parentheses",
            "warning: unknown variable: text",
        ]
        # Run test.
        self.helper(output, expected)

    def test2(self) -> None:
        """
        Test that output with no warnings returns an empty list.
        """
        # Prepare inputs.
        # TODO(ai_gp): Use """ and hprint.dedent() instead of escaped \n in
        # string literals (testing.rules.md:## Use Triple-Quote Assignment with
        # `hprint.dedent` for Multi-line Strings)
        output = "compiling test.typ\nwritten test.pdf"
        # Prepare outputs.
        expected: List[str] = []
        # Run test.
        self.helper(output, expected)

    # TODO(ai_gp): Add test for single warning case - boundary condition example
    # from rule (testing.rules.md:## What to Test)


# #############################################################################
# Test__compile_typst
# #############################################################################


# TODO(ai_gp): Remove implementation details from docstring - should only
# document WHAT is being tested, not HOW or why (e.g., mocking details)
# (testing.rules.md:## Test Class Documentation)
class Test__compile_typst(hunitest.TestCase):
    """
    Test the `_compile_typst()` function.

    `dshdlity.run_dockerized_typst()` and `hsystem.system_to_string()` are mocked
    since they require a real Docker/Typst toolchain; this class only verifies
    the warning-detection orchestration logic.
    """

    def helper(self, output: str, *, abort_on_warnings: bool) -> None:
        """
        Test helper for `_compile_typst()`.

        :param output: fake `typst compile` output returned by the mocked
            `hsystem.system_to_string()`
        :param abort_on_warnings: value passed through to `_compile_typst()`
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        # Run test.
        with (
            mock.patch.object(
                dshdlity,
                "run_dockerized_typst",
                return_value="typst compile book.typ book.pdf",
            ),
            # TODO(ai_gp): Do not mock internal wrapper dshtruty.hsystem.
            # Mock the external library instead (testing.rules.md:## Mock Only
            # External Dependencies)
            mock.patch.object(
                dshtruty.hsystem, "system_to_string", return_value=(0, output)
            ),
        ):
            dshtruty._compile_typst(
                in_file_path,
                out_file_path,
                "/repo_root",
                abort_on_warnings=abort_on_warnings,
            )

    def test1(self) -> None:
        """
        Test that warnings abort the build by default.
        """
        # Prepare inputs.
        output = "warning: unused import"
        # TODO(ai_gp): Change section comment to "# Run test and check output."
        # when using assertRaises for exception testing
        # (testing.rules.md:## Testing Exceptions)
        # Run test.
        with self.assertRaises(AssertionError):
            self.helper(output, abort_on_warnings=True)

    def test2(self) -> None:
        """
        Test that `abort_on_warnings=False` only logs, without raising.
        """
        # Prepare inputs.
        output = "warning: unused import"
        # Run test (should not raise).
        # TODO(ai_gp): Add explicit "# Check outputs." or "# Run test and check
        # outputs." section (testing.rules.md:## Use Three Sections in Testing
        # Methods)
        self.helper(output, abort_on_warnings=False)

    def test3(self) -> None:
        """
        Test that output without warnings never aborts.
        """
        # Prepare inputs.
        output = "written book.pdf"
        # Run test (should not raise).
        # TODO(ai_gp): Add explicit "# Check outputs." or "# Run test and check
        # outputs." section (testing.rules.md:## Use Three Sections in Testing
        # Methods)
        self.helper(output, abort_on_warnings=True)


# #############################################################################
# Test_run_typst_py
# #############################################################################


# TODO(ai_gp): Test should verify externally observable behavior (generated
# files, exit codes, stdout/stderr) rather than mocking internal functions
# (_compile_typst, _render_images). Do not mock orchestration logic per rule
# (testing.rules.md:## Test Behavior, Not Implementation)
# TODO(ai_gp): Do not mock internal helpers (_compile_typst, _render_images)
# or internal wrappers (hsystem.system_to_string, hopen.open_file). Only mock
# external dependencies (3rd-party providers, cloud infra, databases, external
# APIs) (testing.rules.md:## Mock Only External Dependencies)
class Test_run_typst_py(hunitest.TestCase):
    """
    End-to-end tests for the `run_typst.py` executable.
    """

    # TODO(ai_gp): Rename helper method from _run_main to helper or helper1 to
    # follow naming convention (testing.rules.md:## Order Helper Methods First in
    # Test Classes)
    def _run_main(self, argv: List[str]) -> None:
        """
        Run `dshtruty._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshtruty._parse()
        with mock.patch("sys.argv", argv):
            dshtruty._main(parser)

    # TODO(ai_gp): Rename helper method from _write_input_file to helper1 or
    # helper2 to follow naming convention (testing.rules.md:## Order Helper
    # Methods First in Test Classes)
    def _write_input_file(self) -> str:
        """
        Create `book.typ` in the scratch space.

        :return: path to the created input file
        """
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
        return in_file_path

    # TODO(ai_gp): Split test into separate test methods - this test verifies
    # both default output path and render_images behavior, should test only one
    # case per method (testing.rules.md:## Test One Thing)
    def test1(self) -> None:
        """
        Test that the default output path swaps the `.typ` extension for
        `.pdf`, and that `render_images` runs by default.
        """
        # Prepare inputs.
        in_file_path = self._write_input_file()
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--skip_action",
            "open_pdf",
        ]
        # Prepare outputs.
        expected_out_file_path = os.path.join(
            self.get_scratch_space(), "book.pdf"
        )
        # Run test.
        with (
            mock.patch.object(dshtruty, "_compile_typst") as mock_compile,
            mock.patch.object(dshtruty, "_render_images") as mock_render,
        ):
            self._run_main(argv)
        # Check outputs.
        actual_out_file_path = mock_compile.call_args.args[1]
        # TODO(ai_gp): Use self.assert_equal() instead of self.assertEqual()
        # for string comparison (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual_out_file_path, expected_out_file_path)
        self.assertEqual(mock_render.call_count, 1)

    def test2(self) -> None:
        """
        Test that an explicit `--output` path is respected.
        """
        # Prepare inputs.
        in_file_path = self._write_input_file()
        # TODO(ai_gp): Separate expected output (out_file_path) into "# Prepare
        # outputs." section instead of mixing with inputs
        # (testing.rules.md:## Consolidate Inputs and Outputs)
        out_file_path = os.path.join(self.get_scratch_space(), "custom.pdf")
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--output",
            out_file_path,
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with mock.patch.object(dshtruty, "_compile_typst") as mock_compile:
            self._run_main(argv)
        # Check outputs.
        actual_out_file_path = mock_compile.call_args.args[1]
        # TODO(ai_gp): Use self.assert_equal() instead of self.assertEqual()
        # for string comparison (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual_out_file_path, out_file_path)

    def test3(self) -> None:
        """
        Test that the "open_pdf" action opens the compiled PDF.
        """
        # Prepare inputs.
        in_file_path = self._write_input_file()
        # TODO(ai_gp): Separate expected output (out_file_path) into "# Prepare
        # outputs." section instead of mixing with inputs
        # (testing.rules.md:## Consolidate Inputs and Outputs)
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        argv = ["run_typst.py", "--input", in_file_path]
        # Run test.
        with (
            mock.patch.object(dshtruty, "_compile_typst"),
            mock.patch.object(dshtruty.hopen, "open_file") as mock_open,
        ):
            self._run_main(argv)
        # Check outputs.
        mock_open.assert_called_once_with(out_file_path)

    def test4(self) -> None:
        """
        Test that `--action render_images` triggers the optional rendering
        step.
        """
        # Prepare inputs.
        in_file_path = self._write_input_file()
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--action",
            "render_images",
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with (
            mock.patch.object(dshtruty, "_compile_typst"),
            mock.patch.object(dshtruty, "_render_images") as mock_render,
        ):
            self._run_main(argv)
        # Check outputs.
        self.assertEqual(mock_render.call_count, 1)

    def test5(self) -> None:
        """
        Test that `--root` overrides the default Git-root-based value.
        """
        # Prepare inputs.
        in_file_path = self._write_input_file()
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--root",
            "/custom/root",
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with mock.patch.object(dshtruty, "_compile_typst") as mock_compile:
            self._run_main(argv)
        # Check outputs.
        actual_root = mock_compile.call_args.args[2]
        # TODO(ai_gp): Use self.assert_equal() instead of self.assertEqual()
        # for string comparison (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual_root, "/custom/root")

    def test6(self) -> None:
        """
        Test that `--no_abort_on_warnings` is threaded through to
        `_compile_typst()`.
        """
        # Prepare inputs.
        in_file_path = self._write_input_file()
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--no_abort_on_warnings",
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with mock.patch.object(dshtruty, "_compile_typst") as mock_compile:
            self._run_main(argv)
        # Check outputs.
        self.assertEqual(
            mock_compile.call_args.kwargs["abort_on_warnings"], False
        )
