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
        _LOG.debug(hprint.to_str("txt"))
        # Normalize input and write to temp file.
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        _LOG.debug("return=%s", in_file)
        return in_file

    def create_input_file1(self) -> str:
        # Create test markdown with multiple header levels and list items.
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

    # TODO(gp): Run this calling directly the code and not executing the script.
    def run_notes_to_pdf(
        self, in_file: str, type_: str, cmd_opts: str, expected: str = ""
    ) -> Tuple[str, str]:
        """
        Run the `notes_to_pdf.py` script with the specified options.

        This function constructs and executes a command to convert notes
        to a PDF or HTML file using the `notes_to_pdf.py` script.

        :param in_file: Path to the input file containing the notes
        :param type_: The output format, either 'pdf' or 'html'
        :param cmd_opts: Additional command-line options to pass to the script
        :param expected: Expected output to compare against (if provided, assertion is performed)
        :return: A tuple containing the script content and the output content
        """
        _LOG.debug(hprint.to_str("in_file type_"))
        # Construct command to invoke notes_to_pdf.py with specified options.
        # notes_to_pdf.py \
        #   --input lectures_source/Lesson1-Intro.txt \
        #   --type slides \
        #   --output tmp.pdf \
        #   --skip_action copy_to_gdrive \
        #   --skip_action open \
        #   --skip_action cleanup_after
        cmd = []
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append(f"--type {type_}")
        out_dir = self.get_scratch_space()
        # Save script file to capture all executed commands for inspection.
        script_file = os.path.join(out_dir, "script.sh")
        cmd.append(f"--script {script_file}")
        out_file = os.path.join(out_dir, f"output.{type_}")
        cmd.append(f"--output {out_file}")
        cmd.append(cmd_opts)
        # cmd.append("--skip_action copy_to_gdrive")
        cmd.append("--skip_action open")
        # The command line looks like:
        # /app/helpers_root/dev_scripts_helpers/documentation/notes_to_pdf.py \
        #   --input /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/input.md \
        #   --type pdf \
        #   --tmp_dir /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch \
        #   --script /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/script.sh \
        #   --output /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/output.pdf
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
        # Read output file if it was generated.
        output_txt = ""
        if os.path.exists(out_file):
            output_txt = hio.from_file(out_file)
        # Read generated script with all executed commands.
        script_txt = ""
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        _LOG.debug("return=(script_txt[%d], output_txt[%d])", len(script_txt), len(output_txt))
        # Perform assertion if expected output provided.
        if expected:
            actual = f"script_txt:\n{script_txt}\n"
            actual += f"output_txt:\n{output_txt}\n"
            self.assert_equal(actual, expected, purify_text=True)
        return script_txt, output_txt

    def test1(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf --preview
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = "--preview_actions"
        # Run the script.
        script_txt, output_txt = self.run_notes_to_pdf(in_file, type_, cmd_opts)
        # Check that preview mode returns empty output (no actual generation).
        self.assertEqual(script_txt, "")
        self.assertEqual(output_txt, "")

    @pytest.mark.superslow
    def test2(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = ""
        # Expected output from golden file.
        # TODO(ai_gp): Assign using """ with dedent
        expected = (
            "script_txt:\n"
            "#/bin/bash -xe\n"
            "# cleanup_before\n"
            "## skipping this action\n"
            "# preprocess_notes\n"
            "$GIT_ROOT/dev_scripts_helpers/documentation/preprocess_notes.py --input"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/input.md"
            " --output"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt"
            " --type pdf --toc_type none --output_format latex\n"
            "# render_images\n"
            "$GIT_ROOT/dev_scripts_helpers/documentation/render_images.py --input"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt"
            " --output"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image.txt"
            " --action render\n"
            "# run_pandoc\n"
            "container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e"
            " AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e"
            " CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e"
            " CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount"
            " type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image2.txt"
            " --output"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json"
            " -t json --fail-if-warnings\n"
            "container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e"
            " AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e"
            " CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e"
            " CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount"
            " type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json"
            " --output"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.tex"
            " --template /dev_scripts_helpers/documentation/pandoc.latex -f json"
            " -t latex --fail-if-warnings -V geometry:margin=1in"
            " --number-sections --highlight-style=tango -s\n"
            "# latex\n"
            "cp -f $GIT_ROOT/dev_scripts_helpers/documentation/latex_abbrevs.sty"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch\n"
            "container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e"
            " AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e"
            " CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e"
            " CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount"
            " type=bind,source=$GIT_ROOT,target=/app tmp.latex.arm64.417056b0"
            " pdflatex -output-directory"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch"
            " --interaction=nonstopmode --halt-on-error --shell-escape"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.tex\n"
            "# latex again\n"
            "# compress_pdf\n"
            "## skipping this action\n"
            "\\cp -af"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/tmp.notes_to_pdf.pdf"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/output.pdf\n"
            "# copy_to_gdrive\n"
            "## skipping this action\n"
            "# open\n"
            "## skipping this action\n"
            "# cleanup_after\n"
            "## skipping this action\n"
            "output_txt:\n"
            "\n"
        )
        # Run the script and verify output.
        self.run_notes_to_pdf(in_file, type_, cmd_opts, expected=expected)

    @pytest.mark.superslow
    def test3(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf --filter_by_header Header2
        """
        # Prepare inputs.
        in_file = self.create_input_file1()
        type_ = "pdf"
        cmd_opts = "--filter_by_header Header2"
        # Expected output from golden file.
        # TODO(ai_gp): Assign using """ with dedent
        expected = (
            "script_txt:\n"
            "#/bin/bash -xe\n"
            "# cleanup_before\n"
            "## skipping this action\n"
            "# preprocess_notes\n"
            "$GIT_ROOT/dev_scripts_helpers/documentation/preprocess_notes.py --input"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.filter_by_header.txt"
            " --output"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt"
            " --type pdf --toc_type none --output_format latex\n"
            "# render_images\n"
            "$GIT_ROOT/dev_scripts_helpers/documentation/render_images.py --input"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.preprocess_notes.txt"
            " --output"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image.txt"
            " --action render\n"
            "# run_pandoc\n"
            "container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e"
            " AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e"
            " CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e"
            " CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount"
            " type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image2.txt"
            " --output"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json"
            " -t json --fail-if-warnings\n"
            "container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e"
            " AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e"
            " CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e"
            " CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount"
            " type=bind,source=$GIT_ROOT,target=/app pandoc/core:3.7"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.render_image2.txt.ast.json"
            " --output"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.tex"
            " --template /dev_scripts_helpers/documentation/pandoc.latex -f json"
            " -t latex --fail-if-warnings -V geometry:margin=1in"
            " --number-sections --highlight-style=tango -s\n"
            "# latex\n"
            "cp -f $GIT_ROOT/dev_scripts_helpers/documentation/latex_abbrevs.sty"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch\n"
            "container run --rm --user $(id -u):$(id -g) -e AM_GDRIVE_PATH -e"
            " AM_TELEGRAM_TOKEN -e CSFY_AWS_PROFILE -e CSFY_AWS_S3_BUCKET -e"
            " CSFY_ECR_BASE_PATH -e CSFY_HOST_NAME -e CSFY_HOST_OS_NAME -e"
            " CSFY_HOST_OS_VERSION -e CSFY_HOST_USER_NAME --workdir /app --mount"
            " type=bind,source=$GIT_ROOT,target=/app tmp.latex.arm64.417056b0"
            " pdflatex -output-directory"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch"
            " --interaction=nonstopmode --halt-on-error --shell-escape"
            " /dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.tex\n"
            "# latex again\n"
            "# compress_pdf\n"
            "## skipping this action\n"
            "\\cp -af"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/tmp.notes_to_pdf.pdf"
            " $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test3/tmp.scratch/output.pdf\n"
            "# copy_to_gdrive\n"
            "## skipping this action\n"
            "# open\n"
            "## skipping this action\n"
            "# cleanup_after\n"
            "## skipping this action\n"
            "output_txt:\n"
            "\n"
        )
        # Run the script and verify output.
        self.run_notes_to_pdf(in_file, type_, cmd_opts, expected=expected)

    # TODO(ai_gp): Check why this fails.
    @pytest.mark.superslow
    @pytest.mark.skipif(sys.platform == "darwin", reason="")
    def test4(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md --type slides --toc_type navigation
        """
        # Prepare inputs with embedded LaTeX content (for slides with table).
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
        # TODO(gp): Fill in expected value once test runs successfully on Linux.
        expected = ""
        # Run the script and verify output.
        self.run_notes_to_pdf(in_file, type_, cmd_opts, expected=expected)
