import logging
import os
from typing import Optional

import pytest

import dev_scripts_helpers.documentation.lint_txt as dshdlitx
import helpers.hdbg as hdbg
import helpers.hdockerized_executables as hdocexec
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__remove_code_block_extra_indentation
# #############################################################################


class Test__remove_code_block_extra_indentation(hunitest.TestCase):
    """
    Test the _remove_code_block_extra_indentation function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _remove_code_block_extra_indentation.

        :param txt: Input text to process
        :param expected: Expected output after removing extra
            indentation
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._remove_code_block_extra_indentation(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test simple (non-indented) code block with no extra indentation.
        """
        # Prepare inputs.
        txt = """
        # Test Document
        Some text here:
        ```bash
        > docker_jupyter.sh -p 8890 -u
        # Go to localhost:8890
        ```
        More text after.
        """
        # Expected: no changes needed.
        expected = txt
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test indented code block with correct indentation.
        """
        # Prepare inputs.
        txt = """
        - Delete unused reference files
          ```bash
          > rm Dockerfile.ubuntu
          ```
        """
        # Expected: no changes needed.
        expected = txt
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test code block with Dockerfile content that has extra indentation.
        """
        # Prepare inputs.
        txt = """
        - Wrong: Embed everything in the Dockerfile
          ```dockerfile
            RUN pip install my-package
          ```
        """
        # Prepare outputs.
        expected = """
        - Wrong: Embed everything in the Dockerfile
          ```dockerfile
          RUN pip install my-package
          ```
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test multiple code blocks with different types of content.
        """
        # Prepare inputs.
        txt = """
        - Example 1:
          ```bash
            > docker run -it ubuntu
          ```

        - Example 2:
          ```dockerfile
            RUN apt-get update
          ```
        """
        # Prepare outputs - removes extra indentation from both blocks.
        expected = """
        - Example 1:
          ```bash
          > docker run -it ubuntu
          ```

        - Example 2:
          ```dockerfile
          RUN apt-get update
          ```
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test deeply indented code block in nested list.
        """
        # Prepare inputs.
        txt = """
        - Level 1
          - Level 2
            ```python
              print("hello")
            ```
        """
        # Prepare outputs.
        expected = """
        - Level 1
          - Level 2
            ```python
            print("hello")
            ```
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test code block with multiple lines of content.
        """
        # Prepare inputs.
        txt = """
        - Instructions:
          ```bash
            > docker run image
            > docker exec
          ```
        """
        # Prepare outputs.
        expected = """
        - Instructions:
          ```bash
          > docker run image
            > docker exec
          ```
        """
        # Run test.
        self.helper(txt, expected)

    @pytest.mark.superslow("~95 seconds.")
    def test7(self) -> None:
        """
        Test code block with correct indentation already present.
        """
        # Prepare inputs.
        txt = """
        - Example:
          ```python
          def foo():
              return 42
          ```
        """
        # Expected: no changes needed.
        expected = txt
        # Run test.
        self.helper(txt, expected)

    @pytest.mark.superslow("~25 seconds.")
    def test8(self) -> None:
        """
        Test that code blocks without extra indentation are unchanged.
        """
        # Prepare inputs.
        txt = """
        Code example:
        ```javascript
        console.log("test");
        const x = 42;
        ```
        """
        # Expected: no changes needed.
        expected = txt
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test__handle_empty_lines
# #############################################################################


class Test__handle_empty_lines(hunitest.TestCase):
    """
    Test the _handle_empty_lines function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _handle_empty_lines.

        :param txt: Input text to process
        :param expected: Expected output after handling empty lines
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._handle_empty_lines(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing single empty line after header.
        """
        # Prepare inputs.
        txt = """
        ## Front Matter (YAML)

        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Prepare outputs.
        expected = """
        ## Front Matter (YAML)
        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing multiple empty lines after header.
        """
        # Prepare inputs.
        txt = """
        # Front Matter (YAML)



        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Prepare outputs.
        expected = """
        # Front Matter (YAML)
        Every blog post must start with YAML front matter enclosed in `---`:
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing empty lines between text and code block.
        """
        # Prepare inputs.
        txt = """
        - Example:


          ```markdown
          The main advantages are:
          - **First advantage**: Description here
          - **Second advantage**: Description here
            - Sub-point with details
            - Another sub-point
          ```
        """
        # Prepare outputs.
        expected = """
        - Example:
          ```markdown
          The main advantages are:
          - **First advantage**: Description here
          - **Second advantage**: Description here
            - Sub-point with details
            - Another sub-point
          ```
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test with multiple headers and code blocks.
        """
        # Prepare inputs.
        txt = """
        # Header 1

        Some text here.

        ## Header 2


        More text here.


        ```python
        def foo():
            pass
        ```
        """
        # Prepare outputs.
        expected = """
        # Header 1
        Some text here.

        ## Header 2
        More text here.
        ```python
        def foo():
            pass
        ```
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test that text without headers or code blocks remains unchanged.
        """
        # Prepare inputs.
        txt = """
        First line

        Second line

        Third line
        """
        # Prepare outputs.
        expected = """
        First line

        Second line

        Third line
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test that empty lines between text without code blocks are preserved.
        """
        # Prepare inputs.
        txt = """
        Line 1


        Line 2
        """
        # Prepare outputs.
        expected = """
        Line 1


        Line 2
        """
        # Run test.
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test with different header levels.
        """
        # Prepare inputs.
        txt = """
        # Level 1

        ## Level 2

        ### Level 3

        #### Level 4

        Text content
        """
        # Prepare outputs.
        expected = """
        # Level 1
        ## Level 2
        ### Level 3
        #### Level 4
        Text content
        """
        # Run test.
        self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test code block with different language tags.
        """
        # Prepare inputs.
        txt = """
        Example code:


        ```javascript
        console.log("Hello");
        ```
        """
        # Prepare outputs.
        expected = """
        Example code:
        ```javascript
        console.log("Hello");
        ```
        """
        # Run test.
        self.helper(txt, expected)

    def test10(self) -> None:
        """
        Test that empty lines inside code blocks are preserved.
        """
        # Prepare inputs.
        txt = """
        Example:

        ```python
        def foo():
            pass

        def bar():
            pass
        ```
        """
        # Prepare outputs.
        expected = """
        Example:
        ```python
        def foo():
            pass

        def bar():
            pass
        ```
        """
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_remove_page_separators
# #############################################################################


class Test_remove_page_separators(hunitest.TestCase):
    """
    Test the _remove_page_separators function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _remove_page_separators.

        :param txt: Input text to process
        :param expected: Expected output after removing page separators
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._remove_page_separators(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing a single page separator line.
        """
        # Prepare inputs.
        txt = """
        First section
        ---
        Second section
        """
        # Prepare outputs.
        expected = """
        First section

        Second section
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing multiple page separator lines.
        """
        # Prepare inputs.
        txt = """
        Section 1
        ---
        Section 2
        ---
        Section 3
        """
        # Prepare outputs.
        expected = """
        Section 1

        Section 2

        Section 3
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing page separators with trailing spaces.
        """
        # Prepare inputs.
        txt = """
        Content before
        ---
        Content after
        """
        # Prepare outputs.
        expected = """
        Content before

        Content after
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test that text without separators remains unchanged.
        """
        # Prepare inputs.
        txt = """
        First line
        Second line
        Third line
        """
        # Prepare outputs.
        expected = """
        First line
        Second line
        Third line
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test that separators within text content are preserved.
        """
        # Prepare inputs.
        txt = """
        Example:
        This is a --- dash in text
        And another line
        """
        # Prepare outputs.
        expected = """
        Example:
        This is a --- dash in text
        And another line
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_add_blank_lines_between_headers
# #############################################################################


class Test_add_blank_lines_between_headers(hunitest.TestCase):
    """
    Test the _add_blank_lines_between_headers function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _add_blank_lines_between_headers.

        :param txt: Input text to process
        :param expected: Expected output after adding blank lines
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._add_blank_lines_between_headers(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test adding blank line between two consecutive headers.
        """
        # Prepare inputs.
        txt = """
        # Conversational Diagram Designer (CDD)
        ## 1. Overview
        Conversational Diagram Designer (CDD) is a browser-based diagramming tool.
        """
        # Prepare outputs.
        expected = """
        # Conversational Diagram Designer (CDD)

        ## 1. Overview
        Conversational Diagram Designer (CDD) is a browser-based diagramming tool.
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test adding blank lines between multiple consecutive headers.
        """
        # Prepare inputs.
        txt = """
        # Title
        ## Subtitle
        ### Subsubtitle
        #### Deep subtitle
        Content here
        """
        # Prepare outputs.
        expected = """
        # Title

        ## Subtitle

        ### Subsubtitle

        #### Deep subtitle
        Content here
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test that non-consecutive headers are not affected.
        """
        # Prepare inputs.
        txt = """
        # Header 1

        Some text here.

        ## Header 2

        More text here.
        """
        # Prepare outputs.
        expected = """
        # Header 1

        Some text here.

        ## Header 2

        More text here.
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test mixed consecutive and non-consecutive headers.
        """
        # Prepare inputs.
        txt = """
        # Main Title
        ## Section 1
        Content for section 1.

        ## Section 2
        ### Subsection 2.1
        More content.
        """
        # Prepare outputs.
        expected = """
        # Main Title

        ## Section 1
        Content for section 1.

        ## Section 2

        ### Subsection 2.1
        More content.
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test with text without headers.
        """
        # Prepare inputs.
        txt = """
        First line
        Second line
        Third line
        """
        # Prepare outputs.
        expected = """
        First line
        Second line
        Third line
        """
        # Run test.
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test with only one header.
        """
        # Prepare inputs.
        txt = """
        # Single Header
        Some content below.
        """
        # Prepare outputs.
        expected = """
        # Single Header
        Some content below.
        """
        # Run test.
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test headers at beginning and end of file.
        """
        # Prepare inputs.
        txt = """
        # First Header
        ## Second Header
        """
        # Prepare outputs.
        expected = """
        # First Header

        ## Second Header
        """
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_convert_asterisk_bullets_to_dashes
# #############################################################################


class Test_convert_asterisk_bullets_to_dashes(hunitest.TestCase):
    """
    Test the _convert_asterisk_bullets_to_dashes function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _convert_asterisk_bullets_to_dashes.

        :param txt: Input text to process
        :param expected: Expected output after converting asterisk
            bullets
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._convert_asterisk_bullets_to_dashes(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test converting single asterisk bullet to dash.
        """
        # Prepare inputs.
        txt = """
        * First item
        """
        # Prepare outputs.
        expected = """
        - First item
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test converting multiple asterisk bullets to dashes.
        """
        # Prepare inputs.
        txt = """
        * First item
        * Second item
        * Third item
        """
        # Prepare outputs.
        expected = """
        - First item
        - Second item
        - Third item
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test converting nested asterisk bullets with indentation.
        """
        # Prepare inputs.
        txt = """
        * Main item
          * Nested item 1
          * Nested item 2
        * Another main item
        """
        # Prepare outputs.
        expected = """
        - Main item
          - Nested item 1
          - Nested item 2
        - Another main item
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test mixed asterisk and dash bullets.
        """
        # Prepare inputs.
        txt = """
        * Asterisk item
        - Dash item
        * Another asterisk
        """
        # Prepare outputs.
        expected = """
        - Asterisk item
        - Dash item
        - Another asterisk
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test asterisk bullet with tab indentation.
        """
        # Prepare inputs.
        txt = """
\t* First item with tab
\t* Second item with tab
        """
        # Prepare outputs.
        expected = """
\t- First item with tab
\t- Second item with tab
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test that text without asterisk bullets remains unchanged.
        """
        # Prepare inputs.
        txt = """
        - Dash item
        Regular text
        More text
        """
        # Prepare outputs.
        expected = """
        - Dash item
        Regular text
        More text
        """
        # Run test.
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test with empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test with multiple levels of nested indentation.
        """
        # Prepare inputs.
        txt = """
        * Level 1
          * Level 2
            * Level 3
              * Level 4
        """
        # Prepare outputs.
        expected = """
        - Level 1
          - Level 2
            - Level 3
              - Level 4
        """
        # Run test.
        self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test that asterisks not at line start are preserved.
        """
        # Prepare inputs.
        txt = """
        * Item with asterisk *inside* text
        - Item with asterisk * somewhere
        Regular text with * asterisk
        """
        # Prepare outputs.
        expected = """
        - Item with asterisk *inside* text
        - Item with asterisk * somewhere
        Regular text with * asterisk
        """
        # Run test.
        self.helper(txt, expected)

    def test10(self) -> None:
        """
        Test asterisk bullets mixed with other content.
        """
        # Prepare inputs.
        txt = """
        Some introduction text.

        * First point
        * Second point

        Some conclusion text.

        * Another point
        """
        # Prepare outputs.
        expected = """
        Some introduction text.

        - First point
        - Second point

        Some conclusion text.

        - Another point
        """
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_remove_trailing_periods
# #############################################################################


class Test_remove_trailing_periods(hunitest.TestCase):
    """
    Test the _remove_trailing_periods function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _remove_trailing_periods.

        :param txt: Input text to process
        :param expected: Expected output after removing trailing periods
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._remove_trailing_periods(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing period from simple bullet point.
        """
        # Prepare inputs.
        txt = """
        - Bullet point with period.
        """
        # Prepare outputs.
        expected = """
        - Bullet point with period
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing periods from multiple bullet points.
        """
        # Prepare inputs.
        txt = """
        - First item with period.
        - Second item with period.
        - Third item with period.
        """
        # Prepare outputs.
        expected = """
        - First item with period
        - Second item with period
        - Third item with period
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing period from header.
        """
        # Prepare inputs.
        txt = """
        # Main Header with period.
        """
        # Prepare outputs.
        expected = """
        # Main Header with period
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test removing periods from multiple headers at different levels.
        """
        # Prepare inputs.
        txt = """
        # Main Header.
        ## Subheader.
        ### Sub-subheader.
        #### Deep header.
        """
        # Prepare outputs.
        expected = """
        # Main Header
        ## Subheader
        ### Sub-subheader
        #### Deep header
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test removing period from numbered list items.
        """
        # Prepare inputs.
        txt = """
        1. First numbered item with period.
        2. Second numbered item with period.
        3. Third numbered item with period.
        """
        # Prepare outputs.
        expected = """
        1. First numbered item with period
        2. Second numbered item with period
        3. Third numbered item with period
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test removing period from numbered list with closing parenthesis.
        """
        # Prepare inputs.
        txt = """
        1) Item with closing parenthesis.
        2) Another item with closing parenthesis.
        """
        # Prepare outputs.
        expected = """
        1) Item with closing parenthesis
        2) Another item with closing parenthesis
        """
        # Run test.
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test that regular text trailing periods are removed.
        """
        # Prepare inputs.
        txt = """
        Regular text with a period. More text here.
        Another line with a period.
        """
        # Prepare outputs.
        expected = """
        Regular text with a period. More text here
        Another line with a period
        """
        # Run test.
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test mixed bullet points, headers, and regular text.
        """
        # Prepare inputs.
        txt = """
        # Main Section.
        - Bullet point with period.
        Regular text with period.
        1. Numbered item.
        More regular text.
        """
        # Prepare outputs.
        expected = """
        # Main Section
        - Bullet point with period
        Regular text with period
        1. Numbered item
        More regular text
        """
        # Run test.
        self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test nested bullet points with indentation.
        """
        # Prepare inputs.
        txt = """
        - Main bullet.
          - Nested bullet.
            - Deep nested bullet.
        - Another main bullet.
        """
        # Prepare outputs.
        expected = """
        - Main bullet
          - Nested bullet
            - Deep nested bullet
        - Another main bullet
        """
        # Run test.
        self.helper(txt, expected)

    def test10(self) -> None:
        """
        Test that bullet points without periods are unchanged.
        """
        # Prepare inputs.
        txt = """
        - Bullet point without period
        - Another without period
        - Yet another without
        """
        # Prepare outputs.
        expected = """
        - Bullet point without period
        - Another without period
        - Yet another without
        """
        # Run test.
        self.helper(txt, expected)

    def test11(self) -> None:
        """
        Test with trailing spaces after period.
        """
        # Prepare inputs.
        txt = """
        - Bullet point with period and trailing space.
        # Header with trailing space.
        """
        # Prepare outputs.
        expected = """
        - Bullet point with period and trailing space
        # Header with trailing space
        """
        # Run test.
        self.helper(txt, expected)

    def test12(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)

    def test13(self) -> None:
        """
        Test that periods in URLs are preserved (in regular text).
        """
        # Prepare inputs.
        txt = """
        - Visit example.com for more info.
        - Check https://example.com/path.html.
        """
        # Prepare outputs.
        expected = """
        - Visit example.com for more info
        - Check https://example.com/path.html
        """
        # Run test.
        self.helper(txt, expected)

    def test14(self) -> None:
        """
        Test multiple periods at the end (edge case).
        """
        # Prepare inputs.
        txt = """
        - Bullet with multiple periods...
        # Header with multiple periods...
        """
        # Prepare outputs.
        expected = """
        - Bullet with multiple periods
        # Header with multiple periods
        """
        # Run test.
        self.helper(txt, expected)

    def test15(self) -> None:
        """
        Test combination of all patterns: headers, bullets, and numbered lists.
        """
        # Prepare inputs.
        txt = """
        # Feature List.
        ## Implementation Steps.
        1. First step in process.
        2. Second step in process.
           - Sub-item for step 2.
           - Another sub-item.
        ## Results.
        - Positive result.
        - Negative result.
        Regular conclusion text.
        """
        # Prepare outputs.
        expected = """
        # Feature List
        ## Implementation Steps
        1. First step in process
        2. Second step in process
           - Sub-item for step 2
           - Another sub-item
        ## Results
        - Positive result
        - Negative result
        Regular conclusion text
        """
        # Run test.
        self.helper(txt, expected)

    def test16(self) -> None:
        """
        Test removing periods from regular text lines (user's example case).
        """
        # Prepare inputs.
        txt = """
        Some applications of decision-making include:
        Decision-making applications (medical diagnosis, terrorism detection).
        Another example with more details.
        """
        # Prepare outputs.
        expected = """
        Some applications of decision-making include:
        Decision-making applications (medical diagnosis, terrorism detection)
        Another example with more details
        """
        # Run test.
        self.helper(txt, expected)


# #############################################################################
# Test_remove_markdown_formatting
# #############################################################################


class Test_remove_markdown_formatting(hunitest.TestCase):
    """
    Test the _remove_markdown_formatting function.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Test helper for _remove_markdown_formatting.

        :param txt: Input text to process
        :param expected: Expected output after removing markdown formatting
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = dshdlitx._remove_markdown_formatting(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removing bold formatting with double asterisks.
        """
        # Prepare inputs.
        txt = """
        This is **bold text** in a sentence.
        """
        # Prepare outputs.
        expected = """
        This is bold text in a sentence.
        """
        # Run test.
        self.helper(txt, expected)

    def test2(self) -> None:
        """
        Test removing bold formatting with double underscores.
        """
        # Prepare inputs.
        txt = """
        This is __bold text__ in a sentence.
        """
        # Prepare outputs.
        expected = """
        This is bold text in a sentence.
        """
        # Run test.
        self.helper(txt, expected)

    def test3(self) -> None:
        """
        Test removing italic formatting with single asterisks.
        """
        # Prepare inputs.
        txt = """
        This is *italic text* in a sentence.
        """
        # Prepare outputs.
        expected = """
        This is italic text in a sentence.
        """
        # Run test.
        self.helper(txt, expected)

    def test4(self) -> None:
        """
        Test removing italic formatting with single underscores.
        """
        # Prepare inputs.
        txt = """
        This is _italic text_ in a sentence.
        """
        # Prepare outputs.
        expected = """
        This is italic text in a sentence.
        """
        # Run test.
        self.helper(txt, expected)

    def test5(self) -> None:
        """
        Test removing strikethrough formatting.
        """
        # Prepare inputs.
        txt = """
        This is ~~strikethrough text~~ in a sentence.
        """
        # Prepare outputs.
        expected = """
        This is strikethrough text in a sentence.
        """
        # Run test.
        self.helper(txt, expected)

    def test6(self) -> None:
        """
        Test removing inline code formatting.
        """
        # Prepare inputs.
        txt = """
        Use the `function_name()` to do something.
        """
        # Prepare outputs.
        expected = """
        Use the function_name() to do something.
        """
        # Run test.
        self.helper(txt, expected)

    def test7(self) -> None:
        """
        Test removing link formatting, keeping the text.
        """
        # Prepare inputs.
        txt = """
        Visit [Google](https://google.com) for more info.
        """
        # Prepare outputs.
        expected = """
        Visit Google for more info.
        """
        # Run test.
        self.helper(txt, expected)

    def test8(self) -> None:
        """
        Test removing image formatting, keeping the alt text.
        """
        # Prepare inputs.
        txt = """
        ![alt text](image.png) is shown above.
        """
        # Prepare outputs.
        expected = """
        alt text is shown above.
        """
        # Run test.
        self.helper(txt, expected)

    def test9(self) -> None:
        """
        Test removing header formatting.
        """
        # Prepare inputs.
        txt = """
        # Main Header
        ## Subheader
        ### Sub-subheader
        """
        # Prepare outputs.
        expected = """
        Main Header
        Subheader
        Sub-subheader
        """
        # Run test.
        self.helper(txt, expected)

    def test10(self) -> None:
        """
        Test mixed markdown formatting.
        """
        # Prepare inputs.
        txt = """
        The **bold** and *italic* text with a [link](http://example.com).
        # Header with **bold**.
        """
        # Prepare outputs.
        expected = """
        The bold and italic text with a link.
        Header with bold.
        """
        # Run test.
        self.helper(txt, expected)

    def test11(self) -> None:
        """
        Test that code blocks are preserved.
        """
        # Prepare inputs.
        txt = """
        Here is a code example:
        ```python
        result = **bold** and *italic*
        # This is a comment with [link](url)
        ```
        After the code block.
        """
        # Prepare outputs.
        expected = """
        Here is a code example:
        ```python
        result = **bold** and *italic*
        # This is a comment with [link](url)
        ```
        After the code block.
        """
        # Run test.
        self.helper(txt, expected)

    def test12(self) -> None:
        """
        Test multiple formatting types on single line.
        """
        # Prepare inputs.
        txt = """
        **Bold**, *italic*, ~~strikethrough~~, and `code` together.
        """
        # Prepare outputs.
        expected = """
        Bold, italic, strikethrough, and code together.
        """
        # Run test.
        self.helper(txt, expected)

    def test13(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        txt = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(txt, expected)

    def test14(self) -> None:
        """
        Test text without any markdown formatting.
        """
        # Prepare inputs.
        txt = """
        This is plain text without any markdown formatting.
        It has multiple lines and sentences.
        """
        # Prepare outputs.
        expected = """
        This is plain text without any markdown formatting.
        It has multiple lines and sentences.
        """
        # Run test.
        self.helper(txt, expected)

    def test15(self) -> None:
        """
        Test nested code blocks with different languages.
        """
        # Prepare inputs.
        txt = """
        Text before code.
        ```javascript
        const x = **bold** and *italic*;
        ```
        ```python
        def function(**kwargs):
            pass
        ```
        Text after code.
        """
        # Prepare outputs.
        expected = """
        Text before code.
        ```javascript
        const x = **bold** and *italic*;
        ```
        ```python
        def function(**kwargs):
            pass
        ```
        Text after code.
        """
        # Run test.
        self.helper(txt, expected)

    def test16(self) -> None:
        """
        Test variable names with underscores are preserved.
        """
        # Prepare inputs.
        txt = """
        The variable _my_variable should not be modified.
        Use _some_function() for processing.
        """
        # Prepare outputs.
        expected = """
        The variable _my_variable should not be modified.
        Use _some_function() for processing.
        """
        # Run test.
        self.helper(txt, expected)


def _get_text1() -> str:
    """
    Get sample text containing mathematical equations in LaTeX format.
    """
    txt = r"""
    * Gradient descent for logistic regression
    - The typical implementations of gradient descent (basic or advanced) need
      two inputs:
        - The cost function $E_{in}(\vw)$ (to monitor convergence)
        - The gradient of the cost function
          $\frac{\partial E}{w_j} \text{ for all } j$ (to optimize)
    - The cost function is:
        $$E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)$$

    - In case of general probabilistic model $h(\vx)$ in \{0, 1\}):
        $$
        E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)
        $$

    - In case of logistic regression in \{+1, -1\}:
        $$E_{in}(\vw) = \frac{1}{N} \sum_i \log(1 + \exp(-y_i \vw^T \vx_i))$$

    - It can be proven that the function $E_{in}(\vw)$ to minimize is convex in
      $\vw$ (sum of exponentials and flipped exponentials is convex and log is
      monotone)"""
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    return txt


# #############################################################################
# Test_capitalize_header
# #############################################################################


class Test_capitalize_header(hunitest.TestCase):
    """
    Test the capitalize_header function handling of apostrophes.

    The capitalize_header function should properly handle words with
    apostrophes, like "won't" -> "Won't" (not "Won'T"). This tests the
    fix for the bug where Python's str.title() capitalizes letters after
    apostrophes.
    """

    def helper(self, input_lines: str, expected: str) -> None:
        """
        Test helper for capitalize_header.

        :param input_lines: Input markdown lines to process
        :param expected: Expected output after capitalize_header
            processing
        """
        import helpers.hmarkdown_headers as hmarhead

        # Prepare inputs.
        lines = input_lines.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual = hmarhead.capitalize_header(lines)
        # Check outputs.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test word with apostrophe: "won't" -> "Won't" (not "Won'T").
        """
        # Prepare inputs.
        input_lines = """
        ### Jupyter won't connect
        """
        # Prepare outputs.
        expected = """
        ### Jupyter Won't Connect
        """
        # Run test.
        self.helper(input_lines, expected)

    def test2(self) -> None:
        """
        Test correcting wrongly capitalized apostrophe: "Won'T" -> "Won't".
        """
        # Prepare inputs.
        input_lines = """
        ### Jupyter Won'T Connect
        """
        # Prepare outputs.
        expected = """
        ### Jupyter Won't Connect
        """
        # Run test.
        self.helper(input_lines, expected)

    def test3(self) -> None:
        """
        Test normal word capitalization still works.
        """
        # Prepare inputs.
        input_lines = """
        ### Jupyter connect test
        """
        # Prepare outputs.
        expected = """
        ### Jupyter Connect Test
        """
        # Run test.
        self.helper(input_lines, expected)

    def test4(self) -> None:
        """
        Test all-caps acronym is preserved.
        """
        # Prepare inputs.
        input_lines = """
        ### ML theory and API usage
        """
        # Prepare outputs.
        expected = """
        ### ML Theory and API Usage
        """
        # Run test.
        self.helper(input_lines, expected)

    def test5(self) -> None:
        """
        Test internal-capital words like "SimpleFeedForward" are preserved.
        """
        # Prepare inputs.
        input_lines = """
        ### SimpleFeedForward network
        """
        # Prepare outputs.
        expected = """
        ### SimpleFeedForward Network
        """
        # Run test.
        self.helper(input_lines, expected)

    def test6(self) -> None:
        """
        Test multiple apostrophes: "don't won't" -> "Don't Won't".
        """
        # Prepare inputs.
        input_lines = """
        ### don't won't shouldn't
        """
        # Prepare outputs.
        expected = """
        ### Don't Won't Shouldn't
        """
        # Run test.
        self.helper(input_lines, expected)


# #############################################################################
# Test_lint_txt1
# #############################################################################


class Test_lint_txt1(hunitest.TestCase):
    """
    Test the text preprocessing functionality.
    """

    def helper(self, txt: str, expected: str) -> None:
        """
        Process text with `_preprocess_txt()` and compare with expected output.

        :param txt: Input text to preprocess
        :param expected: Expected output after preprocessing
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run.
        actual = dshdlitx._preprocess_txt(lines)
        # Check.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    # //////////////////////////////////////////////////////////////////////////

    def test_preprocess1(self) -> None:
        txt = r"""$$E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)$$"""
        expected = r"""
        $$
        E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)
        $$"""
        self.helper(txt, expected)

    def test_preprocess2(self) -> None:
        txt = r"""
        $$E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)$$"""
        expected = r"""
        $$
        E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        \big)
        $$"""
        self.helper(txt, expected)

    def test_preprocess3(self) -> None:
        txt = _get_text1()
        expected = r"""
        - STARGradient descent for logistic regression
        - The typical implementations of gradient descent (basic or advanced) need
          two inputs:
            - The cost function $E_{in}(\vw)$ (to monitor convergence)
            - The gradient of the cost function
              $\frac{\partial E}{w_j} \text{ for all } j$ (to optimize)
        - The cost function is:
            $$
            E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)
            $$

        - In case of general probabilistic model $h(\vx)$ in \{0, 1\}):
            $$
            E_{in}(\vw) = \frac{1}{N} \sum_i \big(
            -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
            \big)
            $$

        - In case of logistic regression in \{+1, -1\}:
            $$
            E_{in}(\vw) = \frac{1}{N} \sum_i \log(1 + \exp(-y_i \vw^T \vx_i))
            $$

        - It can be proven that the function $E_{in}(\vw)$ to minimize is convex in
          $\vw$ (sum of exponentials and flipped exponentials is convex and log is
          monotone)"""
        self.helper(txt, expected)

    def test_preprocess4(self) -> None:
        txt = r"""
        # #########################
        # test
        # #############################################################################"""
        expected = r"""# test"""
        self.helper(txt, expected)

    def test_preprocess5(self) -> None:
        txt = r"""
        ## ////////////////
        # test
        # ////////////////"""
        expected = r"""# test"""
        self.helper(txt, expected)


# #############################################################################
# Test_lint_txt2
# #############################################################################


class Test_lint_txt2(hunitest.TestCase):
    @staticmethod
    def get_text_problematic_for_prettier1() -> str:
        txt = r"""
        * Python formatting
        - Python has several built-in ways of formatting strings
          1) `%` format operator
          2) `format` and `str.format`


        * `%` format operator
        - Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        return txt

    def helper(self, txt: str, expected: Optional[str], file_name: str) -> str:
        """
        Helper function to process the given text and compare the result with
        the expected output.

        :param txt: The text to be processed.
        :param expected: The expected output after processing the text.
            If None, no comparison is made.
        :param file_name: The name of the file to be used for
            processing.
        :return: The processed text.
        """
        # Prepare inputs.
        txt_str = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        lines = txt_str.split("\n")
        file_name = os.path.join(self.get_scratch_space(), file_name)
        # Run function.
        actual = dshdlitx._perform_actions(lines, file_name)
        # Check.
        actual = "\n".join(actual)
        if expected:
            expected_str = hprint.dedent(
                expected, remove_lead_trail_empty_lines_=True
            )
            self.assert_equal(actual, expected_str)
        return actual

    # //////////////////////////////////////////////////////////////////////////

    def test1(self) -> None:
        txt = _get_text1()
        expected = None
        file_name = "test.txt"
        actual = self.helper(txt, expected, file_name)
        self.check_string(actual)

    def test2(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        expected = r"""
        - Good time management

        1. Choose the right tasks
           - Avoid non-essential tasks
        """
        file_name = "test.txt"
        self.helper(txt, expected, file_name)

    @pytest.mark.superslow
    def test3(self) -> None:
        """
        Run the text linter on a md file.
        """
        txt = r"""
        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        expected = r"""
        <!-- toc -->

        - [Good](#good)
          * [Bad](#bad)

        <!-- tocstop -->

        # Good
        - Good time management
          1. Choose the right tasks
          - Avoid non-essential tasks

        ## Bad
        - Hello
          - World
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)

    @pytest.mark.superslow
    def test4(self) -> None:
        """
        Check that no replacement happens inside a ``` block.
        """
        txt = r"""
        <!-- toc -->
        <!-- tocstop -->

        - Good
        - Hello

        ```test
        - hello
            - world
        1) oh no!
        ```
        """
        expected = r"""
        <!-- toc -->



        <!-- tocstop -->

        - Good
        - Hello
        ```test
        - hello
            - world
        1) oh no!
        ```
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)

    def test5(self) -> None:
        """
        For some reason prettier replaces - with * when there are 2 empty lines.
        """
        txt = self.get_text_problematic_for_prettier1()
        actual = hdocexec.prettier_on_str(txt, file_type="txt")
        expected = r"""
        - Python formatting

        * Python has several built-in ways of formatting strings
          1. `%` format operator
          2. `format` and `str.format`

        - `%` format operator

        * Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    @pytest.mark.superslow
    def test6(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = self.get_text_problematic_for_prettier1()
        expected = r"""
        * Python Formatting
        - Python has several built-in ways of formatting strings
          1. `%` format operator
          2. `format` and `str.format`

        * `%` Format Operator
        - Text template as a format string
          - Values to insert are provided as a value or a `tuple`
        """
        file_name = "test.txt"
        self.helper(txt, expected, file_name)

    def test7(self) -> None:
        """
        Run the text linter on a txt file.
        """
        txt = r"""
        * `str.format`
        - Python 3 allows to format multiple values, e.g.,
           ```python
           key = 'my_var'
           value = 1.234
           ```
        """
        expected = r"""
        - str.format
        - Python 3 allows to format multiple values, e.g.,
          ```python
          key = 'my_var'
           value = 1.234
          ```
        """
        file_name = "test.txt"
        self.helper(txt, expected, file_name)

    @pytest.mark.superslow
    def test8(self) -> None:
        """
        Test that YAML front matter is preserved in markdown files.
        """
        txt = r"""
        ---
        title: My Document
        date: 2024-01-01
        author: Test Author
        ---

        # Main Content

        - This is a list
          - With nested items
        """
        expected = r"""
        ---
        title: My Document
        date: 2024-01-01
        author: Test Author
        ---

        <!-- toc -->

        - [Main Content](#main-content)

        <!-- tocstop -->

        # Main Content
        - This is a list
          - With nested items
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)

    @pytest.mark.superslow
    def test9(self) -> None:
        """
        Test that page separators are removed but YAML front matter is
        preserved.
        """
        txt = r"""
        ---
        title: Test
        ---

        # Section 1

        Content here.

        ---

        # Section 2

        More content.
        """
        expected = r"""
        ---
        title: Test
        ---

        <!-- toc -->

        - [Section 1](#section-1)
        - [Section 2](#section-2)

        <!-- tocstop -->

        # Section 1
        Content here.

        # Section 2
        More content.
        """
        file_name = "test.md"
        self.helper(txt, expected, file_name)


# #############################################################################
# Test_lint_txt_cmd_line1
# #############################################################################


class Test_lint_txt_cmd_line1(hunitest.TestCase):
    """
    Test the lint_txt.py command-line script with different file types.
    """

    def run_lint_txt(
        self,
        in_file: str,
        type_: str,
        use_script: bool,
        cmd_opts: str,
    ) -> Optional[str]:
        """
        Run lint_txt processing directly by calling the code.

        :param in_file: Path to the input file containing the notes.
        :param type_: The output format, either 'md' or 'tex'. :param
            use_script
        :param cmd_opts: Additional command-line options to pass to the
            script.
        :return: The processed text content.
        """
        if use_script:
            # lint_txt.py \
            #  -i papers/DataFlow_stream_computing_framework/DataFlow_stream_computing_framework.tex \
            #  --use_dockerized_prettier \
            cmd = []
            exec_path = hgit.find_file_in_git_tree("lint_txt.py")
            hdbg.dassert_path_exists(exec_path)
            cmd.append(exec_path)
            cmd.append(f"--input {in_file}")
            cmd.append("--use_dockerized_prettier")
            # Save a script file to store the commands.
            hdbg.dassert_in(type_, ["md", "tex"])
            out_dir = self.get_scratch_space()
            out_file = os.path.join(out_dir, f"output.{type_}")
            cmd.append(f"--output {out_file}")
            cmd.append(cmd_opts)
            cmd = " ".join(cmd)
            hsystem.system(cmd)
            # Check the content of the file, if needed.
            output_txt: Optional[str] = None
            if os.path.exists(out_file):
                output_txt = hio.from_file(out_file)
        else:
            hdbg.dassert_in(type_, ["md", "tex"])
            # Read input file.
            txt = hio.from_file(in_file)
            lines = txt.split("\n")
            # Process the content directly.
            out_lines = dshdlitx._perform_actions(
                lines,
                in_file,
                actions=None,
                print_width=80,
                use_dockerized_prettier=True,
                use_dockerized_markdown_toc=True,
            )
            # Return the processed text.
            output_txt = "\n".join(out_lines)
        return output_txt

    # ///////////////////////////////////////////////////////////////////////////

    @pytest.mark.superslow
    def test1(self) -> None:
        """
        Run lint_to_txt.py on a markdown file by calling the function directly.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "text.md")
        type_ = "md"
        use_script = False
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check.
        self.check_string(output_txt)

    def test2(self) -> None:
        """
        Run lint_to_txt.py on a markdown file using the command-line script.

        This test uses the same input file as test1 and should
        produce the same output. It uses test_method_name to reuse the
        golden outcome from test1.
        """
        # Prepare inputs.
        in_file = os.path.join(
            self.get_input_dir(test_method_name="test1"), "text.md"
        )
        type_ = "md"
        use_script = True
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check using the same golden outcome as test1.
        self.check_string(output_txt, test_method_name="test1")

    @pytest.mark.slow
    def test3(self) -> None:
        """
        Run lint_to_txt.py on a latex file by calling the function directly.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), "text.tex")
        type_ = "tex"
        use_script = False
        cmd_opts = ""
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check.
        self.check_string(output_txt)

    @pytest.mark.slow
    def test4(self) -> None:
        """
        Run lint_to_txt.py on a latex file using the command-line script.

        This test uses the same input file as test3 and should
        produce the same output. It uses test_method_name to reuse the
        golden outcome from test3.
        """
        # Prepare inputs.
        in_file = os.path.join(
            self.get_input_dir(test_method_name="test4"), "text.tex"
        )
        type_ = "tex"
        use_script = True
        cmd_opts = "--print-width 80"
        # Run the script.
        output_txt = self.run_lint_txt(in_file, type_, use_script, cmd_opts)
        # Check using the same golden outcome as test3.
        self.check_string(output_txt, test_method_name="test4")


# #############################################################################
# Test_lint_txt_idempotency
# #############################################################################


class Test_lint_txt_idempotency(hunitest.TestCase):
    """
    Test that lint_txt.py does not modify already formatted files.
    """

    def run_lint_txt(
        self,
        in_file: str,
        type_: str,
        cmd_opts: str,
    ) -> Optional[str]:
        """
        Run lint_txt processing directly by calling the code.

        :param in_file: Path to the input file containing the notes.
        :param type_: The output format, either 'md' or 'tex'.
        :param cmd_opts: Additional command-line options to pass to the
            script.
        :return: The processed text content.
        """
        hdbg.dassert_in(type_, ["md", "tex"])
        # Read input file.
        txt = hio.from_file(in_file)
        lines = txt.split("\n")
        # Process the content directly with default actions (no link checking).
        out_lines = dshdlitx._perform_actions(
            lines,
            in_file,
            actions=dshdlitx._DEFAULT_ACTIONS,
            print_width=80,
            use_dockerized_prettier=True,
            use_dockerized_markdown_toc=True,
        )
        # Return the processed text.
        output_txt = "\n".join(out_lines)
        return output_txt

    def test1(self) -> None:
        """
        Test idempotency for all markdown files in the input directory.

        This test verifies that running lint_txt twice on each file in
        the input directory produces identical output.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        hdbg.dassert_dir_exists(input_dir)
        # Get all markdown files from input directory.
        input_files = []
        for file in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file)
            if os.path.isfile(file_path) and file.endswith(".md"):
                input_files.append(file_path)
        # Check that we have at least one file.
        hdbg.dassert_lt(
            0, len(input_files), "No markdown files found in input directory"
        )
        # Test idempotency for each file.
        for in_file in input_files:
            _LOG.info("Testing idempotency for file: %s", in_file)
            # Prepare outputs.
            type_ = "md"
            cmd_opts = ""
            # Run the script once.
            output_txt_1 = self.run_lint_txt(in_file, type_, cmd_opts)
            # Format the output again using the same formatter.
            lines = output_txt_1.split("\n")
            output_lines = dshdlitx._perform_actions(
                lines,
                in_file,
                actions=dshdlitx._DEFAULT_ACTIONS,
                print_width=80,
                use_dockerized_prettier=True,
                use_dockerized_markdown_toc=True,
            )
            output_txt_2 = "\n".join(output_lines)
            # Check that both runs produce identical output (idempotency).
            self.assert_equal(output_txt_1, output_txt_2)
