import logging
import os
from typing import Optional, Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_notes_to_pdf1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_notes_to_pdf1(hunitest.TestCase):

    def create_input_file(self) -> str:
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
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        in_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(in_file, txt)
        return in_file

    # TODO(gp): Run this calling directly the code and not executing the script.
    def run_notes_to_pdf(
        self, in_file: str, type_: str, cmd_opts: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Run the `notes_to_pdf.py` script with the specified options.

        This function constructs and executes a command to convert notes
        to a PDF or HTML file using the `notes_to_pdf.py` script.

        :param in_file: Path to the input file containing the notes.
        :param type_: The output format, either 'pdf' or 'html'.
        :param cmd_opts: Additional command-line options to pass to the
            script.
        :returns: A tuple containing the script content and the output
            content.
        """
        # notes_to_pdf.py \
        #   --input notes/MSML610/Lesson1-Intro.txt \
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
        # Save a script file to store the commands.
        script_file = os.path.join(out_dir, "script.sh")
        cmd.append(f"--script {script_file}")
        hdbg.dassert_in(type_, ["pdf", "html"])
        out_file = os.path.join(out_dir, f"output.{type_}")
        cmd.append(f"--output {out_file}")
        cmd.append(cmd_opts)
        # The command line looks like:
        # /app/helpers_root/dev_scripts_helpers/documentation/notes_to_pdf.py \
        #   --input /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/input.md \
        #   --type pdf \
        #   --tmp_dir /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch \
        #   --script /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/script.sh \
        #   --output /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes_to_pdf1.test2/tmp.scratch/output.pdf
        cmd = " ".join(cmd)
        hsystem.system(cmd)
        # Check that the file exists.
        if type_ == "pdf":
            out_file = os.path.join(out_dir, "tmp.pandoc.tex")
        elif type_ == "html":
            out_file = os.path.join(out_dir, "tmp.pandoc.html")
        else:
            raise ValueError(f"Invalid type_='{type_}'")
        # Check the content of the file, if needed.
        output_txt: Optional[str] = None
        if os.path.exists(out_file):
            output_txt = hio.from_file(out_file)
        # Read generated script with all the commands.
        script_txt: Optional[str] = None
        if os.path.exists(script_file):
            script_txt = hio.from_file(script_file)
        return script_txt, output_txt

    # ///////////////////////////////////////////////////////////////////////////

    def test1(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf --preview
        """
        # Prepare inputs.
        in_file = self.create_input_file()
        type_ = "pdf"
        cmd_opts = "--preview_actions"
        # Run the script.
        script_txt, output_txt = self.run_notes_to_pdf(in_file, type_, cmd_opts)
        # Check.
        self.assertEqual(script_txt, None)
        self.assertEqual(output_txt, None)

    def test2(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf
        """
        # Prepare inputs.
        in_file = self.create_input_file()
        type_ = "pdf"
        cmd_opts = ""
        # Run the script.
        script_txt, output_txt = self.run_notes_to_pdf(in_file, type_, cmd_opts)
        # Check.
        txt = "script_txt:\n%s\n" % script_txt
        txt += "output_txt:\n%s\n" % output_txt
        self.check_string(txt, purify_text=True)

    def test3(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf --filter_by_header Header2
        """
        # Prepare inputs.
        in_file = self.create_input_file()
        type_ = "pdf"
        cmd_opts = "--filter_by_header Header2"
        # Run the script.
        script_txt, output_txt = self.run_notes_to_pdf(in_file, type_, cmd_opts)
        # Check.
        txt = "script_txt:\n%s\n" % script_txt
        txt += "output_txt:\n%s\n" % output_txt
        self.check_string(txt, purify_text=True)
