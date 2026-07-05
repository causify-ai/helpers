import os
from typing import List
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.clean_markdown as dshdclma


# #############################################################################
# Test_clean_markdown_py
# #############################################################################


class Test_clean_markdown_py(hunitest.TestCase):
    """
    End-to-end tests for the `clean_markdown.py` executable.
    """

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `dshdclma._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshdclma._parse()
        with mock.patch("sys.argv", argv):
            dshdclma._main(parser)

    def test1(self) -> None:
        """
        Test junk markup is removed from the output file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        output_file = os.path.join(scratch_dir, "output.md")
        content = 'Text <span class="label">Part I.</span> end'
        hio.to_file(input_file, content)
        argv = [
            "clean_markdown.py",
            "--input",
            input_file,
            "--output",
            output_file,
        ]
        # Prepare outputs.
        expected = "Text Part I. end"
        # Run test.
        self._run_main(argv)
        # Check outputs.
        actual = hio.from_file(output_file).strip()
        self.assert_equal(actual, expected)