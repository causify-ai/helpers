#!/usr/bin/env python
"""
Unit tests for lib_notes_to_pdf.py.

Tests the markdown to PDF/HTML/slides conversion pipeline functions
including pandoc orchestration, file operations, and system calls.
"""

import logging
import os
import pprint
from typing import Any, Dict, List
from unittest import mock

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.documentation.lib_notes_to_pdf as dshdlntpd

_LOG = logging.getLogger(__name__)


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
        with hunteuti.capture_sys_calls() as invocations:
            result = dshdlntpd._preprocess_notes(
                file_name, prefix, type_, toc_type
            )
        # Check outputs.
        expected_result = f"{prefix}.preprocess_notes.txt"
        self.assert_equal(result, expected_result)
        git_root = hgit.find_git_root()
        expected_invocations = [
            {
                "function": "hsystem.system_to_string",
                "args": (
                    f"find {git_root} "
                    r"\( -path '*/.git' -o -path '*/.mypy_cache' \) -prune "
                    '-o -name "preprocess_notes.py" -print',
                ),
                "kwargs": {},
            },
            {
                "function": "hsystem.system",
                "args": (
                    f" --input {file_name} --output"
                    f" {prefix}.preprocess_notes.txt --type {type_}"
                    f" --toc_type {toc_type} --output_format {output_format}",
                ),
                "kwargs": {"log_level": logging.DEBUG, "suppress_output": False},
            },
        ]
        expected_str = pprint.pformat(expected_invocations)
        hunteuti.assert_sys_calls(
            self,
            invocations,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
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
        with hunteuti.capture_sys_calls() as invocations:
            result = dshdlntpd._render_images(file_name, prefix)
        # Check outputs.
        expected_result = f"{prefix}.render_image2.txt"
        self.assert_equal(result, expected_result)
        git_root = hgit.find_git_root()
        expected_invocations = [
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
        expected_str = pprint.pformat(expected_invocations)
        hunteuti.assert_sys_calls(
            self,
            invocations,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )


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
        with hunteuti.capture_sys_calls() as invocations:
            # Mock hdbg: prevents dassert_file_exists() from failing when
            # latex_abbrevs.sty or template files don't exist at expected paths.
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                result = dshdlntpd._run_pandoc_to_pdf(
                    curr_path,
                    file_name,
                    prefix,
                    toc_type,
                    no_run_latex_again,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    tex_only=no_pdf,
                )
        # Check outputs.
        invocations_str = hunteuti.sys_calls_to_str(invocations)
        self.assert_equal(
            invocations_str,
            expected,
            fuzzy_match=True,
            dedent=True,
            purify_text=True,
        )
        return result

    def test1(self) -> None:
        """
        Test single-shot pandoc to PDF conversion.
        """
        # Prepare inputs.
        toc_type = "none"
        no_pdf = False
        # TODO(ai_gp): Make it look better and add dedent
        expected = r"""
        [{'args': ('pandoc '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/input.txt '
'-V geometry:margin=1in -f markdown --number-sections '
'--highlight-style=tango -s --fail-if-warnings -t latex --template '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/pandoc.latex '
'-o '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/tmp.pdf.tex',),
'function': 'hsystem.system',
'kwargs': {'log_level': 10, 'suppress_output': False}},
{'args': ('find $GIT_ROOT \\( -path '
"'*/.git' -o -path '*/.mypy_cache' \\) -prune -o -name "
'"dev_scripts_helpers" -print',),
'function': 'hsystem.system_to_string',
'kwargs': {}},
{'args': ('cp -f documentation/latex_abbrevs.sty '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch',),
'function': 'hsystem.system',
'kwargs': {'log_level': 10, 'suppress_output': False}},
{'args': ('pdflatex -output-directory '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch '
'-interaction=nonstopmode -halt-on-error -shell-escape '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test1/tmp.scratch/tmp.pdf.tex',),
'function': 'hsystem.system',
'kwargs': {'log_level': 10, 'suppress_output': False}}]
        """
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
        [{'args': ('pandoc '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test2/tmp.scratch/input.txt '
'-V geometry:margin=1in -f markdown --number-sections '
'--highlight-style=tango -s --fail-if-warnings -t latex --template '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test2/tmp.scratch/pandoc.latex '
'-o '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test2/tmp.scratch/tmp.tex.tex',),
'function': 'hsystem.system',
'kwargs': {'log_level': 10, 'suppress_output': False}}]
        """
        # Run test.
        result = self.helper(toc_type, no_pdf, expected, prefix_suffix="tmp.tex")
        # Check outputs.
        expected_result = r"$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test2/tmp.scratch/tmp.tex.tex"
        self.assert_equal(
            result, expected_result, fuzzy_match=True, purify_text=True
        )

    def test3(self) -> None:
        """
        Test table of contents inclusion.
        """
        # Prepare inputs.
        toc_type = "pandoc_native"
        no_pdf = True
        expected = r"""
        [{'args': ('pandoc '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test3/tmp.scratch/input.txt '
'-V geometry:margin=1in -f markdown --number-sections '
'--highlight-style=tango -s --fail-if-warnings -t latex --template '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test3/tmp.scratch/pandoc.latex '
'-o '
'$GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_run_pandoc_to_pdf.test3/tmp.scratch/tmp.pdf.tex '
'--toc --toc-depth 2',),
'function': 'hsystem.system',
'kwargs': {'log_level': 10, 'suppress_output': False}}]
        """
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
        with hunteuti.capture_sys_calls() as invocations:
            # Mock hdbg: prevents dassert_path_exists() from failing when HTML
            # output file doesn't exist (since we're not actually running pandoc).
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                result = dshdlntpd._run_pandoc_to_html(
                    file_in,
                    prefix,
                    toc_type,
                )
        # Check outputs.
        self.assert_equal(result, "$GIT_ROOT/tmp.html", fuzzy_match=True, purify_text=True)
        invocations_str = hunteuti.sys_calls_to_str(invocations)
        self.assert_equal(
            invocations_str,
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
        [{'args': ('pandoc input.md -V geometry:margin=1in -f markdown '
                   '--number-sections --highlight-style=tango -s --fail-if-warnings -t '
                   "html --metadata pagetitle='input.md' -o tmp.html",),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 10, 'suppress_output': False}}]
        """
        # Run test.
        self.helper(file_in, toc_type, expected)

    def test2(self) -> None:
        """
        Test HTML with table of contents.
        """
        # Prepare inputs.
        file_in = "input.md"
        toc_type = "pandoc_native"
        # TODO(ai_gp): Make it look better and use dedent.
        expected = r"""
        [{'args': ('pandoc input.md -V geometry:margin=1in -f markdown '
'--number-sections --highlight-style=tango -s --fail-if-warnings -t '
"html --metadata pagetitle='input.md' -o tmp.html --toc --toc-depth "
'2',),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 10, 'suppress_output': False}}]
        """
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
        [{'args': ('pandoc notes.md -V geometry:margin=1in -f markdown '
                   '--number-sections --highlight-style=tango -s --fail-if-warnings -t '
                   "html --metadata pagetitle='notes.md' -o tmp.html",),
          'function': 'hsystem.system',
          'kwargs': {'log_level': 10, 'suppress_output': False}}]
        """
        # Run test.
        self.helper(file_in, toc_type, expected)


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
    def _build_expected_invocations(
        curr_path: str, file_name: str, typ_file: str, typst_only: bool
    ) -> List[Dict[str, Any]]:
        """
        Build the invocations expected from `_run_pandoc_to_typst_slides()`.
        """
        template = f"{curr_path}/pandoc_touying.typ"
        rel_path = os.path.relpath(os.path.dirname(file_name), os.getcwd())
        expected_invocations = [
            {
                "function": "hsystem.system",
                "args": (
                    f"pandoc {file_name} -f markdown --number-sections -s"
                    f" -t typst --template {template}"
                    f" --resource-path={rel_path} -o {typ_file}",
                ),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False,
                },
            },
        ]
        if not typst_only:
            pdf_file = typ_file.replace(".typ", ".pdf")
            root = os.getcwd()
            expected_invocations.append(
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
        return expected_invocations

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
        with hunteuti.capture_sys_calls() as invocations:
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
                        result = dshdlntpd._run_pandoc_to_typst_slides(
                            curr_path,
                            file_name,
                            use_host_tools,
                            dockerized_force_rebuild,
                            dockerized_use_sudo,
                            typst_only=typst_only,
                        )
        # Check outputs.
        self.assert_equal(result, file_name.replace(".txt", expected_ext))
        expected_invocations = self._build_expected_invocations(
            curr_path, file_name, typ_file, typst_only
        )
        expected_str = pprint.pformat(expected_invocations)
        hunteuti.assert_sys_calls(
            self,
            invocations,
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
        with hunteuti.capture_sys_calls() as invocations:
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
                        result = dshdlntpd._run_pandoc_to_typst_slides(
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
        expected_invocations = self._build_expected_invocations(
            curr_path, file_name, typ_file, typst_only
        )
        expected_str = pprint.pformat(expected_invocations)
        hunteuti.assert_sys_calls(
            self,
            invocations,
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
        with hunteuti.capture_sys_calls() as invocations:
            result = dshdlntpd._copy_to_output(file_in, output)
        # Check outputs.
        self.assert_equal(result, output)
        expected_invocations = [
            {
                "function": "hsystem.system",
                "args": (rf"\cp -af {file_in} {output}",),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False,
                },
            },
        ]
        expected_str = pprint.pformat(expected_invocations)
        hunteuti.assert_sys_calls(
            self,
            invocations,
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
            dshdlntpd._copy_to_output(file_in, output)  # type: ignore


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
        with hunteuti.capture_sys_calls() as invocations:
            dshdlntpd._copy_to_gdrive(file_name, ext, input_, gdrive_dir)
        # Check outputs.
        basename = os.path.basename(input_).replace(".txt", "." + ext)
        dst_file = os.path.join(gdrive_dir, basename)
        expected_invocations = [
            {
                "function": "hsystem.system",
                "args": (rf"\cp -af {file_name} {dst_file}",),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False,
                },
            },
        ]
        expected_str = pprint.pformat(expected_invocations)
        hunteuti.assert_sys_calls(
            self,
            invocations,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )

    def test1(self) -> None:
        """
        Test copy to specified Google Drive directory.
        """
        # Prepare inputs.
        ext = "pdf"
        input_ = "notes.txt"
        # Run test.
        self.helper(ext, input_)


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
        with hunteuti.capture_sys_calls() as invocations:
            result = dshdlntpd._compress_pdf(pdf_file)
        # Check outputs.
        self.assert_equal(result, pdf_file)
        out_dir = os.path.dirname(pdf_file)
        basename = os.path.basename(pdf_file)
        compressed_file = os.path.join(out_dir, f"compressed-{basename}")
        expected_invocations = [
            {
                "function": "hsystem.system",
                "args": (
                    "/opt/homebrew/bin/gs -sDEVICE=pdfwrite"
                    " -dPDFSETTINGS=/printer -dNOPAUSE -dQUIET -dBATCH"
                    f" -sOutputFile={compressed_file} {pdf_file}",
                ),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False,
                },
            },
            {
                "function": "hsystem.system",
                "args": (f"mv {compressed_file} {pdf_file}",),
                "kwargs": {
                    "log_level": logging.DEBUG,
                    "suppress_output": False,
                },
            },
        ]
        expected_str = pprint.pformat(expected_invocations)
        hunteuti.assert_sys_calls(
            self,
            invocations,
            expected_str,
            purify_text=True,
            purify_expected_text=True,
        )
