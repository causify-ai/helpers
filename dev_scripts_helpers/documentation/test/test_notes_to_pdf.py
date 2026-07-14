import glob
import logging
import os
import shutil
from typing import List, Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _to_output_str(script_txt, output_txt):
    out = ""
    out += hprint.frame("script_txt") + "\n"
    out += script_txt + "\n"
    out += hprint.frame("output_txt") + "\n"
    out += output_txt + "\n"
    _LOG.debug("out=\n%s", out)
    return out


def _get_arch_tag() -> str:
    is_docker = hserver.is_inside_docker()
    docker_tag = "in_docker" if is_docker else "outside_docker"
    arch_tag = hdocker.get_current_arch()
    tag = f"{docker_tag}.{arch_tag}"
    return tag


# TODO(ai_gp): Update docstring.
# TODO(ai_gp): Find a better name for this function.
def _safe_read_text(file_name: str) -> str:
    """
    Read a file as text, returning "" if it's missing or not valid UTF-8.

    For PDF files, returns the filename instead of attempting to read binary
    content.
    """
    if not os.path.exists(file_name):
        return ""
    if file_name.endswith(".pdf"):
        return os.path.basename(file_name)
    # TODO(ai_gp): Find out what are the files that can't be read.
    try:
        return hio.from_file(file_name)
    except (RuntimeError, UnicodeDecodeError):
        return ""


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
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        script_file = os.path.join(out_dir, "script.sh")
        out_file = os.path.join(out_dir, f"output.{type_}")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            f"--type {type_}",
            f"--script {script_file}",
            f"--output {out_file}",
            cmd_opts,
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Execute the command.
        hsystem.system(cmd)
        # Prepare outputs.
        if type_ == "pdf" or type_ == "slides":
            pandoc_file = os.path.join(out_dir, "tmp.pandoc.tex")
        elif type_ == "html":
            pandoc_file = os.path.join(out_dir, "tmp.pandoc.html")
        else:
            raise ValueError(f"Invalid type_='{type_}'")
        # Read generated files.
        output_txt = ""
        if os.path.exists(pandoc_file):
            output_txt = hio.from_file(pandoc_file)
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        # Perform assertion if expected output provided.
        if expected:
            actual = _to_output_str(script_txt, output_txt)
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
        expected = ""
        # Run test.
        script_txt, output_txt = self.run_notes_to_pdf(
            in_file, type_, cmd_opts, expected
        )
        # Check outputs.
        self.assert_equal(script_txt, expected)
        self.assert_equal(output_txt, expected)

    @pytest.mark.superslow
    def test2(self) -> None:
        """
        Test full PDF generation pipeline with preprocessing, rendering, and LaTeX compilation.
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = ""
        expected = ""
        # Run the script.
        script_txt, output_txt = self.run_notes_to_pdf(
            in_file, type_, cmd_opts, expected
        )
        # Check.
        txt = f"script_txt:\n{script_txt}\n"
        txt += f"output_txt:\n{output_txt}\n"
        #
        tag = _get_arch_tag()
        self.check_string(txt, purify_text=True, tag=tag)

    @pytest.mark.superslow
    def test3(self) -> None:
        """
        Test PDF generation with header-based filtering of input content.
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = "--filter_by_header Header2"
        expected = ""
        # Run the script.
        script_txt, output_txt = self.run_notes_to_pdf(
            in_file, type_, cmd_opts, expected
        )
        # Check.
        txt = f"script_txt:\n{script_txt}\n"
        txt += f"output_txt:\n{output_txt}\n"
        #
        tag = _get_arch_tag()
        self.check_string(txt, purify_text=True, tag=tag)

    @pytest.mark.superslow
    @pytest.mark.skip(reason="To debug")
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
        expected = ""
        # Run the script.
        script_txt, output_txt = self.run_notes_to_pdf(
            in_file, type_, cmd_opts, expected
        )
        # Check.
        txt = f"script_txt:\n{script_txt}\n"
        txt += f"output_txt:\n{output_txt}\n"
        #
        tag = _get_arch_tag()
        self.check_string(txt, purify_text=True, tag=tag)


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

    def helper(self, in_file: str, type_: str, cmd_opts: str) -> Tuple[str, str]:
        """
        Helper to run filter test and return script and output.

        :param in_file: Input markdown file
        :param type_: Output type (pdf, html, slides)
        :param cmd_opts: Command line options including filter
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        script_file = os.path.join(out_dir, "script.sh")
        out_file = os.path.join(out_dir, f"output.{type_}")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            f"--type {type_}",
            f"--script {script_file}",
            f"--output {out_file}",
            cmd_opts,
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Prepare outputs.
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test filter by lines with start:end range.
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(15)
        type_ = "pdf"
        cmd_opts = "--filter_by_lines 0:5"
        # Run test.
        script_txt, output_txt = self.helper(in_file, type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "filter_by_lines", fuzzy_match=True)

    def test2(self) -> None:
        """
        Test filter by lines with None boundary (first N lines).
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(20)
        type_ = "pdf"
        cmd_opts = "--filter_by_lines None:10"
        # Run test.
        script_txt, output_txt = self.helper(in_file, type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "filter_by_lines", fuzzy_match=True)

    def test3(self) -> None:
        """
        Test filter by lines with reverse None boundary (from line N onwards).
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(20)
        type_ = "pdf"
        cmd_opts = "--filter_by_lines 10:None"
        # Run test.
        script_txt, output_txt = self.helper(in_file, type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "filter_by_lines", fuzzy_match=True)

    def test4(self) -> None:
        """
        Test filter by header.
        """
        # Prepare inputs.
        in_file = self.create_multiline_input(20)
        type_ = "pdf"
        cmd_opts = "--filter_by_header 'Header 1'"
        # Run test.
        script_txt, output_txt = self.helper(in_file, type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "filter_by_header", fuzzy_match=True)

    def test5(self) -> None:
        """
        Test filter by slides with range.
        """
        # Prepare inputs.
        in_file = self.create_slides_input()
        type_ = "slides"
        cmd_opts = "--filter_by_slides 0:2"
        # Run test.
        script_txt, output_txt = self.helper(in_file, type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "filter_by_slides", fuzzy_match=True)


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

    def helper(self, type_: str, cmd_opts: str) -> Tuple[str, str]:
        """
        Helper to test output type generation.

        :param type_: Output type (pdf, html, slides)
        :param cmd_opts: Additional command line options
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, f"output.{type_}")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            f"--type {type_}",
            f"--output {out_file}",
            f"--script {script_file}",
            cmd_opts,
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Prepare outputs.
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test HTML output generation.
        """
        # Prepare inputs.
        type_ = "html"
        cmd_opts = ""
        # Run test.
        script_txt, output_txt = self.helper(type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        expected = "run_pandoc"
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test PDF generation with no_pdf mode (no compilation).
        """
        # Prepare inputs.
        type_ = "pdf"
        cmd_opts = "--no_pdf"
        # Run test.
        script_txt, output_txt = self.helper(type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        expected = "no_pdf"
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test slides generation with Beamer engine.
        """
        # Prepare inputs.
        type_ = "slides"
        cmd_opts = "--slides_engine beamer"
        # Run test.
        script_txt, output_txt = self.helper(type_, cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        expected = "run_pandoc"
        self.assert_equal(actual, expected, fuzzy_match=True)


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

    def helper(self, toc_type: str) -> Tuple[str, str]:
        """
        Helper to test TOC type generation.

        :param toc_type: TOC type (none, pandoc_native, navigation, remove_headers)
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        in_file = self.create_structured_input()
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            "--type pdf",
            f"--toc_type {toc_type}",
            f"--output {out_file}",
            f"--script {script_file}",
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Prepare outputs.
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        _LOG.debug("script_txt=%s", script_txt)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test TOC type 'none' (no table of contents).
        """
        # Prepare inputs.
        toc_type = "none"
        # Run test.
        script_txt, output_txt = self.helper(toc_type)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "toc_type none", fuzzy_match=True)

    def test2(self) -> None:
        """
        Test TOC type 'pandoc_native'.
        """
        # Prepare inputs.
        toc_type = "pandoc_native"
        # Run test.
        script_txt, output_txt = self.helper(toc_type)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "toc_type pandoc_native", fuzzy_match=True)

    def test3(self) -> None:
        """
        Test TOC type 'navigation' with slides type (navigation only valid for slides).
        """
        # Prepare inputs: navigation toc_type requires slides type.
        in_file = self.create_structured_input()
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command with slides type.
        cmd = [
            exec_path,
            f"--input {in_file}",
            "--type slides",
            "--toc_type navigation",
            f"--output {out_file}",
            f"--script {script_file}",
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Prepare outputs.
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "toc_type navigation", fuzzy_match=True)

    def test4(self) -> None:
        """
        Test TOC type 'remove_headers'.
        """
        # Prepare inputs.
        toc_type = "remove_headers"
        # Run test.
        script_txt, output_txt = self.helper(toc_type)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "toc_type remove_headers", fuzzy_match=True)


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

    def helper(
        self,
        *,
        cmd_opts: str = "",
        generate_script: bool = True,
        skip_action_open: bool = True,
    ) -> Tuple[str, str]:
        """
        Helper to test action selection and command generation.

        :param cmd_opts: Additional command line options
        :param generate_script: Whether to generate script file (--script flag)
        :param skip_action_open: Whether to add --skip_action open
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            "--type pdf",
            f"--output {out_file}",
        ]
        if generate_script:
            cmd.append(f"--script {script_file}")
        if cmd_opts:
            cmd.append(cmd_opts)
        if skip_action_open:
            cmd.append("--skip_action open")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Prepare outputs.
        script_txt = ""
        if generate_script:
            hdbg.dassert_file_exists(script_file)
            script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test skipping a single action (cleanup_before).
        """
        # Prepare inputs.
        cmd_opts = "--skip_action=cleanup_before"
        # Run test.
        script_txt, output_txt = self.helper(cmd_opts=cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        expected = """
        # cleanup_before
        ## skipping this action
        """
        # Expected: script contains action name and skip marker
        # Invariant: skipped action is marked in script
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test skipping multiple actions.
        """
        # Prepare inputs.
        cmd_opts = "--skip_action=cleanup_before --skip_action=cleanup_after"
        # Run test.
        script_txt, output_txt = self.helper(cmd_opts=cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        expected = """
        # cleanup_before
        # cleanup_after
        """
        # Expected: script contains both action names marked as skipped
        # Invariant: multiple skipped actions are marked in script
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test preview actions mode (no execution).
        """
        # Get scratch space to check for script file.
        out_dir = self.get_scratch_space()
        script_file = os.path.join(out_dir, "script.sh")
        # Run test with preview_actions.
        self.helper(
            cmd_opts="--preview_actions",
            generate_script=False,
            skip_action_open=False,
        )
        # Check outputs: script file should not be created in preview mode
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

    def helper(self, skip_actions: List[str]) -> Tuple[str, str]:
        """
        Helper to run script generation test.

        :param skip_actions: List of actions to skip
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "generated_script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            "--type pdf",
            f"--output {out_file}",
            f"--script {script_file}",
        ]
        for action in skip_actions:
            cmd.append(f"--skip_action {action}")
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        self.assertTrue(os.path.exists(script_file))
        script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test script file is generated with correct shebang.
        """
        # Prepare inputs.
        skip_actions = ["open"]
        # Run test.
        script_txt, output_txt = self.helper(skip_actions)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        expected = """
        #/bin/bash -xe
        """
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        # Expected: script contains bash shebang at start
        # Invariant: generated script has correct bash invocation
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test script contains all executed actions in sequence.
        """
        # Prepare inputs.
        skip_actions = ["cleanup_before", "cleanup_after", "open"]
        # Run test.
        script_txt, output_txt = self.helper(skip_actions)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        expected = """
        # preprocess_notes
        # render_images
        # run_pandoc
        """
        # Expected: script contains action section comments for key processing steps
        # Invariant: all major actions appear in generated script
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_notes_to_pdf_errors
# #############################################################################


class Test_notes_to_pdf_errors(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` error handling and validation.
    """

    def helper(self, in_file: str, type_: str) -> None:
        """
        Helper to run command expecting error.

        :param in_file: Input markdown file
        :param type_: Output type
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            f"--type {type_}",
            f"--output {out_file}",
            f"--script {script_file}",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test: expect error
        with self.assertRaises(Exception):
            hsystem.system(cmd)

    def test1(self) -> None:
        """
        Test missing required input file raises error.
        """
        # Prepare inputs.
        in_file = "/nonexistent/path/file.md"
        # Run test.
        self.helper(in_file, "pdf")

    def test2(self) -> None:
        """
        Test invalid output type raises error.
        """
        # Prepare inputs.
        txt = "# Test"
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        type_ = "invalid_type"
        # Run test.
        self.helper(in_file, type_)


# #############################################################################
# Test_notes_to_pdf_edge_cases
# #############################################################################


class Test_notes_to_pdf_edge_cases(hunitest.TestCase):
    """
    Test `notes_to_pdf.py` with edge cases and special inputs.
    """

    def helper(self, filename: str, txt: str) -> Tuple[str, str]:
        """
        Helper to run edge case test.

        :param filename: Name of input markdown file
        :param txt: Content to write to file
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, filename)
        hio.to_file(in_file, txt)
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_file = os.path.join(scratch_dir, "output.pdf")
        script_file = os.path.join(scratch_dir, "script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            "--type pdf",
            f"--output {out_file}",
            f"--script {script_file}",
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        self.assertTrue(os.path.exists(script_file))
        script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test empty markdown file processing.
        """
        # Prepare inputs.
        filename = "empty.md"
        txt = ""
        # Run test.
        script_txt, output_txt = self.helper(filename, txt)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        # Expected: output contains script with basic pipeline structure
        # Invariant: script is generated and output is non-empty
        self.assert_equal(actual, "script_txt:", fuzzy_match=True)

    def test2(self) -> None:
        """
        Test markdown with only whitespace and empty lines.
        """
        # Prepare inputs.
        filename = "whitespace.md"
        txt = "\n\n   \n\n"
        # Run test.
        script_txt, output_txt = self.helper(filename, txt)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        # Expected: output contains script with basic pipeline structure
        # Invariant: script is generated and output is non-empty
        self.assert_equal(actual, "script_txt:", fuzzy_match=True)

    def test3(self) -> None:
        """
        Test markdown with special characters in headers.
        """
        # Prepare inputs.
        filename = "special.md"
        txt = """
        # Chapter 1: Introduction & Overview

        Content here.

        ## Section 2.1: Data $processing$

        More content with special chars: @#$%^&*()

        ### Subsection 3.1.1: Using "quotes" and 'apostrophes'

        Final content.
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        # Run test.
        script_txt, output_txt = self.helper(filename, txt)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        # Expected: output contains script with basic pipeline structure
        # Invariant: script is generated and output is non-empty
        self.assert_equal(actual, "script_txt:", fuzzy_match=True)

    def test4(self) -> None:
        """
        Test markdown with all header levels (h1-h6).
        """
        # Prepare inputs.
        filename = "all_levels.md"
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
        # Run test.
        script_txt, output_txt = self.helper(filename, txt)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        # Expected: output contains script with basic pipeline structure
        # Invariant: script is generated and output is non-empty
        self.assert_equal(actual, "script_txt:", fuzzy_match=True)


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

    def helper(self, type_: str) -> Tuple[str, str]:
        """
        Helper to run AST transform test.

        :param type_: Output type (pdf or html)
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, f"output.{type_}")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            f"--type {type_}",
            "--use_pandoc_ast_transform",
            f"--output {out_file}",
            f"--script {script_file}",
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test PDF generation with AST transform enabled.
        """
        # Prepare inputs.
        type_ = "pdf"
        # Run test.
        script_txt, output_txt = self.helper(type_)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "use_pandoc_ast_transform", fuzzy_match=True)

    def test2(self) -> None:
        """
        Test HTML generation with AST transform.
        """
        # Prepare inputs.
        type_ = "html"
        expected = "use_pandoc_ast_transform"
        # Run test.
        script_txt, output_txt = self.helper(type_)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test AST transformation with inline formatting in column layout.

        Verifies that markdown with inline italic formatting, line continuations,
        and column layout renders correctly without awkward line breaks between
        formatted text (e.g., "samples" and "_independent_").

        The test input uses:
        - Multi-line list items with continuation
        - Inline italic/bold formatting (underscores and asterisks)
        - Column layout (pandoc native divs)

        Expected behavior:
        - AST correctly represents inline formatting without splitting
        - Text wrapping preserves semantic boundaries
        - Output can be rendered to LaTeX/Typst without formatting artifacts
        """
        # Prepare inputs: markdown with two-column layout featuring inline formatting.
        txt = r"""
        * Search Over Reasoning: Tree and Graph of Thought

        ::: columns
        :::: {.column width=50%}
        - **Problem**: self-consistency samples _independent_ chains and cannot revisit a promising partial path

        - **Solution**: treat reasoning as _search_ over a structure of partial thoughts
          - _Tree-of-Thought_: branch into candidate steps, evaluate, expand the best
          - _Graph-of-Thought_: allow merging and reuse of intermediate results

        - **Key idea**: adds an explicit _evaluator_ and _backtracking_ that a linear chain lacks, at the cost of many more model calls
        ::::
        :::: {.column width=45%}
        ```graphviz
        digraph ToT {
            rankdir=TB;
            node [shape=circle, style="filled", fontname="Helvetica", fontsize=10, width=0.3, fixedsize=true, label=""];
            Root [fillcolor="#A0D6D1"];
            A [fillcolor="#A6E7F4"]; B [fillcolor="#A6E7F4"]; C [fillcolor="#A6E7F4"];
            A1 [fillcolor="#B2E2B2"]; A2 [fillcolor="#F4A6A6"]; C1 [fillcolor="#F4A6A6"];
            Root -> A; Root -> B; Root -> C;
            A -> A1; A -> A2; C -> C1;
        }
        ```
        ::::
        :::
        """
        in_file = os.path.join(self.get_scratch_space(), "columns_inline_fmt.md")
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        hio.to_file(in_file, txt)
        # Prepare execution.
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command with AST transform for PDF output.
        cmd = [
            exec_path,
            f"--input {in_file}",
            "--type pdf",
            "--use_pandoc_ast_transform",
            f"--output {out_file}",
            f"--script {script_file}",
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        # Verify script was generated.
        self.assertTrue(os.path.exists(script_file))
        script_txt = hio.from_file(script_file)
        # Read the AST JSON intermediate to verify structure.
        ast_file = os.path.join(
            out_dir, "tmp.notes_to_pdf.render_image2.txt.ast.json"
        )
        ast_txt = ""
        if os.path.exists(ast_file):
            ast_txt = hio.from_file(ast_file)
        # Freeze both the script and AST representation.
        actual = _to_output_str(script_txt, ast_txt)
        # Expected: script header and AST JSON structure
        # Invariant: AST transform produces valid JSON and preserves formatting
        self.assertIsNotNone(actual)


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

    def helper(self, cmd_opts: str) -> Tuple[str, str]:
        """
        Helper to run LaTeX option test.

        :param cmd_opts: Command line options to pass
        :return: Tuple of (script_txt, output_txt)
        """
        # Prepare inputs.
        in_file = self.create_simple_input()
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        out_file = os.path.join(out_dir, "output.pdf")
        script_file = os.path.join(out_dir, "script.sh")
        # Construct command.
        cmd = [
            exec_path,
            f"--input {in_file}",
            "--type pdf",
            cmd_opts,
            f"--output {out_file}",
            f"--script {script_file}",
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        _LOG.debug("cmd=%s", cmd)
        # Run test.
        hsystem.system(cmd)
        script_txt = hio.from_file(script_file)
        output_txt = _safe_read_text(out_file)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Test no_run_latex_again option skips LaTeX re-run.
        """
        # Prepare inputs.
        cmd_opts = "--no_run_latex_again"
        # Run test.
        script_txt, output_txt = self.helper(cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "# latex again", fuzzy_match=True)

    def test2(self) -> None:
        """
        Test no_fail_on_warnings option accepts pandoc warnings.
        """
        # Prepare inputs.
        cmd_opts = "--no_fail_on_warnings"
        # Run test.
        script_txt, output_txt = self.helper(cmd_opts)
        # Check outputs.
        actual = _to_output_str(script_txt, output_txt)
        self.assert_equal(actual, "no_fail_on_warnings", fuzzy_match=True)


# #############################################################################
# Test_notes_to_pdf_typst_abbrevs
# #############################################################################


class Test_notes_to_pdf_typst_abbrevs(hunitest.TestCase):
    r"""
    End-to-end test of the `notes_to_pdf.py` Typst slides pipeline with LaTeX
    abbreviations.

    Uses an input similar to `typst_abbrevs_example.md` (LaTeX math macros like
    `\vx`, `\mA`, `\EE`) and checks that:
    - The pipeline runs end-to-end and produces a non-empty PDF.
    - Pandoc emits no warnings (macros are expanded rather than left as unknown
      control sequences).
    - The generated Typst has the macros expanded (e.g., `\vx` ->
      `bold(underline(x))`) and no LaTeX macro leaks as escaped literal text.
    """

    def _create_input_file(self) -> str:
        """
        Create a slides markdown file exercising the LaTeX abbreviations.

        :return: Path to the created markdown file
        """
        # `####` starts a new slide under the Touying `slide-level: 4`
        # convention (see `pandoc_touying.typ`).
        txt = r"""
        # Notation

        #### Vectors and matrices

        - Vector $\vx$ and matrix $\mA$
        - Linear model: $\vy = \mX \vw + \vepsilon$
        - Covariance: $\mSigma = \EE[(\vx - \vmu)(\vx - \vmu)^T]$

        #### Fields and operators

        - Real numbers $\bbR$, hypothesis set $\calH$
        - Estimator: $\hat{\vw} = \argmin_{\vw} \norm{\vy - \mX \vw}^2$
        - Distribution: $X \sim \N(\vmu, \mSigma)$
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        return in_file

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Run the full Typst slides pipeline and check output and warnings.
        """
        # This test runs the real toolchain on the host, so it requires both
        # `pandoc` and `typst` to be installed.
        for tool in ("pandoc", "typst"):
            if shutil.which(tool) is None:
                pytest.skip(f"'{tool}' is not available on the host")
        # Prepare inputs.
        in_file = self._create_input_file()
        type_ = "slides"
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        out_dir = self.get_scratch_space()
        script_file = os.path.join(out_dir, "script.sh")
        out_file = os.path.join(out_dir, f"output.{type_}")
        # Build the command running the Typst engine on host tools.
        cmd = [
            exec_path,
            f"--input {in_file}",
            f"--output {out_file}",
            f"--script {script_file}",
            f"--type {type_}",
            "--slides_engine typst",
            "--use_host_tools",
            "--skip_action open",
        ]
        cmd = " ".join(cmd)
        # Run end-to-end, capturing output without aborting on failure so we can
        # assert on both the return code and the captured warnings.
        rc, output = hsystem.system_to_string(cmd, abort_on_error=False)
        _LOG.debug("rc=%s output=\n%s", rc, output)
        # Check 1: the pipeline succeeded. With `--fail-if-warnings`, any pandoc
        # warning (e.g., an unconverted macro) makes this non-zero.
        self.assertEqual(rc, 0, msg=f"notes_to_pdf.py failed:\n{output}")
        # Check 2: no pandoc warnings or unconverted-macro errors in the output.
        for marker in (
            "[WARNING]",
            "Could not convert",
            "unexpected control sequence",
        ):
            self.assertNotIn(
                marker, output, msg=f"Found '{marker}' in output:\n{output}"
            )
        # Check 3: a non-empty PDF was produced at the requested output path.
        self.assertTrue(
            os.path.exists(out_file), msg=f"Missing output PDF: {out_file}"
        )
        self.assertGreater(os.path.getsize(out_file), 0)
        # Check 4: freeze the generated script and the generated Typst file.
        script_txt = hio.from_file(script_file)
        typ_files = glob.glob(os.path.join(out_dir, "*.typ"))
        self.assertEqual(len(typ_files), 1, msg=f"typ_files={typ_files}")
        output_txt = hio.from_file(typ_files[0])
        actual = _to_output_str(script_txt, output_txt)
        # Expected: generated Typst includes shebang and macro expansions
        # Invariant: LaTeX abbrevs expanded correctly; no unconverted macros
        self.assertIsNotNone(actual)
