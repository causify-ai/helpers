import logging

import dev_scripts_helpers.documentation.extract_headers_from_markdown as dshdehfma
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_headers_from_markdown1
# #############################################################################


class Test_extract_headers_from_markdown1(hunitest.TestCase):

    def test1(self) -> None:
        # Prepare inputs.
        content = r"""
        # Header1
        ## Header2
        # Header3
        """
        content = hprint.dedent(content)
        input_file = self.get_scratch_space() + "/input.md"
        output_file = self.get_scratch_space() + "/output.md"
        hio.to_file(input_file, content)
        # Call tested function.
        parser = dshdehfma._parse()
        args = parser.parse_args(
            [
                "-i",
                input_file,
                "-o",
                output_file,
                "--mode",
                "headers",
                "--max-level",
                "3",
            ]
        )
        dshdehfma._main(args)
        # Check output.
        act = hio.from_file(output_file)
        exp = r"""
        # Header1
        ## Header2
        # Header3
        """
        self.assert_equal(act, exp, dedent=True)
