import os
from typing import Any, Dict, List, Tuple

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

    def helper(self, container: Any, expected: List[Tuple[str, Any]]) -> None:
        """
        Test helper for _extract_columns.

        :param container: Columns container element
        :param expected: Expected result
        """
        actual = dshdcpdfe._extract_columns(container)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test extraction of two columns with explicit widths.

        Markdown input:
        ```
        :::columns
        ::: column
        Left
        :::
        ::: column
        Right
        :::
        :::
        ```
        """
        container = {
            "t": "Div",
            "c": [
                ["", ["columns"], []],
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["column"], [["width", "55%"]]],
                            [{"t": "Para", "c": [{"t": "Str", "c": "Left"}]}],
                        ],
                    },
                    {
                        "t": "Div",
                        "c": [
                            ["", ["column"], [["width", "45%"]]],
                            [{"t": "Para", "c": [{"t": "Str", "c": "Right"}]}],
                        ],
                    },
                ],
            ],
        }
        expected = [
            ("55%", [{"t": "Para", "c": [{"t": "Str", "c": "Left"}]}]),
            ("45%", [{"t": "Para", "c": [{"t": "Str", "c": "Right"}]}]),
        ]
        self.helper(container, expected)

    def test2(self) -> None:
        """
        Test that missing width defaults to '1fr'.

        Markdown input:
        ```
        :::columns
        ::: column
        Default width
        :::
        :::
        ```
        """
        container = {
            "t": "Div",
            "c": [
                ["", ["columns"], []],
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["column"], []],
                            [{"t": "Para", "c": []}],
                        ],
                    },
                ],
            ],
        }
        expected = [
            ("1fr", [{"t": "Para", "c": []}]),
        ]
        self.helper(container, expected)

    def test3(self) -> None:
        """
        Test that non-column child divs are skipped.

        Markdown input:
        ```
        :::columns
        ::: other
        Ignored
        :::
        ::: column
        Included
        :::
        :::
        ```
        """
        container = {
            "t": "Div",
            "c": [
                ["", ["columns"], []],
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["other"], []],
                            [],
                        ],
                    },
                    {
                        "t": "Div",
                        "c": [
                            ["", ["column"], [["width", "50%"]]],
                            [],
                        ],
                    },
                ],
            ],
        }
        expected = [
            ("50%", []),
        ]
        self.helper(container, expected)


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
        self.assertEqual(actual, expected)

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
        expected = (
            "#grid(\n"
            "  columns: (55%, 45%),\n"
            "  gutter: 0.5em,\n"
            "  [\n"
            "  Content 1\n"
            "  ],\n"
            "  [\n"
            "  Content 2\n"
            "  ]\n"
            ")"
        )
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
        expected = (
            "#grid(\n"
            "  columns: (1fr, 1fr, 1fr),\n"
            "  gutter: 0.5em,\n"
            "  [\n"
            "  Left\n"
            "  ],\n"
            "  [\n"
            "  Middle\n"
            "  ],\n"
            "  [\n"
            "  Right\n"
            "  ]\n"
            ")"
        )
        self.helper(widths, contents, expected)


# #############################################################################
# Test__transform_elem
# #############################################################################


class Test__transform_elem(hunitest.TestCase):
    """
    Test the `_transform_elem()` function.
    """

    # TODO(ai_gp): Make this helper similar to Test_end_to_end.helper
    # where the callers pass a markdown_input, which gets converted into
    # an ast, the ast transformed by dshdcpdfe._transform_elem, and then the content of outcome
    # is compared to the expected value using outcome_to_str and self.check_string
    def helper(self, elem: Any, expected: str) -> None:
        """
        Test helper for _transform_elem.

        :param elem: AST element to transform
        :param expected: Expected JSON string of transformed element
        """
        api_version = [1, 23, 1]
        actual = dshdcpdfe._transform_elem(elem, api_version)
        actual_str = dshdcpdfe.ast_to_str(actual)
        self.assert_equal(actual_str, expected)

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
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [
                ["", ["columns"], []],
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["column"], [["width", "50%"]]],
                            [{"t": "RawBlock", "c": ["typst", "col1"]}],
                        ],
                    },
                    {
                        "t": "Div",
                        "c": [
                            ["", ["column"], [["width", "50%"]]],
                            [{"t": "RawBlock", "c": ["typst", "col2"]}],
                        ],
                    },
                ],
            ],
        }
        # Prepare outputs.
        expected = hprint.dedent(
            r"""
			{
			  "t": "RawBlock",
			  "c": [
			    "typst",
			    "#grid(\n  columns: (50%, 50%),\n  gutter: 0.5em,\n  [\n  col1\n  ],\n  [\n  col2\n  ]\n)"
			  ]
			}
			"""
        )
        # Run test.
        self.helper(elem, expected)

    def test2(self) -> None:
        """
        Test that non-columns Div children are recursively transformed.

        Markdown input:
        ```markdown
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
        ```
        """
        # Prepare inputs.
        elem = {
            "t": "Div",
            "c": [
                ["id1", [], []],
                [
                    {
                        "t": "Div",
                        "c": [
                            ["", ["columns"], []],
                            [
                                {
                                    "t": "Div",
                                    "c": [
                                        ["", ["column"], [["width", "50%"]]],
                                        [
                                            {
                                                "t": "RawBlock",
                                                "c": ["typst", "nested"],
                                            }
                                        ],
                                    ],
                                },
                                {
                                    "t": "Div",
                                    "c": [
                                        ["", ["column"], [["width", "50%"]]],
                                        [
                                            {
                                                "t": "RawBlock",
                                                "c": ["typst", "col"],
                                            }
                                        ],
                                    ],
                                },
                            ],
                        ],
                    }
                ],
            ],
        }
        # Prepare outputs.
        expected = hprint.dedent(
            r"""
			{
			  "t": "Div",
			  "c": [
			    [
			      "id1",
			      [],
			      []
			    ],
			    [
			      {
			        "t": "RawBlock",
			        "c": [
			          "typst",
			          "#grid(\n  columns: (50%, 50%),\n  gutter: 0.5em,\n  [\n  nested\n  ],\n  [\n  col\n  ]\n)"
			        ]
			      }
			    ]
			  ]
			}
			"""
        )
        # Run test.
        self.helper(elem, expected)

    def test3(self) -> None:
        """
        Test that Para elements pass through unchanged.

        Markdown input:
        ```markdown
        text
        ```
        """
        # Prepare inputs.
        elem = {"t": "Para", "c": [{"t": "Str", "c": "text"}]}
        # Prepare outputs.
        expected = hprint.dedent(
            """
			{
			  "t": "Para",
			  "c": [
			    {
			      "t": "Str",
			      "c": "text"
			    }
			  ]
			}
			"""
        )
        # Run test.
        self.helper(elem, expected)

    def test4(self) -> None:
        """
        Test that BulletList items containing nested divs are transformed.

        Verifies that _transform_elem recursively processes items in a
        BulletList, transforming any Divs containing columns within the items.

        Markdown input:
        ```markdown
        - Item 1
        - Item 2:
          :::columns
          ::: column
          content
          :::
          :::
        ```
        """
        # Prepare inputs: BulletList with a nested columns Div in second item
        elem = {
            "t": "BulletList",
            "c": [
                [
                    {"t": "Para", "c": [{"t": "Str", "c": "Item 1"}]}
                ],
                [
                    {"t": "Para", "c": [{"t": "Str", "c": "Item 2:"}]},
                    {
                        "t": "Div",
                        "c": [
                            ["", ["columns"], []],
                            [
                                {
                                    "t": "Div",
                                    "c": [
                                        ["", ["column"], [["width", "50%"]]],
                                        [{"t": "Para", "c": [{"t": "Str", "c": "content"}]}],
                                    ],
                                }
                            ],
                        ],
                    },
                ],
            ],
        }
        result = self.helper(elem)


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
        self.helper(markdown_input)

    def test2(self) -> None:
        """
        Test AST with no columns remains unchanged.
        """
        markdown_input = """
		text
		"""
        self.helper(markdown_input)


# #############################################################################
# Test_end_to_end
# #############################################################################


class Test_end_to_end(hunitest.TestCase):
    """
    End-to-end test using pandoc to convert markdown with columns to typst.
    """

    def helper(
        self, markdown_input: str
    ) -> None:
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
        markdown_input = r"""
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
        self.helper(markdown_input)
