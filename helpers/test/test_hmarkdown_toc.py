from typing import Optional

import helpers.hmarkdown as hmarkdo
import helpers.hmarkdown_toc as hmartoc
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# Test_extract_yaml_frontmatter
# #############################################################################


class Test_extract_yaml_frontmatter(hunitest.TestCase):
    """
    Test the `extract_yaml_frontmatter()` function.
    """

    def helper(
        self,
        txt: str,
        expected_frontmatter: list,
        expected_remaining: list,
    ) -> None:
        """
        Test helper for `extract_yaml_frontmatter()`.

        :param txt: Input text to process
        :param expected_frontmatter: Expected front matter lines
        :param expected_remaining: Expected remaining lines
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        frontmatter, remaining = hmartoc.extract_yaml_frontmatter(lines)
        # Check outputs.
        self.assertEqual(frontmatter, expected_frontmatter)
        self.assertEqual(remaining, expected_remaining)

    def test1(self) -> None:
        """
        Test extracting YAML front matter from a file.
        """
        # Prepare inputs.
        txt = """
        ---
        title: My Document
        date: 2024-01-01
        ---
        # Content
        This is the main content.
        """
        # Prepare outputs.
        expected_frontmatter = [
            "---",
            "title: My Document",
            "date: 2024-01-01",
            "---",
        ]
        expected_remaining = ["# Content", "This is the main content."]
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test2(self) -> None:
        """
        Test processing a file without YAML front matter.
        """
        # Prepare inputs.
        txt = """
        # Content
        This is the main content.
        """
        # Prepare outputs.
        expected_frontmatter = []
        expected_remaining = ["# Content", "This is the main content."]
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test3(self) -> None:
        """
        Test handling incomplete YAML front matter (missing closing delimiter).
        """
        # Prepare inputs.
        txt = """
        ---
        title: My Document
        # Content without closing delimiter
        """
        # Prepare outputs.
        expected_frontmatter = []
        lines = txt.split("\n")
        expected_remaining = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test4(self) -> None:
        """
        Test extracting empty YAML front matter.
        """
        # Prepare inputs.
        txt = """
        ---
        ---
        # Content
        """
        # Prepare outputs.
        expected_frontmatter = ["---", "---"]
        expected_remaining = ["# Content"]
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)

    def test5(self) -> None:
        """
        Test that separators not at the beginning are not treated as front matter.
        """
        # Prepare inputs.
        txt = """
        # Content
        ---
        More content
        """
        # Prepare outputs.
        expected_frontmatter = []
        lines = txt.split("\n")
        expected_remaining = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        self.helper(txt, expected_frontmatter, expected_remaining)


# #############################################################################
# Test_remove_table_of_contents
# #############################################################################


class Test_remove_table_of_contents(hunitest.TestCase):
    """
    Test the `remove_table_of_contents()` function.
    """

    def helper(self, text: str, expected: str) -> None:
        """
        Test helper for `remove_table_of_contents()`.

        :param text: Input markdown text
        :param expected: Expected output text
        """
        # Prepare inputs.
        text = hprint.dedent(text)
        # Run test.
        actual = hmarkdo.remove_table_of_contents(text)
        # Check outputs.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
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
        # Prepare outputs.
        expected = """
        # Introduction

        This is an introduction.



        ## Section 1

        Content of section 1.
        """
        # Run test.
        self.helper(text, expected)

    def test2(self) -> None:
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
        # Prepare outputs.
        expected = text
        # Run test.
        self.helper(text, expected)

    def test3(self) -> None:
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
        # Prepare outputs.
        expected = """
        # Introduction



        ## Section 1
        """
        # Run test.
        self.helper(text, expected)




# #############################################################################
# Test_add_navigation_slides
# #############################################################################


class Test_add_navigation_slides(hunitest.TestCase):
    """
    Test the `add_navigation_slides()` function with detailed output.
    """

    def helper(
        self,
        input_text: str,
        max_level: int,
        expand_all: bool,
        expected: str,
    ) -> None:
        """
        Helper method to test `add_navigation_slides()` function.

        :param input_text: Input text with dedent applied
        :param max_level: Maximum header level
        :param expand_all: Whether to expand all headers in navigation
        :param expected: Expected output (if None, uses golden file)
        """
        # Prepare inputs.
        input_text = hprint.dedent(input_text)
        lines = input_text.strip().split("\n")
        # Run test.
        actual = hmartoc.add_navigation_slides(lines, max_level, expand_all=expand_all)
        actual_str = "\n".join(actual)
        # Check outputs.
        expected_str = hprint.dedent(expected)
        self.assert_equal(actual_str, expected_str)

    def test1(self) -> None:
        """
        Test navigation slides added for headers.
        """
        # Prepare inputs.
        input_text = """
            # Part 1
            Content here
            ## Section 1.1
            More content
            """
        max_level = 2
        # Prepare outputs.
        expected = r"""
            ####
            - _**\textcolor{red}{Part 1}**_
              - Section 1.1

            Content here
            ####
            - Part 1
              - _**\textcolor{red}{Section 1.1}**_

            More content
            """
        # Run test.
        self.helper(input_text, max_level, expected=expected)

    def test2(self) -> None:
        """
        Test navigation with single level headers only.
        """
        # Prepare inputs.
        input_text = """
            # Main Title
            Content
            """
        max_level = 1
        # Prepare outputs.
        expected = r"""
            ####
            - _**\textcolor{red}{Main Title}**_

            Content
            """
        # Run test.
        self.helper(input_text, max_level, expected=expected)

    def test3(self) -> None:
        """
        Test adding navigation slides to multiple sections with two levels.
        """
        # Prepare inputs.
        input_text = """
            # Section 1
            Some content
            ## Subsection 1.1
            More content
            # Section 2
            Another content
            """
        max_level = 2
        expected = r"""
            ####
            - _**\textcolor{red}{Section 1}**_
              - Subsection 1.1
            - Section 2

            Some content
            ####
            - Section 1
              - _**\textcolor{red}{Subsection 1.1}**_
            - Section 2

            More content
            ####
            - Section 1
            - _**\textcolor{red}{Section 2}**_

            Another content
            """
        # Run test.
        self.helper(input_text, max_level, expected=expected)

    def test4(self) -> None:
        """
        Test navigation slides with expand_all=True.
        """
        # Prepare inputs.
        input_text = """
            # Section 1
            Content 1
            ## Subsection 1.1
            Content 1.1
            # Section 2
            Content 2
            """
        max_level = 2
        expected = r"""
            ####
            - _**\textcolor{red}{Section 1}**_
              - Subsection 1.1
            - Section 2

            Content 1
            ####
            - Section 1
              - _**\textcolor{red}{Subsection 1.1}**_
            - Section 2

            Content 1.1
            ####
            - Section 1
              - Subsection 1.1
            - _**\textcolor{red}{Section 2}**_

            Content 2
            """
        # Run test.
        self.helper(input_text, max_level, expand_all=True, expected=expected)

    def test5(self) -> None:
        """
        Test that non-header lines are preserved.
        """
        # Prepare inputs.
        input_text = """
            Some initial content
            # Section 1
            Content under section 1
            """
        max_level = 1
        expected = r"""
            Some initial content
            ####
            - _**\textcolor{red}{Section 1}**_

            Content under section 1
            """
        # Run test.
        self.helper(input_text, max_level, expected=expected)

    def test6(self) -> None:
        """
        Test with max_level limiting which headers get navigation.
        """
        # Prepare inputs.
        input_text = """
            # Section 1
            Content
            ## Subsection 1.1
            More content
            ### Subsubsection 1.1.1
            Even more content
            """
        max_level = 1
        expected = r"""
            ####
            - _**\textcolor{red}{Section 1}**_

            Content
            ## Subsection 1.1
            More content
            ### Subsubsection 1.1.1
            Even more content
            """
        # Run test.
        self.helper(input_text, max_level, expected=expected)
