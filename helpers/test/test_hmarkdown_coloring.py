import helpers.hmarkdown as hmarkdo
import helpers.hunit_test as hunitest


# #############################################################################
# Test_process_color_commands1
# #############################################################################


class Test_process_color_commands1(hunitest.TestCase):
    def test_text_content1(self) -> None:
        """
        Test with plain text content.
        """
        txt_in = r"\red{Hello world}"
        expected = r"\textcolor{red}{\text{Hello world}}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_math_content1(self) -> None:
        """
        Test color command with mathematical content.
        """
        txt_in = r"\blue{x + y = z}"
        expected = r"\textcolor{blue}{x + y = z}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_multiple_colors1(self) -> None:
        """
        Test multiple color commands in the same line.
        """
        txt_in = r"The \red{quick} \blue{fox} \green{jumps}"
        expected = r"The \textcolor{red}{\text{quick}} \textcolor{blue}{\text{fox}} \textcolor{darkgreen}{\text{jumps}}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_mixed_content1(self) -> None:
        """
        Test color commands with both text and math content.
        """
        txt_in = r"\red{Result: x^2 + y^2}"
        expected = r"\textcolor{red}{Result: x^2 + y^2}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)

    def test_nested_braces1(self) -> None:
        """
        Test color command with nested braces.
        """
        txt_in = r"\blue{f(x) = {x + 1}}"
        expected = r"\textcolor{blue}{f(x) = {x + 1}}"
        actual = hmarkdo.process_color_commands(txt_in)
        self.assert_equal(actual, expected)


# #############################################################################
# Test_colorize_bullet_points_in_slide1
# #############################################################################


class Test_colorize_bullet_points_in_slide1(hunitest.TestCase):
    def test1(self) -> None:
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
        # Run function.
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

        actual = hmarkdo.colorize_bullet_points_in_slide(
            text, all_md_colors=all_md_colors
        )
        # Check output.
        expected = r"""
        - **\red{VC Theory}**
            - Measures model

        - **\yellow{Bias-Variance Decomposition}**
            - Prediction error
                - **\green{Bias}**
                - **\cyan{Variance}**

        - **\purple{Computation Complexity}**
            - Balances model
            - Related to
            - E.g., Minimum

        - **\magenta{Bayesian Approach}**
            - Treats ML as probability
            - Combines prior knowledge with observed data to update belief about a model

        - **\brown{Problem in ML Theory:}**
            - Assumptions may not align with practical problems
        """
        self.assert_equal(actual, expected)

    def test2(self) -> None:
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
        # Run function.
        actual = hmarkdo.colorize_bullet_points_in_slide(text)
        # Check output.
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
        self.assert_equal(actual, expected)
