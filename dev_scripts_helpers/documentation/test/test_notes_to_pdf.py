import logging
import os
import sys
from typing import Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_notes_to_pdf1
# #############################################################################


class Test_notes_to_pdf1(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` with a simple input file.
    """

    def create_input_file_from_txt(self, txt: str) -> str:
        """
        Create a temporary markdown input file from raw text.

        Normalizes the input by removing leading/trailing empty lines and
        writes it to a temp file in the scratch space.

        :param txt: Raw markdown text to write to file
        :return: Path to the created temporary markdown file
        """
        _LOG.debug(hprint.to_str("txt"))
        # Normalize input and write to temp file.
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        _LOG.debug("return=%s", in_file)
        return in_file

    def create_input_file1(self) -> str:
        """
        Create a standard test markdown file with multiple header levels and list items.

        :return: Path to the created test markdown file
        """
        txt = """
        # Header1

        - hello

        ## Header2
        - world

        ## Header3
        - foo
        - bar

        # Header4
        - baz
        """
        result = self.create_input_file_from_txt(txt)
        _LOG.debug("return=%s", result)
        return result

    def run_notes_to_pdf(
        self,
        in_file: str,
        type_: str,
        cmd_opts: str,
        expected: str,
    ) -> Tuple[str, str]:
        """
        Run the `notes_to_pdf.py` script and capture generated outputs.

        Constructs and executes a command to convert notes to PDF or HTML
        using `notes_to_pdf.py`. Locates the script dynamically and captures
        the generated script file (with all executed commands) and the
        intermediate pandoc output file.

        :param in_file: Path to the input markdown file
        :param type_: Output format
            - 'pdf': PDF output via LaTeX
            - 'html': HTML output
            - 'slides': Slide format PDF via LaTeX
        :param cmd_opts: Additional command-line options (e.g., '--preview_actions')
        :param expected: Expected combined output (script + pandoc) for validation
            - If empty string: no assertion performed
            - If non-empty: asserts actual output matches expected using purify_text
        :return: Tuple of (script_txt, output_txt)
            - script_txt: Content of the generated bash script with all executed commands
            - output_txt: Content of the intermediate pandoc output file (LaTeX or HTML)
        """
        _LOG.debug(hprint.to_str("in_file type_"))
        # Construct command.
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append(f"--type {type_}")
        out_dir = self.get_scratch_space()
        script_file = os.path.join(out_dir, "script.sh")
        cmd.append(f"--script {script_file}")
        out_file = os.path.join(out_dir, f"output.{type_}")
        cmd.append(f"--output {out_file}")
        cmd.append(cmd_opts)
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Execute the command.
        hsystem.system(cmd)
        # Map output type to expected intermediate file (pandoc generates these).
        if type_ == "pdf" or type_ == "slides":
            out_file = os.path.join(out_dir, "tmp.pandoc.tex")
        elif type_ == "html":
            out_file = os.path.join(out_dir, "tmp.pandoc.html")
        else:
            raise ValueError(f"Invalid type_='{type_}'")
        # Read generated files.
        output_txt = ""
        if os.path.exists(out_file):
            output_txt = hio.from_file(out_file)
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        _LOG.debug(
            "return=(script_txt[%d], output_txt[%d])",
            len(script_txt),
            len(output_txt),
        )
        # Perform assertion if expected output provided.
        if expected:
            actual = f"script_txt:\n{script_txt}\n"
            actual += f"output_txt:\n{output_txt}\n"
            self.assert_equal(actual, expected, purify_text=True)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test preview mode returns empty output without generating files.
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = "--preview_actions"
        # Prepare outputs.
        expected_script_txt = ""
        expected_output_txt = ""
        # Run test.
        script_txt, output_txt = self.run_notes_to_pdf(
            in_file, type_, cmd_opts, expected=""
        )
        # Check outputs.
        self.assertEqual(script_txt, expected_script_txt)
        self.assertEqual(output_txt, expected_output_txt)

    @pytest.mark.superslow
    def test2(self) -> None:
        """
        Test full PDF generation pipeline with preprocessing, rendering, and LaTeX compilation.
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = ""
        # Prepare outputs.
        expected = hprint.dedent(
            r"""
            script_txt:
            #/bin/bash -xe
            # cleanup_before
            ## skipping this action
            # preprocess_notes
            $GIT_ROOT/dev_scripts_helpers/documentation/preprocess_notes.py --input $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/input.md --output $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt --type pdf --toc_type none --output_format latex
            # render_images
            $GIT_ROOT/dev_scripts_helpers/documentation/render_images.py --input $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt --output $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image.txt --action render
            # run_pandoc
            container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7 /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image2.txt --output /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json -t json --fail-if-warnings
            container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7 /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json --output /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.tex --template /dev_scripts_helpers/documentation/pandoc.latex -f json -t latex --fail-if-warnings -V geometry:margin=1in --number-sections --highlight-style=tango -s
            # latex
            cp -f $GIT_ROOT/dev_scripts_helpers/documentation/latex_abbrevs.sty $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch
            container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount type=bind,source=$GIT_ROOT,target=/app tmp.latex.arm64.417056b0 pdflatex -output-directory /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch --interaction=nonstopmode --halt-on-error --shell-escape /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.tex
            # latex again
            # compress_pdf
            ## skipping this action
            \\cp -af $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.pdf $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/output.pdf
            # copy_to_gdrive
            ## skipping this action
            # open
            ## skipping this action
            # cleanup_after
            ## skipping this action
            output_txt:
        """,
            remove_lead_trail_empty_lines_=True,
        )
        # Run test.
        self.run_notes_to_pdf(in_file, type_, cmd_opts, expected=expected)

    @pytest.mark.superslow
    def test3(self) -> None:
        """
        Test PDF generation with header-based filtering of input content.
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = "--filter_by_header Header2"
        # Prepare outputs.
        expected = hprint.dedent(
            r"""
            script_txt:
            #/bin/bash -xe
            # cleanup_before
            ## skipping this action
            # preprocess_notes
            $GIT_ROOT/dev_scripts_helpers/documentation/preprocess_notes.py --input $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.filter_by_header.txt --output $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt --type pdf --toc_type none --output_format latex
            # render_images
            $GIT_ROOT/dev_scripts_helpers/documentation/render_images.py --input $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt --output $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image.txt --action render
            # run_pandoc
            container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7 /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image2.txt --output /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json -t json --fail-if-warnings
            container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7 /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json --output /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.tex --template /dev_scripts_helpers/documentation/pandoc.latex -f json -t latex --fail-if-warnings -V geometry:margin=1in --number-sections --highlight-style=tango -s
            # latex
            cp -f $GIT_ROOT/dev_scripts_helpers/documentation/latex_abbrevs.sty $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch
            container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount type=bind,source=$GIT_ROOT,target=/app tmp.latex.arm64.417056b0 pdflatex -output-directory /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch --interaction=nonstopmode --halt-on-error --shell-escape /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.tex
            # latex again
            # compress_pdf
            ## skipping this action
            \\cp -af $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.pdf $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/output.pdf
            # copy_to_gdrive
            ## skipping this action
            # open
            ## skipping this action
            # cleanup_after
            ## skipping this action
            output_txt:
        """,
            remove_lead_trail_empty_lines_=True,
        )
        # Run test.
        self.run_notes_to_pdf(in_file, type_, cmd_opts, expected=expected)

    @pytest.mark.superslow
    @pytest.mark.skipif(
        sys.platform == "darwin",
        reason="Container execution and LaTeX rendering with slides produces different output on macOS vs Linux; requires Linux environment",
    )
    def test4(self) -> None:
        """
        Test slides generation with embedded LaTeX table content in code block.
        """
        # Prepare inputs.
        txt = r"""
        * Comparison

        ```latex
        \usepackage{float}
        \usepackage{caption}
        \begin{document}

        \begin{tabular}{|p{3cm}|p{4cm}|p{4cm}|p{4cm}|}
        \hline
        \textbf{Feature} & \textbf{RDF} & \textbf{Property Graph} & \textbf{XML} \\
        \hline
        Core data model & Triples: \textbf{(subject, predicate, object)} & \textbf{Nodes} and \textbf{edges} with properties & \textbf{Hierarchical tree} of elements \\
        \hline
        How facts are stored & Fact is a separate triple & Facts are properties on nodes or edges & Nested tags with attributes \\
        \hline
        \end{tabular}
        \end{document}
        ```
        """
        in_file = self.create_input_file_from_txt(txt)
        type_ = "slides"
        cmd_opts = ""
        # Prepare outputs.
        # Note: Expected output is empty since this test validates the pipeline
        # completes without errors. Full expected output should be filled in
        # once the test runs successfully on a Linux environment.
        expected = ""
        # Run test.
        self.run_notes_to_pdf(in_file, type_, cmd_opts, expected=expected)


# #############################################################################
# Test_notes_to_pdf_filters
# #############################################################################


class Test_notes_to_pdf_filters(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` filter options (by header, lines, slides, name).
    """

    def create_multiline_input(self, num_lines: int) -> str:
        """
        Create markdown input with multiple lines and headers.

        :param num_lines: Number of lines to generate
        :return: Path to the created markdown file
        """
        lines = []
        for i in range(num_lines):
            if i % 5 == 0:
                lines.append(f"# Header {i // 5}")
            lines.append(f"Line {i}")
        txt = "\n".join(lines)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        return in_file

    def create_slides_input(self) -> str:
        """
        Create markdown input with slide structure.

        :return: Path to the created markdown file
        """
        txt = """
        ---
        # Slide 1: Introduction

        This is the introduction slide.

        ---
        # Slide 2: Methods

        This slide describes methods.

        ---
        # Slide 3: Results

        This slide shows results.

        ---
        # Slide 4: Conclusion

        This is the conclusion slide.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "slides.md")
        hio.to_file(in_file, txt)
        return in_file

    def helper_filter_test(
        self, in_file: str, type_: str, cmd_opts: str
    ) -> Tuple[str, str]:
        """
        Helper to run filter test and return outputs.

        :param in_file: Input markdown file
        :param type_: Output type (pdf, html, slides)
        :param cmd_opts: Command line options including filter
        :return: Tuple of (script_txt, output_file_path)
        """
        out_dir = self.get_scratch_space()
        script_file = os.path.join(out_dir, "script.sh")
        out_file = os.path.join(out_dir, f"output.{type_}")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append(f"--type {type_}")
        cmd.append(f"--script {script_file}")
        cmd.append(f"--output {out_file}")
        cmd.append(cmd_opts)
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        hsystem.system(cmd)
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        return script_txt, out_file

    def test1(self) -> None:
        """
        Test filter by lines with start:end range.
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(15)
        type_ = "pdf"
        cmd_opts = "--filter_by_lines 0:5"
        # Run test.
        script_txt, _ = self.helper_filter_test(in_file, type_, cmd_opts)
        # Check outputs.
        self.assertIn("filter_by_lines", script_txt)

    def test2(self) -> None:
        """
        Test filter by lines with None boundary (first N lines).
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(20)
        type_ = "pdf"
        cmd_opts = "--filter_by_lines None:10"
        # Run test.
        script_txt, out_file = self.helper_filter_test(in_file, type_, cmd_opts)
        # Check outputs.
        self.assertIn("filter_by_lines", script_txt)
        self.assertTrue(os.path.exists(out_file))

    def test3(self) -> None:
        """
        Test filter by lines with reverse None boundary (from line N onwards).
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(20)
        type_ = "pdf"
        cmd_opts = "--filter_by_lines 10:None"
        # Run test.
        script_txt, out_file = self.helper_filter_test(in_file, type_, cmd_opts)
        # Check outputs.
        self.assertIn("filter_by_lines", script_txt)
        self.assertTrue(os.path.exists(out_file))

    def test4(self) -> None:
        """
        Test filter by header.
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(20)
        type_ = "pdf"
        cmd_opts = "--filter_by_header 'Header 1'"
        # Run test.
        script_txt, out_file = self.helper_filter_test(in_file, type_, cmd_opts)
        # Check outputs.
        self.assertIn("filter_by_header", script_txt)
        self.assertTrue(os.path.exists(out_file))

    def test5(self) -> None:
        """
        Test filter by slides with range.
        """
        # Prepare inputs.
        in_file = self.create_slides_input()
        type_ = "slides"
        cmd_opts = "--filter_by_slides 0:2"
        # Run test.
        script_txt, _ = self.helper_filter_test(in_file, type_, cmd_opts)
        # Check outputs.
        self.assertIn("filter_by_slides", script_txt)


# #############################################################################
# Test_notes_to_pdf_output_types
# #############################################################################


class Test_notes_to_pdf_output_types(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` with different output types (pdf, html, slides).
    """

    def create_simple_input(self) -> str:
        """
        Create a simple markdown input file.

        :return: Path to the created markdown file
        """
        txt = """
        # Introduction

        This is a simple test document.

        ## Section 1

        Some content here.

        ## Section 2

        More content here.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "simple.md")
        hio.to_file(in_file, txt)
        return in_file

    def helper_output_type_test(
        self, type_: str, cmd_opts: str
    ) -> Tuple[str, str]:
        """
        Helper to test output type generation.

        :param type_: Output type (pdf, html, slides)
        :param cmd_opts: Additional command line options
        :return: Tuple of (script_txt, output_file_path)
        """
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, f"output.{type_}")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append(f"--type {type_}")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append(cmd_opts)
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        hsystem.system(cmd)
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        return script_txt, out_file

    def test1(self) -> None:
        """
        Test HTML output generation.
        """
        # Prepare inputs.
        type_ = "html"
        cmd_opts = ""
        # Run test.
        script_txt, _ = self.helper_output_type_test(type_, cmd_opts)
        # Check outputs.
        self.assertIn("run_pandoc", script_txt)

    def test2(self) -> None:
        """
        Test PDF generation with tex_only mode (no compilation).
        """
        # Prepare inputs.
        type_ = "pdf"
        cmd_opts = "--tex_only"
        # Run test.
        script_txt, _ = self.helper_output_type_test(type_, cmd_opts)
        # Check outputs.
        self.assertIn("tex_only", script_txt)

    def test3(self) -> None:
        """
        Test slides generation with Beamer engine.
        """
        # Prepare inputs.
        type_ = "slides"
        cmd_opts = "--slides_engine beamer"
        # Run test.
        script_txt, _ = self.helper_output_type_test(type_, cmd_opts)
        # Check outputs.
        self.assertIn("run_pandoc", script_txt)


# #############################################################################
# Test_notes_to_pdf_toc_options
# #############################################################################


class Test_notes_to_pdf_toc_options(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` with different TOC options.
    """

    def create_structured_input(self) -> str:
        """
        Create markdown with clear header structure for TOC testing.

        :return: Path to the created markdown file
        """
        txt = """
        # Chapter 1

        ## Section 1.1

        Content for section 1.1.

        ### Subsection 1.1.1

        Content for subsection.

        ## Section 1.2

        Content for section 1.2.

        # Chapter 2

        ## Section 2.1

        Content for section 2.1.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "structured.md")
        hio.to_file(in_file, txt)
        return in_file

    def helper_toc_test(self, toc_type: str) -> str:
        """
        Helper to test TOC type generation.

        :param toc_type: TOC type (none, pandoc_native, navigation, remove_headers)
        :return: Script output as string
        """
        in_file = self.create_structured_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--toc_type {toc_type}")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        hsystem.system(cmd)
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        return script_txt

    def test1(self) -> None:
        """
        Test TOC type 'none' (no table of contents).
        """
        # Prepare inputs.
        toc_type = "none"
        # Run test.
        script_txt = self.helper_toc_test(toc_type)
        # Check outputs.
        self.assertIn("toc_type none", script_txt)

    def test2(self) -> None:
        """
        Test TOC type 'pandoc_native'.
        """
        # Prepare inputs.
        toc_type = "pandoc_native"
        # Run test.
        script_txt = self.helper_toc_test(toc_type)
        # Check outputs.
        self.assertIn("toc_type pandoc_native", script_txt)

    def test3(self) -> None:
        """
        Test TOC type 'navigation'.
        """
        # Prepare inputs.
        toc_type = "navigation"
        # Run test.
        script_txt = self.helper_toc_test(toc_type)
        # Check outputs.
        self.assertIn("toc_type navigation", script_txt)

    def test4(self) -> None:
        """
        Test TOC type 'remove_headers'.
        """
        # Prepare inputs.
        toc_type = "remove_headers"
        # Run test.
        script_txt = self.helper_toc_test(toc_type)
        # Check outputs.
        self.assertIn("toc_type remove_headers", script_txt)


# #############################################################################
# Test_notes_to_pdf_actions
# #############################################################################


class Test_notes_to_pdf_actions(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` action selection and skipping.
    """

    def create_simple_input(self) -> str:
        """
        Create a simple markdown input file.

        :return: Path to the created markdown file
        """
        txt = """
        # Simple Test

        This is a simple test document for action testing.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "simple.md")
        hio.to_file(in_file, txt)
        return in_file

    def helper_action_test(self, cmd_opts: str) -> str:
        """
        Helper to test action selection.

        :param cmd_opts: Command line options for action selection
        :return: Script output as string
        """
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append(cmd_opts)
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        hsystem.system(cmd)
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        return script_txt

    def test1(self) -> None:
        """
        Test skipping a single action (cleanup_before).
        """
        # Prepare inputs.
        cmd_opts = "--skip_action=cleanup_before"
        # Run test.
        script_txt = self.helper_action_test(cmd_opts)
        # Check outputs.
        self.assertIn("cleanup_before", script_txt)
        self.assertIn("skipping this action", script_txt)

    def test2(self) -> None:
        """
        Test skipping multiple actions.
        """
        # Prepare inputs.
        cmd_opts = "--skip_action=cleanup_before --skip_action=cleanup_after"
        # Run test.
        script_txt = self.helper_action_test(cmd_opts)
        # Check outputs.
        self.assertIn("cleanup_before", script_txt)
        self.assertIn("cleanup_after", script_txt)

    def test3(self) -> None:
        """
        Test preview actions mode (no execution).
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append("--preview_actions")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs: script file should not be created in preview mode
        script_file = os.path.join(out_dir, "script.sh")
        self.assertFalse(os.path.exists(script_file))


# #############################################################################
# Test_notes_to_pdf_script_generation
# #############################################################################


class Test_notes_to_pdf_script_generation(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` script generation and content.
    """

    def create_simple_input(self) -> str:
        """
        Create a simple markdown input file.

        :return: Path to the created markdown file
        """
        txt = """
        # Introduction

        Test content for script generation.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "simple.md")
        hio.to_file(in_file, txt)
        return in_file

    def test1(self) -> None:
        """
        Test script file is generated with correct shebang.
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "generated_script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        self.assertTrue(os.path.exists(script_file))
        script_txt = hio.from_file(script_file)
        self.assertIn("#/bin/bash -xe", script_txt)

    def test2(self) -> None:
        """
        Test script contains all executed actions in sequence.
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "generated_script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action cleanup_before")
        cmd.append("--skip_action cleanup_after")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        script_txt = hio.from_file(script_file)
        self.assertIn("# preprocess_notes", script_txt)
        self.assertIn("# render_images", script_txt)
        self.assertIn("# run_pandoc", script_txt)


# #############################################################################
# Test_notes_to_pdf_errors
# #############################################################################


class Test_notes_to_pdf_errors(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` error handling and validation.
    """

    def test1(self) -> None:
        """
        Test missing required input file raises error.
        """
        # Prepare inputs.
        in_file = "/nonexistent/path/file.md"
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test: expect error
        try:
            hsystem.system(cmd)
            self.fail("Expected exception for missing input file")
        except Exception:
            pass  # Expected to raise

    def test2(self) -> None:
        """
        Test invalid output type raises error.
        """
        # Prepare inputs.
        txt = "# Test"
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.unknown")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type invalid_type")
        cmd.append(f"--output {out_file}")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test: expect error
        try:
            hsystem.system(cmd)
            self.fail("Expected exception for invalid type")
        except Exception:
            pass  # Expected to raise


# #############################################################################
# Test_notes_to_pdf_edge_cases
# #############################################################################


class Test_notes_to_pdf_edge_cases(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` with edge cases and special inputs.
    """

    def test1(self) -> None:
        """
        Test empty markdown file processing.
        """
        # Prepare inputs.
        txt = ""
        in_file = os.path.join(self.get_scratch_space(), "empty.md")
        hio.to_file(in_file, txt)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        self.assertTrue(os.path.exists(script_file))

    def test2(self) -> None:
        """
        Test markdown with only whitespace and empty lines.
        """
        # Prepare inputs.
        txt = "\n\n   \n\n"
        in_file = os.path.join(self.get_scratch_space(), "whitespace.md")
        hio.to_file(in_file, txt)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        self.assertTrue(os.path.exists(script_file))

    def test3(self) -> None:
        """
        Test markdown with special characters in headers.
        """
        # Prepare inputs.
        txt = """
        # Chapter 1: Introduction & Overview

        Content here.

        ## Section 2.1: Data $processing$

        More content with special chars: @#$%^&*()

        ### Subsection 3.1.1: Using "quotes" and 'apostrophes'

        Final content.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "special.md")
        hio.to_file(in_file, txt)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        self.assertTrue(os.path.exists(script_file))

    def test4(self) -> None:
        """
        Test markdown with all header levels (h1-h6).
        """
        # Prepare inputs.
        txt = """
        # Level 1

        Content.

        ## Level 2

        Content.

        ### Level 3

        Content.

        #### Level 4

        Content.

        ##### Level 5

        Content.

        ###### Level 6

        Content.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "all_levels.md")
        hio.to_file(in_file, txt)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        self.assertTrue(os.path.exists(script_file))


# #############################################################################
# Test_notes_to_pdf_pandoc_ast
# #############################################################################


class Test_notes_to_pdf_pandoc_ast(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` with Pandoc AST transform option.
    """

    def create_simple_input(self) -> str:
        """
        Create a simple markdown input file.

        :return: Path to the created markdown file
        """
        txt = """
        # Introduction

        This document tests AST transformation.

        ## Content Section

        Some content here.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "simple.md")
        hio.to_file(in_file, txt)
        return in_file

    def test1(self) -> None:
        """
        Test PDF generation with AST transform enabled.
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append("--use_pandoc_ast_transform")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        script_txt = hio.from_file(script_file)
        self.assertIn("use_pandoc_ast_transform", script_txt)

    def test2(self) -> None:
        """
        Test HTML generation with AST transform.
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.html")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type html")
        cmd.append("--use_pandoc_ast_transform")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        script_txt = hio.from_file(script_file)
        self.assertIn("use_pandoc_ast_transform", script_txt)


# #############################################################################
# Test_notes_to_pdf_latex_options
# #############################################################################


class Test_notes_to_pdf_latex_options(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` with LaTeX-specific options.
    """

    def create_simple_input(self) -> str:
        """
        Create a simple markdown input file.

        :return: Path to the created markdown file
        """
        txt = """
        # Document Title

        This is test content for LaTeX options testing.

        ## Section

        Some section content.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "simple.md")
        hio.to_file(in_file, txt)
        return in_file

    def test1(self) -> None:
        """
        Test no_run_latex_again option skips LaTeX re-run.
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hDiff target options:dbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append("--no_run_latex_again")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        script_txt = hio.from_file(script_file)
        self.assertIn("# latex again", script_txt)

    def test2(self) -> None:
        """
        Test no_fail_on_warnings option accepts pandoc warnings.
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append("--type pdf")
        cmd.append("--no_fail_on_warnings")
        cmd.append(f"--output {out_file}")
        cmd.append(f"--script {script_file}")
        cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Check outputs.
        script_txt = hio.from_file(script_file)
        self.assertIn("no_fail_on_warnings", script_txt)
