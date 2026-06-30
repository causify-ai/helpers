#!/usr/bin/env python
"""
Unit tests for lib_notes_to_pdf.py.

Tests the markdown to PDF/HTML/slides conversion pipeline functions
including pandoc orchestration, file operations, and system calls.
"""

import hashlib
import logging
import os
from typing import List, Optional
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.documentation.lib_notes_to_pdf as dshdlntpd

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_file_hash
# #############################################################################


class Test_file_hash(hunitest.TestCase):
    """
    Test `_file_hash()` function that computes MD5 hashes of files.
    """

    def helper(self, content: str) -> None:
        """
        Test helper for _file_hash.

        :param content: File content to hash
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "test.txt")
        hio.to_file(test_file, content)
        # Prepare outputs.
        expected_hash = hashlib.md5(content.encode()).hexdigest()
        # Run test.
        actual = dshdlntpd._file_hash(test_file)
        # Check outputs.
        self.assert_equal(actual, expected_hash)

    def test1(self) -> None:
        """
        Test hash of empty file.
        """
        # Prepare inputs.
        content = ""
        # Run test.
        self.helper(content)

    def test2(self) -> None:
        """
        Test hash of file with known content.
        """
        # Prepare inputs.
        content = "Hello, World!"
        # Run test.
        self.helper(content)

    def test3(self) -> None:
        """
        Test that different files produce different hashes.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "file1.txt")
        file2 = os.path.join(scratch_dir, "file2.txt")
        content1 = "Content A"
        content2 = "Content B"
        hio.to_file(file1, content1)
        hio.to_file(file2, content2)
        # Run test.
        hash1 = dshdlntpd._file_hash(file1)
        hash2 = dshdlntpd._file_hash(file2)
        # Check outputs.
        expected_hash1 = hashlib.md5(content1.encode()).hexdigest()
        expected_hash2 = hashlib.md5(content2.encode()).hexdigest()
        self.assert_equal(hash1, expected_hash1)
        self.assert_equal(hash2, expected_hash2)

    def test4(self) -> None:
        """
        Test hash of large file (>65536 bytes to exercise chunking).
        """
        # Prepare inputs.
        content = "x" * 100000
        # Run test.
        self.helper(content)

    def test5(self) -> None:
        """
        Test that same file produces same hash consistently.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "consistent.txt")
        content = "Consistent content"
        hio.to_file(test_file, content)
        # Run test.
        hash1 = dshdlntpd._file_hash(test_file)
        hash2 = dshdlntpd._file_hash(test_file)
        # Check outputs.
        self.assert_equal(hash1, hash2)


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
        with hunteuti.capture_system_calls() as invocations:
            result = dshdlntpd.preprocess_notes(
                file_name, prefix, type_, toc_type, output_format
            )
        # Check outputs.
        self.assert_equal(result, ".preprocess_notes.txt", fuzzy_match=True)
        invocations_str = hunteuti.to_invocations_str(invocations)
        expected = """
        preprocess_notes.py
        --type pdf
        --toc_type pandoc_native
        """
        self.assert_equal(
            invocations_str, expected, fuzzy_match=True, dedent=True
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
        hio.to_file(file_name, "# Notes\n\n![image](test.png)")
        prefix = os.path.join(scratch_dir, "tmp.notes")
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            result = dshdlntpd.render_images(file_name, prefix)
        self.assert_equal(result, "render_image", fuzzy_match=True)
        invocations_str = hunteuti.to_invocations_str(invocations)
        expected = "render_images.py"
        self.assert_equal(invocations_str, expected, fuzzy_match=True)


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
        expected: str,
    ) -> None:
        """
        Test helper for _run_pandoc_to_ast.

        :param file_in: Input markdown file
        :param fail_on_warnings: Whether to fail on warnings
        :param expected: Expected invocation string
        """
        # Prepare inputs.
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            # Mock hdbg to prevent assertions in pandoc wrapper functions.
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
        self.assert_equal(result, ".ast.json", fuzzy_match=True)
        invocations_str = hunteuti.to_invocations_str(invocations)
        self.assert_equal(
            invocations_str, expected, fuzzy_match=True, dedent=True
        )

    def test1(self) -> None:
        """
        Test pandoc to AST conversion with host tools.
        """
        # Prepare inputs.
        file_in = "input.md"
        fail_on_warnings = True
        expected = """
        pandoc
        -t json
        --fail-if-warnings
        """
        # Run test.
        self.helper(file_in, fail_on_warnings, expected)

    def test2(self) -> None:
        """
        Test pandoc to AST without fail-on-warnings.
        """
        # Prepare inputs.
        file_in = "input.md"
        fail_on_warnings = False
        expected = """
        pandoc
        -t json
        """
        # Run test.
        self.helper(file_in, fail_on_warnings, expected)


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
        expected: str,
        *,
        extra_opts: Optional[List[str]] = None,
    ) -> None:
        """
        Test helper for _run_pandoc_from_ast.

        :param output_format: Output format (latex, html, etc)
        :param expected: Expected invocation string
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
        with hunteuti.capture_system_calls() as invocations:
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
                    extra_opts=extra_opts if extra_opts else None,
                )
        # Check outputs.
        invocations_str = hunteuti.to_invocations_str(invocations)
        self.assert_equal(
            invocations_str, expected, fuzzy_match=True, dedent=True
        )

    def test1(self) -> None:
        """
        Test convert AST to LaTeX format.
        """
        # Prepare inputs.
        output_format = "latex"
        expected = """
        pandoc
        -t latex
        """
        # Run test.
        self.helper(output_format, expected)

    def test2(self) -> None:
        """
        Test convert AST to HTML format.
        """
        # Prepare inputs.
        output_format = "html"
        expected = """
        pandoc
        -t html
        """
        # Run test.
        self.helper(output_format, expected)

    def test3(self) -> None:
        """
        Test apply extra options to command.
        """
        # Prepare inputs.
        output_format = "latex"
        extra_opts = ["--number-sections", "--toc"]
        expected = """
        pandoc
        -t latex
        --number-sections
        --toc
        """
        # Run test.
        self.helper(output_format, expected, extra_opts=extra_opts)


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
        tex_only: bool,
        expected: str,
    ) -> None:
        """
        Test helper for run_pandoc_to_pdf.

        :param toc_type: Type of table of contents
        :param tex_only: Whether to only generate TeX
        :param expected: Expected invocation string
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        curr_path = scratch_dir
        file_name = os.path.join(scratch_dir, "input.txt")
        prefix = os.path.join(scratch_dir, "tmp.pdf")
        no_run_latex_again = False
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Create template file.
        template_file = os.path.join(curr_path, "pandoc.latex")
        hio.to_file(template_file, "LaTeX template")
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
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
                    tex_only=tex_only,
                )
        # Check outputs.
        invocations_str = hunteuti.to_invocations_str(invocations)
        self.assert_equal(
            invocations_str, expected, fuzzy_match=True, dedent=True
        )

    def test1(self) -> None:
        """
        Test single-shot pandoc to PDF conversion.
        """
        # Prepare inputs.
        toc_type = "none"
        tex_only = False
        expected = """
        pandoc
        pdflatex
        """
        # Run test.
        self.helper(toc_type, tex_only, expected)

    def test2(self) -> None:
        """
        Test return TeX file when tex_only=True.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        curr_path = scratch_dir
        file_name = os.path.join(scratch_dir, "input.txt")
        prefix = os.path.join(scratch_dir, "tmp.tex")
        toc_type = "none"
        tex_only = True
        # Create template file.
        template_file = os.path.join(curr_path, "pandoc.latex")
        hio.to_file(template_file, "LaTeX template")
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                no_run_latex_again = False
                use_host_tools = True
                dockerized_force_rebuild = False
                dockerized_use_sudo = False
                result = dshdlntpd.run_pandoc_to_pdf(
                    curr_path,
                    file_name,
                    prefix,
                    toc_type,
                    no_run_latex_again,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    tex_only=True,
                )
        # Check outputs.
        self.assert_equal(result, ".tex", fuzzy_match=True)
        invocations_str = hunteuti.to_invocations_str(invocations)
        expected_invocations = "pandoc"
        self.assert_equal(invocations_str, expected_invocations, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test table of contents inclusion.
        """
        # Prepare inputs.
        toc_type = "pandoc_native"
        tex_only = True
        expected = """
        pandoc
        --toc
        --toc-depth 2
        """
        # Run test.
        self.helper(toc_type, tex_only, expected)


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
        prefix = "tmp.html"
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
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
        self.assert_equal(result, ".html", fuzzy_match=True)
        invocations_str = hunteuti.to_invocations_str(invocations)
        self.assert_equal(
            invocations_str, expected, fuzzy_match=True, dedent=True
        )

    def test1(self) -> None:
        """
        Test single-shot pandoc to HTML conversion.
        """
        # Prepare inputs.
        file_in = "input.md"
        toc_type = "none"
        expected = """
        pandoc
        -t html
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
        expected = """
        pandoc
        -t html
        --toc
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
        expected = """
        pandoc
        -t html
        --metadata pagetitle=
        """
        # Run test.
        self.helper(file_in, toc_type, expected)


# #############################################################################
# Test_build_pandoc_cmd
# #############################################################################


class Test_build_pandoc_cmd(hunitest.TestCase):
    """
    Test `_build_pandoc_cmd()` function for slide command building.
    """

    def helper(
        self,
        file_name: str,
        use_tex: bool,
        expected: str,
        expected_ext: str,
    ) -> None:
        """
        Test helper for _build_pandoc_cmd.

        :param file_name: Input slide file
        :param use_tex: Whether to output TeX instead of PDF
        :param expected: Expected pandoc command
        :param expected_ext: Expected output file extension
        """
        # Prepare inputs.
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        toc_type = "none"
        # Run test.
        cmd, output_file = dshdlntpd._build_pandoc_cmd(
            file_name,
            toc_type,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            use_tex=use_tex,
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
        use_tex = False
        expected_ext = ".pdf"
        expected = """
        pandoc
        -t beamer
        """
        # Run test.
        self.helper(file_name, use_tex, expected, expected_ext)

    def test2(self) -> None:
        """
        Test build beamer TeX command.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        use_tex = True
        expected_ext = ".tex"
        expected = """
        pandoc
        -t beamer
        """
        # Run test.
        self.helper(file_name, use_tex, expected, expected_ext)

    def test3(self) -> None:
        """
        Test resource path inclusion.
        """
        # Prepare inputs.
        file_name = "subdir/slides.txt"
        use_tex = False
        expected_ext = ".pdf"
        expected = """
        pandoc
        -t beamer
        --resource-path=
        """
        # Run test.
        self.helper(file_name, use_tex, expected, expected_ext)

    def test4(self) -> None:
        """
        Test table of contents in slides.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        use_tex = False
        expected_ext = ".pdf"
        expected = """
        pandoc
        -t beamer
        --toc
        --toc-depth 2
        """
        # Prepare additional input for helper.
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        toc_type = "pandoc_native"
        # Run test.
        cmd, output_file = dshdlntpd._build_pandoc_cmd(
            file_name,
            toc_type,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            use_tex=use_tex,
        )
        # Check outputs.
        self.assert_equal(output_file, expected_ext, fuzzy_match=True)
        self.assert_equal(cmd, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# Test_run_pandoc_to_slides
# #############################################################################


class Test_run_pandoc_to_slides(hunitest.TestCase):
    """
    Test `run_pandoc_to_slides()` function for slide generation.
    """

    def helper(
        self,
        toc_type: str,
        tex_only: bool,
        expected_ext: str,
    ) -> None:
        """
        Test helper for run_pandoc_to_slides.

        :param toc_type: Type of table of contents
        :param tex_only: Whether to only generate TeX
        :param expected_ext: Expected file extension
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "slides.txt")
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                result = dshdlntpd.run_pandoc_to_slides(
                    file_name,
                    toc_type,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    tex_only=tex_only,
                )
        # Check outputs.
        self.assert_equal(result, expected_ext, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test generate PDF slides with single-shot pandoc.
        """
        # Prepare inputs.
        toc_type = "none"
        tex_only = False
        expected_ext = ".pdf"
        # Run test.
        self.helper(toc_type, tex_only, expected_ext)

    def test2(self) -> None:
        """
        Test return TeX file when tex_only=True.
        """
        # Prepare inputs.
        toc_type = "none"
        tex_only = True
        expected_ext = ".tex"
        # Run test.
        self.helper(toc_type, tex_only, expected_ext)


# #############################################################################
# Test_run_pandoc_to_typst_slides
# #############################################################################


class Test_run_pandoc_to_typst_slides(hunitest.TestCase):
    """
    Test `run_pandoc_to_typst_slides()` function for Typst slide generation.
    """

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
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Create template file.
        template_file = os.path.join(curr_path, "pandoc_touying.typ")
        hio.to_file(template_file, "Typst template")
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                with mock.patch(
                    "dev_scripts_helpers.documentation.lib_notes_to_pdf.hgit"
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
        self.assert_equal(result, expected_ext, fuzzy_match=True)

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
        # Create template file.
        template_file = os.path.join(curr_path, "pandoc_touying.typ")
        hio.to_file(template_file, "Typst template")
        # Create a mock typ file with relative image paths.
        typ_file = file_name.replace(".txt", ".typ")
        image_content = 'image("path/to/image.png")'
        hio.to_file(typ_file, image_content)
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch(
                "dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"
            ):
                with mock.patch(
                    "dev_scripts_helpers.documentation.lib_notes_to_pdf.hgit"
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
                            typst_only=False,
                        )
        # Check outputs.
        typ_content = hio.from_file(typ_file)
        expected = 'image("/'
        self.assert_equal(typ_content, expected, fuzzy_match=True)


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
        with hunteuti.capture_system_calls() as invocations:
            result = dshdlntpd.copy_to_output(file_in, output)
        # Check outputs.
        self.assert_equal(result, output)
        invocations_str = hunteuti.to_invocations_str(invocations)
        # Expected: cp command invoked to copy file to output location
        # Invariant: cp command executes for file copy operation
        expected = "cp"
        self.assert_equal(invocations_str, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test output path is required (not None).
        """
        # Prepare inputs.
        file_in = "source.txt"
        output = None
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dshdlntpd.copy_to_output(file_in, output)


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
        expected: str,
    ) -> None:
        """
        Test helper for copy_to_gdrive.

        :param ext: File extension
        :param input_: Input filename
        :param expected: Expected invocation string pattern
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, f"output.{ext}")
        hio.to_file(file_name, "content")
        gdrive_dir = scratch_dir
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            dshdlntpd.copy_to_gdrive(file_name, ext, input_, gdrive_dir)
        # Check outputs.
        invocations_str = hunteuti.to_invocations_str(invocations)
        self.assert_equal(invocations_str, expected, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test copy to specified Google Drive directory.
        """
        # Prepare inputs.
        ext = "pdf"
        input_ = "notes.txt"
        expected = "cp.*notes.pdf"
        # Run test.
        self.helper(ext, input_, expected)


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
        with hunteuti.capture_system_calls() as invocations:
            result = dshdlntpd.compress_pdf(pdf_file)
        # Check outputs.
        self.assert_equal(result, pdf_file)
        invocations_str = hunteuti.to_invocations_str(invocations)
        expected = """
        gs
        pdfwrite
        """
        self.assert_equal(
            invocations_str, expected, fuzzy_match=True, dedent=True
        )
