#!/usr/bin/env python
"""
Unit tests for lib_notes_to_pdf.py.

Tests the markdown to PDF/HTML/slides conversion pipeline functions
including pandoc orchestration, file operations, and system calls.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from unittest import mock

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.documentation.lib_notes_to_pdf as dshdlntpd


# #############################################################################
# Test_preprocess_notes
# #############################################################################


class Test_preprocess_notes(hunitest.TestCase):
    """
    Test `preprocess_notes()` function.
    """

    def test1(self) -> None:
        """
        Test preprocess command construction.
        """
        # Prepare inputs.
        file_name = "input.txt"
        prefix = "tmp.pandoc"
        type_ = "pdf"
        toc_type = "pandoc_native"
        output_format = "latex"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            result = dshdlntpd.preprocess_notes(
                file_name, prefix, type_, toc_type, output_format
            )
        # Check outputs.
        expected_result = f"{prefix}.preprocess_notes.txt"
        self.assert_equal(result, expected_result)
        expected_str = r"""
        [
        {
        'function': hsystem.system_to_string,
        'args': ('find $GIT_ROOT \\( -path \'*/.git\' -o -path \'*/.mypy_cache\' \\) -prune -o -name "preprocess_notes.py" -print',),
        'kwargs': {},
        },
        {
        'function': hsystem.system,
        'args': (' --input input.txt --output tmp.pandoc.preprocess_notes.txt --type pdf --toc_type pandoc_native --output_format latex',),
        'kwargs': {'log_level': 10, 'suppress_output': False},
        },
        ]
        """
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
        )


# #############################################################################
# Test_render_images
# #############################################################################


class Test_render_images(hunitest.TestCase):
    """
    Test `render_images()` function.
    """

    def test1(self) -> None:
        """
        Test render images command construction.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "notes.txt")
        prefix = os.path.join(scratch_dir, "tmp.notes")
        file2 = f"{prefix}.render_image.txt"
        hio.to_file(file_name, "# Notes\n\n![image](test.png)")
        hio.to_file(file2, "# Notes\n\n![image](test.png)")
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            result = dshdlntpd.render_images(file_name, prefix)
        # Check outputs.
        expected_result = f"{prefix}.render_image2.txt"
        self.assert_equal(result, expected_result)
        git_root = hgit.find_git_root()
        # We use a dictionary and we convert it since there are info to
        # plug in.
        expected_sys_calls = [
            {
                "function": "hsystem.system_to_string",
                "args": (
                    f"find {git_root} "
                    r"\( -path '*/.git' -o -path '*/.mypy_cache' \) -prune "
                    '-o -name "render_images.py" -print',
                ),
                "kwargs": {},
            },
            {
                "function": "hsystem.system",
                "args": (
                    f" --input {file_name} --output {file2} --action render",
                ),
                "kwargs": {"log_level": logging.DEBUG, "suppress_output": False},
            },
        ]
        expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )


# #############################################################################
# Test_run_pandoc_to_ast
# #############################################################################


class Test_run_pandoc_to_ast(hunitest.TestCase):
    """
    Test `_run_pandoc_to_ast()` function.
    """

    def helper(
        self,
        file_in: str,
        fail_on_warnings: bool,
    ) -> None:
        """
        Test helper for _run_pandoc_to_ast.

        :param file_in: Input markdown file
        :param fail_on_warnings: Whether to fail on warnings
        """
        # Prepare inputs.
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            # Mock hdbg: prevents dassert_path_exists() from failing when pandoc
            # output files don't exist (since we're not actually running pandoc).
            # These are unit tests that verify command construction, not execution.
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                result = dshdlntpd._run_pandoc_to_ast(
                    file_in,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    fail_on_warnings=fail_on_warnings,
                )
        # Check outputs.
        ast_file = f"{file_in}.ast.json"
        self.assert_equal(result, ast_file)
        cmd = f"pandoc {file_in} -t json"
        if fail_on_warnings:
            cmd += " --fail-if-warnings"
        cmd += f" -o {ast_file}"
        # We use a dictionary and we convert it since there are info to
        # plug in.
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": (cmd,),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False, "print_command": True,
                },
            },
        ]
        expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test1(self) -> None:
        """
        Test pandoc to AST conversion with host tools.
        """
        # Prepare inputs.
        file_in = "input.md"
        fail_on_warnings = True
        # Run test.
        self.helper(file_in, fail_on_warnings)

    def test2(self) -> None:
        """
        Test pandoc to AST without fail-on-warnings.
        """
        # Prepare inputs.
        file_in = "input.md"
        fail_on_warnings = False
        # Run test.
        self.helper(file_in, fail_on_warnings)


# #############################################################################
# Test_run_pandoc_from_ast
# #############################################################################


class Test_run_pandoc_from_ast(hunitest.TestCase):
    """
    Test `_run_pandoc_from_ast()` function.
    """

    def helper(
        self,
        output_format: str,
        *,
        extra_opts: Optional[List[str]] = None,
    ) -> None:
        """
        Test helper for _run_pandoc_from_ast.

        :param output_format: Output format (latex, html, etc)
        :param extra_opts: Additional pandoc options
        """
        # Prepare inputs.
        ast_file = "input.ast.json"
        output_file = f"output.{output_format}"
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        if extra_opts is None:
            extra_opts = []
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            # Mock hdbg: prevents dassert_path_exists() from failing when output
            # files don't exist (since we're not actually running pandoc).
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                dshdlntpd._run_pandoc_from_ast(
                    ast_file,
                    output_format,
                    output_file,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    extra_opts=extra_opts,
                )
        # Check outputs.
        cmd = f"pandoc {ast_file} -f json -t {output_format} --fail-if-warnings"
        for opt in extra_opts:
            cmd += f" {opt}"
        cmd += f" -o {output_file}"
        # We use a dictionary and we convert it since there are info to
        # plug in.
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": (cmd,),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False, "print_command": True,
                },
            },
        ]
        expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test1(self) -> None:
        """
        Test convert AST to LaTeX format.
        """
        # Prepare inputs.
        output_format = "latex"
        # Run test.
        self.helper(output_format)

    def test2(self) -> None:
        """
        Test convert AST to HTML format.
        """
        # Prepare inputs.
        output_format = "html"
        # Run test.
        self.helper(output_format)

    def test3(self) -> None:
        """
        Test apply extra options to command.
        """
        # Prepare inputs.
        output_format = "latex"
        extra_opts = ["--number-sections", "--toc"]
        # Run test.
        self.helper(output_format, extra_opts=extra_opts)


# #############################################################################
# Test_run_pandoc_to_pdf
# #############################################################################


class Test_run_pandoc_to_pdf(hunitest.TestCase):
    """
    Test `run_pandoc_to_pdf()` function for PDF generation.
    """

    def helper(
        self,
        toc_type: str,
        no_pdf: bool,
        expected: str,
        *,
        prefix_suffix: str = "tmp.pdf",
    ) -> str:
        """
        Test helper for run_pandoc_to_pdf.

        :param toc_type: Type of table of contents
        :param no_pdf: Whether to only generate TeX
        :param expected: Expected invocation string
        :param prefix_suffix: Suffix for the prefix path (e.g., "tmp.pdf")
        :return: Result from run_pandoc_to_pdf
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        curr_path = scratch_dir
        file_name = os.path.join(scratch_dir, "input.txt")
        prefix = os.path.join(scratch_dir, prefix_suffix)
        no_run_latex_again = False
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Create template file.
        template_file = os.path.join(curr_path, "pandoc.latex")
        hio.to_file(template_file, "LaTeX template")
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            # Mock hdbg: prevents dassert_file_exists() from failing when
            # latex_abbrevs.sty or template files don't exist at expected paths.
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                result = dshdlntpd.run_pandoc_to_pdf(
                    curr_path,
                    file_name,
                    prefix,
                    toc_type,
                    no_run_latex_again,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    no_pdf=no_pdf,
                )
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected)
        return result

    def test1(self) -> None:
        """
        Test single-shot pandoc to PDF conversion.
        """
        # Prepare inputs.
        toc_type = "none"
        no_pdf = False
        expected = r"""
        [
        {'function': hsystem.system,
        'args': ('pandoc $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/input.txt -V geometry:margin=1in -f markdown --number-sections --highlight-style=tango -s --fail-if-warnings -t latex --template $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/pandoc.latex -o $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/tmp.pdf.tex',),
        'kwargs': {'log_level': 10, 'suppress_output': False}, },
        {'function': hsystem.system_to_string,
        'args': ('find $GIT_ROOT \\( -path \'*/.git\' -o -path \'*/.mypy_cache\' \\) -prune -o -name "dev_scripts_helpers" -print',),
        'kwargs': {}, },
        {'function': hsystem.system,
        'args': ('cp -f documentation/latex_abbrevs.sty $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch',),
        'kwargs': {'log_level': 10, 'suppress_output': False}, },
        {'function': hsystem.system,
        'args': ('pdflatex -output-directory $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch -interaction=nonstopmode -halt-on-error -shell-escape $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/tmp.pdf.tex',),
        'kwargs': {'log_level': 10, 'suppress_output': False}, },]
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(toc_type, no_pdf, expected)

    def test2(self) -> None:
        """
        Test return TeX file when no_pdf=True.
        """
        # Prepare inputs.
        toc_type = "none"
        no_pdf = True
        expected = r"""
        [
        {'function': hsystem.system,
        'args': ('pandoc $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test2/tmp.scratch/input.txt -V geometry:margin=1in -f markdown --number-sections --highlight-style=tango -s --fail-if-warnings -t latex --template $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test2/tmp.scratch/pandoc.latex -o $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test2/tmp.scratch/tmp.pdf.tex',),
        'kwargs': {'log_level': 10, 'suppress_output': False}, },]
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(toc_type, no_pdf, expected, prefix_suffix="tmp.pdf")

    def test3(self) -> None:
        """
        Test table of contents inclusion.
        """
        # Prepare inputs.
        toc_type = "pandoc_native"
        no_pdf = True
        expected = r"""
        [
        {'function': hsystem.system,
        'args': ('pandoc $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test3/tmp.scratch/input.txt -V geometry:margin=1in -f markdown --number-sections --highlight-style=tango -s --fail-if-warnings -t latex --template $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test3/tmp.scratch/pandoc.latex -o $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test3/tmp.scratch/tmp.pdf.tex --toc --toc-depth 2',),
        'kwargs': {'log_level': 10, 'suppress_output': False}, },]
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(toc_type, no_pdf, expected)


# #############################################################################
# Test_run_pandoc_to_html
# #############################################################################


class Test_run_pandoc_to_html(hunitest.TestCase):
    """
    Test `run_pandoc_to_html()` function for HTML generation.
    """

    def helper(
        self,
        file_in: str,
        toc_type: str,
        expected: str,
    ) -> None:
        """
        Test helper for run_pandoc_to_html.

        :param file_in: Input markdown file
        :param toc_type: Type of table of contents
        :param expected: Expected invocation string
        """
        # Prepare inputs.
        prefix = "tmp"
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            # Mock hdbg: prevents dassert_path_exists() from failing when HTML
            # output file doesn't exist (since we're not actually running pandoc).
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                result = dshdlntpd.run_pandoc_to_html(
                    file_in,
                    prefix,
                    toc_type,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                )
        # Check outputs.
        self.assert_equal(
            result, "$GIT_ROOT/tmp.html", fuzzy_match=True, purify_text=True
        )
        sys_calls_str = repr(sys_calls)
        self.assert_equal(
            sys_calls_str,
            expected,
            fuzzy_match=True,
            dedent=True,
            purify_text=True,
        )

    def test1(self) -> None:
        """
        Test single-shot pandoc to HTML conversion.
        """
        # Prepare inputs.
        file_in = "input.md"
        toc_type = "none"
        expected = r"""
        [
        {'function': 'hsystem.system',
        'args': ("pandoc input.md -V geometry:margin=1in -f markdown --number-sections --highlight-style=tango -s --fail-if-warnings -t html --metadata pagetitle='input.md' -o tmp.html",),
        'kwargs': {'log_level': 10, 'suppress_output': False},},]
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(file_in, toc_type, expected)

    def test2(self) -> None:
        """
        Test HTML with table of contents.
        """
        # Prepare inputs.
        file_in = "input.md"
        toc_type = "pandoc_native"
        expected = r"""
        [
        {'function': 'hsystem.system',
        'args': ("pandoc input.md -V geometry:margin=1in -f markdown --number-sections --highlight-style=tango -s --fail-if-warnings -t html --metadata pagetitle='input.md' -o tmp.html --toc --toc-depth 2",),
        'kwargs': {'log_level': 10, 'suppress_output': False},},]
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(file_in, toc_type, expected)

    def test3(self) -> None:
        """
        Test metadata pagetitle included.
        """
        # Prepare inputs.
        file_in = "notes.md"
        toc_type = "none"
        expected = r"""
        [
        {'function': 'hsystem.system',
        'args': ("pandoc notes.md -V geometry:margin=1in -f markdown --number-sections --highlight-style=tango -s --fail-if-warnings -t html --metadata pagetitle='notes.md' -o tmp.html",),
        'kwargs': {'log_level': 10, 'suppress_output': False},},]
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(file_in, toc_type, expected)


# #############################################################################
# Test_build_pandoc_latex_cmd
# #############################################################################


class Test_build_pandoc_latex_cmd(hunitest.TestCase):
    """
    Test `_build_pandoc_latex_cmd()` function for slide command building.
    """

    def helper(
        self,
        file_name: str,
        no_pdf: bool,
        expected: str,
        expected_ext: str,
        *,
        toc_type: str = "none",
    ) -> None:
        """
        Test helper for _build_pandoc_latex_cmd.

        :param file_name: Input slide file
        :param no_pdf: Whether to output TeX instead of PDF
        :param expected: Expected pandoc command
        :param expected_ext: Expected output file extension
        :param toc_type: Type of table of contents
        """
        # Prepare inputs.
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test.
        cmd, output_file = dshdlntpd._build_pandoc_latex_cmd(
            file_name,
            toc_type,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            no_pdf=no_pdf,
        )
        # Check outputs.
        self.assert_equal(output_file, expected_ext, fuzzy_match=True)
        self.assert_equal(cmd, expected, fuzzy_match=True, dedent=True)

    def test1(self) -> None:
        """
        Test build beamer PDF command.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        no_pdf = False
        expected_ext = "slides.pdf"
        expected = "pandoc slides.txt -t beamer --slide-level 4 -V theme:SimplePlus --include-in-header=latex_abbrevs.sty --fail-if-warnings --resource-path=. -o slides.pdf"
        # Run test.
        self.helper(file_name, no_pdf, expected, expected_ext)

    def test2(self) -> None:
        """
        Test build beamer TeX command.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        no_pdf = True
        expected_ext = "slides.tex"
        expected = "pandoc slides.txt -t beamer --slide-level 4 -V theme:SimplePlus --include-in-header=latex_abbrevs.sty --fail-if-warnings --resource-path=. -o slides.tex"
        # Run test.
        self.helper(file_name, no_pdf, expected, expected_ext)

    def test3(self) -> None:
        """
        Test resource path inclusion.
        """
        # Prepare inputs.
        file_name = "subdir/slides.txt"
        no_pdf = False
        expected_ext = "subdir/slides.pdf"
        expected = "pandoc subdir/slides.txt -t beamer --slide-level 4 -V theme:SimplePlus --include-in-header=latex_abbrevs.sty --fail-if-warnings --resource-path=subdir -o subdir/slides.pdf"
        # Run test.
        self.helper(file_name, no_pdf, expected, expected_ext)

    def test4(self) -> None:
        """
        Test table of contents in slides.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        no_pdf = False
        expected_ext = "slides.pdf"
        expected = "pandoc slides.txt -t beamer --slide-level 4 -V theme:SimplePlus --include-in-header=latex_abbrevs.sty --fail-if-warnings --resource-path=. --toc --toc-depth 2 -o slides.pdf"
        # Run test.
        self.helper(
            file_name, no_pdf, expected, expected_ext, toc_type="pandoc_native"
        )


# #############################################################################
# Test_run_pandoc_to_slides
# #############################################################################


class Test_run_pandoc_to_slides(hunitest.TestCase):
    """
    Test `run_pandoc_to_latex_slides()` function for slide generation.
    """

    def helper(
        self,
        toc_type: str,
        no_pdf: bool,
        expected_ext: str,
    ) -> None:
        """
        Test helper for run_pandoc_to_latex_slides.

        :param toc_type: Type of table of contents
        :param no_pdf: Whether to only generate TeX
        :param expected_ext: Expected file extension
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "slides.txt")
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            # Mock hdbg: prevents dassert_path_exists() from failing when slide
            # output files (PDF/TeX) don't exist (not actually running pandoc).
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                result = dshdlntpd.run_pandoc_to_latex_slides(
                    file_name,
                    toc_type,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    no_pdf=no_pdf,
                )
        # Check outputs.
        file_out = file_name.replace(".txt", expected_ext)
        self.assert_equal(result, file_out)
        rel_path = os.path.relpath(os.path.dirname(file_name), os.getcwd())
        cmd = (
            f"pandoc {file_name} -t beamer --slide-level 4"
            " -V theme:SimplePlus --include-in-header=latex_abbrevs.sty"
            " --fail-if-warnings"
            f" --resource-path={rel_path}"
        )
        if toc_type == "pandoc_native":
            cmd += " --toc --toc-depth 2"
        cmd += f" -o {file_out}"
        expected_sys_calls = [
            {
                "function": "hsystem.system_to_string",
                "args": (cmd,),
                "kwargs": {"log_level": logging.DEBUG, "abort_on_error": False},
            },
        ]
        expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )

    def test1(self) -> None:
        """
        Test generate PDF slides with single-shot pandoc.
        """
        # Prepare inputs.
        toc_type = "none"
        no_pdf = False
        expected_ext = ".pdf"
        # Run test.
        self.helper(toc_type, no_pdf, expected_ext)

    def test2(self) -> None:
        """
        Test return TeX file when no_pdf=True.
        """
        # Prepare inputs.
        toc_type = "none"
        no_pdf = True
        expected_ext = ".tex"
        # Run test.
        self.helper(toc_type, no_pdf, expected_ext)


# #############################################################################
# Test_run_pandoc_to_typst_slides
# #############################################################################


class Test_run_pandoc_to_typst_slides(hunitest.TestCase):
    """
    Test `run_pandoc_to_typst_slides()` function for Typst slide generation.
    """

    @staticmethod
    def _find_file_side_effect(real_dev_scripts_helpers_dir: str) -> Any:
        """
        Build a `hgit.find_file()` stand-in used inside the mocked context.

        `_extract_latex_math_defs()` needs the real `dev_scripts_helpers` dir
        to read the real `latex_abbrevs.sty` content; every other lookup
        (e.g., `convert_pandoc_divved_fence.py`) is only used to build a
        command string that is captured, never executed, so it is echoed
        back unchanged.
        """

        def _side_effect(file_name_: str) -> str:
            if file_name_ == "dev_scripts_helpers":
                return real_dev_scripts_helpers_dir
            return file_name_

        return _side_effect

    @staticmethod
    def _build_expected_sys_calls(
        curr_path: str, file_name: str, typ_file: str, typst_only: bool
    ) -> List[Dict[str, Any]]:
        """
        Build the sys_calls expected from `run_pandoc_to_typst_slides()`.
        """
        file_with_defs = f"{file_name}.with_defs.txt"
        ast_file = f"{file_with_defs}.ast.json"
        transformed_ast_file = f"{file_name}.divved.ast.json"
        template = f"{curr_path}/pandoc_touying.typ"
        rel_path = os.path.relpath(os.path.dirname(file_name), os.getcwd())
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": (
                    f"pandoc {file_with_defs} -t json --fail-if-warnings"
                    f" -o {ast_file}",
                ),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False, "print_command": True,
                },
            },
            {
                "function": "hsystem.system",
                "args": (
                    f"convert_pandoc_divved_fence.py -i {ast_file}"
                    f" -o {transformed_ast_file}",
                ),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False,
                },
            },
            {
                "function": "hsystem.system",
                "args": (
                    f"pandoc {transformed_ast_file} -f json -t typst"
                    " --fail-if-warnings --number-sections -s"
                    f" --template {template} --resource-path={rel_path}"
                    f" -o {typ_file}",
                ),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False, "print_command": True,
                },
            },
        ]
        if not typst_only:
            pdf_file = typ_file.replace(".typ", ".pdf")
            root = os.getcwd()
            expected_sys_calls.append(
                {
                    "function": "hsystem.system",
                    "args": (
                        f"typst compile --root {root} {typ_file} {pdf_file}",
                    ),
                    "kwargs": {
                        "log_level": logging.DEBUG,
                        "suppress_output": False,
                    },
                }
            )
        return expected_sys_calls

    def helper(
        self,
        typst_only: bool,
        expected_ext: str,
    ) -> None:
        """
        Test helper for run_pandoc_to_typst_slides.

        :param typst_only: Whether to only generate Typst
        :param expected_ext: Expected file extension
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        curr_path = scratch_dir
        file_name = os.path.join(scratch_dir, "slides.txt")
        hio.to_file(file_name, "# Slides\n\nContent")
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Create template file.
        template_file = os.path.join(curr_path, "pandoc_touying.typ")
        hio.to_file(template_file, "Typst template")
        # Create the intermediate `.typ` file that the (mocked) pandoc call
        # would have produced, since `run_pandoc_to_typst_slides()` reads it
        # back for real to rewrite image paths.
        typ_file = file_name.replace(".txt", ".typ")
        hio.to_file(typ_file, "placeholder typst content")
        # Resolve the real `dev_scripts_helpers` dir before entering the
        # system-call-capturing context, since `hgit.find_file()` itself goes
        # through a system call that we are about to mock out.
        real_dev_scripts_helpers_dir = hgit.find_file("dev_scripts_helpers")
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            # Mock hdbg: prevents dassert_* from failing when output files don't
            # exist (Typst/PDF generation not actually run).
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                # Mock hgit.find_file() only (not the whole module): it needs
                # to keep returning the real `dev_scripts_helpers` dir so
                # `_extract_latex_math_defs()` can read the real
                # `latex_abbrevs.sty`.
                with mock.patch.object(
                    dshdlntpd.hgit,
                    "find_file",
                    side_effect=self._find_file_side_effect(
                        real_dev_scripts_helpers_dir
                    ),
                ):
                    # Mock dshdlity: skips Typst infrastructure/pipeline operations
                    # that require external tools and project-specific configuration.
                    with mock.patch(
                        "dev_scripts_helpers.documentation.lib_notes_to_pdf.dshdlity"
                    ):
                        result = dshdlntpd.run_pandoc_to_typst_slides(
                            curr_path,
                            file_name,
                            use_host_tools,
                            dockerized_force_rebuild,
                            dockerized_use_sudo,
                            typst_only=typst_only,
                        )
        # Check outputs.
        self.assert_equal(result, file_name.replace(".txt", expected_ext))
        expected_sys_calls = self._build_expected_sys_calls(
            curr_path, file_name, typ_file, typst_only
        )
        expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )

    def test1(self) -> None:
        """
        Test Typst 3-stage pipeline stages.
        """
        # Prepare inputs.
        typst_only = False
        expected_ext = ".pdf"
        # Run test.
        self.helper(typst_only, expected_ext)

    def test2(self) -> None:
        """
        Test return .typ file when typst_only=True.
        """
        # Prepare inputs.
        typst_only = True
        expected_ext = ".typ"
        # Run test.
        self.helper(typst_only, expected_ext)

    def test3(self) -> None:
        """
        Test image path conversion to root-absolute.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        curr_path = scratch_dir
        file_name = os.path.join(scratch_dir, "slides.txt")
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        typst_only = False
        hio.to_file(file_name, "# Slides\n\nContent")
        template_file = os.path.join(curr_path, "pandoc_touying.typ")
        hio.to_file(template_file, "Typst template")
        typ_file = file_name.replace(".txt", ".typ")
        image_content = 'image("path/to/image.png")'
        hio.to_file(typ_file, image_content)
        real_dev_scripts_helpers_dir = hgit.find_file("dev_scripts_helpers")
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                with mock.patch.object(
                    dshdlntpd.hgit,
                    "find_file",
                    side_effect=self._find_file_side_effect(
                        real_dev_scripts_helpers_dir
                    ),
                ):
                    with mock.patch(
                        "dev_scripts_helpers.documentation.lib_notes_to_pdf.dshdlity"
                    ):
                        result = dshdlntpd.run_pandoc_to_typst_slides(
                            curr_path,
                            file_name,
                            use_host_tools,
                            dockerized_force_rebuild,
                            dockerized_use_sudo,
                            typst_only=typst_only,
                        )
        # Check outputs.
        expected_result = file_name.replace(".txt", ".pdf")
        self.assert_equal(result, expected_result)
        expected_typ_content = 'image("/path/to/image.png")'
        actual_typ_content = hio.from_file(typ_file)
        self.assert_equal(actual_typ_content, expected_typ_content)
        expected_str = r"""[
        {
        'function': hsystem.system,
        'args': ('pandoc $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_typst_slides.test3/tmp.scratch/slides.txt -f markdown --number-sections -s -t typst --template $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_typst_slides.test3/tmp.scratch/pandoc_touying.typ --resource-path=dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_typst_slides.test3/tmp.scratch -o $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_typst_slides.test3/tmp.scratch/slides.typ',),
        'kwargs': {'log_level': 10, 'suppress_output': False},
        },
        {
        'function': hsystem.system,
        'args': ('typst compile --root $GIT_ROOT/helpers_root $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_typst_slides.test3/tmp.scratch/slides.typ $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_typst_slides.test3/tmp.scratch/slides.pdf',),
        'kwargs': {'log_level': 10, 'suppress_output': False},
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )


# #############################################################################
# Test_copy_to_output
# #############################################################################


class Test_copy_to_output(hunitest.TestCase):
    """
    Test `copy_to_output()` function.
    """

    def test1(self) -> None:
        """
        Test copy file to output location.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_in = os.path.join(scratch_dir, "source.txt")
        hio.to_file(file_in, "content")
        output = os.path.join(scratch_dir, "output.txt")
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            result = dshdlntpd.copy_to_output(file_in, output)
        # Check outputs.
        self.assert_equal(result, output)
        expected_str = r"""
        [
        {
        'function': hsystem.system,
        'args': ('\\cp -af $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_copy_to_output.test1/tmp.scratch/source.txt $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_copy_to_output.test1/tmp.scratch/output.txt',),
        'kwargs': {'log_level': 10, 'suppress_output': False},
        },
        ]
        """
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )

    def test2(self) -> None:
        """
        Test output path is required (not None).
        """
        # Prepare inputs.
        file_in = "source.txt"
        output = None
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dshdlntpd.copy_to_output(file_in, output)  # type: ignore


# #############################################################################
# Test_copy_to_gdrive
# #############################################################################


class Test_copy_to_gdrive(hunitest.TestCase):
    """
    Test `copy_to_gdrive()` function.
    """

    def helper(
        self,
        ext: str,
        input_: str,
    ) -> None:
        """
        Test helper for copy_to_gdrive.

        :param ext: File extension
        :param input_: Input filename
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, f"output.{ext}")
        hio.to_file(file_name, "content")
        gdrive_dir = scratch_dir
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshdlntpd.copy_to_gdrive(file_name, ext, input_, gdrive_dir)
        # Check outputs.
        basename = os.path.basename(input_).replace(".txt", "." + ext)
        dst_file = os.path.join(gdrive_dir, basename)
        # We use a dictionary and we convert it since there are info to plug
        # in.
        expected_sys_calls = [
            {
                "function": "hsystem.system",
                "args": (rf"\cp -af {file_name} {dst_file}",),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False,
                },
            },
        ]
        expected_str = hunteuti._sys_calls_to_str(expected_sys_calls)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )

    def test1(self) -> None:
        """
        Test copy to specified Google Drive directory.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "output.pdf")
        hio.to_file(file_name, "content")
        gdrive_dir = scratch_dir
        ext = "pdf"
        input_ = "notes.txt"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshdlntpd.copy_to_gdrive(file_name, ext, input_, gdrive_dir)
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system,
        'args': ('\\cp -af $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_copy_to_gdrive.test1/tmp.scratch/output.pdf $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_copy_to_gdrive.test1/tmp.scratch/notes.pdf',),
        'kwargs': {'log_level': 10, 'suppress_output': False},
        },
        ]"""
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )


# #############################################################################
# Test_compress_pdf
# #############################################################################


class Test_compress_pdf(hunitest.TestCase):
    """
    Test `compress_pdf()` function.
    """

    def test1(self) -> None:
        """
        Test system calls for PDF compression.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        pdf_file = os.path.join(scratch_dir, "document.pdf")
        hio.to_file(pdf_file, "PDF content")
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as sys_calls:
            result = dshdlntpd.compress_pdf(pdf_file)
        # Check outputs.
        self.assert_equal(result, pdf_file)
        expected_str = r"""[
        {
        'function': hsystem.system,
        'args': ('/opt/homebrew/bin/gs -sDEVICE=pdfwrite -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH -sOutputFile=$GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_compress_pdf.test1/tmp.scratch/compressed-document.pdf $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_compress_pdf.test1/tmp.scratch/document.pdf',),
        'kwargs': {'log_level': 10, 'suppress_output': False},
        },
        {
        'function': hsystem.system,
        'args': ('mv $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_compress_pdf.test1/tmp.scratch/compressed-document.pdf $GIT_ROOT/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_compress_pdf.test1/tmp.scratch/document.pdf',),
        'kwargs': {'log_level': 10, 'suppress_output': False},
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )
