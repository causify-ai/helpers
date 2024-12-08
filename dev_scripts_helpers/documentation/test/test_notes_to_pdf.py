import logging
import os
from typing import Any, Optional, Tuple

import pytest

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _create_in_file(self_: Any) -> str:
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
    in_file = os.path.join(self_.get_scratch_space(), "input.md")
    hio.to_file(in_file, txt)
    return in_file


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_notes_to_pdf1(hunitest.TestCase):
    def test1(self) -> None:
        """
        > notes_to_pdf.py --input input.md -t pdf --preview.
        """
        in_file = _create_in_file(self)
        cmd_opts = "--preview_actions"
        self.run_notes_to_pdf(in_file, "pdf", cmd_opts)

    def test2(self) -> None:
        """
        > notes_to_pdf.py --input input.md -t pdf.
        """
        in_file = _create_in_file(self)
        cmd_opts = ""
        self.run_notes_to_pdf(in_file, "pdf", cmd_opts)

    def test3(self) -> None:
        """
        > notes_to_pdf.py --input input.md -t pdf --filter_by_header Header2.
        """
        in_file = _create_in_file(self)
        cmd_opts = "--filter_by_header Header2"
        self.run_notes_to_pdf(in_file, "pdf", cmd_opts)

    def run_notes_to_pdf(
        self, in_file: str, type_: str, cmd_opts: str
    ) -> Tuple[Optional[str], Optional[str]]:
        # notes_to_pdf.py \
        #   --input notes/MSML610/Lesson1-Intro.txt \
        #   --type slides \
        #   --output tmp.pdf \
        #   --skip_action copy_to_gdrive \
        #   --skip_action open \
        #   --skip_action cleanup_after
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        #
        tmp_dir = self.get_scratch_space()
        out_file = os.path.join(tmp_dir, "output.pdf")
        #
        script_file = os.path.join(tmp_dir, "script.sh")
        #
        cmd = []
        cmd.append(exec_path)
        cmd.append(f"--input {in_file}")
        cmd.append(f"--type {type_}")
        cmd.append(f"--tmp_dir {tmp_dir}")
        cmd.append(f"--script {script_file}")
        cmd.append(f"--output {out_file}")
        cmd.append(cmd_opts)
        # cmd.append("--action preprocess_notes")
        # cmd.append("--action run_pandoc")
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
