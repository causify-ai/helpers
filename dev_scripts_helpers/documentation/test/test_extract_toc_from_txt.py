import logging

import dev_scripts_helpers.documentation.extract_toc_from_txt as dshdetoftr
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_toc_from_txt1
# #############################################################################


class Test_extract_toc_from_txt1(hunitest.TestCase):
    def test1(self) -> None:
        # Prepare inputs.
        content = r"""
        # Header1
        ## Header2
        # Header3
        """
        input_file_name = "dummy"
        content = hprint.dedent(content)
        content = content.split("\n")
        mode = "headers"
        max_level = 3
        output_file = self.get_scratch_space() + "/output.md"
        # Call tested function.
        dshdetoftr._extract_headers_from_markdown(
            input_file_name, content, mode, max_level, output_file
        )
        # Check output.
        actual = hio.from_file(output_file)
        expected = r"""
        # Header1
        ## Header2
        # Header3
        """
        self.assert_equal(actual, expected, dedent=True)
