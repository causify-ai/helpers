import glob
import logging
import os

import pytest

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class Test_notes_to_pdf1(hunitest.TestCase):
    @pytest.mark.skip
    def test1(self) -> None:
        """
        Convert one txt file to PDF and check that the .tex file is as
        expected.
        """
        file_name = "code_style.txt.test"
        file_name = os.path.join(self.get_input_dir(), file_name)
        file_name = os.path.abspath(file_name)
        #
        act = self._helper(file_name, "pdf")
        self.check_string(act)

    # TODO(gp): This seems flakey.
    @pytest.mark.skip
    def test2(self) -> None:
        """
        Convert one txt file to HTML and check that the .tex file is as
        expected.
        """
        file_name = "code_style.txt.test"
        file_name = os.path.join(
            self.get_input_dir(test_method_name="test1"), file_name
        )
        file_name = os.path.abspath(file_name)
        #
        act = self._helper(file_name, "html")
        self.check_string(act)

    def test_all_notes(self) -> None:
        """
        Convert all the notes in docs/notes to PDF.
        """
        git_dir = hgit.get_client_root(super_module=False)
        dir_name = os.path.join(git_dir, "docs/notes/*.txt")
        file_names = glob.glob(dir_name)
        for file_name in file_names:
            _LOG.debug(hprint.frame(f"file_name={file_name}"))
            self._helper(file_name, "html")

    def _helper(self, in_file: str, type_: str) -> str:
        exec_path = hgit.find_file_in_git_tree("notes_to_pdf.py")
        hdbg.dassert_path_exists(exec_path)
        #
        tmp_dir = self.get_scratch_space()
        out_file = os.path.join(tmp_dir, "output.pdf")
        #
        cmd = []
        cmd.append(exec_path)
        cmd.append(f"--type {type_}")
        cmd.append(f"--tmp_dir {tmp_dir}")
        cmd.append(f"--input {in_file}")
        cmd.append(f"--output {out_file}")
        cmd.append("--action preprocess_notes")
        cmd.append("--action run_pandoc")
        cmd = " ".join(cmd)
        hsystem.system(cmd)
        # Check.
        if type_ == "pdf":
            out_file = os.path.join(tmp_dir, "tmp.pandoc.tex")
        elif type_ == "html":
            out_file = os.path.join(tmp_dir, "tmp.pandoc.html")
        else:
            raise ValueError(f"Invalid type_='{type_}'")
        act: str = hio.from_file(out_file)
        return act
