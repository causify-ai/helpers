import logging

import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)
# #############################################################################
# Test_remove_table_of_contents1
# #############################################################################


class Test_remove_table_of_contents1(hunitest.TestCase):
    def test_with_toc(self) -> None:
        """
        Test removing table of contents from markdown text.
        """
        # Prepare inputs.
        text = """
        # Introduction

        This is an introduction.

        <!-- toc -->
        - [Section 1](#section-1)
        - [Section 2](#section-2)
        <!-- tocstop -->

        ## Section 1

        Content of section 1.
        """
        expected = """
        # Introduction

        This is an introduction.



        ## Section 1

        Content of section 1.
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmarkdo.remove_table_of_contents(text)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test_without_toc(self) -> None:
        """
        Test text without table of contents remains unchanged.
        """
        # Prepare inputs.
        text = """
        # Introduction

        This is an introduction.

        ## Section 1

        Content of section 1.
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmarkdo.remove_table_of_contents(text)
        # Check output.
        self.assert_equal(actual, text)

    def test_multiline_toc(self) -> None:
        """
        Test removing multi-line table of contents.
        """
        # Prepare inputs.
        text = """
        # Introduction

        <!-- toc -->
        - [Section 1](#section-1)
          - [Subsection 1.1](#subsection-11)
        - [Section 2](#section-2)
          - [Subsection 2.1](#subsection-21)
          - [Subsection 2.2](#subsection-22)
        <!-- tocstop -->

        ## Section 1
        """
        expected = """
        # Introduction



        ## Section 1
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmarkdo.remove_table_of_contents(text)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)
