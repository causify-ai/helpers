#!/usr/bin/env python
"""
Unit tests for lib_notes_to_pdf.py.

Tests the markdown to PDF/HTML/slides conversion pipeline functions
including pandoc orchestration, file operations, and system calls.
"""

import hashlib
import logging
import os
import re
from typing import List
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.documentation.lib_notes_to_pdf as dsdlntp

_LOG = logging.getLogger(__name__)


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
        actual = dsdlntp._file_hash(test_file)
        # Check outputs.
        self.assertEqual(actual, expected_hash)

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
        hio.to_file(file1, "Content A")
        hio.to_file(file2, "Content B")
        # Run test.
        hash1 = dsdlntp._file_hash(file1)
        hash2 = dsdlntp._file_hash(file2)
        # Check outputs.
        self.assertNotEqual(hash1, hash2)

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
        hash1 = dsdlntp._file_hash(test_file)
        hash2 = dsdlntp._file_hash(test_file)
        # Check outputs.
        self.assertEqual(hash1, hash2)


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
            result = dsdlntp.preprocess_notes(
                file_name, prefix, type_, toc_type, output_format
            )
        # Check outputs.
        # Expected: result contains preprocessing output filename with .preprocess_notes.txt suffix
        # Invariant: output includes correct suffix indicating preprocessing completion
        self.assertIn(".preprocess_notes.txt", result)
        invocations_str = hunteuti.to_invocations_str(invocations)
        # Expected invocations: preprocess_notes.py called with type and toc_type arguments
        # Invariant: preprocessing script invoked with all required parameters
        expected = """
        preprocess_notes.py
        --type pdf
        --toc_type pandoc_native
        """
        self.assert_equal(invocations_str, expected, fuzzy_match=True, dedent=True)


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
            result = dsdlntp.render_images(file_name, prefix)
        # Check outputs.
        # Expected: result contains render_image reference in output filename
        # Invariant: rendered images filename includes render_image marker
        self.assertIn("render_image", result)
        invocations_str = hunteuti.to_invocations_str(invocations)
        # Expected: render_images.py script invoked for image rendering
        # Invariant: image rendering script execution with correct command
        expected = "render_images.py"
        self.assertIn(expected, invocations_str)


class Test_run_pandoc_to_ast(hunitest.TestCase):
    """
    Test `_run_pandoc_to_ast()` function.
    """

    def helper(
        self,
        file_in: str,
        fail_on_warnings: bool,
        expect_fail_flag: bool,
    ) -> None:
        """
        Test helper for _run_pandoc_to_ast.

        :param file_in: Input markdown file
        :param fail_on_warnings: Whether to fail on warnings
        :param expect_fail_flag: Whether --fail-if-warnings should appear
        """
        # Prepare inputs.
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                result = dsdlntp._run_pandoc_to_ast(
                    file_in,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    fail_on_warnings=fail_on_warnings,
                )
        # Check outputs.
        # Expected: AST output filename with .ast.json extension
        # Invariant: AST JSON file generated as output
        self.assertIn(".ast.json", result)
        invocations_str = hunteuti.to_invocations_str(invocations)
        # Expected: pandoc command invoked with JSON output format and optional fail-on-warnings
        # Invariant: pandoc with -t json flag for AST generation
        expected_parts = ["pandoc", "-t json"]
        if expect_fail_flag:
            expected_parts.append("--fail-if-warnings")
        expected = " ".join(expected_parts)
        for part in expected_parts:
            self.assertIn(part, invocations_str)

    def test1(self) -> None:
        """
        Test pandoc to AST conversion with host tools.
        """
        # Prepare inputs.
        file_in = "input.md"
        fail_on_warnings = True
        expect_fail_flag = True
        # Run test.
        self.helper(file_in, fail_on_warnings, expect_fail_flag)

    def test2(self) -> None:
        """
        Test pandoc to AST without fail-on-warnings.
        """
        # Prepare inputs.
        file_in = "input.md"
        fail_on_warnings = False
        expect_fail_flag = False
        # Run test.
        self.helper(file_in, fail_on_warnings, expect_fail_flag)


class Test_run_pandoc_from_ast(hunitest.TestCase):
    """
    Test `_run_pandoc_from_ast()` function.
    """

    def helper(
        self,
        output_format: str,
        expected_format_flag: str,
        extra_opts: List[str] = None,  # type: ignore
    ) -> None:
        """
        Test helper for _run_pandoc_from_ast.

        :param output_format: Output format (latex, html, etc)
        :param expected_format_flag: Expected -t flag in command
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
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                dsdlntp._run_pandoc_from_ast(
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
        # Expected: pandoc invoked with format flag and any extra options
        # Invariant: pandoc with output format and optional extra arguments present
        expected_parts = ["pandoc", expected_format_flag]
        if extra_opts:
            expected_parts.extend(extra_opts)
        expected = "\n".join(expected_parts)
        self.assert_equal(invocations_str, expected, fuzzy_match=True, dedent=True)

    def test1(self) -> None:
        """
        Test convert AST to LaTeX format.
        """
        # Prepare inputs.
        output_format = "latex"
        expected_format_flag = "-t latex"
        # Run test.
        self.helper(output_format, expected_format_flag)

    def test2(self) -> None:
        """
        Test convert AST to HTML format.
        """
        # Prepare inputs.
        output_format = "html"
        expected_format_flag = "-t html"
        # Run test.
        self.helper(output_format, expected_format_flag)

    def test3(self) -> None:
        """
        Test apply extra options to command.
        """
        # Prepare inputs.
        output_format = "latex"
        expected_format_flag = "-t latex"
        extra_opts = ["--number-sections", "--toc"]
        # Run test.
        self.helper(output_format, expected_format_flag, extra_opts)


class Test_run_pandoc_to_pdf(hunitest.TestCase):
    """
    Test `run_pandoc_to_pdf()` function for PDF generation.
    """

    def helper(
        self,
        toc_type: str,
        tex_only: bool,
        expect_pdflatex: bool,
        expect_toc: bool,
    ) -> None:
        """
        Test helper for run_pandoc_to_pdf.

        :param toc_type: Type of table of contents
        :param tex_only: Whether to only generate TeX
        :param expect_pdflatex: Whether pdflatex should be invoked
        :param expect_toc: Whether --toc flags should appear
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
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                result = dsdlntp.run_pandoc_to_pdf(
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
        # Expected: pandoc always invoked, optionally pdflatex and TOC flags
        # Invariant: pandoc command present, pdflatex/TOC flags match parameters
        expected_parts = ["pandoc"]
        if expect_pdflatex:
            expected_parts.append("pdflatex")
        if expect_toc:
            expected_parts.extend(["--toc", "--toc-depth 2"])
        expected = "\n".join(expected_parts)
        self.assert_equal(invocations_str, expected, fuzzy_match=True, dedent=True)

    def test1(self) -> None:
        """
        Test single-shot pandoc to PDF conversion.
        """
        # Prepare inputs.
        toc_type = "none"
        tex_only = False
        expect_pdflatex = True
        expect_toc = False
        # Run test.
        self.helper(toc_type, tex_only, expect_pdflatex, expect_toc)

    def test2(self) -> None:
        """
        Test return TeX file when tex_only=True.
        """
        # Prepare inputs.
        toc_type = "none"
        tex_only = True
        expect_pdflatex = False
        expect_toc = False
        # Run test and check outputs.
        scratch_dir = self.get_scratch_space()
        curr_path = scratch_dir
        file_name = os.path.join(scratch_dir, "input.txt")
        prefix = os.path.join(scratch_dir, "tmp.tex")
        # Create template file.
        template_file = os.path.join(curr_path, "pandoc.latex")
        hio.to_file(template_file, "LaTeX template")
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                result = dsdlntp.run_pandoc_to_pdf(
                    curr_path,
                    file_name,
                    prefix,
                    toc_type,
                    False,
                    True,
                    False,
                    False,
                    tex_only=True,
                )
        # Check outputs.
        # Expected: result contains .tex suffix when tex_only=True
        # Invariant: TeX file generated instead of PDF
        self.assertIn(".tex", result)
        invocations_str = hunteuti.to_invocations_str(invocations)
        self.assertNotIn("pdflatex", invocations_str)

    def test3(self) -> None:
        """
        Test table of contents inclusion.
        """
        # Prepare inputs.
        toc_type = "pandoc_native"
        tex_only = True
        expect_pdflatex = False
        expect_toc = True
        # Run test.
        self.helper(toc_type, tex_only, expect_pdflatex, expect_toc)


class Test_run_pandoc_to_html(hunitest.TestCase):
    """
    Test `run_pandoc_to_html()` function for HTML generation.
    """

    def helper(
        self,
        file_in: str,
        toc_type: str,
        expect_toc: bool = False,
        expect_metadata: bool = False,
    ) -> None:
        """
        Test helper for run_pandoc_to_html.

        :param file_in: Input markdown file
        :param toc_type: Type of table of contents
        :param expect_toc: Whether --toc should appear
        :param expect_metadata: Whether metadata should be included
        """
        # Prepare inputs.
        prefix = "tmp.html"
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                result = dsdlntp.run_pandoc_to_html(
                    file_in,
                    prefix,
                    toc_type,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                )
        # Check outputs.
        # Expected: result contains .html suffix
        # Invariant: HTML output file generated
        self.assertIn(".html", result)
        invocations_str = hunteuti.to_invocations_str(invocations)
        # Expected: pandoc with HTML format, optional TOC and metadata flags
        # Invariant: pandoc with -t html and optional TOC/metadata parameters
        expected_parts = ["pandoc", "-t html"]
        if expect_toc:
            expected_parts.append("--toc")
        if expect_metadata:
            expected_parts.append("--metadata pagetitle=")
        expected = "\n".join(expected_parts)
        self.assert_equal(invocations_str, expected, fuzzy_match=True, dedent=True)

    def test1(self) -> None:
        """
        Test single-shot pandoc to HTML conversion.
        """
        # Prepare inputs.
        file_in = "input.md"
        toc_type = "none"
        expect_toc = False
        expect_metadata = False
        # Run test.
        self.helper(file_in, toc_type, expect_toc, expect_metadata)

    def test2(self) -> None:
        """
        Test HTML with table of contents.
        """
        # Prepare inputs.
        file_in = "input.md"
        toc_type = "pandoc_native"
        expect_toc = True
        expect_metadata = False
        # Run test.
        self.helper(file_in, toc_type, expect_toc, expect_metadata)

    def test3(self) -> None:
        """
        Test metadata pagetitle included.
        """
        # Prepare inputs.
        file_in = "notes.md"
        toc_type = "none"
        expect_toc = False
        expect_metadata = True
        # Run test.
        self.helper(file_in, toc_type, expect_toc, expect_metadata)


class Test_build_pandoc_cmd(hunitest.TestCase):
    """
    Test `_build_pandoc_cmd()` function for slide command building.
    """

    def helper(
        self,
        file_name: str,
        toc_type: str,
        use_tex: bool = False,
        expect_resource_path: bool = False,
    ) -> None:
        """
        Test helper for _build_pandoc_cmd.

        :param file_name: Input slide file
        :param toc_type: Type of table of contents
        :param use_tex: Whether to output TeX instead of PDF
        :param expect_resource_path: Whether resource path should be included
        """
        # Prepare inputs.
        use_host_tools = True
        dockerized_force_rebuild = False
        dockerized_use_sudo = False
        # Run test.
        cmd, output_file = dsdlntp._build_pandoc_cmd(
            file_name,
            toc_type,
            use_host_tools,
            dockerized_force_rebuild,
            dockerized_use_sudo,
            use_tex=use_tex,
        )
        # Check outputs.
        # Expected: output file has correct extension based on use_tex
        # Invariant: .tex for TeX output, .pdf for PDF output
        expected_ext = ".tex" if use_tex else ".pdf"
        self.assertIn(expected_ext, output_file)
        # Expected: pandoc beamer command with optional resource-path and TOC
        # Invariant: pandoc with -t beamer, optional --resource-path and TOC flags
        expected_parts = ["pandoc", "-t beamer"]
        if expect_resource_path:
            expected_parts.append("--resource-path=")
        if toc_type == "pandoc_native":
            expected_parts.extend(["--toc", "--toc-depth 2"])
        expected = "\n".join(expected_parts)
        self.assert_equal(cmd, expected, fuzzy_match=True, dedent=True)

    def test1(self) -> None:
        """
        Test build beamer PDF command.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        toc_type = "none"
        use_tex = False
        # Run test.
        self.helper(file_name, toc_type, use_tex)

    def test2(self) -> None:
        """
        Test build beamer TeX command.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        toc_type = "none"
        use_tex = True
        # Run test.
        self.helper(file_name, toc_type, use_tex)

    def test3(self) -> None:
        """
        Test resource path inclusion.
        """
        # Prepare inputs.
        file_name = "subdir/slides.txt"
        toc_type = "none"
        use_tex = False
        expect_resource_path = True
        # Run test.
        self.helper(file_name, toc_type, use_tex, expect_resource_path)

    def test4(self) -> None:
        """
        Test table of contents in slides.
        """
        # Prepare inputs.
        file_name = "slides.txt"
        toc_type = "pandoc_native"
        use_tex = False
        # Run test.
        self.helper(file_name, toc_type, use_tex)


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
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                result = dsdlntp.run_pandoc_to_slides(
                    file_name,
                    toc_type,
                    use_host_tools,
                    dockerized_force_rebuild,
                    dockerized_use_sudo,
                    tex_only=tex_only,
                )
        # Check outputs.
        # Expected: result contains correct file extension
        # Invariant: output extension matches tex_only parameter (.tex or .pdf)
        self.assertIn(expected_ext, result)

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
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hgit"):
                    with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.dshdlity"):
                        result = dsdlntp.run_pandoc_to_typst_slides(
                            curr_path,
                            file_name,
                            use_host_tools,
                            dockerized_force_rebuild,
                            dockerized_use_sudo,
                            typst_only=typst_only,
                        )
        # Check outputs.
        # Expected: result contains correct file extension
        # Invariant: output extension matches typst_only parameter
        self.assertIn(expected_ext, result)

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
            with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hdbg"):
                with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.hgit"):
                    with mock.patch("dev_scripts_helpers.documentation.lib_notes_to_pdf.dshdlity"):
                        result = dsdlntp.run_pandoc_to_typst_slides(
                            curr_path,
                            file_name,
                            use_host_tools,
                            dockerized_force_rebuild,
                            dockerized_use_sudo,
                            typst_only=False,
                        )
        # Check outputs.
        typ_content = hio.from_file(typ_file)
        # Expected: image paths converted from relative to root-absolute
        # Invariant: image paths start with / for root-absolute reference
        expected = 'image("/'
        self.assertIn(expected, typ_content)


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
            result = dsdlntp.copy_to_output(file_in, output)
        # Check outputs.
        self.assertEqual(result, output)
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
            dsdlntp.copy_to_output(file_in, output)


class Test_copy_to_gdrive(hunitest.TestCase):
    """
    Test `copy_to_gdrive()` function.
    """

    def helper(
        self,
        ext: str,
        input_: str,
        expected_filename: str,
    ) -> None:
        """
        Test helper for copy_to_gdrive.

        :param ext: File extension
        :param input_: Input filename
        :param expected_filename: Expected output filename with extension
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, f"output.{ext}")
        hio.to_file(file_name, "content")
        gdrive_dir = scratch_dir
        # Run test and capture system calls.
        with hunteuti.capture_system_calls() as invocations:
            dsdlntp.copy_to_gdrive(file_name, ext, input_, gdrive_dir)
        # Check outputs.
        invocations_str = hunteuti.to_invocations_str(invocations)
        # Expected: cp command with renamed output filename
        # Invariant: file copied to gdrive directory with correct name and extension
        expected = f"cp.*{expected_filename}"
        self.assert_equal(invocations_str, expected, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test copy to specified Google Drive directory.
        """
        # Prepare inputs.
        ext = "pdf"
        input_ = "notes.txt"
        expected_filename = "notes.pdf"
        # Run test.
        self.helper(ext, input_, expected_filename)

    def test2(self) -> None:
        """
        Test file extension handling.
        """
        # Prepare inputs.
        ext = "html"
        input_ = "notes.txt"
        expected_filename = "notes.html"
        # Run test.
        self.helper(ext, input_, expected_filename)

    def test3(self) -> None:
        """
        Test directory existence check.
        """
        # Prepare inputs.
        file_name = "output.pdf"
        ext = "pdf"
        input_ = "notes.txt"
        gdrive_dir = "/nonexistent/path/to/gdrive"
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dsdlntp.copy_to_gdrive(file_name, ext, input_, gdrive_dir)


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
            result = dsdlntp.compress_pdf(pdf_file)
        # Check outputs.
        self.assertEqual(result, pdf_file)
        invocations_str = hunteuti.to_invocations_str(invocations)
        # Expected: Ghostscript (gs) invoked with pdfwrite device
        # Invariant: gs and pdfwrite parameters present for PDF compression
        expected = """
        gs
        pdfwrite
        """
        self.assert_equal(invocations_str, expected, fuzzy_match=True, dedent=True)

    def test2(self) -> None:
        """
        Test input must be PDF file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        not_pdf = os.path.join(scratch_dir, "document.txt")
        hio.to_file(not_pdf, "text content")
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dsdlntp.compress_pdf(not_pdf)

    def test3(self) -> None:
        """
        Test file must exist.
        """
        # Prepare inputs.
        pdf_file = "/nonexistent/document.pdf"
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dsdlntp.compress_pdf(pdf_file)
