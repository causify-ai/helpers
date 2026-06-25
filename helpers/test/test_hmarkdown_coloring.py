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
        actual = hmarkdo.process_color_commands(txt_in, output_format=output_format)
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
            actual = hmarkdo.colorize_bullet_points_in_slide(
                text, output_format
            )
        else:
            actual = hmarkdo.colorize_bullet_points_in_slide(
                text, output_format, all_md_colors=all_md_colors
            )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test with multiple bold items and nested bullet structure.
        """
        # Prepare inputs.
        text = r"""
        - **VC Theory**
            - Measures model

        - **Bias-Variance Decomposition**
            - Prediction error
                - **Bias**
                - **Variance**

        - **Computation Complexity**
            - Balances model
            - Related to
            - E.g., Minimum

        - **Bayesian Approach**
            - Treats ML as probability
            - Combines prior knowledge with observed data to update belief about a model

        - **Problem in ML Theory:**
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

        - **Not all phases are equally important!**
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


# #############################################################################
# Test_process_color_commands2 (Typst)
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
        actual = hmarkdo.process_color_commands(txt_in, output_format=output_format)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test Typst output with plain text content.
        """
        # Prepare inputs.
        txt_in = r"\red{Hello world}"
        # Prepare outputs.
        expected = r"#text(fill: red, Hello world)"
        # Run test.
        self.helper(txt_in, expected)

    def test2(self) -> None:
        """
        Test Typst output with mathematical content.
        """
        # Prepare inputs.
        txt_in = r"\blue{x + y = z}"
        # Prepare outputs.
        expected = r"#text(fill: blue, x + y = z)"
        # Run test.
        self.helper(txt_in, expected)

    def test3(self) -> None:
        """
        Test Typst output with multiple color commands.
        """
        # Prepare inputs.
        txt_in = r"The \red{quick} \blue{fox} \green{jumps}"
        # Prepare outputs.
        expected = r"The #text(fill: red, quick) #text(fill: blue, fox) #text(fill: green, jumps)"
        # Run test.
        self.helper(txt_in, expected)

    def test4(self) -> None:
        """
        Test Typst output with colors that require rgb() definitions.
        """
        # Prepare inputs.
        txt_in = r"\violet{important}"
        # Prepare outputs.
        expected = r'#text(fill: rgb("#8B00FF"), important)'
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
        - **Item One**
        - **Item Two**
        - **Item Three**
        """
        use_abbreviations = False
        # Prepare outputs.
        expected = r"""
        - **#text(fill: red, Item One)**
        - **#text(fill: green, Item Two)**
        - **#text(fill: blue, Item Three)**
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test2(self) -> None:
        """
        Test Typst output with abbreviated syntax (use_abbreviations=True).
        """
        # Prepare inputs.
        text = r"""
        - **Item One**
        - **Item Two**
        """
        use_abbreviations = True
        # Prepare outputs.
        expected = r"""
        - **#red[Item One]**
        - **#blue[Item Two]**
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test3(self) -> None:
        """
        Test Typst output with single bold item.
        """
        # Prepare inputs.
        text = r"""
        Some text with **one bold item** and more text.
        """
        use_abbreviations = False
        # Prepare outputs.
        expected = r"""
        Some text with **#text(fill: red, one bold item)** and more text.
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test4(self) -> None:
        """
        Test that Typst output preserves code blocks.
        """
        # Prepare inputs.
        text = r"""
        - **First**

        ```python
        **not_bold** = True
        ```

        - **Second**
        """
        use_abbreviations = False
        # Prepare outputs.
        expected = r"""
        - **#text(fill: red, First)**

        ```python
        **not_bold** = True
        ```

        - **#text(fill: blue, Second)**
        """
        # Run test.
        self.helper(text, expected, use_abbreviations=use_abbreviations)

    def test5(self) -> None:
        """
        Test Typst output cycling through color list for 5+ items.
        """
        # Prepare inputs.
        text = r"""
        - **One**
        - **Two**
        - **Three**
        - **Four**
        - **Five**
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
        - **#text(fill: red, One)**
        - **#text(fill: orange, Two)**
        - **#text(fill: yellow, Three)**
        - **#text(fill: rgb("#00FF00"), Four)**
        - **#text(fill: green, Five)**
        """
        # Run test.
        self.helper(
            text,
            expected,
            use_abbreviations=use_abbreviations,
            all_md_colors=all_md_colors,
        )
