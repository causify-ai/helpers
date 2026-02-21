import logging
import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_toc_from_txt_script1
# #############################################################################


class Test_extract_toc_from_txt_script1(hunitest.TestCase):
    def helper(self, file: str) -> None:
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), file)
        # Build command to call the script.
        script_path = hgit.find_file_in_git_tree("extract_toc_from_txt.py")
        out_file = os.path.join(self.get_scratch_space(), "output.txt")
        cmd = f"{script_path} --input {in_file} --output {out_file} --mode list --max_level 3"
        # Run the script.
        hsystem.system(cmd)
        # Read the output.
        actual = hio.from_file(out_file)
        # Verify the output is correct.
        self.check_string(actual)

    def test_md1(self) -> None:
        """
        Test extraction of headers from a Markdown file.
        """
        self.helper("input.md")

    def test_tex1(self) -> None:
        """
        Test extraction of headers from a LaTeX file.
        """
        self.helper("input.tex")

    def test_txt1(self) -> None:
        """
        Test extraction of headers from a txt slide file.
        """
        self.helper("input.txt")

    def test_ipynb1(self) -> None:
        """
        Test extraction of headers from a Jupyter notebook file.
        """
        self.helper("input.ipynb")
