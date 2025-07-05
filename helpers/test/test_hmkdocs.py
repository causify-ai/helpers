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
        # Run test.
        actual = hmkdocs.remove_table_of_contents(text)
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
        actual = hmkdocs.remove_table_of_contents(text)
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
        actual = hmkdocs.remove_table_of_contents(text)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_dedent_python_code_blocks1
# #############################################################################


class Test_dedent_python_code_blocks1(hunitest.TestCase):

    def test_simple_code_block(self) -> None:
        """
        Test dedenting a simple Python code block.
        """
        # Prepare inputs.
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
        # Run test.
        actual = hmkdocs.dedent_python_code_blocks(text)
        # Check output.
        self.assert_equal(actual, expected)

    def test_multiple_code_blocks(self) -> None:
        """
        Test dedenting multiple Python code blocks.
        """
        # Prepare inputs.
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
        # Run test.
        actual = hmkdocs.dedent_python_code_blocks(text)
        # Check output.
        self.assert_equal(actual, expected)

    def test_no_python_blocks(self) -> None:
        """
        Test text without Python code blocks remains unchanged.
        """
        # Prepare inputs.
        text = """
        # Example

        This is just text.

        ```javascript
            console.log("Hello");
        ```
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.dedent_python_code_blocks(text)
        # Check output.
        self.assert_equal(actual, text)

    def test_already_aligned_code(self) -> None:
        """
        Test code that is already aligned.
        """
        # Prepare inputs.
        text = """
        # Example

        ```python
        def hello():
            print("Hello")
        ```
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.dedent_python_code_blocks(text)
        # Check output.
        self.assert_equal(actual, text)


# #############################################################################
# Test_replace_indentation1
# #############################################################################


class Test_replace_indentation1(hunitest.TestCase):

    def test_two_to_four_spaces(self) -> None:
        """
        Test replacing 2-space indentation with 4-space indentation.
        """
        # Prepare inputs.
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
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=2, output_spaces=4)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test_four_to_two_spaces(self) -> None:
        """
        Test replacing 4-space indentation with 2-space indentation.
        """
        # Prepare inputs.
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
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=4, output_spaces=2)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test_two_to_eight_spaces(self) -> None:
        """
        Test replacing 2-space indentation with 8-space indentation.
        """
        # Prepare inputs.
        text = """
        - Item 1
          - Sub item 1
            - Sub sub item 1
        """
        expected = """
        - Item 1
                - Sub item 1
                        - Sub sub item 1
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=2, output_spaces=8)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test_three_to_six_spaces(self) -> None:
        """
        Test replacing 3-space indentation with 6-space indentation.
        """
        # Prepare inputs.
        text = """
        - Item 1
           - Sub item 1
              - Sub sub item 1
        """
        expected = """
        - Item 1
              - Sub item 1
                    - Sub sub item 1
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=3, output_spaces=6)
        # Check output.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test_mixed_indentation_only_matches_input(self) -> None:
        """
        Test that only lines with exact input_spaces multiples are changed.
        """
        # Prepare inputs.
        text = """
        - Item 1
          - Sub item 1 (2 spaces)
           - Sub item 2 (1 space, should not change)
             - Sub item 3 (3 spaces, should not change)
            - Sub item 4 (4 spaces, should not change)
        """
        expected = """
        - Item 1
            - Sub item 1 (2 spaces)
           - Sub item 2 (1 space, should not change)
             - Sub item 3 (3 spaces, should not change)
            - Sub item 4 (4 spaces, should not change)
        """
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=2, output_spaces=4)
        # Check output.
        self.assert_equal(actual, expected)

    def test_no_indentation(self) -> None:
        """
        Test text without indentation remains unchanged.
        """
        # Prepare inputs.
        text = """
        - Item 1
        - Item 2
        - Item 3
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=2, output_spaces=4)
        # Check output.
        self.assert_equal(actual, text)

    def test_same_input_output_spaces(self) -> None:
        """
        Test that using same input and output spaces leaves text unchanged.
        """
        # Prepare inputs.
        text = """
        - Item 1
          - Sub item 1
            - Sub sub item 1
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=2, output_spaces=2)
        # Check output.
        self.assert_equal(actual, text)

    def test_empty_text(self) -> None:
        """
        Test empty text handling.
        """
        # Prepare inputs.
        text = ""
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=2, output_spaces=4)
        # Check output.
        self.assert_equal(actual, text)

    def test_zero_to_four_spaces(self) -> None:
        """
        Test converting zero indentation to 4 spaces (edge case).
        """
        # Prepare inputs.
        text = """
        Item 1
        Item 2
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.replace_indentation(text, input_spaces=1, output_spaces=4)
        # Check output.
        self.assert_equal(actual, text)


# #############################################################################
# Test_preprocess_mkdocs_markdown1
# #############################################################################


class Test_preprocess_mkdocs_markdown1(hunitest.TestCase):

    def test_full_preprocessing(self) -> None:
        """
        Test the complete preprocessing pipeline.
        """
        # Prepare inputs.
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
        # Run test.
        actual = hmkdocs.preprocess_mkdocs_markdown(text)
        # Check output.
        self.assert_equal(actual, expected)

    def test_empty_text(self) -> None:
        """
        Test preprocessing empty text.
        """
        # Prepare inputs.
        text = ""
        # Run test.
        actual = hmkdocs.preprocess_mkdocs_markdown(text)
        # Check output.
        self.assert_equal(actual, text)

    def test_text_without_preprocessing_needs(self) -> None:
        """
        Test text that doesn't need any preprocessing.
        """
        # Prepare inputs.
        text = """
        # Simple Markdown

        This is just simple text.

        - Item 1
        - Item 2
        """
        text = hprint.dedent(text)
        # Run test.
        actual = hmkdocs.preprocess_mkdocs_markdown(text)
        # Check output.
        self.assert_equal(actual, text)