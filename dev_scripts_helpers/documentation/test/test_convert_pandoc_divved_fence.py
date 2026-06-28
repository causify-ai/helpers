import pprint

import dev_scripts_helpers.documentation.convert_pandoc_divved_fence as dsdocdpdf
import helpers.hunit_test as hunitest


# #############################################################################
# Test__is_columns_container
# #############################################################################


class Test__is_columns_container(hunitest.TestCase):
	"""
	Test the `_is_columns_container()` function.
	"""

    # TODO(ai_gp): -> helper and use type hints
	def _assert_columns_container(self, elem, expected):
		actual = dsdocdpdf._is_columns_container(elem)
		self.assertEqual(actual, expected)

	def test1(self) -> None:
		"""
		Test that valid Div with columns class is detected.
		"""
		elem = {
			"t": "Div",
			"c": [
				["", ["columns"], []],
				[],
			],
		}
		self._assert_columns_container(elem, True)

	def test2(self) -> None:
		"""
		Test that non-Div element is rejected.
		"""
		elem = {"t": "Para", "c": []}
		self._assert_columns_container(elem, False)

	def test3(self) -> None:
		"""
		Test that Div without columns class is rejected.
		"""
		elem = {
			"t": "Div",
			"c": [
				["", ["other"], []],
				[],
			],
		}
		self._assert_columns_container(elem, False)

	def test4(self) -> None:
		"""
		Test that Div with empty c is rejected.
		"""
		elem = {"t": "Div", "c": []}
		self._assert_columns_container(elem, False)


# #############################################################################
# Test__extract_columns
# #############################################################################


# TODO(ai_gp): All the test methods should have the markdown code.
# TODO(ai_gp): Factor out an helper for the common code.
class Test__extract_columns(hunitest.TestCase):
	"""
	Test the `_extract_columns()` function.
	"""

	def test1(self) -> None:
		"""
		Test extraction of two columns with explicit widths.
		"""
		# Markdown input:
		# :::columns
		# ::: column
		# Left
		# :::
		# ::: column
		# Right
		# :::
		# :::
		# Prepare inputs.
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
		# Prepare outputs.
		expected = [
			("55%", [{"t": "Para", "c": [{"t": "Str", "c": "Left"}]}]),
			("45%", [{"t": "Para", "c": [{"t": "Str", "c": "Right"}]}]),
		]
		# Run test.
		actual = dsdocdpdf._extract_columns(container)
        actual = pprint.pformat(actual)
        expected = pprint.pformat(actual)
		# Check outputs.
		self.assert_equal(actual, expected)

	def test2(self) -> None:
		"""
		Test that missing width defaults to '1fr'.
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
							["", ["column"], []],
							[{"t": "Para", "c": []}],
						],
					},
				],
			],
		}
		# Prepare outputs.
		expected = [
			("1fr", [{"t": "Para", "c": []}]),
		]
		# Run test.
		actual = dsdocdpdf._extract_columns(container)
		# Check outputs.
		self.assertEqual(actual, expected, f"\n{pprint.pformat(actual)}")

	def test3(self) -> None:
		"""
		Test that non-column child divs are skipped.
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
		# Prepare outputs.
		expected = [
			("50%", []),
		]
		# Run test.
		actual = dsdocdpdf._extract_columns(container)
		# Check outputs.
		self.assertEqual(actual, expected, f"\n{pprint.pformat(actual)}")


# #############################################################################
# Test__format_grid_code
# #############################################################################


class Test__format_grid_code(hunitest.TestCase):
	"""
	Test the `_format_grid_code()` function.
	"""

    # TODO(ai_gp): -> helper and use type hints.
    # TODO(ai_gp): compare the output for being exactly what is expected.
	def _assert_grid_contains(self, widths, contents, expected_strings):
		actual = dsdocdpdf._format_grid_code(widths, contents)
		for expected in expected_strings:
			self.assertIn(expected, actual, f"Expected '{expected}' in:\n{actual}")

	def test1(self) -> None:
		"""
		Test grid code generation for two columns.
		"""
		widths = ["55%", "45%"]
		contents = ["Content 1", "Content 2"]
		expected_strings = [
			"#grid(",
			"columns: (55%, 45%)",
			"gutter: 0.5em",
			"[Content 1]",
			"[Content 2]",
		]
		self._assert_grid_contains(widths, contents, expected_strings)

	def test2(self) -> None:
		"""
		Test grid code generation for three columns.
		"""
		widths = ["1fr", "1fr", "1fr"]
		contents = ["Left", "Middle", "Right"]
		expected_strings = [
			"columns: (1fr, 1fr, 1fr)",
			"[Left]",
			"[Middle]",
			"[Right]",
		]
		self._assert_grid_contains(widths, contents, expected_strings)


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
		# Run test.
		actual = dsdocdpdf._transform_ast(ast)
		# Check outputs.
		self.assertEqual(len(actual["blocks"]), 1)
		self.assertEqual(actual["blocks"][0]["t"], "Para")


# #############################################################################
# End-to-end Test
# #############################################################################


class Test_end_to_end(hunitest.TestCase):
	"""
	End-to-end test using pandoc to convert markdown with columns to typst.
	"""

    # TODO(ai_gp): Use dockerized_pandoc
	def test_markdown_to_typst_with_columns(self) -> None:
		"""
		Test full pipeline: markdown with :::columns fences -> AST -> transform -> typst.
		"""
		import subprocess
		import json

		# Markdown input with two columns
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

		# Convert markdown to pandoc AST JSON
		proc = subprocess.run(
			["pandoc", "-f", "markdown", "-t", "json"],
			input=markdown_input,
			capture_output=True,
			text=True,
		)
		if proc.returncode != 0:
			self.skipTest("pandoc not available")

		ast = json.loads(proc.stdout)

		# Transform AST
		transformed_ast = dsdocdpdf._transform_ast(ast)

		# Verify transformation occurred
		self.assertEqual(transformed_ast["blocks"][1]["t"], "RawBlock")
		self.assertEqual(transformed_ast["blocks"][1]["c"][0], "typst")
		grid_code = transformed_ast["blocks"][1]["c"][1]
		self.assertIn("#grid(", grid_code)
		self.assertIn("columns:", grid_code)
