import os
from typing import List
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
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

        :param output: `typst compile` output to scan
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
        output = "compiling test.typ\nwritten test.pdf"
        # Prepare outputs.
        expected: List[str] = []
        # Run test.
        self.helper(output, expected)


# #############################################################################
# Test__compile_typst
# #############################################################################


class Test__compile_typst(hunitest.TestCase):
    """
    Test the `_compile_typst()` function.

    `dshdlity.run_dockerized_typst()` and `hsystem.system_to_string()` are
    mocked since they require a real Docker/Typst toolchain; this class only
    verifies the warning-detection orchestration logic.
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
                dshtruty.dshdlity,
                "run_dockerized_typst",
                return_value="typst compile book.typ book.pdf",
            ),
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
        self.helper(output, abort_on_warnings=False)

    def test3(self) -> None:
        """
        Test that output without warnings never aborts.
        """
        # Prepare inputs.
        output = "written book.pdf"
        # Run test (should not raise).
        self.helper(output, abort_on_warnings=True)


# #############################################################################
# Test_run_typst_py
# #############################################################################


class Test_run_typst_py(hunitest.TestCase):
    """
    End-to-end tests for the `run_typst.py` executable.
    """

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `dshtyrt._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshtruty._parse()
        with mock.patch("sys.argv", argv):
            dshtruty._main(parser)

    # TODO(ai_gp): Factor out more code.
    def test1(self) -> None:
        """
        Test that the default output path swaps the `.typ` extension for
        `.pdf`, and that `render_images` doesn't run by default.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
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
            mock.patch.object(dshtyrt, "_compile_typst") as mock_compile,
            mock.patch.object(dshtyrt, "_render_images") as mock_render,
        ):
            self._run_main(argv)
        # Check outputs.
        actual_out_file_path = mock_compile.call_args.args[1]
        self.assertEqual(actual_out_file_path, expected_out_file_path)
        self.assertEqual(mock_render.call_count, 0)

    def test2(self) -> None:
        """
        Test that an explicit `--output` path is respected.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
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
        with mock.patch.object(dshtyrt, "_compile_typst") as mock_compile:
            self._run_main(argv)
        # Check outputs.
        actual_out_file_path = mock_compile.call_args.args[1]
        self.assertEqual(actual_out_file_path, out_file_path)

    def test3(self) -> None:
        """
        Test that the "open_pdf" action opens the compiled PDF.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        argv = ["run_typst.py", "--input", in_file_path]
        # Run test.
        with (
            mock.patch.object(dshtyrt, "_compile_typst"),
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
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
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
            mock.patch.object(dshtyrt, "_compile_typst"),
            mock.patch.object(dshtyrt, "_render_images") as mock_render,
        ):
            self._run_main(argv)
        # Check outputs.
        self.assertEqual(mock_render.call_count, 1)

    def test5(self) -> None:
        """
        Test that `--root` overrides the default Git-root-based value.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
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
        with mock.patch.object(dshtyrt, "_compile_typst") as mock_compile:
            self._run_main(argv)
        # Check outputs.
        actual_root = mock_compile.call_args.args[2]
        self.assertEqual(actual_root, "/custom/root")

    def test6(self) -> None:
        """
        Test that `--no_abort_on_warnings` is threaded through to
        `_compile_typst()`.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--no_abort_on_warnings",
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with mock.patch.object(dshtyrt, "_compile_typst") as mock_compile:
            self._run_main(argv)
        # Check outputs.
        self.assertEqual(
            mock_compile.call_args.kwargs["abort_on_warnings"], False
        )
