import os
from typing import Any, Dict, List

import dev_scripts_helpers.documentation.convert_pandoc_divved_fence as dshdcpdfe
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


def outcome_to_str(outcome: Dict[str, str]) -> str:
    hdbg.dassert_isinstance(outcome, dict)
    outcome_list = []
    for key, val in outcome.items():
        outcome_list.append(hprint.frame(key))
        outcome_list.append(val)
    outcome_str = "\n".join(outcome_list)
    return outcome_str


# TODO(ai_gp): Move to static if it's used in a single place.
def _find_columns_container(ast: Any) -> Any:
    """
    Recursively search AST for the first Div with 'columns' class.

    :param ast: AST or AST element to search
    :return: First columns container found, or None
    """
    if isinstance(ast, dict):
        if dshdcpdfe._is_columns_container(ast):
            return ast
        for value in ast.values():
            result = _find_columns_container(value)
            if result is not None:
                return result
    elif isinstance(ast, list):
        for item in ast:
            result = _find_columns_container(item)
            if result is not None:
                return result
    return None


# #############################################################################
# Test__is_columns_container
# #############################################################################


class Test__is_columns_container(hunitest.TestCase):
    """
    Test the `_is_columns_container()` function.
    """

    def helper(self, elem: Any, expected: bool) -> None:
        """
        Test helper for _is_columns_container.

        :param elem: Element to test
        :param expected: Expected result
        """
        # Run test.
        actual = dshdcpdfe._is_columns_container(elem)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that valid Div with columns class is detected.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [
                ["", ["columns"], []],
                [],
            ],
        }
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(elem, expected)

    def test2(self) -> None:
        """
        Test that non-Div element is rejected.
        """
        # Prepare inputs.
        elem = {"t": "Para", "c": []}
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(elem, expected)

    def test3(self) -> None:
        """
        Test that Div without columns class is rejected.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [
                ["", ["other"], []],
                [],
            ],
        }
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(elem, expected)

    def test4(self) -> None:
        """
        Test that Div with empty c is rejected.
        """
        # Prepare inputs.
        elem = {"t": "Div", "c": []}
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(elem, expected)


# #############################################################################
# Test__extract_columns
# #############################################################################


class Test__extract_columns(hunitest.TestCase):
    """
    Test the `_extract_columns()` function.
    """

    def helper(self, markdown_input: str) -> None:
        """
        Run full pipeline from markdown to extracted columns.

        :param markdown_input: Markdown text to convert
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdcpdfe.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdcpdfe.ast_to_str(ast)
        # Find columns container in AST.
        container = _find_columns_container(ast)
        hdbg.dassert(container is not None, "No columns container found in AST")
        # Extract columns.
        actual = dshdcpdfe._extract_columns(container)
        outcome["3. extracted_columns"] = str(actual)
        actual_outcome = outcome_to_str(outcome)
        self.check_string(actual_outcome)

    def test1(self) -> None:
        """
        Test extraction of two columns with explicit widths.
        """
        markdown_input = """
        ::: {.columns}

        ::: {.column width="55%"}
        Left
        :::

        ::: {.column width="45%"}
        Right
        :::

        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)

    def test2(self) -> None:
        """
        Test that missing width defaults to '1fr'.
        """
        markdown_input = """
        ::: {.columns}

        ::: {.column}
        Default width
        :::

        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)

    def test3(self) -> None:
        """
        Test that non-column child divs are skipped.
        """
        markdown_input = """
        ::: {.columns}

        ::: {.other}
        Ignored
        :::

        ::: {.column width="50%"}
        Included
        :::

        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)


# #############################################################################
# Test__format_grid_code
# #############################################################################


class Test__format_grid_code(hunitest.TestCase):
    """
    Test the `_format_grid_code()` function.
    """

    def helper(
        self, widths: List[str], contents: List[str], expected: str
    ) -> None:
        """
        Test helper for _format_grid_code.

        :param widths: Column widths
        :param contents: Column contents
        :param expected: Expected output
        """
        actual = dshdcpdfe._format_grid_code(widths, contents)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test grid code generation for two columns.

        Markdown input:
        ```
        :::columns
        ::: column {width="55%"}
        Content 1
        :::
        ::: column {width="45%"}
        Content 2
        :::
        :::
        ```
        """
        widths = ["55%", "45%"]
        contents = ["Content 1", "Content 2"]
        expected = hprint.dedent(
            """
            #grid(
              columns: (55%, 45%),
              gutter: 0.5em,
              [
              Content 1
              ],
              [
              Content 2
              ]
            )
            """
        ).strip()
        self.helper(widths, contents, expected)

    def test2(self) -> None:
        """
        Test grid code generation for three columns.

        Markdown input:
        ```
        :::columns
        ::: column
        Left
        :::
        ::: column
        Middle
        :::
        ::: column
        Right
        :::
        :::
        ```
        """
        widths = ["1fr", "1fr", "1fr"]
        contents = ["Left", "Middle", "Right"]
        expected = hprint.dedent(
            """
            #grid(
              columns: (1fr, 1fr, 1fr),
              gutter: 0.5em,
              [
              Left
              ],
              [
              Middle
              ],
              [
              Right
              ]
            )
            """
        ).strip()
        self.helper(widths, contents, expected)


# #############################################################################
# Test__transform_elem
# #############################################################################


class Test__transform_elem(hunitest.TestCase):
    """
    Test the `_transform_elem()` function.
    """

    def helper(self, markdown_input: str) -> None:
        """
        Run full pipeline from markdown to transformed elem.

        :param markdown_input: Markdown text to convert
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdcpdfe.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdcpdfe.ast_to_str(ast)
        # Transform AST.
        actual_ast = dshdcpdfe._transform_ast(ast)
        outcome["3. ast_output"] = dshdcpdfe.ast_to_str(actual_ast)
        actual_outcome = outcome_to_str(outcome)
        self.check_string(actual_outcome)

    def test1(self) -> None:
        """
        Test that columns container is transformed to RawBlock with #grid().

        Markdown input:
        ```markdown
        :::columns
        ::: column {width="50%"}
        col1
        :::
        ::: column {width="50%"}
        col2
        :::
        :::
        ```
        """
        markdown_input = """
        :::columns
        ::: column {width="50%"}
        col1
        :::
        ::: column {width="50%"}
        col2
        :::
        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)

    def test2(self) -> None:
        """
        Test that non-columns Div children are recursively transformed.
        """
        markdown_input = """
        ::: {#id1}
        :::columns
        ::: column {width="50%"}
        nested
        :::
        ::: column {width="50%"}
        col
        :::
        :::
        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)

    def test3(self) -> None:
        """
        Test that Para elements pass through unchanged.
        """
        markdown_input = """
        text
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)

    def test4(self) -> None:
        """
        Test that BulletList items containing nested divs are transformed.

        Verifies that _transform_elem recursively processes items in a
        BulletList, transforming any Divs containing columns within the items.
        """
        markdown_input = """
        - Item 1
        - Item 2:
          :::columns
          ::: column
          content
          :::
          :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)


# #############################################################################
# Test__transform_ast
# #############################################################################


class Test__transform_ast(hunitest.TestCase):
    """
    Test the `_transform_ast()` function.
    """

    def helper(self, markdown_input: str) -> None:
        """
        Run full pipeline from markdown to transformed AST.

        :param markdown_input: Markdown text to convert
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdcpdfe.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdcpdfe.ast_to_str(ast)
        # Transform AST.
        actual_ast = dshdcpdfe._transform_ast(ast)
        outcome["3. ast_output"] = dshdcpdfe.ast_to_str(actual_ast)
        actual_outcome = outcome_to_str(outcome)
        self.check_string(actual_outcome)

    def test1(self) -> None:
        """
        Test full AST transformation with one columns Div.
        """
        markdown_input = """
        # Title

        :::columns
        ::: column {width="50%"}
        left
        :::
        ::: column {width="50%"}
        right
        :::
        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)

    def test2(self) -> None:
        """
        Test AST with no columns remains unchanged.
        """
        markdown_input = """
        text
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)


# #############################################################################
# Test_end_to_end
# #############################################################################


class Test_end_to_end(hunitest.TestCase):
    """
    End-to-end test using pandoc to convert markdown with columns to typst.
    """

    def helper(self, markdown_input: str) -> None:
        """
        Run full pipeline from markdown to transformed AST and typst.

        :param markdown_input: Markdown text to convert
        :param scratch_dir: Directory to store intermediate files
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdcpdfe.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdcpdfe.ast_to_str(ast)
        # Transform AST.
        actual_ast = dshdcpdfe._transform_ast(ast)
        outcome["3. ast_output"] = dshdcpdfe.ast_to_str(actual_ast)
        # Convert transformed AST back to typst.
        transformed_ast_file = os.path.join(scratch_dir, "transformed_ast.json")
        actual_str = dshdcpdfe.ast_to_str(actual_ast)
        hio.to_file(transformed_ast_file, actual_str)
        actual_typst, _ = dshdcpdfe.convert_pandoc_ast_to_typst(
            transformed_ast_file, scratch_dir
        )
        outcome["4. typst_output"] = actual_typst
        actual_outcome = outcome_to_str(outcome)
        self.check_string(actual_outcome)

    def test1(self) -> None:
        """
        Test full pipeline:
        - markdown with :::columns
        - AST
        - transform
        - typst
        """
        markdown_input = """
        # Title

        :::columns
        ::: column
        Left content
        :::

        ::: column
        Right content
        :::
        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)

    def test2(self) -> None:
        """
        Test AST transformation with inline formatting (bold/italic) in columns.

        This test specifically addresses the rendering issue where inline
        formatted text in multi-line list items could be split awkwardly
        across lines (e.g., "samples" and "_independent_" separated).

        Expected behavior:
        - AST preserves all inline formatting in blocks
        - Columns are correctly extracted with content preserved
        - Transformation produces valid typst grid code
        """
        markdown_input = """
        * Search Over Reasoning

        :::columns
        ::: column {width="50%"}
        - **Problem**: self-consistency samples _independent_ chains and cannot revisit
        - **Solution**: treat reasoning as _search_ over structure
        :::

        ::: column {width="45%"}
        Text in second column
        :::
        :::
        """
        markdown_input = hprint.dedent(markdown_input)
        self.helper(markdown_input)
