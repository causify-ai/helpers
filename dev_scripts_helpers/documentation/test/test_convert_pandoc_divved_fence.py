import json
import os
from typing import Any, List, Tuple

import dev_scripts_helpers.documentation.convert_pandoc_divved_fence as dshdcpdfe
import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


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
            "  [Content 1], [Content 2]\n"
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
            "  [Left], [Middle], [Right]\n"
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

    def helper(self, elem: Any, expected: str) -> None:
        """
        Test helper for _transform_elem.

        :param elem: AST element to transform
        :param expected: Expected JSON string of transformed element
        """
        api_version = [1, 23, 1]
        actual = dshdcpdfe._transform_elem(elem, api_version)
        actual_str = json.dumps(actual, indent=2)
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
			    "#grid(\n  columns: (50%, 50%),\n  gutter: 0.5em,\n  [col1], [col2]\n)"
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
			          "#grid(\n  columns: (50%, 50%),\n  gutter: 0.5em,\n  [nested], [col]\n)"
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


# #############################################################################
# Test__transform_ast
# #############################################################################


class Test__transform_ast(hunitest.TestCase):
    """
    Test the `_transform_ast()` function.
    """

    def helper(self, ast: Any, expected: str) -> None:
        """
        Test helper for _transform_ast.

        :param ast: Full pandoc AST dict
        :param expected: Expected JSON string of transformed AST
        """
        actual = dshdcpdfe._transform_ast(ast)
        actual_str = json.dumps(actual, indent=2)
        self.assert_equal(actual_str, expected)

    def test1(self) -> None:
        """
        Test full AST transformation with one columns Div.

        Markdown input:
        ```markdown
        # Title

        :::columns
        ::: column {width="50%"}
        left
        :::
        ::: column {width="50%"}
        right
        :::
        :::
        ```
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [
                {
                    "t": "Header",
                    "c": [1, ["title", [], []], [{"t": "Str", "c": "Title"}]],
                },
                {
                    "t": "Div",
                    "c": [
                        ["", ["columns"], []],
                        [
                            {
                                "t": "Div",
                                "c": [
                                    ["", ["column"], [["width", "50%"]]],
                                    [{"t": "RawBlock", "c": ["typst", "left"]}],
                                ],
                            },
                            {
                                "t": "Div",
                                "c": [
                                    ["", ["column"], [["width", "50%"]]],
                                    [{"t": "RawBlock", "c": ["typst", "right"]}],
                                ],
                            },
                        ],
                    ],
                },
            ],
        }
        # Prepare outputs.
        expected = hprint.dedent(
            r"""
			{
			  "pandoc-api-version": [
			    1,
			    23,
			    1
			  ],
			  "meta": {},
			  "blocks": [
			    {
			      "t": "Header",
			      "c": [
			        1,
			        [
			          "title",
			          [],
			          []
			        ],
			        [
			          {
			            "t": "Str",
			            "c": "Title"
			          }
			        ]
			      ]
			    },
			    {
			      "t": "RawBlock",
			      "c": [
			        "typst",
			        "#grid(\n  columns: (50%, 50%),\n  gutter: 0.5em,\n  [left], [right]\n)"
			      ]
			    }
			  ]
			}
			"""
        )
        # Run test.
        self.helper(ast, expected)

    def test2(self) -> None:
        """
        Test AST with no columns remains unchanged.

        Markdown input:
        ```markdown
        text
        ```
        """
        # Prepare inputs.
        ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [{"t": "Para", "c": [{"t": "Str", "c": "text"}]}],
        }
        # Prepare outputs.
        expected = hprint.dedent(
            """
			{
			  "pandoc-api-version": [
			    1,
			    23,
			    1
			  ],
			  "meta": {},
			  "blocks": [
			    {
			      "t": "Para",
			      "c": [
			        {
			          "t": "Str",
			          "c": "text"
			        }
			      ]
			    }
			  ]
			}
			"""
        )
        # Run test.
        self.helper(ast, expected)


# #############################################################################
# Test_end_to_end
# #############################################################################


class Test_end_to_end(hunitest.TestCase):
    """
    End-to-end test using pandoc to convert markdown with columns to typst.
    """

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
        #
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(in_file, markdown_input)
        #
        ast_file = os.path.join(scratch_dir, "ast.json")
        cmd = f"pandoc {in_file} -f markdown -t json -o {ast_file}"
        dshdlipa.run_dockerized_pandoc(cmd, "pandoc_only")
        #
        ast = json.loads(hio.from_file(ast_file))
        actual_ast = dshdcpdfe._transform_ast(ast)
        actual_str = json.dumps(actual_ast, indent=2)
        expected = hprint.dedent(
            r"""
			{
			  "pandoc-api-version": [
			    1,
			    23,
			    1
			  ],
			  "meta": {},
			  "blocks": [
			    {
			      "t": "Header",
			      "c": [
			        1,
			        [
			          "title",
			          [],
			          []
			        ],
			        [
			          {
			            "t": "Str",
			            "c": "Title"
			          }
			        ]
			      ]
			    },
			    {
			      "t": "RawBlock",
			      "c": [
			        "typst",
			        "#grid(\n  columns: (1fr, 1fr),\n  gutter: 0.5em,\n  [Left content], [Right content]\n)"
			      ]
			    }
			  ]
			}
			"""
        )
        self.assert_equal(actual_str, expected)
