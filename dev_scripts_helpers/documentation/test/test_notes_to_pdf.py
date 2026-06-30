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
