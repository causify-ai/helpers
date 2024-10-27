import logging
import os
from typing import List

import dev_scripts_helpers.documentation.transform_txt as dsdoremd
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


class Test_markdown_to_latex1(hunitest.TestCase):

    def test_simple_nested_list(self):
        """
        Test a simple nested list with no frame title.
        """
        markdown = [
            "* Item 1",
            "  * Subitem 1.1",
            "  * Subitem 1.2",
            "* Item 2"
        ]
        expected_output = (
            "\\begin{itemize}\n"
            "  \\item Item 1\n"
            "    \\item Subitem 1.1\n"
            "    \\item Subitem 1.2\n"
            "  \\item Item 2\n"
            "\\end{itemize}\n"
        )
        self.assertEqual(markdown_to_latex(markdown), expected_output)

    def test_list_with_frame_title(self):
        """Test a nested list that includes a frame title."""
        markdown = [
            "* Title of Frame",
            "  * Item 1",
            "    * Subitem 1.1",
            "  * Item 2"
        ]
        expected_output = (
            "\\begin{frame}{Title of Frame}\n"
            "\\begin{itemize}\n"
            "  \\item Title of Frame\n"
            "    \\item Item 1\n"
            "      \\item Subitem 1.1\n"
            "    \\item Item 2\n"
            "\\end{itemize}\n"
            "\\end{frame}\n"
        )
        self.assertEqual(markdown_to_latex(markdown), expected_output)

    def test_deeply_nested_list(self):
        """Test a deeply nested list structure."""
        markdown = [
            "* Level 1",
            "  * Level 2",
            "    * Level 3",
            "      * Level 4"
        ]
        expected_output = (
            "\\begin{itemize}\n"
            "  \\item Level 1\n"
            "    \\item Level 2\n"
            "      \\item Level 3\n"
            "        \\item Level 4\n"
            "\\end{itemize}\n"
        )
        self.assertEqual(markdown_to_latex(markdown), expected_output)

    def test1(self) -> None:
        """
        Check output dir and file names correctness for absolute destination
        path.
        """
        # Example Usage:
        markdown_text = """
        * Title of Frame
        - Item 1
          - Subitem 1.1
            - Subitem 1.1.1
          - Subitem 1.2
        - Item 2
          1. Ordered Subitem 2.1
          2. Ordered Subitem 2.2
        """

        latex_text = dsdoremd.markdown_to_latex(markdown_text)
        print(latex_text)


