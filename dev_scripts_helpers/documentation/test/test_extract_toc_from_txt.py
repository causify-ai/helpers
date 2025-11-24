import logging

import dev_scripts_helpers.documentation.extract_toc_from_txt as dshdetoftr
import helpers.hio as hio
import helpers.hlatex as hlatex
import helpers.hmarkdown_headers as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_toc_from_txt1
# #############################################################################


class Test_extract_toc_from_txt1(hunitest.TestCase):
    def test_md1(self) -> None:
        """
        Test extraction of headers from a Markdown file.
        """
        # TODO(ai_gp): Implement the testing functions.
        # Read a file using self.get_input() + "/input.md"
        # Call the script extract_toc_from_txt.py using a hsystem
        # Read the output of the script
        # Use check_string to verify the output is correct


    def test_tex1(self) -> None:
        """
        Test extraction of headers from a LaTeX file.
        """
        # TODO(ai_gp): Implement the testing functions.
        # Read a file using self.get_input() + "/input.md"
        # Call the script extract_toc_from_txt.py using a hsystem
        # Read the output of the script
        # Use check_string to verify the output is correct
