import json
import subprocess
from typing import Any, List, Tuple

import dev_scripts_helpers.documentation.convert_pandoc_divved_fence as dsdocdpdf
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
		actual = dsdocdpdf._is_columns_container(elem)
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

	def helper(
		self, container: Any, expected: List[Tuple[str, Any]]
	) -> None:
		"""
		Test helper for _extract_columns.

		:param container: Columns container element
		:param expected: Expected result
		"""
		actual = dsdocdpdf._extract_columns(container)
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
		actual = dsdocdpdf._format_grid_code(widths, contents)
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

	def test1(self) -> None:
		"""
		Test that columns container is transformed to RawBlock.
		"""
		# Prepare inputs.
		container = {
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
		api_version = [1, 23, 1]
		# Run test.
		actual = dsdocdpdf._transform_elem(container, api_version)
		# Check outputs.
		self.assertEqual(actual["t"], "RawBlock")
		self.assertEqual(actual["c"][0], "typst")
		self.assertIn("#grid(", actual["c"][1])

	def test2(self) -> None:
		"""
		Test that non-columns Div children are recursively transformed.
		"""
		# Prepare inputs.
		div = {
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
										[{"t": "RawBlock", "c": ["typst", "nested"]}],
									],
								},
								{
									"t": "Div",
									"c": [
										["", ["column"], [["width", "50%"]]],
										[{"t": "RawBlock", "c": ["typst", "col"]}],
									],
								},
							],
						],
					}
				],
			],
		}
		api_version = [1, 23, 1]
		# Run test.
		actual = dsdocdpdf._transform_elem(div, api_version)
		# Check outputs.
		self.assertEqual(actual["t"], "Div")
		inner = actual["c"][1][0]
		self.assertEqual(inner["t"], "RawBlock")
		self.assertIn("#grid(", inner["c"][1])

	def test3(self) -> None:
		"""
		Test that Para elements are unchanged.
		"""
		# Prepare inputs.
		para = {"t": "Para", "c": [{"t": "Str", "c": "text"}]}
		api_version = [1, 23, 1]
		# Run test.
		actual = dsdocdpdf._transform_elem(para, api_version)
		# Check outputs.
		self.assertEqual(actual["t"], "Para")


# #############################################################################
# Test__transform_ast
# #############################################################################


class Test__transform_ast(hunitest.TestCase):
	"""
	Test the `_transform_ast()` function.
	"""

	def test1(self) -> None:
		"""
		Test full AST transformation with one columns Div.
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
		# Run test.
		actual = dsdocdpdf._transform_ast(ast)
		# Check outputs.
		self.assertEqual(len(actual["blocks"]), 2)
		self.assertEqual(actual["blocks"][0]["t"], "Header")
		self.assertEqual(actual["blocks"][1]["t"], "RawBlock")
		self.assertIn("#grid(", actual["blocks"][1]["c"][1])

	def test2(self) -> None:
		"""
		Test AST with no columns remains unchanged.
		"""
		# Prepare inputs.
		ast = {
			"pandoc-api-version": [1, 23, 1],
			"meta": {},
			"blocks": [{"t": "Para", "c": [{"t": "Str", "c": "text"}]}],
		}
		# Prepare outputs.
		expected_block_count = 1
		expected_block_type = "Para"
		# Run test.
		actual = dsdocdpdf._transform_ast(ast)
		# Check outputs.
		self.assertEqual(len(actual["blocks"]), expected_block_count)
		self.assertEqual(actual["blocks"][0]["t"], expected_block_type)


# #############################################################################
# End-to-end Test
# #############################################################################


class Test_end_to_end(hunitest.TestCase):
	"""
	End-to-end test using pandoc to convert markdown with columns to typst.
	"""

	def test1(self) -> None:
		"""
		Test full pipeline: markdown with :::columns -> AST -> transform -> typst.
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
		proc = subprocess.run(
			["pandoc", "-f", "markdown", "-t", "json"],
			input=markdown_input,
			capture_output=True,
			text=True,
		)
		if proc.returncode != 0:
			self.skipTest("pandoc not available")

		ast = json.loads(proc.stdout)
		actual_ast = dsdocdpdf._transform_ast(ast)

		self.assertEqual(len(actual_ast["blocks"]), 2)
		self.assertEqual(actual_ast["blocks"][0]["t"], "Header")
		self.assertEqual(actual_ast["blocks"][1]["t"], "RawBlock")
		self.assertEqual(actual_ast["blocks"][1]["c"][0], "typst")
		self.assertIn("#grid(", actual_ast["blocks"][1]["c"][1])
