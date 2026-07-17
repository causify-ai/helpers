import os
from typing import List
from unittest import mock

import pytest

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.run_latex as dshdrula


# #############################################################################
# Test__report_log_warnings
# #############################################################################


class Test__report_log_warnings(hunitest.TestCase):
    """
    Test the `_report_log_warnings()` function.
    """

    def helper(self, content: str, expected: List[str]) -> None:
        """
        Test helper for `_report_log_warnings()`.

        :param content: contents of the `.log` file to scan
        :param expected: warning lines expected to be extracted
        """
        # Prepare inputs.
        log_file_path = os.path.join(self.get_scratch_space(), "test.log")
        content = hprint.dedent(content)
        hio.to_file(log_file_path, content)
        # Run test.
        actual = dshdrula._report_log_warnings(log_file_path)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that `LaTeX`/`Package`/`Class` warning lines are extracted.
        """
        # Prepare inputs.
        content = """
        This is pdfTeX, Version 3.14
        LaTeX Warning: Reference `fig:1' on page 3 undefined on input line 42.
        Some other text.
        Package hyperref Warning: Token not allowed in a PDF string.
        Class article Warning: Unused option `12pt' on input line 1.
        Output written on book.pdf (10 pages).
        """
        # Prepare outputs.
        expected = [
            "LaTeX Warning: Reference `fig:1' on page 3 undefined on input line 42.",
            "Package hyperref Warning: Token not allowed in a PDF string.",
            "Class article Warning: Unused option `12pt' on input line 1.",
        ]
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test that a log file with no warnings returns an empty list.
        """
        # Prepare inputs.
        content = """
        This is pdfTeX, Version 3.14
        Output written on book.pdf (10 pages).
        """
        # Prepare outputs.
        expected: List[str] = []
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that a missing log file returns an empty list.
        """
        # Prepare inputs.
        log_file_path = os.path.join(self.get_scratch_space(), "missing.log")
        # Prepare outputs.
        expected: List[str] = []
        # Run test.
        actual = dshdrula._report_log_warnings(log_file_path)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test__copy_to_google_drive
# #############################################################################


class Test__copy_to_google_drive(hunitest.TestCase):
    """
    Test the `_copy_to_google_drive()` function.
    """

    def test1(self) -> None:
        """
        Test that the PDF is copied to both folders when they exist.
        """
        # Prepare inputs.
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        hio.to_file(out_file_path, "%PDF-1.4 fake content")
        papers_dir = os.path.join(self.get_scratch_space(), "papers")
        internal_dir = os.path.join(self.get_scratch_space(), "internal")
        hio.create_dir(papers_dir, incremental=True)
        hio.create_dir(internal_dir, incremental=True)
        # Run test.
        with mock.patch.object(dshdrula, "_GDRIVE_PAPERS_DIR", papers_dir):
            with mock.patch.object(
                dshdrula, "_GDRIVE_INTERNAL_DIR", internal_dir
            ):
                dshdrula._copy_to_google_drive(out_file_path)
        # Check outputs.
        self.assertTrue(os.path.exists(os.path.join(papers_dir, "book.pdf")))
        self.assertTrue(os.path.exists(os.path.join(internal_dir, "book.pdf")))

    def test2(self) -> None:
        """
        Test that a missing folder is skipped without raising an error.
        """
        # Prepare inputs.
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        hio.to_file(out_file_path, "%PDF-1.4 fake content")
        papers_dir = os.path.join(self.get_scratch_space(), "papers")
        hio.create_dir(papers_dir, incremental=True)
        missing_dir = os.path.join(self.get_scratch_space(), "does_not_exist")
        # Run test.
        with mock.patch.object(dshdrula, "_GDRIVE_PAPERS_DIR", papers_dir):
            with mock.patch.object(
                dshdrula, "_GDRIVE_INTERNAL_DIR", missing_dir
            ):
                dshdrula._copy_to_google_drive(out_file_path)
        # Check outputs.
        self.assertTrue(os.path.exists(os.path.join(papers_dir, "book.pdf")))
        self.assertFalse(os.path.exists(missing_dir))


# #############################################################################
# Test__compile_latex
# #############################################################################


class Test__compile_latex(hunitest.TestCase):
    """
    Test the `_compile_latex()` function.

    `dshdlila.run_basic_latex()` and `dshdlila.run_dockerized_bibtex()` are
    mocked since they require a real Docker/LaTeX toolchain; this class only
    verifies the pass/bibtex orchestration logic.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        """
        Setup and teardown for each test.
        """
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Save the current directory since `_compile_latex()` calls
        `os.chdir()`.
        """
        self._original_cwd = os.getcwd()

    def tear_down_test(self) -> None:
        """
        Restore the directory saved in `set_up_test()`.
        """
        os.chdir(self._original_cwd)

    def helper(self, num_passes: int, expected_run_latex_again: bool) -> None:
        """
        Test helper for `_compile_latex()` with 1 or 2 `pdflatex` passes.

        :param num_passes: number of `pdflatex` compilation passes
        :param expected_run_latex_again: expected `run_latex_again` value
            passed to `run_basic_latex()`
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.tex")
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        # Prepare outputs.
        expected_calls = str(
            [
                mock.call(
                    in_file_path,
                    [],
                    expected_run_latex_again,
                    out_file_path,
                    force_rebuild=False,
                    use_sudo=False,
                )
            ]
        )
        # Run test.
        with mock.patch.object(
            dshdrula.dshdlila, "run_basic_latex"
        ) as mock_run_basic_latex:
            with mock.patch.object(
                dshdrula.dshdlila, "run_dockerized_bibtex"
            ) as mock_run_bibtex:
                dshdrula._compile_latex(in_file_path, out_file_path, num_passes)
        # Check outputs.
        self.assert_equal(
            str(list(mock_run_basic_latex.call_args_list)), expected_calls
        )
        self.assertEqual(mock_run_bibtex.call_count, 0)

    def test1(self) -> None:
        """
        Test a single `pdflatex` pass.
        """
        # Prepare inputs.
        num_passes = 1
        # Prepare outputs.
        expected_run_latex_again = False
        # Run test.
        self.helper(num_passes, expected_run_latex_again)

    def test2(self) -> None:
        """
        Test two `pdflatex` passes (resolves cross-references).
        """
        # Prepare inputs.
        num_passes = 2
        # Prepare outputs.
        expected_run_latex_again = True
        # Run test.
        self.helper(num_passes, expected_run_latex_again)

    def test3(self) -> None:
        """
        Test the full 3-pass build: 2 passes, `bibtex`, then 2 more passes.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.tex")
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        bib_file_path = os.path.join(self.get_scratch_space(), "refs.bib")
        hio.to_file(bib_file_path, "@article{a, title={t}}")
        aux_file_path = os.path.join(self.get_scratch_space(), "book.aux")
        # Prepare outputs.
        expected_basic_latex_calls = str(
            [
                mock.call(
                    in_file_path,
                    [],
                    True,
                    out_file_path,
                    force_rebuild=False,
                    use_sudo=False,
                ),
                mock.call(
                    in_file_path,
                    [],
                    True,
                    out_file_path,
                    force_rebuild=False,
                    use_sudo=False,
                ),
            ]
        )
        expected_bibtex_calls = str(
            [mock.call(aux_file_path, force_rebuild=False, use_sudo=False)]
        )
        # Run test.
        with mock.patch.object(
            dshdrula.dshdlila, "run_basic_latex"
        ) as mock_run_basic_latex:
            with mock.patch.object(
                dshdrula.dshdlila, "run_dockerized_bibtex"
            ) as mock_run_bibtex:
                dshdrula._compile_latex(in_file_path, out_file_path, 3)
        # Check outputs.
        self.assert_equal(
            str(list(mock_run_basic_latex.call_args_list)),
            expected_basic_latex_calls,
        )
        self.assert_equal(
            str(list(mock_run_bibtex.call_args_list)), expected_bibtex_calls
        )

    def test4(self) -> None:
        """
        Test that `bibtex` is skipped when no `.bib` file is present.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.tex")
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        # Run test.
        with mock.patch.object(
            dshdrula.dshdlila, "run_basic_latex"
        ) as mock_run_basic_latex:
            with mock.patch.object(
                dshdrula.dshdlila, "run_dockerized_bibtex"
            ) as mock_run_bibtex:
                dshdrula._compile_latex(in_file_path, out_file_path, 3)
        # Check outputs.
        self.assertEqual(mock_run_basic_latex.call_count, 1)
        self.assertEqual(mock_run_bibtex.call_count, 0)


# #############################################################################
# Test_run_latex_py
# #############################################################################


class Test_run_latex_py(hunitest.TestCase):
    """
    End-to-end tests for the `run_latex.py` executable.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        """
        Setup and teardown for each test.
        """
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Save the current directory since `_main()` calls `os.chdir()`.
        """
        self._original_cwd = os.getcwd()

    def tear_down_test(self) -> None:
        """
        Restore the directory saved in `set_up_test()`.
        """
        os.chdir(self._original_cwd)

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `dshdrula._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshdrula._parse()
        with mock.patch("sys.argv", argv):
            dshdrula._main(parser)

    def test1(self) -> None:
        """
        Test that the default output path swaps the `.tex` extension for
        `.pdf`.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.tex")
        argv = ["run_latex.py", "--input", in_file_path]
        # Prepare outputs.
        expected_out_file_path = os.path.join(
            self.get_scratch_space(), "book.pdf"
        )
        # Run test.
        with mock.patch.object(
            dshdrula.dshdlila, "run_basic_latex"
        ) as mock_run_basic_latex:
            self._run_main(argv)
        # Check outputs.
        actual_out_file_path = mock_run_basic_latex.call_args.args[3]
        self.assertEqual(actual_out_file_path, expected_out_file_path)

    def test2(self) -> None:
        """
        Test that an explicit `--output` path is respected.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.tex")
        out_file_path = os.path.join(self.get_scratch_space(), "custom.pdf")
        argv = [
            "run_latex.py",
            "--input",
            in_file_path,
            "--output",
            out_file_path,
        ]
        # Run test.
        with mock.patch.object(
            dshdrula.dshdlila, "run_basic_latex"
        ) as mock_run_basic_latex:
            self._run_main(argv)
        # Check outputs.
        actual_out_file_path = mock_run_basic_latex.call_args.args[3]
        self.assertEqual(actual_out_file_path, out_file_path)

    def test3(self) -> None:
        """
        Test that `--open` opens the compiled PDF on macOS.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.tex")
        out_file_path = os.path.join(self.get_scratch_space(), "book.pdf")
        argv = ["run_latex.py", "--input", in_file_path, "--open"]
        # Run test.
        with mock.patch.object(dshdrula.dshdlila, "run_basic_latex"):
            with mock.patch.object(
                dshdrula.dshddout, "open_file_on_macos"
            ) as mock_open:
                self._run_main(argv)
        # Check outputs.
        mock_open.assert_called_once_with(out_file_path)

    def test4(self) -> None:
        """
        Test that `--copy_to_gdrive` triggers the Google Drive copy.
        """
        # Prepare inputs.
        in_file_path = os.path.join(self.get_scratch_space(), "book.tex")
        argv = ["run_latex.py", "--input", in_file_path, "--copy_to_gdrive"]
        # Run test.
        with mock.patch.object(dshdrula.dshdlila, "run_basic_latex"):
            with mock.patch.object(
                dshdrula, "_copy_to_google_drive"
            ) as mock_copy:
                self._run_main(argv)
        # Check outputs.
        self.assertEqual(mock_copy.call_count, 1)
