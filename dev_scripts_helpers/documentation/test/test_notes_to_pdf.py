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

    def create_in_file(self) -> str:
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

    def run_notes_to_pdf(
        self, in_file: str, type_: str, cmd_opts: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Run the notes_to_pdf script with the specified options.

        This function constructs and executes a command to convert notes
        to a PDF or HTML file using the notes_to_pdf script.

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
        tmp_dir = self.get_scratch_space()
        cmd.append(f"--tmp_dir {tmp_dir}")
        script_file = os.path.join(tmp_dir, "script.sh")
        cmd.append(f"--script {script_file}")
        hdbg.dassert_in(type_, ["pdf", "html"])
        out_file = os.path.join(tmp_dir, f"output.{type_}")
        cmd.append(f"--output {out_file}")
        cmd.append(cmd_opts)
        #
        cmd = " ".join(cmd)
        hsystem.system(cmd)
        # Check that the file exists.
        if type_ == "pdf":
            out_file = os.path.join(tmp_dir, "tmp.pandoc.tex")
        elif type_ == "html":
            out_file = os.path.join(tmp_dir, "tmp.pandoc.html")
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

    def test1(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf --preview
        """
        in_file = self.create_in_file()
        cmd_opts = "--preview_actions"
        script_txt, output_txt = self.run_notes_to_pdf(in_file, "pdf", cmd_opts)
        self.assertEqual(script_txt, None)
        self.assertEqual(output_txt, None)

    def test2(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf
        """
        in_file = self.create_in_file()
        cmd_opts = ""
        script_txt, output_txt = self.run_notes_to_pdf(in_file, "pdf", cmd_opts)
        #
        txt = "script_txt:\n%s\n" % script_txt
        txt += "output_txt:\n%s\n" % output_txt
        self.check_string(txt)

    def test3(self) -> None:
        """
        Run:
        > notes_to_pdf.py --input input.md -t pdf --filter_by_header Header2
        """
        in_file = self.create_in_file()
        cmd_opts = "--filter_by_header Header2"
        script_txt, output_txt = self.run_notes_to_pdf(in_file, "pdf", cmd_opts)
        #
        txt = "script_txt:\n%s\n" % script_txt
        txt += "output_txt:\n%s\n" % output_txt
        self.check_string(txt)
