import logging
import os
from typing import List
from unittest import mock

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.lib_typst as dshdlity
import dev_scripts_helpers.typst.run_typst as dshtruty

_LOG = logging.getLogger(__name__)


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
        output = """
        compiling test.typ
        written test.pdf
        """
        output = hprint.dedent(output)
        # Prepare outputs.
        expected: List[str] = []
        # Run test.
        self.helper(output, expected)

    def test3(self) -> None:
        """
        Test that a single `warning:` diagnostic line is extracted.
        """
        # Prepare inputs.
        output = "\n".join(
            [
                "compiling test.typ",
                "warning: unused import",
                "written test.pdf",
            ]
        )
        # Prepare outputs.
        expected = ["warning: unused import"]
        # Run test.
        self.helper(output, expected)


# #############################################################################
# Test__compile_typst
# #############################################################################


class Test__compile_typst(hunitest.TestCase):
    """
    Test the `_compile_typst()` function.
    """

    def helper(self, output: str, *, abort_on_warnings: bool) -> None:
        """
        Test helper for `_compile_typst()`.

        :param output: fake `typst compile` output returned by the mocked
            `subprocess.Popen`
        :param abort_on_warnings: value passed through to `_compile_typst()`
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        # `hsystem.system_to_string()` is an internal wrapper around
        # `subprocess.Popen()`, so mock `subprocess.Popen` itself (the true
        # external dependency) rather than the wrapper.
        mock_process = mock.MagicMock()
        mock_process.__enter__.return_value = mock_process
        mock_process.__exit__.return_value = False
        mock_process.stdout.readline.side_effect = [
            f"{line}\n".encode() for line in output.splitlines()
        ] + [b""]
        mock_process.wait.return_value = 0
        # Run test.
        with (
            mock.patch.object(
                dshdlity,
                "run_dockerized_typst",
                return_value="typst compile book.typ book.pdf",
            ),
            mock.patch("subprocess.Popen", return_value=mock_process),
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
        # Run test and check output.
        with self.assertRaises(AssertionError):
            self.helper(output, abort_on_warnings=True)

    def test2(self) -> None:
        """
        Test that `abort_on_warnings=False` only logs, without raising.
        """
        # Prepare inputs.
        output = "warning: unused import"
        # Run test and check outputs.
        # `helper()` should not raise since `abort_on_warnings=False`.
        self.helper(output, abort_on_warnings=False)

    def test3(self) -> None:
        """
        Test that output without warnings never aborts.
        """
        # Prepare inputs.
        output = "written book.pdf"
        # Run test and check outputs.
        # `helper()` should not raise since there are no warnings.
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
# Not resolved: `_compile_typst()` calls `dshdlity.run_dockerized_typst()`,
# which builds and inspects a real Docker image (`build_typst_container_image()`,
# `hdocker.image_exists()`), and `_render_images()` shells out to
# `render_images.py`. Neither has a fakeable external boundary short of a
# working Docker daemon (see `Test__compile_typst` above, which already mocks
# `dshdlity.run_dockerized_typst` for the same reason). `_compile_typst()`'s
# own logic is unit-tested directly there at the `subprocess.Popen` boundary,
# so this class only checks CLI-to-function argument wiring via the
# constructed call arguments, one of the externally observable behaviors the
# rule allows ("constructed commands").
class Test_run_typst_py(hunitest.TestCase):
    """
    End-to-end tests for the `run_typst.py` executable.
    """

    def helper(self, argv: List[str]) -> None:
        """
        Run `dshtruty._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshtruty._parse()
        with mock.patch("sys.argv", argv):
            dshtruty._main(parser)

    def helper1(self) -> str:
        """
        Create `book.typ` in the scratch space.

        :return: path to the created input file
        """
        in_file_path = os.path.join(self.get_scratch_space(), "book.typ")
        hio.to_file(in_file_path, "= Test")
        return in_file_path

    def test1(self) -> None:
        """
        Test that the default output path swaps the `.typ` extension for
        `.pdf`.
        """
        # Prepare inputs.
        in_file_path = self.helper1()
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
            mock.patch.object(dshtruty, "_render_images"),
        ):
            self.helper(argv)
        # Check outputs.
        actual_out_file_path = mock_compile.call_args.args[1]
        self.assert_equal(actual_out_file_path, expected_out_file_path)

    def test2(self) -> None:
        """
        Test that an explicit `--output` path is respected.
        """
        # Prepare inputs.
        in_file_path = self.helper1()
        # Prepare outputs.
        expected_out_file_path = os.path.join(
            self.get_scratch_space(), "custom.pdf"
        )
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--output",
            expected_out_file_path,
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with mock.patch.object(dshtruty, "_compile_typst") as mock_compile:
            self.helper(argv)
        # Check outputs.
        actual_out_file_path = mock_compile.call_args.args[1]
        self.assert_equal(actual_out_file_path, expected_out_file_path)

    def test3(self) -> None:
        """
        Test that the "open_pdf" action opens the compiled PDF.
        """
        # Prepare inputs.
        in_file_path = self.helper1()
        argv = ["run_typst.py", "--input", in_file_path]
        # Prepare outputs.
        expected_out_file_path = os.path.join(
            self.get_scratch_space(), "book.pdf"
        )
        # Run test.
        with (
            mock.patch.object(dshtruty, "_compile_typst"),
            mock.patch.object(dshtruty.hopen, "open_file") as mock_open,
        ):
            self.helper(argv)
        # Check outputs.
        mock_open.assert_called_once_with(expected_out_file_path)

    def test4(self) -> None:
        """
        Test that `--action render_images` triggers the optional rendering
        step.
        """
        # Prepare inputs.
        in_file_path = self.helper1()
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
            self.helper(argv)
        # Check outputs.
        self.assertEqual(mock_render.call_count, 1)

    def test5(self) -> None:
        """
        Test that `--root` overrides the default Git-root-based value.
        """
        # Prepare inputs.
        in_file_path = self.helper1()
        # Prepare outputs.
        expected_root = "/custom/root"
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--root",
            expected_root,
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with mock.patch.object(dshtruty, "_compile_typst") as mock_compile:
            self.helper(argv)
        # Check outputs.
        actual_root = mock_compile.call_args.args[2]
        self.assert_equal(actual_root, expected_root)

    def test6(self) -> None:
        """
        Test that `--no_abort_on_warnings` is threaded through to
        `_compile_typst()`.
        """
        # Prepare inputs.
        in_file_path = self.helper1()
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
            self.helper(argv)
        # Check outputs.
        self.assertEqual(
            mock_compile.call_args.kwargs["abort_on_warnings"], False
        )

    def test7(self) -> None:
        """
        Test that `render_images` runs by default.
        """
        # Prepare inputs.
        in_file_path = self.helper1()
        argv = [
            "run_typst.py",
            "--input",
            in_file_path,
            "--skip_action",
            "open_pdf",
        ]
        # Run test.
        with (
            mock.patch.object(dshtruty, "_compile_typst"),
            mock.patch.object(dshtruty, "_render_images") as mock_render,
        ):
            self.helper(argv)
        # Check outputs.
        self.assertEqual(mock_render.call_count, 1)
