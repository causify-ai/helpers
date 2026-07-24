import helpers.hmarkdown as hmarkdo
import helpers.hunit_test as hunitest


# #############################################################################
# Test_process_color_commands1
# #############################################################################


class Test_process_color_commands1(hunitest.TestCase):
    """
    Test `process_color_commands()` with LaTeX output format.
    """

    def helper(self, txt_in: str, expected: str) -> None:
        """
        Test helper for `process_color_commands()`.

        :param txt_in: Input text with color commands
        :param expected: Expected output
        """
        # Run test.
        output_format = "latex"
        actual = hmarkdo.process_color_commands(
            txt_in, output_format=output_format
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test with plain text content.
        """
        # Prepare inputs.
        txt_in = r"\red{Hello world}"
        # Prepare outputs.
        expected = r"\textcolor{red}{\text{Hello world}}"
        # Run test.
        self.helper(txt_in, expected)

    def test2(self) -> None:
        """
        Test color command with mathematical content.
        """
        # Prepare inputs.
        txt_in = r"\blue{x + y = z}"
        # Prepare outputs.
        expected = r"\textcolor{blue}{x + y = z}"
        # Run test.
        self.helper(txt_in, expected)

    def test3(self) -> None:
        """
        Test multiple color commands in the same line.
        """
        # Prepare inputs.
        txt_in = r"The \red{quick} \blue{fox} \green{jumps}"
        # Prepare outputs.
        expected = r"The \textcolor{red}{\text{quick}} \textcolor{blue}{\text{fox}} \textcolor{darkgreen}{\text{jumps}}"
        # Run test.
        self.helper(txt_in, expected)

    def test4(self) -> None:
        """
        Test color commands with both text and math content.
        """
        # Prepare inputs.
        txt_in = r"\red{Result: x^2 + y^2}"
        # Prepare outputs.
        expected = r"\textcolor{red}{Result: x^2 + y^2}"
        # Run test.
        self.helper(txt_in, expected)

    def test5(self) -> None:
        """
        Test color command with nested braces.
        """
        # Prepare inputs.
        txt_in = r"\blue{f(x) = {x + 1}}"
        # Prepare outputs.
        expected = r"\textcolor{blue}{f(x) = {x + 1}}"
        # Run test.
        self.helper(txt_in, expected)


# #############################################################################
# Test_colorize_bullet_points_in_slide1
# #############################################################################


class Test_colorize_bullet_points_in_slide1(hunitest.TestCase):
    """
    Test `colorize_bullet_points_in_slide()` with default output format.
    """

    def helper(self, text: str, expected: str, all_md_colors=None) -> None:
        """
        Test helper for `colorize_bullet_points_in_slide()`.

        :param text: Input markdown text
        :param expected: Expected output
        :param all_md_colors: Optional list of colors to cycle through
        """
        # Run test.
        output_format = "latex"
        if all_md_colors is None:
            actual = hmarkdo.colorize_bullet_points_in_slide(text, output_format)
        else:
            actual = hmarkdo.colorize_bullet_points_in_slide(
                text, output_format, all_md_colors=all_md_colors
            )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test with multiple `@text@` markers and nested bullet structure.
        """
        # Prepare inputs.
        text = r"""
        - @VC Theory@
            - Measures model

        - @Bias-Variance Decomposition@
            - Prediction error
                - @Bias@
                - @Variance@

        - @Computation Complexity@
            - Balances model
            - Related to
            - E.g., Minimum

        - @Bayesian Approach@
            - Treats ML as probability
            - Combines prior knowledge with observed data to update belief about a model

        - @Problem in ML Theory:@
            - Assumptions may not align with practical problems
        """
        all_md_colors = [
            "red",
            "orange",
            "yellow",
            "lime",
            "green",
            "teal",
            "cyan",
            "blue",
            "purple",
            "violet",
            "magenta",
            "pink",
            "brown",
            "olive",
            "gray",
            "darkgray",
            "lightgray",
            "black",
            "white",
        ]
        # Prepare outputs.
        expected = r"""
        - **\red{VC Theory}**
            - Measures model

        - **\orange{Bias-Variance Decomposition}**
            - Prediction error
                - **\yellow{Bias}**
                - **\lime{Variance}**

        - **\green{Computation Complexity}**
            - Balances model
            - Related to
            - E.g., Minimum

        - **\teal{Bayesian Approach}**
            - Treats ML as probability
            - Combines prior knowledge with observed data to update belief about a model

        - **\cyan{Problem in ML Theory:}**
            - Assumptions may not align with practical problems
        """
        # Run test.
        self.helper(text, expected, all_md_colors=all_md_colors)

    def test2(self) -> None:
        """
        Test with Pandoc columns and code blocks.
        """
        # Prepare inputs.
        text = r"""
        * Machine Learning Flow

        ::: columns
        :::: {.column width=90%}
        - Question
        - E.g., "How can we predict house prices?"
        - Input data
        - E.g., historical data of house sales

        - _"If I were given one hour to save the planet, I would spend 59 minutes
        defining the problem and one minute resolving it"_ (Albert Einstein)

        - @Not all phases are equally important!@
        - Question $>$ Data $>$ Features $>$ Algorithm
        - Clarity of the question impacts project success
        - Quality and relevance of data are crucial for performance
        - Proper feature selection simplifies the model and improves accuracy
        - Algorithm is often less important (contrary to popular belief!)
        ::::
        :::: {.column width=5%}

        ```graphviz[height=90%]
        digraph BayesianFlow {
            rankdir=TD;
            splines=true;
            ...
        }
        ```
        ::::
        :::
        """
        # Prepare outputs.
        expected = r"""
        * Machine Learning Flow

        ::: columns
        :::: {.column width=90%}
        - Question
        - E.g., "How can we predict house prices?"
        - Input data
        - E.g., historical data of house sales

        - _"If I were given one hour to save the planet, I would spend 59 minutes
        defining the problem and one minute resolving it"_ (Albert Einstein)

        - **\red{Not all phases are equally important!}**
        - Question $>$ Data $>$ Features $>$ Algorithm
        - Clarity of the question impacts project success
        - Quality and relevance of data are crucial for performance
        - Proper feature selection simplifies the model and improves accuracy
        - Algorithm is often less important (contrary to popular belief!)
        ::::
        :::: {.column width=5%}

        ```graphviz[height=90%]
        digraph BayesianFlow {
            rankdir=TD;
            splines=true;
            ...
        }
        ```
        ::::
        :::
        """
        # Run test.
        self.helper(text, expected)

    def test3(self) -> None:
        """
        Test `@label@` and `**text**` combined on one line: only the `@...@`
        marker is colorized, `**text**` stays plain bold.
        """
        # Prepare inputs.
        text = r"""
        - @Definition@: **Knowledge Representation (KR)** is the study of how to formally
          encode information so that machines can reason with it
        """
        # Prepare outputs.
        expected = r"""
        - **\red{Definition}**: **Knowledge Representation (KR)** is the study of how to formally
          encode information so that machines can reason with it
        """
        # Run test.
        self.helper(text, expected)

    def test4(self) -> None:
        """
        Test that plain `**text**` with no `@...@` marker is left unchanged.
        """
        # Prepare inputs.
        text = r"""
        This has **plain bold** only, no color markers.
        """
        # Prepare outputs.
        expected = text
        # Run test.
        self.helper(text, expected)

    def test5(self) -> None:
        """
        Test that email addresses are not mistaken for `@...@` markers.
        """
        # Prepare inputs.
        text = "Contact **Dr. Saggese** at gsaggese@umd.edu for questions."
        # Prepare outputs: `**Dr. Saggese**` stays plain bold, email untouched.
        expected = text
        # Run test.
        self.helper(text, expected)

    def test6(self) -> None:
        """
        Test that two raw emails on the same non-table line are not merged
        into a single false-positive `@...@` marker.
        """
        # Prepare inputs.
        text = (
            "101: Name: Florian, Home: florian@wobegon.org, Office: fk@phc.com"
        )
        # Prepare outputs: no marker detected, text unchanged.
        expected = text
        # Run test.
        self.helper(text, expected)


# #############################################################################
# Test_process_color_commands2
# #############################################################################


class Test_process_color_commands2(hunitest.TestCase):
    """
    Test `process_color_commands()` with Typst output format.
    """

    def helper(self, txt_in: str, expected: str) -> None:
        """
        Test helper for `process_color_commands()` with Typst format.

        :param txt_in: Input text with color commands
        :param expected: Expected Typst output
        """
        # Run test.
        output_format = "typst"
        actual = hmarkdo.process_color_commands(
            txt_in, output_format=output_format
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test Typst output with plain text content.
        """
        # Prepare inputs.
        txt_in = r"\red{Hello world}"
        # Prepare outputs.
        expected = r'`#text(fill: red, weight: "bold")[Hello world]`{=typst}'
        # Run test.
        self.helper(txt_in, expected)

    def test2(self) -> None:
        """
        Test Typst output with mathematical content.
        """
        # Prepare inputs.
        txt_in = r"\blue{x + y = z}"
        # Prepare outputs.
        expected = r'`#text(fill: blue, weight: "bold")[x + y = z]`{=typst}'
        # Run test.
        self.helper(txt_in, expected)

    def test3(self) -> None:
        """
        Test Typst output with multiple color commands.
        """
        # Prepare inputs.
        txt_in = r"The \red{quick} \blue{fox} \green{jumps}"
        # Prepare outputs.
        expected = r'The `#text(fill: red, weight: "bold")[quick]`{=typst} `#text(fill: blue, weight: "bold")[fox]`{=typst} `#text(fill: green, weight: "bold")[jumps]`{=typst}'
        # Run test.
        self.helper(txt_in, expected)

    def test4(self) -> None:
        """
        Test Typst output with colors that require rgb() definitions.
        """
        # Prepare inputs.
        txt_in = r"\violet{important}"
        # Prepare outputs.
        expected = r'`#text(fill: rgb("#8B00FF"), weight: "bold")[important]`{=typst}'
        # Run test.
        self.helper(txt_in, expected)

    def test5(self) -> None:
        r"""
        Test that bold text in Typst output is wrapped in typst code fence.

        This test verifies the fix for the issue where colored text like
        `\red{Target node}` is not rendered properly in typst because it's
        missing the `{=typst}` fence syntax needed by pandoc.
        """
        # Prepare inputs.
        txt_in = r"- **\red{Target node}**"
        # Prepare outputs - should be wrapped with backticks and {=typst}.
        expected = r'- **`#text(fill: red, weight: "bold")[Target node]`{=typst}**'
        # Run test.
        self.helper(txt_in, expected)

    def test6(self) -> None:
        r"""
        Test color commands inside math mode are converted for typst.

        This test reproduces the bug where color commands like `\blue{...}`
        inside `$$...$$` math blocks are not converted to typst syntax,
        causing them to not render properly.
        """
        # Prepare inputs with color commands inside math mode.
        txt_in = r"$$\Pr(\blue{x_1}, \red{x_2}) = \blue{x_1} \red{x_2}$$"
        # For typst output, color commands inside math should be converted.
        expected = r'$$\Pr(`#text(fill: blue, weight: "bold")[x_1]`{=typst}, `#text(fill: red, weight: "bold")[x_2]`{=typst}) = `#text(fill: blue, weight: "bold")[x_1]`{=typst} `#text(fill: red, weight: "bold")[x_2]`{=typst}$$'
        # Run test.
        self.helper(txt_in, expected)

    def test7(self) -> None:
        r"""
        Test that colors work inside inline math mode too.

        This test verifies color commands work in inline math ($...$) delimiters.
        """
        # Prepare inputs with color in inline math
        txt_in = r"Solve $\blue{a + b} = \red{c}$ using the method."
        # For typst output, color commands should be converted even in inline math
        expected = r'Solve $`#text(fill: blue, weight: "bold")[a + b]`{=typst} = `#text(fill: red, weight: "bold")[c]`{=typst}$ using the method.'
        # Run test.
        self.helper(txt_in, expected)


# #############################################################################
# Test_colorize_bullet_points_in_slide2
# #############################################################################


class Test_colorize_bullet_points_in_slide2(hunitest.TestCase):
    """
    Test `colorize_bullet_points_in_slide()` with Typst output format.
    """

    def helper(
        self,
        text: str,
        expected: str,
        use_abbreviations: bool = False,
        all_md_colors=None,
    ) -> None:
        """
        Test helper for `colorize_bullet_points_in_slide()` with Typst.

        :param text: Input markdown text
        :param expected: Expected output
        :param use_abbreviations: Whether to use abbreviated syntax
        :param all_md_colors: Optional list of colors to cycle through
        """
        # Run test.
        output_format = "typst"
        if all_md_colors is None:
            actual = hmarkdo.colorize_bullet_points_in_slide(
                text,
                output_format,
                use_abbreviations=use_abbreviations,
            )
        else:
            actual = hmarkdo.colorize_bullet_points_in_slide(
                text,
                output_format,
                use_abbreviations=use_abbreviations,
                all_md_colors=all_md_colors,
            )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test Typst output with full syntax (use_abbreviations=False).
        """
        # Prepare inputs.
        text = r"""
        - @Item One@
        - @Item Two@
        - @Item Three@
        """
        use_abbreviations = False
        # Prepare outputs.
        expected = r"""
        - `#text(fill: red, weight: "bold")[Item One]`{=typst}
        - `#text(fill: green, weight: "bold")[Item Two]`{=typst}
        - `#text(fill: blue, weight: "bold")[Item Three]`{=typst}
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test2(self) -> None:
        """
        Test Typst output with abbreviated syntax (use_abbreviations=True).
        """
        # Prepare inputs.
        text = r"""
        - @Item One@
        - @Item Two@
        """
        use_abbreviations = True
        # Prepare outputs.
        expected = r"""
        - `#text(fill: red, weight: "bold")[Item One]`{=typst}
        - `#text(fill: blue, weight: "bold")[Item Two]`{=typst}
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test3(self) -> None:
        """
        Test Typst output with a single `@...@` marker.
        """
        # Prepare inputs.
        text = r"""
        Some text with @one bold item@ and more text.
        """
        use_abbreviations = False
        # Prepare outputs.
        expected = r"""
        Some text with `#text(fill: red, weight: "bold")[one bold item]`{=typst} and more text.
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test4(self) -> None:
        """
        Test that Typst output preserves code blocks (markers inside are not
        colorized).
        """
        # Prepare inputs.
        text = r"""
        - @First@

        ```python
        # @not_a_marker@ = True
        ```

        - @Second@
        """
        use_abbreviations = False
        # Prepare outputs.
        expected = r"""
        - `#text(fill: red, weight: "bold")[First]`{=typst}

        ```python
        # @not_a_marker@ = True
        ```

        - `#text(fill: blue, weight: "bold")[Second]`{=typst}
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test5(self) -> None:
        """
        Test Typst output cycling through color list for 5+ items.
        """
        # Prepare inputs.
        text = r"""
        - @One@
        - @Two@
        - @Three@
        - @Four@
        - @Five@
        """
        use_abbreviations = False
        all_md_colors = [
            "red",
            "orange",
            "yellow",
            "lime",
            "green",
            "teal",
            "cyan",
            "blue",
        ]
        # Prepare outputs.
        expected = r"""
        - `#text(fill: red, weight: "bold")[One]`{=typst}
        - `#text(fill: orange, weight: "bold")[Two]`{=typst}
        - `#text(fill: yellow, weight: "bold")[Three]`{=typst}
        - `#text(fill: rgb("#00FF00"), weight: "bold")[Four]`{=typst}
        - `#text(fill: green, weight: "bold")[Five]`{=typst}
        """
        # Run test.
        self.helper(
            text,
            expected,
            use_abbreviations=use_abbreviations,
            all_md_colors=all_md_colors,
        )


# #############################################################################
# Test_bold_text_colorization_e2e
# #############################################################################


# TODO(ai_gp): Factor out a helper. Use expected string.
class Test_bold_text_colorization_e2e(hunitest.TestCase):
    """
    End-to-end tests for bold text colorization in slides with Typst output.

    Verifies the complete workflow: markdown bold text -> colorization ->
    valid Typst syntax with colors and weight applied.
    """

    def test_bold_text_colorization_typst_abbreviated(self) -> None:
        """
        Test abbreviated syntax produces valid Typst with color and weight.
        """
        text = "- @Definition@: Knowledge Representation"
        output_format = "typst"
        result = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=True
        )
        expected = '- `#text(fill: red, weight: "bold")[Definition]`{=typst}: Knowledge Representation'
        self.assert_equal(result, expected)

    def test_bold_text_colorization_typst_full(self) -> None:
        """
        Test full syntax produces valid Typst with color and weight.
        """
        text = "- @Definition@: Knowledge Representation"
        output_format = "typst"
        result = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=False
        )
        expected = '- `#text(fill: red, weight: "bold")[Definition]`{=typst}: Knowledge Representation'
        self.assert_equal(result, expected)

    def test_multiple_bold_items_different_colors(self) -> None:
        """
        Test multiple `@...@` markers get different colors.
        """
        text = r"""
        - @Definition@: First item
        - @Fact@: Second item
        - @Example@: Third item
        """
        output_format = "typst"
        result = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=False
        )
        # Verify each bold item has a different color.
        self.assertIn("fill: red", result)
        self.assertIn("fill: green", result)
        self.assertIn("fill: blue", result)
        # Verify all have weight: "bold".
        self.assertEqual(result.count('weight: "bold"'), 3)

    def test_bold_text_with_special_characters(self) -> None:
        """
        Test marker text containing special characters is properly colorized.
        """
        text = "- @Key insight@: Use `_` for emphasis"
        output_format = "typst"
        result = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=False
        )
        # Verify the bold part is colorized with proper syntax.
        self.assertIn(
            '`#text(fill: red, weight: "bold")[Key insight]`{=typst}', result
        )

    def test_bold_and_italic_combined(self) -> None:
        """
        Test marker and italic text formatting together.
        """
        text = "- @Definition@: _Knowledge Representation_ is important"
        output_format = "typst"
        result = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=False
        )
        # Verify marker is colorized, italic remains.
        self.assertIn(
            '`#text(fill: red, weight: "bold")[Definition]`{=typst}', result
        )
        self.assertIn("_Knowledge Representation_", result)

    def test_no_bold_text_unchanged(self) -> None:
        """
        Test that lines without `@...@` markers are unchanged.
        """
        text = "- Just regular text without markers"
        output_format = "typst"
        result = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=False
        )
        self.assert_equal(result, text)

    def test_abbreviated_vs_full_syntax_equivalence(self) -> None:
        """
        Test that abbreviated and full syntax produce equivalent Typst output.
        """
        text = "- @Item@: Description"
        output_format = "typst"
        abbreviated = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=True
        )
        full = hmarkdo.colorize_bullet_points_in_slide(
            text, output_format, use_abbreviations=False
        )
        # Both should produce the same Typst syntax.
        self.assert_equal(abbreviated, full)

    def test_rgb_color_values_in_typst(self) -> None:
        """
        Test that colors requiring rgb() values are properly formatted.
        """
        text = "- @Item1@: Test\n- @Item2@: Test\n- @Item3@: Test\n- @Item4@: Test\n- @Item5@: Test"
        output_format = "typst"
        all_md_colors = ["red", "orange", "violet", "magenta", "pink"]
        result = hmarkdo.colorize_bullet_points_in_slide(
            text,
            output_format,
            use_abbreviations=False,
            all_md_colors=all_md_colors,
        )
        # Verify rgb() colors are present (for items where rgb is needed).
        self.assertIn('rgb("#8B00FF")', result)  # violet
        self.assertIn('rgb("#FF00FF")', result)  # magenta
