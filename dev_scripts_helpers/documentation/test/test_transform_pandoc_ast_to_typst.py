import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Tuple

import pytest

import dev_scripts_helpers.documentation.transform_pandoc_ast_to_typst as dshdtpatt
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

# TODO(ai_gp): replace assertEqual with self.assert_equal
# TODO(ai_gp): Add self.assert_equal or self.check_string everywhere needed

# #############################################################################
# Helper Functions
# #############################################################################


def outcome_to_str(outcome: Dict[str, str]) -> str:
    """
    Convert outcome dict to formatted string.

    :param outcome: Dict with keys for framing and values for content
    :return: Formatted string with frames and content
    """
    hdbg.dassert_isinstance(outcome, dict)
    outcome_list = []
    for key, val in outcome.items():
        outcome_list.append(hprint.frame(key))
        outcome_list.append(val)
    outcome_str = "\n".join(outcome_list)
    return outcome_str


def markdown_to_ast_outcome(
    markdown_input: str, scratch_dir: str
) -> Tuple[Dict[str, Any], str]:
    """
    Convert markdown to AST and return outcome dict with formatted output.

    :param markdown_input: Markdown text to convert
    :param scratch_dir: Directory for scratch files
    :return: Tuple of (AST, formatted outcome string)
    """
    outcome = {}
    markdown_input = hprint.dedent(markdown_input)
    outcome["1. markdown_input"] = markdown_input
    ast, _, _ = dshdtpatt.convert_markdown_to_pandoc_ast(
        markdown_input, scratch_dir
    )
    outcome["2. ast_input"] = dshdtpatt.ast_to_str(ast)
    return ast, outcome_to_str(outcome)


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
        actual = dshdtpatt._is_columns_container(elem)
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

    @staticmethod
    def _find_columns_container(ast: Any) -> Any:
        """
        Recursively search AST for the first Div with 'columns' class.

        :param ast: AST or AST element to search
        :return: First columns container found, or None
        """
        if isinstance(ast, dict):
            if dshdtpatt._is_columns_container(ast):
                return ast
            for value in ast.values():
                result = Test__extract_columns._find_columns_container(value)
                if result is not None:
                    return result
        elif isinstance(ast, list):
            for item in ast:
                result = Test__extract_columns._find_columns_container(item)
                if result is not None:
                    return result
        return None

    def helper(self, markdown_input: str) -> str:
        """
        Run full pipeline from markdown to extracted columns.

        :param markdown_input: Markdown text to convert
        :return: Formatted outcome string
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdtpatt.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdtpatt.ast_to_str(ast)
        # Find columns container in AST.
        container = self._find_columns_container(ast)
        hdbg.dassert(container is not None, "No columns container found in AST")
        # Extract columns.
        actual = dshdtpatt._extract_columns(container)
        outcome["3. extracted_columns"] = str(actual)
        actual_outcome = outcome_to_str(outcome)
        return actual_outcome

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify extraction completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("extracted_columns", actual)

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify extraction completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("extracted_columns", actual)

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify extraction completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("extracted_columns", actual)


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
        actual = dshdtpatt._format_grid_code(widths, contents)
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

    def helper(self, markdown_input: str) -> str:
        """
        Run full pipeline from markdown to transformed elem.

        :param markdown_input: Markdown text to convert
        :return: Formatted outcome string
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdtpatt.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdtpatt.ast_to_str(ast)
        # Transform AST.
        actual_ast = dshdtpatt._transform_ast_divved_fence(ast)
        outcome["3. ast_output"] = dshdtpatt.ast_to_str(actual_ast)
        actual_outcome = outcome_to_str(outcome)
        return actual_outcome

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify transformation completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("ast_output", actual)

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify transformation completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("ast_output", actual)

    def test3(self) -> None:
        """
        Test that Para elements pass through unchanged.
        """
        markdown_input = """
        text
        """
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify transformation completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("ast_output", actual)

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify transformation completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("ast_output", actual)


# #############################################################################
# Test__transform_ast
# #############################################################################


class Test__transform_ast(hunitest.TestCase):
    """
    Test the `_transform_ast()` function.
    """

    def helper(self, markdown_input: str) -> str:
        """
        Run full pipeline from markdown to transformed AST.

        :param markdown_input: Markdown text to convert
        :return: Formatted outcome string
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdtpatt.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdtpatt.ast_to_str(ast)
        # Transform AST.
        actual_ast = dshdtpatt._transform_ast_divved_fence(ast)
        outcome["3. ast_output"] = dshdtpatt.ast_to_str(actual_ast)
        actual_outcome = outcome_to_str(outcome)
        return actual_outcome

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify transformation completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("ast_output", actual)

    def test2(self) -> None:
        """
        Test AST with no columns remains unchanged.
        """
        markdown_input = """
        text
        """
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify transformation completed and has content.
        self.assertIsNotNone(actual)
        self.assertIn("ast_output", actual)


# #############################################################################
# Test_end_to_end
# #############################################################################


class Test_end_to_end(hunitest.TestCase):
    """
    End-to-end test using pandoc to convert markdown with columns to typst.
    """

    def helper(self, markdown_input: str) -> str:
        """
        Run full pipeline from markdown to transformed AST and typst.

        :param markdown_input: Markdown text to convert
        :return: Formatted outcome string
        """
        scratch_dir = self.get_scratch_space()
        outcome = {}
        markdown_input = hprint.dedent(markdown_input)
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdtpatt.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_input"] = dshdtpatt.ast_to_str(ast)
        # Transform AST.
        actual_ast = dshdtpatt._transform_ast_divved_fence(ast)
        outcome["3. ast_output"] = dshdtpatt.ast_to_str(actual_ast)
        # Convert transformed AST back to typst.
        transformed_ast_file = os.path.join(scratch_dir, "transformed_ast.json")
        actual_str = dshdtpatt.ast_to_str(actual_ast)
        hio.to_file(transformed_ast_file, actual_str)
        actual_typst, _ = dshdtpatt.convert_pandoc_ast_to_typst(
            transformed_ast_file, scratch_dir
        )
        outcome["4. typst_output"] = actual_typst
        actual_outcome = outcome_to_str(outcome)
        return actual_outcome

    @pytest.mark.skipif(
        shutil.which("pandoc") is None, reason="pandoc is not installed"
    )
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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify full pipeline completed and generated typst output.
        self.assertIsNotNone(actual)
        self.assertIn("typst_output", actual)

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
        # Run test.
        actual = self.helper(markdown_input)
        # Check outputs: verify full pipeline completed and generated typst output.
        self.assertIsNotNone(actual)
        self.assertIn("typst_output", actual)


# #############################################################################
# Test__find_textcolor_calls
# #############################################################################


class Test__find_textcolor_calls(hunitest.TestCase):
    """
    Test the `_find_textcolor_calls()` brace-aware parser.
    """

    def test_flat_content(self) -> None:
        r"""
        Test extraction of a single call with no nested braces.
        """
        latex_string = r"\textcolor{red}{hello}"
        calls = dshdtpatt._find_textcolor_calls(latex_string)
        self.assertEqual(len(calls), 1)
        start, end, color, content = calls[0]
        self.assertEqual(latex_string[start:end], latex_string)
        self.assertEqual(color, "red")
        self.assertEqual(content, "hello")

    def test_nested_braces(self) -> None:
        r"""
        Test extraction when `content` contains a nested brace group, e.g. a
        subscript `x_{n-1}`.

        A naive `[^}]*` regex stops at the first `}` and truncates
        `content`; this must capture it whole.
        """
        latex_string = r"\textcolor{blue}{x_1, ..., x_{n-1}}"
        calls = dshdtpatt._find_textcolor_calls(latex_string)
        self.assertEqual(len(calls), 1)
        _, end, color, content = calls[0]
        self.assertEqual(color, "blue")
        self.assertEqual(content, "x_1, ..., x_{n-1}")
        self.assertEqual(end, len(latex_string))

    def test_multiple_calls(self) -> None:
        r"""
        Test extraction of multiple `\textcolor` calls in one formula.
        """
        latex_string = r"\Pr(\textcolor{blue}{x}, \textcolor{red}{y})"
        calls = dshdtpatt._find_textcolor_calls(latex_string)
        self.assertEqual(len(calls), 2)
        self.assertEqual((calls[0][2], calls[0][3]), ("blue", "x"))
        self.assertEqual((calls[1][2], calls[1][3]), ("red", "y"))

    def test_no_textcolor(self) -> None:
        r"""
        Test that a formula without `\textcolor` yields no calls.
        """
        calls = dshdtpatt._find_textcolor_calls("x + y")
        self.assertEqual(calls, [])


# #############################################################################
# Test_ColorTransformer
# #############################################################################


class Test_ColorTransformer(hunitest.TestCase):
    def test_textcolor_basic(self) -> None:
        r"""
        Test basic \textcolor transformation.
        """
        transformer = dshdtpatt.ColorTransformer()
        latex_string = r"\textcolor{red}{hello}"
        result = transformer.textcolor_to_typst(latex_string)
        expected = r"#text(fill: red)[hello]"
        self.assertEqual(result, expected)

    def test_textcolor_with_special_chars(self) -> None:
        r"""
        Test \textcolor with special characters.
        """
        transformer = dshdtpatt.ColorTransformer()
        latex_string = r"\textcolor{blue}{test [content]}"
        result = transformer.textcolor_to_typst(latex_string)
        expected = r"#text(fill: blue)[test \[content\]]"
        self.assertEqual(result, expected)

    def test_color_command(self) -> None:
        r"""
        Test \color command (placeholder behavior).
        """
        transformer = dshdtpatt.ColorTransformer()
        latex_string = r"\color{green}"
        result = transformer.color_to_typst(latex_string)
        expected = r"\color{green}"
        self.assertEqual(result, expected)

    @pytest.mark.skipif(
        shutil.which("pandoc") is None, reason="pandoc is not installed"
    )
    def test_math_node_with_textcolor(self) -> None:
        r"""
        Test transformation of Math node with \textcolor.

        The node must be re-tagged from `Math` to `RawInline` (format
        `typst`): once `\textcolor` has been turned into `#text(fill:
        ...)[...]`, the string is Typst syntax, not LaTeX, so it must not be
        re-parsed as TeX math again downstream.
        """
        transformer = dshdtpatt.ColorTransformer()
        node = {
            "t": "Math",
            "c": ["DisplayMath", r"\textcolor{red}{x + y}"],
        }
        result = transformer.process_math_node(node)
        self.assertEqual(result["t"], "RawInline")
        self.assertEqual(result["c"][0], "typst")
        self.assertIn("red", result["c"][1])
        self.assertNotIn(r"\textcolor", result["c"][1])
        self.assertEqual(transformer.stats["math_nodes_processed"], 1)
        self.assertEqual(transformer.stats["formulas_transformed"], 1)

    def test_math_node_without_color(self) -> None:
        r"""
        Test Math node without color commands remains unchanged.
        """
        transformer = dshdtpatt.ColorTransformer()
        node = {
            "t": "Math",
            "c": ["DisplayMath", "x + y"],
        }
        result = transformer.process_math_node(node)
        self.assertEqual(result, node)
        self.assertEqual(transformer.stats["math_nodes_processed"], 1)
        self.assertEqual(transformer.stats["formulas_transformed"], 0)

    @pytest.mark.skipif(
        shutil.which("pandoc") is None, reason="pandoc is not installed"
    )
    def test_ast_walk_with_colors(self) -> None:
        """
        Test walking full AST and transforming Math nodes.
        """
        transformer = dshdtpatt.ColorTransformer()
        ast = {
            "t": "Para",
            "c": [
                {"t": "Math", "c": ["InlineMath", r"\textcolor{red}{a}"]},
                {"t": "Str", "c": "text"},
            ],
        }
        result = transformer.walk(ast)
        self.assertIn("red", str(result))

    def test_textcolor_nested_braces(self) -> None:
        r"""
        Test \textcolor with a nested brace group in content (e.g. a
        subscript).

        Regression test: the original `\{([^}]*)\}` regex stops at the
        first inner `}`, truncating `content` to `"x_1, ..., x_{n-1"` and
        leaving a dangling `}` in the output, e.g.
        `#text(fill: blue)[x_1, ..., x_{n-1]}`.
        """
        transformer = dshdtpatt.ColorTransformer()
        latex_string = r"\textcolor{blue}{x_1, ..., x_{n-1}}"
        result = transformer.textcolor_to_typst(latex_string)
        expected = r"#text(fill: blue)[x_1, ..., x_{n-1}]"
        self.assertEqual(result, expected)

    def test_stats_collection(self) -> None:
        """
        Test that stats are properly collected.
        """
        transformer = dshdtpatt.ColorTransformer()
        transformer.textcolor_to_typst(r"\textcolor{red}{a}")
        transformer.textcolor_to_typst(r"\textcolor{blue}{b}")
        transformer.color_to_typst(r"\color{green}")
        stats = transformer.get_stats()
        self.assertEqual(stats["textcolor_count"], 2)
        self.assertEqual(stats["color_count"], 1)


# #############################################################################
# Test_colorized_math
# #############################################################################


class Test_colorized_math(hunitest.TestCase):
    """
    Test the AST transformation with real-world mathematical content:
    Chain Rule for Joint Distributions theorem with LaTeX colors.
    """

    @pytest.mark.skipif(
        shutil.which("pandoc") is None, reason="pandoc is not installed"
    )
    def test1(self) -> None:
        r"""
        Test AST transformation of Chain Rule theorem with colored LaTeX.

        Input: Markdown with theorem statement, proof, and colored math
        expressions using LaTeX \textcolor directives.

        Expected behavior:
        - Markdown parses to valid AST with Math nodes
        - Color transformation converts \textcolor{color}{content} to
          #text(fill: color)[content]
        - AST converts to valid typst code
        - Bullet points and nested structures are preserved
        - Aligned math environment (align*) is correctly handled
        """
        # Prepare inputs.
        markdown_input = hprint.dedent(
            r"""
            # Chain Rule for a Joint Distribution

            - **Theorem**: A joint distribution can always be expressed using the
              chain rule for any:
              - Subset of its random variables
              - Ordering of the random variables

            - **Proof**
              1. **Express one variable** conditionally to the remaining ones
                 $$
                 \Pr(\textcolor{blue}{x_1, ..., x_{n-1}}, \textcolor{red}{x_n})
                 = \Pr(\textcolor{red}{x_n} | \textcolor{blue}{x_{n-1}, ..., x_1})
                 \Pr(\textcolor{blue}{x_{n-1}, ..., x_1})
                 $$

              2. Apply the same formula **recursively**, until you get an
                 unconditional probability
                 $$
                 \begin{align*}
                 & \Pr(\textcolor{gray}{x_1}, \textcolor{violet}{x_2}, ...,
                   \textcolor{teal}{x_{n-2}}, \textcolor{olive}{x_{n-1}},
                   \textcolor{orange}{x_n}) \\
                 & = \Pr(\textcolor{orange}{x_n} | x_{n-1}, ..., x_1)
                   \Pr(x_{n-1}, ..., x_1) \\
                 & = \Pr(\textcolor{orange}{x_n} | x_{n-1}, ..., x_1)
                   \Pr(\textcolor{olive}{x_{n-1}} | x_{n-2}, ..., x_1)
                   \Pr(x_{n-2}, ..., x_1) \\
                 & ... \\
                 & = \Pr(\textcolor{orange}{x_n} | x_{n-1}, ..., x_1)
                   \Pr(\textcolor{olive}{x_{n-1}} | x_{n-2}, ..., x_1)
                   \Pr(\textcolor{teal}{x_{n-2}} | x_{n-3}, ..., x_1)
                   ...
                   \Pr(\textcolor{violet}{x_2} | x_1) \Pr(\textcolor{gray}{x_1}) \\
                 & = \prod_{i=1}^n \Pr(x_i | x_{i-1}, ..., x_1)
                 \end{align*}
                 $$
            """
        )
        scratch_dir = self.get_scratch_space()
        outcome = {}
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdtpatt.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_generated"] = "AST generated successfully"
        # Transform AST: apply color transformation.
        transformed_ast = dshdtpatt._transform_ast_color_text(ast)
        outcome["3. color_transform_applied"] = "Color transformation applied"
        # Convert transformed AST to typst.
        transformed_ast_file = os.path.join(scratch_dir, "transformed_ast.json")
        ast_str = dshdtpatt.ast_to_str(transformed_ast)
        hio.to_file(transformed_ast_file, ast_str)
        typst_output, _ = dshdtpatt.convert_pandoc_ast_to_typst(
            transformed_ast_file, scratch_dir
        )
        outcome["4. typst_output_length"] = f"{len(typst_output)} characters"
        outcome["5. typst_output_preview"] = typst_output[:500] + "..."
        # Run test.
        actual_outcome = outcome_to_str(outcome)
        # Check outputs: verify transformation completed and produced output.
        self.assertIsNotNone(actual_outcome)
        self.assertIn("typst_output_length", actual_outcome)

    def test2(self) -> None:
        r"""
        Test color transformation in display math environment.

        Verifies that \textcolor commands in $$ ... $$ equations are
        properly transformed to #text(fill: color)[...] syntax.
        """
        transformer = dshdtpatt.ColorTransformer()
        latex_formula = (
            r"\Pr(\textcolor{blue}{x_1, ..., x_{n-1}}, "
            r"\textcolor{red}{x_n}) = \Pr(\textcolor{red}{x_n} | "
            r"\textcolor{blue}{x_{n-1}, ..., x_1})"
        )
        result = transformer.transform_formula(latex_formula)
        # Verify all colors were transformed.
        self.assertIn("blue", result)
        self.assertIn("red", result)
        self.assertNotIn(r"\textcolor", result)
        self.assertIn("#text(fill:", result)
        expected = (
            r"\Pr(#text(fill: blue)[x_1, ..., x_{n-1}], "
            r"#text(fill: red)[x_n]) = \Pr(#text(fill: red)[x_n] | "
            r"#text(fill: blue)[x_{n-1}, ..., x_1])"
        )
        self.assertEqual(result, expected)

    def test_multiple_colors_in_formula(self) -> None:
        """
        Test transformation with multiple colors in single formula.

        Input uses 6 different colors (gray, violet, teal, olive, orange)
        to highlight different random variables.
        """
        transformer = dshdtpatt.ColorTransformer()
        latex_formula = (
            r"\Pr(\textcolor{gray}{x_1}, \textcolor{violet}{x_2}, "
            r"\textcolor{teal}{x_{n-2}}, \textcolor{olive}{x_{n-1}}, "
            r"\textcolor{orange}{x_n})"
        )
        result = transformer.transform_formula(latex_formula)
        # Verify all colors present in result.
        expected_colors = ["gray", "violet", "teal", "olive", "orange"]
        for color in expected_colors:
            self.assertIn(color, result)
        # Verify all \textcolor removed.
        self.assertNotIn(r"\textcolor", result)
        expected = (
            r"\Pr(#text(fill: gray)[x_1], #text(fill: violet)[x_2], "
            r"#text(fill: teal)[x_{n-2}], #text(fill: olive)[x_{n-1}], "
            r"#text(fill: orange)[x_n])"
        )
        self.assertEqual(result, expected)


# #############################################################################
# Test__is_small_code_div
# #############################################################################


class Test__is_small_code_div(hunitest.TestCase):
    """
    Test the `_is_small_code_div()` function.
    """

    def test1(self) -> None:
        """
        Detect basic Div with 'small-code' class.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [
                ["", ["small-code"], []],
                [{"t": "Para", "c": []}],
            ],
        }
        # Run test.
        actual = dshdtpatt._is_small_code_div(elem)
        # Check outputs.
        self.assertTrue(actual)

    def test2(self) -> None:
        """
        Detect small-code among other class names.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [["", ["container", "small-code", "custom"], []], []],
        }
        # Run test.
        actual = dshdtpatt._is_small_code_div(elem)
        # Check outputs.
        self.assertTrue(actual)

    def test3(self) -> None:
        """
        Reject Div without small-code class.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [["", ["other-class"], []], []],
        }
        # Run test.
        actual = dshdtpatt._is_small_code_div(elem)
        # Check outputs.
        self.assertFalse(actual)

    def test4(self) -> None:
        """
        Reject non-Div elements.
        """
        # Prepare inputs.
        elem = {"t": "Para", "c": []}
        # Run test.
        actual = dshdtpatt._is_small_code_div(elem)
        # Check outputs.
        self.assertFalse(actual)

    def test5(self) -> None:
        """
        Reject malformed Div without 'c' key.
        """
        # Prepare inputs.
        elem = {"t": "Div"}
        # Run test.
        actual = dshdtpatt._is_small_code_div(elem)
        # Check outputs.
        self.assertFalse(actual)


# #############################################################################
# Test__transform_small_code_div
# #############################################################################


class Test__transform_small_code_div(hunitest.TestCase):
    """
    Test the `_transform_small_code_div()` function.
    """

    def test1(self) -> None:
        """
        Transform small-code Div to RawBlock with typst formatting.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [["", ["small-code"], []], [{"t": "Para", "c": []}]],
        }
        # Run test.
        result = dshdtpatt._transform_small_code_div(elem)
        # Check outputs.
        self.assertEqual(result["t"], "RawBlock")
        self.assertEqual(result["c"][0], "typst")
        self.assertIn("#text(size: 0.8em)", result["c"][1])

    def test2(self) -> None:
        """
        Non-small-code Divs pass through unchanged.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [["", ["other-class"], []], [{"t": "Para", "c": []}]],
        }
        # Run test.
        result = dshdtpatt._transform_small_code_div(elem)
        # Check outputs.
        self.assertEqual(result, elem)

    def test3(self) -> None:
        """
        Empty small-code Div passes through unchanged.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [["", ["small-code"], []], []],
        }
        # Run test.
        result = dshdtpatt._transform_small_code_div(elem)
        # Check outputs.
        self.assertEqual(result, elem)


# #############################################################################
# Test__walk_transform_small_code
# #############################################################################


class Test__walk_transform_small_code(hunitest.TestCase):
    """
    Test the `_walk_transform_small_code()` function.
    """

    def test1(self) -> None:
        """
        Walker transforms top-level small-code Div.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [["", ["small-code"], []], [{"t": "Para", "c": []}]],
        }
        # Run test.
        result = dshdtpatt._walk_transform_small_code(elem)
        # Check outputs.
        self.assertEqual(result["t"], "RawBlock")

    def test2(self) -> None:
        """
        Walker finds and transforms nested small-code Div.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [
                ["", ["outer"], []],
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["small-code"], []],
                            [{"t": "Para", "c": []}],
                        ],
                    }
                ],
            ],
        }
        # Run test.
        result = dshdtpatt._walk_transform_small_code(elem)
        # Check outputs.
        self.assertEqual(result["c"][1][0]["t"], "RawBlock")

    def test3(self) -> None:
        """
        Walker transforms small-code Divs inside list items.
        """
        # Prepare inputs.
        elem = {
            "t": "BulletList",
            "c": [
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["small-code"], []],
                            [{"t": "Para", "c": []}],
                        ],
                    }
                ],
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["small-code"], []],
                            [{"t": "Para", "c": []}],
                        ],
                    }
                ],
            ],
        }
        # Run test.
        result = dshdtpatt._walk_transform_small_code(elem)
        # Check outputs.
        self.assertEqual(result["c"][0][0]["t"], "RawBlock")
        self.assertEqual(result["c"][1][0]["t"], "RawBlock")

    def test4(self) -> None:
        """
        Walker preserves non-small-code elements.
        """
        # Prepare inputs.
        elem = {
            "t": "Para",
            "c": [{"t": "Str", "c": "text"}],
        }
        # Run test.
        result = dshdtpatt._walk_transform_small_code(elem)
        # Check outputs.
        self.assertEqual(result, elem)


# #############################################################################
# Test__transform_ast_small_code
# #############################################################################


class Test__transform_ast_small_code(hunitest.TestCase):
    """
    Test the `_transform_ast_small_code()` function.
    """

    def test1(self) -> None:
        """
        Transform AST with single small-code block.
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [
                {
                    "t": "Div",
                    "c": [["", ["small-code"], []], [{"t": "Para", "c": []}]],
                }
            ],
        }
        # Run test.
        result = dshdtpatt._transform_ast_small_code(ast)
        # Check outputs.
        self.assertEqual(result["blocks"][0]["t"], "RawBlock")

    def test2(self) -> None:
        """
        Transformation preserves AST structure and metadata.
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {"title": "Test"},
            "blocks": [
                {
                    "t": "Div",
                    "c": [["", ["small-code"], []], [{"t": "Para", "c": []}]],
                }
            ],
        }
        # Run test.
        result = dshdtpatt._transform_ast_small_code(ast)
        # Check outputs.
        self.assertEqual(result["pandoc-api-version"], [1, 23, 1])
        self.assertEqual(result["meta"], {"title": "Test"})

    def test3(self) -> None:
        """
        Transform AST with mixed block types.
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [
                {"t": "Para", "c": []},
                {
                    "t": "Div",
                    "c": [["", ["small-code"], []], [{"t": "Para", "c": []}]],
                },
                {"t": "Para", "c": []},
            ],
        }
        # Run test.
        result = dshdtpatt._transform_ast_small_code(ast)
        # Check outputs.
        self.assertEqual(result["blocks"][0]["t"], "Para")
        self.assertEqual(result["blocks"][1]["t"], "RawBlock")
        self.assertEqual(result["blocks"][2]["t"], "Para")

    def test4(self) -> None:
        """
        Transform empty AST with no blocks.
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [],
        }
        # Run test.
        result = dshdtpatt._transform_ast_small_code(ast)
        # Check outputs.
        self.assertEqual(result["blocks"], [])

    def test5(self) -> None:
        """
        AST without small-code blocks remains unchanged.
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [
                {"t": "Div", "c": [["", ["other-class"], []], []]},
            ],
        }
        # Run test.
        result = dshdtpatt._transform_ast_small_code(ast)
        # Check outputs.
        self.assertEqual(result["blocks"][0]["t"], "Div")
        self.assertEqual(result["blocks"][0]["c"][0][1], ["other-class"])


# #############################################################################
# Test_small_code_end_to_end
# #############################################################################


class Test_small_code_end_to_end(hunitest.TestCase):
    """
    End-to-end tests for small-code transformations.
    """

    def test1(self) -> None:
        """
        Small-code wrapping code block produces valid Typst.
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [
                ["", ["small-code"], []],
                [
                    {
                        "t": "CodeBlock",
                        "c": [["", ["python"], []], "x = 1 + 2"],
                    }
                ],
            ],
        }
        # Run test.
        result = dshdtpatt._transform_small_code_div(elem)
        # Check outputs.
        self.assertEqual(result["t"], "RawBlock")
        self.assertIn("#text(size: 0.8em)", result["c"][1])

    def test2(self) -> None:
        """
        Transformed AST serializes and deserializes correctly.
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [
                {
                    "t": "Div",
                    "c": [["", ["small-code"], []], [{"t": "Para", "c": []}]],
                }
            ],
        }
        # Run test.
        result = dshdtpatt._transform_ast_small_code(ast)
        json_str = json.dumps(result)
        restored = json.loads(json_str)
        # Check outputs.
        self.assertEqual(restored["blocks"][0]["t"], "RawBlock")
        self.assertEqual(restored["blocks"][0]["c"][0], "typst")
        self.assertIn("#text(size: 0.8em)", restored["blocks"][0]["c"][1])

    @pytest.mark.skipif(
        shutil.which("pandoc") is None, reason="pandoc is not installed"
    )
    def test3(self) -> None:
        r"""
        Test full pipeline: markdown -> AST -> small-code transform -> typst.

        Input: Markdown with small-code div wrapping code snippets and text.

        Expected behavior:
        - Markdown parses to valid AST with small-code Div
        - Small-code transformation converts Div to RawBlock with
          #text(size: 0.8em) wrapper
        - AST converts to valid typst code with small-code formatting preserved
        - Output is renderable typst syntax
        """
        # Prepare inputs.
        markdown_input = hprint.dedent(
            r"""
            # Small Code Examples

            ## Python Code

            ::: {.small-code}

            ```python
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)
            ```

            :::

            ## JavaScript Code

            ::: {.small-code}

            ```javascript
            const sum = (a, b) => a + b;
            const result = sum(5, 3);
            ```

            :::

            Normal text between code blocks.

            ## Mixed Content

            ::: {.small-code}

            This is small text explaining a complex formula:

            $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$

            :::
            """
        )
        scratch_dir = self.get_scratch_space()
        outcome = {}
        outcome["1. markdown_input"] = markdown_input
        # Convert markdown to AST.
        ast, _, _ = dshdtpatt.convert_markdown_to_pandoc_ast(
            markdown_input, scratch_dir
        )
        outcome["2. ast_generated"] = "AST generated successfully"
        # Transform AST: apply small-code transformation.
        transformed_ast = dshdtpatt._transform_ast_small_code(ast)
        outcome["3. small_code_transform_applied"] = (
            "Small-code transformation applied"
        )
        # Convert transformed AST to typst.
        transformed_ast_file = os.path.join(scratch_dir, "transformed_ast.json")
        ast_str = dshdtpatt.ast_to_str(transformed_ast)
        hio.to_file(transformed_ast_file, ast_str)
        typst_output, _ = dshdtpatt.convert_pandoc_ast_to_typst(
            transformed_ast_file, scratch_dir
        )
        outcome["4. typst_output_length"] = f"{len(typst_output)} characters"
        outcome["5. typst_output_preview"] = typst_output[:500] + "..."
        # Run test.
        actual_outcome = outcome_to_str(outcome)
        # Check outputs: verify transformation completed and produced typst output.
        self.assertIsNotNone(actual_outcome)
        self.assertIn("typst_output_length", actual_outcome)
        self.assertIn("small_code_transform_applied", actual_outcome)
        # Verify typst output contains formatting and content.
        self.assertGreater(
            len(typst_output), 0, "Typst output should not be empty"
        )
        # Verify code block language is in the output.
        typst_lower = typst_output.lower()
        self.assertTrue(
            "python" in typst_lower or "javascript" in typst_lower,
            "Code block language should be present in output",
        )


# #############################################################################
# Test_tilde_in_inline_code
# #############################################################################


# TODO(ai_gp2): Move this to test_notes_to_pdf.py end-to-end tests.
class Test_tilde_in_inline_code(hunitest.TestCase):
    """
    Test that tilde (~) character is preserved in inline code blocks
    when rendering with typst engine.

    This is a regression test for a bug where tildes in inline code
    (`default ~ credit_limit + credit_score + account_age`) were not
    showing up in the final typst output.
    """

    @pytest.mark.skipif(
        shutil.which("pandoc") is None, reason="pandoc is not installed"
    )
    def test1(self) -> None:
        """
        Test that tilde is preserved in inline code through AST pipeline.
        """
        # Prepare inputs.
        markdown_input = hprint.dedent(
            """
            # Test Tilde

            - _Example_: `default ~ credit_limit + credit_score + account_age`
            """
        )
        # Prepare outputs.
        expected_typst = "`default ~ credit_limit + credit_score + account_age`"
        # Run test: Step 1 - markdown to JSON AST.
        proc1 = subprocess.run(
            ["pandoc", "-f", "markdown", "-t", "json"],
            input=markdown_input,
            capture_output=True,
            text=True,
            check=True,
        )
        ast = json.loads(proc1.stdout)
        # Run test: Step 2 - transform AST (divved fence transformation).
        transformed_ast = dshdtpatt._transform_ast_divved_fence(ast)
        # Run test: Step 3 - JSON AST to typst.
        proc2 = subprocess.run(
            ["pandoc", "-f", "json", "-t", "typst"],
            input=json.dumps(transformed_ast),
            capture_output=True,
            text=True,
            check=True,
        )
        # Check outputs.
        typst_output = proc2.stdout
        self.assertIn(expected_typst, typst_output)

    @pytest.mark.skipif(
        shutil.which("pandoc") is None, reason="pandoc is not installed"
    )
    def test2(self) -> None:
        """
        Test that tilde is preserved with color transformation applied.
        """
        # Prepare inputs.
        markdown_input = hprint.dedent(
            """
            Code with tilde: `a ~ b ~ c`
            """
        )
        # Prepare outputs.
        expected_typst = "`a ~ b ~ c`"
        # Run test: Step 1 - markdown to JSON AST.
        proc1 = subprocess.run(
            ["pandoc", "-f", "markdown", "-t", "json"],
            input=markdown_input,
            capture_output=True,
            text=True,
            check=True,
        )
        ast = json.loads(proc1.stdout)
        # Run test: Step 2 - apply both transformations.
        ast = dshdtpatt._transform_ast_divved_fence(ast)
        ast = dshdtpatt._transform_ast_color_text(ast)
        # Run test: Step 3 - JSON AST to typst.
        proc2 = subprocess.run(
            ["pandoc", "-f", "json", "-t", "typst"],
            input=json.dumps(ast),
            capture_output=True,
            text=True,
            check=True,
        )
        # Check outputs.
        typst_output = proc2.stdout
        self.assertIn(expected_typst, typst_output)

    @pytest.mark.skipif(
        shutil.which("pandoc") is None or shutil.which("typst") is None,
        reason="pandoc or typst is not installed",
    )
    def test3(self) -> None:
        """
        End-to-end test: tilde in inline code compiles successfully with typst.

        Verifies the full pipeline: markdown -> AST -> typst -> PDF with tilde
        preserved (without template to avoid path resolution issues).
        """
        # Prepare inputs.
        markdown_input = hprint.dedent(
            """
            # Slide

            Model: `y ~ x1 + x2 + x3`
            """
        )
        # Prepare inputs: get scratch directory.
        scratch_dir = self.get_scratch_space()
        # Prepare outputs.
        typst_file = os.path.join(scratch_dir, "test.typ")
        pdf_file = os.path.join(scratch_dir, "test.pdf")
        # Run test: Step 1 - markdown to JSON AST.
        proc1 = subprocess.run(
            ["pandoc", "-f", "markdown", "-t", "json"],
            input=markdown_input,
            capture_output=True,
            text=True,
            check=True,
        )
        ast = json.loads(proc1.stdout)
        # Run test: Step 2 - apply transformations.
        ast = dshdtpatt._transform_ast_divved_fence(ast)
        ast = dshdtpatt._transform_ast_color_text(ast)
        # Run test: Step 3 - JSON AST to typst (without template).
        proc2 = subprocess.run(
            ["pandoc", "-f", "json", "-t", "typst"],
            input=json.dumps(ast),
            capture_output=True,
            text=True,
        )
        # Check that pandoc succeeded.
        self.assertEqual(
            proc2.returncode,
            0,
            f"pandoc failed: {proc2.stderr}",
        )
        typst_content = proc2.stdout
        # Run test: Step 4 - verify tilde is in typst content.
        self.assertIn("`y ~ x1 + x2 + x3`", typst_content)
        # Run test: Step 5 - compile typst to PDF.
        hio.to_file(typst_file, typst_content)
        proc3 = subprocess.run(
            ["typst", "compile", typst_file, pdf_file],
            capture_output=True,
            text=True,
        )
        # Check that typst compilation succeeded.
        self.assertEqual(
            proc3.returncode,
            0,
            f"typst compile failed: {proc3.stderr}",
        )
        # Check outputs: verify PDF was created.
        self.assertTrue(
            os.path.exists(pdf_file),
            f"PDF file not created: {pdf_file}",
        )
