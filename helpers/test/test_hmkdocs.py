import logging

import helpers.hmkdocs as hmkdocs
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
        # Run function.
        actual = hmkdocs.remove_table_of_contents(text)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test_without_toc(self) -> None:
        """
        Test text without table of contents remains unchanged.
        """
        text = """
        # Introduction

        This is an introduction.

        ## Section 1

        Content of section 1.
        """
        text = hprint.dedent(text)
        actual = hmkdocs.remove_table_of_contents(text)
        self.assert_equal(actual, text)

    def test_multiline_toc(self) -> None:
        """
        Test removing multi-line table of contents.
        """
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
        expected = hprint.dedent(expected)
        actual = hmkdocs.remove_table_of_contents(text)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_dedent_python_code_blocks1
# #############################################################################


class Test_dedent_python_code_blocks1(hunitest.TestCase):

    def test_simple_code_block(self) -> None:
        """
        Test dedenting a simple Python code block.
        """
        text = """
        # Example

        ```python
            def hello():
                print("Hello")
        ```
        """
        expected = """
        # Example

        ```python
        def hello():
            print("Hello")
        ```
        """
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        actual = hmkdocs.dedent_python_code_blocks(text)
        self.assert_equal(actual, expected)

    def test_multiple_code_blocks(self) -> None:
        """
        Test dedenting multiple Python code blocks.
        """
        text = """
        # Example 1

        ```python
            def hello():
                print("Hello")
        ```

        # Example 2

        ```python
            def goodbye():
                print("Goodbye")
        ```
        """
        expected = """
        # Example 1

        ```python
        def hello():
            print("Hello")
        ```

        # Example 2

        ```python
        def goodbye():
            print("Goodbye")
        ```
        """
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        actual = hmkdocs.dedent_python_code_blocks(text)
        self.assert_equal(actual, expected)

    def test_no_python_blocks(self) -> None:
        """
        Test text without Python code blocks remains unchanged.
        """
        text = """
        # Example

        This is just text.

        ```javascript
            console.log("Hello");
        ```
        """
        text = hprint.dedent(text)
        actual = hmkdocs.dedent_python_code_blocks(text)
        self.assert_equal(actual, text)

    def test_already_aligned_code(self) -> None:
        """
        Test code that is already aligned.
        """
        text = """
        # Example

        ```python
        def hello():
            print("Hello")
        ```
        """
        text = hprint.dedent(text)
        actual = hmkdocs.dedent_python_code_blocks(text)
        self.assert_equal(actual, text)


# #############################################################################
# Test_replace_indentation_with_four_spaces1
# #############################################################################


class Test_replace_indentation_with_four_spaces1(hunitest.TestCase):

    def test_two_space_indentation(self) -> None:
        """
        Test replacing 2-space indentation with 4-space indentation.
        """
        text = """
        - Item 1
          - Sub item 1
            - Sub sub item 1
        - Item 2
          - Sub item 2
        """
        expected = """
        - Item 1
            - Sub item 1
                - Sub sub item 1
        - Item 2
            - Sub item 2
        """
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        actual = hmkdocs.replace_indentation_with_four_spaces(text)
        self.assert_equal(actual, expected)

    def test_mixed_indentation(self) -> None:
        """
        Test text with mixed indentation types.
        """
        text = """
        - Item 1
          - Sub item 1 (2 spaces)
             - Sub item 2 (3 spaces, should not change)
            - Sub item 3 (4 spaces, should not change)
        - Item 2
        """
        expected = """
        - Item 1
            - Sub item 1 (2 spaces)
             - Sub item 2 (3 spaces, should not change)
            - Sub item 3 (4 spaces, should not change)
        - Item 2
        """
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        actual = hmkdocs.replace_indentation_with_four_spaces(text)
        self.assert_equal(actual, expected)

    def test_no_indentation(self) -> None:
        """
        Test text without indentation remains unchanged.
        """
        text = """
        - Item 1
        - Item 2
        - Item 3
        """
        text = hprint.dedent(text)
        actual = hmkdocs.replace_indentation_with_four_spaces(text)
        self.assert_equal(actual, text)

    def test_four_space_indentation(self) -> None:
        """
        Test that 4-space indentation becomes 8-space.
        """
        text = """
        - Item 1
            - Sub item 1 (4 spaces)
        - Item 2
        """
        expected = """
        - Item 1
                - Sub item 1 (4 spaces)
        - Item 2
        """
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        actual = hmkdocs.replace_indentation_with_four_spaces(text)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_preprocess_mkdocs_markdown1
# #############################################################################


class Test_preprocess_mkdocs_markdown1(hunitest.TestCase):

    def test_full_preprocessing(self) -> None:
        """
        Test the complete preprocessing pipeline.
        """
        text = """
        # Introduction

        <!-- toc -->
        - [Section 1](#section-1)
        - [Section 2](#section-2)
        <!-- tocstop -->

        ## Section 1

        Here is some Python code:

        ```python
            def example():
                print("Hello")
                if True:
                    print("World")
        ```

        - Item 1
          - Sub item 1
            - Sub sub item 1
        - Item 2
        """
        expected = """
        # Introduction



        ## Section 1

        Here is some Python code:

        ```python
        def example():
            print("Hello")
            if True:
                print("World")
        ```

        - Item 1
            - Sub item 1
                - Sub sub item 1
        - Item 2
        """
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        actual = hmkdocs.preprocess_mkdocs_markdown(text)
        self.assert_equal(actual, expected)

    def test_empty_text(self) -> None:
        """
        Test preprocessing empty text.
        """
        text = ""
        actual = hmkdocs.preprocess_mkdocs_markdown(text)
        self.assert_equal(actual, text)

    def test_text_without_preprocessing_needs(self) -> None:
        """
        Test text that doesn't need any preprocessing.
        """
        text = """
        # Simple Markdown

        This is just simple text.

        - Item 1
        - Item 2
        """
        text = hprint.dedent(text)
        actual = hmkdocs.preprocess_mkdocs_markdown(text)
        self.assert_equal(actual, text)