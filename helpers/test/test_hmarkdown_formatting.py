import logging
import json
import os
from typing import Optional

import pytest

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown_div_blocks as hmadiblo
import helpers.hmarkdown_formatting as hmarform
import helpers.hprint as hprint
import helpers.htimer as htimer
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_remove_end_of_line_periods1
# #############################################################################


class Test_remove_end_of_line_periods1(hunitest.TestCase):
    """
    Test the remove_end_of_line_periods function.
    """

    def helper(
        self, input_text: str, expected_text: str
    ) -> None:
        """
        Test helper for remove_end_of_line_periods.

        :param input_text: Input text with potential periods at end of lines
        :param expected_text: Expected text after removing end-of-line periods
        """
        input_text = hprint.dedent(input_text).strip()
        expected_text = hprint.dedent(expected_text).strip()
        lines = input_text.split("\n")
        actual_lines = hmarform.remove_end_of_line_periods(lines)
        actual = "\n".join(actual_lines)
        self.assertEqual(actual, expected_text)

    def test1(self) -> None:
        """
        Test standard case with periods at end of lines.
        """
        # Prepare inputs.
        input_text = """
        Hello.
        World.
        This is a test.
        """
        # Prepare outputs.
        expected_text = """
        Hello
        World
        This is a test
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test2(self) -> None:
        """
        Test input without periods.
        """
        # Prepare inputs.
        input_text = """
        Hello
        World
        This is a test
        """
        # Prepare outputs.
        expected_text = """
        Hello
        World
        This is a test
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test3(self) -> None:
        """
        Test multiple periods at end of lines.
        """
        # Prepare inputs.
        input_text = """
        Line 1.....
        Line 2.....
        End.
        """
        # Prepare outputs.
        expected_text = """
        Line 1
        Line 2
        End
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test4(self) -> None:
        """
        Test empty string input.
        """
        # Prepare inputs.
        input_text = ""
        # Prepare outputs.
        expected_text = ""
        # Run test.
        self.helper(input_text, expected_text)

    def test5(self) -> None:
        """
        Test leading and trailing periods.
        """
        # Prepare inputs.
        input_text = """
        .Line 1.
        .Line 2.
        ..End..
        """
        # Prepare outputs.
        expected_text = """
        .Line 1
        .Line 2
        ..End
        """
        # Run test.
        self.helper(input_text, expected_text)


# #############################################################################
# Test_md_clean_up1
# #############################################################################


class Test_md_clean_up1(hunitest.TestCase):
    """
    Test the md_clean_up function.
    """

    def test1(self) -> None:
        """
        Test markdown cleanup with LaTeX math expressions.
        """
        # Prepare inputs.
        txt = r"""
        **States**:
        - \( S = \{\text{Sunny}, \text{Rainy}\} \)
        **Observations**:
        - \( O = \{\text{Yes}, \text{No}\} \) (umbrella)

        ### Initial Probabilities:
        \[
        P(\text{Sunny}) = 0.6, \quad P(\text{Rainy}) = 0.4
        \]

        ### Transition Probabilities:
        \[
        \begin{aligned}
        P(\text{Sunny} \to \text{Sunny}) &= 0.7, \quad P(\text{Sunny} \to \text{Rainy}) = 0.3 \\
        P(\text{Rainy} \to \text{Sunny}) &= 0.4, \quad P(\text{Rainy} \to \text{Rainy}) = 0.6
        \end{aligned}
        \]

        ### Observation (Emission) Probabilities:
        \[
        \begin{aligned}
        P(\text{Yes} \mid \text{Sunny}) &= 0.1, \quad P(\text{No} \mid \text{Sunny}) = 0.9 \\
        P(\text{Yes} \mid \text{Rainy}) &= 0.8, \quad P(\text{No} \mid \text{Rainy}) = 0.2
        \end{aligned}
        \]
        """
        txt = hprint.dedent(txt)
        actual = hmarform.md_clean_up(txt)
        actual = hprint.dedent(actual)
        expected = r"""
        **States**:
        - $S = \{\text{Sunny}, \text{Rainy}\}$
        **Observations**:
        - $O = \{\text{Yes}, \text{No}\}$ (umbrella)

        ### Initial Probabilities:
        $$
        \Pr(\text{Sunny}) = 0.6, \quad \Pr(\text{Rainy}) = 0.4
        $$

        ### Transition Probabilities:
        $$
        \begin{aligned}
        \Pr(\text{Sunny} \to \text{Sunny}) &= 0.7, \quad \Pr(\text{Sunny} \to \text{Rainy}) = 0.3 \\
        \Pr(\text{Rainy} \to \text{Sunny}) &= 0.4, \quad \Pr(\text{Rainy} \to \text{Rainy}) = 0.6
        \end{aligned}
        $$

        ### Observation (Emission) Probabilities:
        $$
        \begin{aligned}
        \Pr(\text{Yes} | \text{Sunny}) &= 0.1, \quad \Pr(\text{No} | \text{Sunny}) = 0.9 \\
        \Pr(\text{Yes} | \text{Rainy}) &= 0.8, \quad \Pr(\text{No} | \text{Rainy}) = 0.2
        \end{aligned}
        $$"""
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_remove_code_delimiters1
# #############################################################################


class Test_remove_code_delimiters1(hunitest.TestCase):
    """
    Test the remove_code_delimiters function.
    """

    def test1(self) -> None:
        """
        Test basic code block removal.
        """
        # Prepare inputs.
        content = r"""
        ```python
        def hello_world():
            print("Hello, World!")
        ```
        """
        content = hprint.dedent(content)
        lines = content.split("\n")
        # Prepare outputs.
        expected = r"""
        def hello_world():
            print("Hello, World!")
        """
        # Run test.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test code block with empty lines at start and end.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        lines = content.split("\n")
        # Prepare outputs.
        expected = r"""
        def check_empty_lines():
            print("Check empty lines are present!")
        """
        # Run test.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test markdown with headings, Python and YAML blocks.
        """
        # Prepare inputs.
        content = r"""
        # Section 1

        This section contains comment and python code.

        > "Knowledge is like a tree, growing stronger with each branch of understanding."

        ```python
        def greet(name):
            return f"Hello, {name}!"
        print(greet("World"))
        ```

        # Section 2

        Key points below.

        - Case Study 1: Implementation in modern industry
        - Case Study 2: Comparative analysis of traditional vs. modern methods

        ```yaml
        future:
        - AI integration
        - Process optimization
        - Sustainable solutions
        ```
        """
        content = hprint.dedent(content)
        lines = content.split("\n")
        # Prepare outputs.
        expected = r"""
        # Section 1

        This section contains comment and python code.

        > "Knowledge is like a tree, growing stronger with each branch of understanding."


        def greet(name):
            return f"Hello, {name}!"
        print(greet("World"))


        # Section 2

        Key points below.

        - Case Study 1: Implementation in modern industry
        - Case Study 2: Comparative analysis of traditional vs. modern methods

        yaml
        future:
        - AI integration
        - Process optimization
        - Sustainable solutions

        """
        # Run test.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test markdown with multiple indented Python blocks.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        content = hprint.dedent(content)
        lines = content.split("\n")
        # Run test.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        # TODO(ai_gp): Replace with self.assert_equal and an expected var.
        self.check_string(actual)

    def test5(self) -> None:
        """
        Test empty string input.
        """
        # Prepare inputs.
        content = ""
        lines = content.split("\n") if content else []
        # Prepare outputs.
        expected = ""
        # Run test.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test6(self) -> None:
        """
        Test Python and markdown code block together.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        lines = content.split("\n")
        # Prepare outputs.
        expected = r"""
        def no_start_python():
            print("No mention of python at the start")



            A markdown paragraph contains
            delimiters that needs to be removed.
        """
        # Run test.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_format_markdown_slide
# #############################################################################


class Test_format_markdown_slide(hunitest.TestCase):
    """
    Test the format_markdown_slide function.
    """

    def helper(self, input_text: str, expected_text: str) -> None:
        """
        Test helper for format_markdown_slide.

        :param input_text: Input markdown with slide markup
        :param expected_text: Expected formatted output
        """
        lines = hprint.dedent(input_text).strip().split("\n")
        actual = hmarform.format_markdown_slide(lines)
        actual = "\n".join(actual)
        expected = hprint.dedent(expected_text).strip()
        _LOG.debug("actual=\n%s", actual)
        _LOG.debug("expected=\n%s", expected)
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test simple slide with bullets.
        """
        # Prepare inputs.
        input_text = """
        * Slide title
        - First bullet
        - Second bullet
        """
        # Prepare outputs.
        expected_text = """
        * Slide Title

        - First bullet

        - Second bullet
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test2(self) -> None:
        """
        Test multiple slides.
        """
        # Prepare inputs.
        input_text = """
        * First slide
        - Point A
        - Point B
        * Second slide
        - Point X
        - Point Y
        """
        # Prepare outputs.
        expected_text = """
        * First Slide

        - Point A

        - Point B
        * Second Slide

        - Point X

        - Point Y
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test3(self) -> None:
        """
        Test slides with nested bullets.
        """
        # Prepare inputs.
        input_text = """
        * Main slide
        - First level
          - Nested point
          - Another nested
        - Second level
        """
        # Prepare outputs.
        expected_text = """
        * Main Slide

        - First level
          - Nested point
          - Another nested

        - Second level
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test4(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        input_text = """
        """
        # Prepare outputs.
        expected_text = """
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test5(self) -> None:
        """
        Test slide title capitalization.
        """
        # Prepare inputs.
        input_text = """
        * mixed case slide title
        - Point one
        """
        # Prepare outputs.
        expected_text = """
        * Mixed Case Slide Title

        - Point one
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test6(self) -> None:
        """
        Test slide with only title, no bullets.
        """
        # Prepare inputs.
        input_text = """
        * Solo slide title
        """
        # Prepare outputs.
        expected_text = """
        * Solo Slide Title
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test7(self) -> None:
        """
        Test slide with deeply nested bullets.
        """
        # Prepare inputs.
        input_text = """
        * Main slide
        - Level 1
          - Level 2
            - Level 3
              - Level 4
        - Back to level 1
        """
        # Prepare outputs.
        expected_text = """
        * Main Slide

        - Level 1
          - Level 2
            - Level 3
              - Level 4

        - Back to level 1
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test8(self) -> None:
        """
        Test slide with nested bullets and special formatting.
        """
        # Prepare inputs.
        input_text = r"""
        * What Are Data Analytics?
        - **Collections of data**

          - Aggregated, organized data sets for analysis

          - E.g., customer purchase histories in a CRM system
        - **Dashboards**

          - Visual displays of key metrics for insights
          - E.g., dashboard showing quarterly revenue, expenses

        - **Descriptive statistics**
          - Summary metrics: mean, median, mode, standard deviation
          - E.g., average sales per quarter to understand trends
        - **Historical reports**

          - Examination of past performance
          - E.g., monthly sales reports for past fiscal year
        - **Models**
          - Statistical representations to forecast, explain phenomena

          - E.g., predictive model to anticipate customer churn based on behavioral data
        """
        # Prepare outputs.
        expected_text = r"""
        * What Are Data Analytics?

        - **Collections of data**
          - Aggregated, organized data sets for analysis
          - E.g., customer purchase histories in a CRM system

        - **Dashboards**
          - Visual displays of key metrics for insights
          - E.g., dashboard showing quarterly revenue, expenses

        - **Descriptive statistics**
          - Summary metrics: mean, median, mode, standard deviation
          - E.g., average sales per quarter to understand trends

        - **Historical reports**
          - Examination of past performance
          - E.g., monthly sales reports for past fiscal year

        - **Models**
          - Statistical representations to forecast, explain phenomena
          - E.g., predictive model to anticipate customer churn based on behavioral data
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test9(self) -> None:
        """
        Test prettier div blocks behavior.
        """
        # Prepare inputs.
        input_text = r"""
        * Incremental vs Iterative
        ::: columns
        :::: {.column width=55%}

        - **Incremental Development**
          - Each increment adds functional components
          - Require upfront planning to divide features meaningfully
          - Integration of increments can be complex

        - **Iterative Development**
          - Each increment delivers usable system
          - Refine and improve product through repeated cycles
          - Get feedback
          - Uncover and adjust for unknown requirements

        - **Incremental $\gg$ Iterative**

        ::::
        :::: {.column width=40%}

        ![](msml610/lectures_source/figures/Lesson02_Monalisa_incremental.png){width=90%}

        \small _Incremental

        \vspace{0.5cm}

        ![](msml610/lectures_source/figures/Lesson02_Monalisa_iterative.png){width=90%}

        \small _Iterative_

        \vspace{0.5cm}

        ![](msml610/lectures_source/figures/Lesson02_Skateboard.png){width=90%}

        \small _Incremental vs Iterative_
        ::::
        :::
        """
        # Prepare outputs.
        expected_text = r"""
        * Incremental vs Iterative
        ::: columns
        :::: {.column width=55%}

        - **Incremental Development**
          - Each increment adds functional components
          - Require upfront planning to divide features meaningfully
          - Integration of increments can be complex

        - **Iterative Development**
          - Each increment delivers usable system
          - Refine and improve product through repeated cycles
          - Get feedback
          - Uncover and adjust for unknown requirements

        - **Incremental $\gg$ Iterative**
        ::::
        :::: {.column width=40%}
        ![](msml610/lectures_source/figures/Lesson02_Monalisa_incremental.png){width=90%}
        \small \_Incremental
        \vspace{0.5cm}
        ![](msml610/lectures_source/figures/Lesson02_Monalisa_iterative.png){width=90%}
        \small _Iterative_
        \vspace{0.5cm}
        ![](msml610/lectures_source/figures/Lesson02_Skateboard.png){width=90%}
        \small _Incremental vs Iterative_
        ::::
        :::
        """
        # Run test.
        self.helper(input_text, expected_text)


# #############################################################################
# Test_format_figures
# #############################################################################


class Test_format_figures(hunitest.TestCase):
    """
    Test the format_figures function.
    """

    def helper(self, input_text: str, expected_text: str) -> None:
        """
        Test helper for format_figures.

        :param input_text: Input markdown text with figures
        :param expected_text: Expected formatted output
        """
        lines = hprint.dedent(input_text).strip().split("\n")
        actual_lines = hmarform.format_figures(lines)
        actual = "\n".join(actual_lines)
        expected = hprint.dedent(expected_text).strip()
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test converting basic text with figures to column format.
        """
        input_text = """
        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
          - Read / write small amounts of data frequently
        - **Columnar DBs**
          - E.g., Amazon Redshift, Snowflake
          - Read / write large amounts of data infrequently
          - Analytics requires a few columns
          - Better data compression

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_1.png)

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_2.png)
        """
        expected_text = """
        ::: columns
        :::: {.column width=65%}
        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
          - Read / write small amounts of data frequently
        - **Columnar DBs**
          - E.g., Amazon Redshift, Snowflake
          - Read / write large amounts of data infrequently
          - Analytics requires a few columns
          - Better data compression
        ::::
        :::: {.column width=40%}

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_1.png)

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_2.png)
        ::::
        :::
        """
        self.helper(input_text, expected_text)

    def test2(self) -> None:
        """
        Test text without figures remains unchanged.
        """
        # Prepare inputs.
        input_text = """
        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
        - **Columnar DBs**
          - E.g., Amazon Redshift, Snowflake
          - Better data compression
        """
        # Prepare outputs.
        expected_text = """
        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
        - **Columnar DBs**
          - E.g., Amazon Redshift, Snowflake
          - Better data compression
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test3(self) -> None:
        """
        Test text already in columns format remains unchanged.
        """
        # Prepare inputs.
        input_text = """
        ::: columns
        :::: {.column width=65%}
        - **Row-based DBs**
          - E.g., MySQL, Postgres
        ::::
        :::: {.column width=40%}
        ![](some_image.png)
        ::::
        :::
        """
        # Prepare outputs.
        expected_text = """
        ::: columns
        :::: {.column width=65%}
        - **Row-based DBs**
          - E.g., MySQL, Postgres
        ::::
        :::: {.column width=40%}
        ![](some_image.png)
        ::::
        :::
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test4(self) -> None:
        """
        Test converting text with a single figure.
        """
        # Prepare inputs.
        input_text = """
        - **Important concept**
          - This is the main point
          - Supporting detail

        ![](path/to/image.png)
        """
        # Prepare outputs.
        expected_text = """
        ::: columns
        :::: {.column width=65%}
        - **Important concept**
          - This is the main point
          - Supporting detail
        ::::
        :::: {.column width=40%}

        ![](path/to/image.png)
        ::::
        :::
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test5(self) -> None:
        """
        Test converting mixed content including text and figures.
        """
        # Prepare inputs.
        input_text = """
        ## Section header

        Some introductory text here.

        - **Point one**
          - Detail A
          - Detail B
        - **Point two**
          - Detail X
          - Detail Y

        ![](image1.png)

        Additional text between figures.

        ![](image2.png)
        """
        # Prepare outputs.
        expected_text = """
        ::: columns
        :::: {.column width=65%}
        ## Section header

        Some introductory text here.

        - **Point one**
          - Detail A
          - Detail B
        - **Point two**
          - Detail X
          - Detail Y
        ::::
        :::: {.column width=40%}

        ![](image1.png)

        Additional text between figures.

        ![](image2.png)
        ::::
        :::
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test6(self) -> None:
        """
        Test empty input returns empty output.
        """
        # Prepare inputs.
        input_text = ""
        # Prepare outputs.
        expected_text = ""
        # Run test.
        self.helper(input_text, expected_text)

    def test7(self) -> None:
        """
        Test slide title is left unchanged.
        """
        # Prepare inputs.
        input_text = """
        * VCS: How to Track Data

        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
          - Read / write small amounts of data frequently

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_1.png)

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_2.png)
        """
        # Prepare outputs.
        expected_text = """
        * VCS: How to Track Data
        ::: columns
        :::: {.column width=65%}
        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
          - Read / write small amounts of data frequently
        ::::
        :::: {.column width=40%}

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_1.png)

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_2.png)
        ::::
        :::
        """
        # Run test.
        self.helper(input_text, expected_text)


# #############################################################################
# Test_format_md_links_to_latex_format
# #############################################################################


class Test_format_md_links_to_latex_format(hunitest.TestCase):
    """
    Test the format_md_links_to_latex_format function.
    """

    def helper(self, input_text: str, expected_text: str) -> None:
        """
        Test helper for format_md_links_to_latex_format.

        :param input_text: Input markdown with links
        :param expected_text: Expected formatted output
        """
        # Prepare inputs.
        lines = hprint.dedent(input_text).strip().split("\n")
        # Run test.
        actual_lines = hmarform.format_md_links_to_latex_format(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        expected = hprint.dedent(expected_text).strip()
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        input_text = ""
        # Prepare outputs.
        expected_text = ""
        # Run test.
        self.helper(input_text, expected_text)

    def test2(self) -> None:
        """
        Test content without any links.
        """
        # Prepare inputs.
        input_text = """
        # Important Notes

        - This is regular text
        - No links here
        - Just plain content
        """
        # Prepare outputs.
        expected_text = """
        # Important Notes

        - This is regular text
        - No links here
        - Just plain content
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test3(self) -> None:
        """
        Test converting single plain HTTP URL.
        """
        # Prepare inputs.
        input_text = """
        Visit http://example.com
        """
        # Prepare outputs.
        expected_text = r"""
        Visit [\textcolor{blue}{\underline{http://example.com}}](http://example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test4(self) -> None:
        """
        Test converting single plain HTTPS URL.
        """
        # Prepare inputs.
        input_text = """
        Visit https://example.com
        """
        # Prepare outputs.
        expected_text = r"""
        Visit [\textcolor{blue}{\underline{https://example.com}}](https://example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test5(self) -> None:
        """
        Test converting plain URLs with paths.
        """
        # Prepare inputs.
        input_text = """
        Check out https://ubuntu.com/tutorials/command-line-for-beginners
        """
        expected_text = r"""
        Check out [\textcolor{blue}{\underline{https://ubuntu.com/tutorials/command-line-for-beginners}}](https://ubuntu.com/tutorials/command-line-for-beginners)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test6(self) -> None:
        """
        Test converting plain URL with query parameters.
        """
        # Prepare inputs.
        input_text = """
        Search: https://example.com/search?q=python&page=1
        """
        expected_text = r"""
        Search: [\textcolor{blue}{\underline{https://example.com/search?q=python&page=1}}](https://example.com/search?q=python&page=1)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test7(self) -> None:
        """
        Test converting plain URL with fragment.
        """
        # Prepare inputs.
        input_text = """
        Docs: https://docs.python.org/3/tutorial/index.html#tutorial-index
        """
        expected_text = r"""
        Docs: [\textcolor{blue}{\underline{https://docs.python.org/3/tutorial/index.html#tutorial-index}}](https://docs.python.org/3/tutorial/index.html#tutorial-index)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test8(self) -> None:
        """
        Test plain URL at beginning of line.
        """
        # Prepare inputs.
        input_text = """
        https://example.com is a good site
        """
        expected_text = r"""
        [\textcolor{blue}{\underline{https://example.com}}](https://example.com) is a good site
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test9(self) -> None:
        """
        Test plain URL at end of line.
        """
        # Prepare inputs.
        input_text = """
        Check this link https://example.com
        """
        expected_text = r"""
        Check this link [\textcolor{blue}{\underline{https://example.com}}](https://example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test10(self) -> None:
        """
        Test converting single URL in backticks.
        """
        # Prepare inputs.
        input_text = """
        Visit `https://example.com` for details
        """
        expected_text = r"""
        Visit [\textcolor{blue}{\underline{https://example.com}}](https://example.com) for details
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test11(self) -> None:
        """
        Test converting simple markdown link [Text](URL).
        """
        # Prepare inputs.
        input_text = """
        Check out [this tutorial](https://example.com/tutorial)
        """
        expected_text = r"""
        Check out [\textcolor{blue}{\underline{this tutorial}}](https://example.com/tutorial)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test12(self) -> None:
        """
        Test that markdown link preserves the display text.
        """
        # Prepare inputs.
        input_text = """
        See [documentation](https://docs.example.com) here
        """
        expected_text = r"""
        See [\textcolor{blue}{\underline{documentation}}](https://docs.example.com) here
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test13(self) -> None:
        """
        Test converting simple email link.
        """
        # Prepare inputs.
        input_text = """
        Contact: [support@example.com](support@example.com)
        """
        expected_text = r"""
        Contact: [\textcolor{blue}{\underline{support@example.com}}](support@example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test14(self) -> None:
        """
        Test converting simple email link.
        """
        # Prepare inputs.
        input_text = """
        Contact: [](support@example.com)
        """
        expected_text = r"""
        Contact: [\textcolor{blue}{\underline{support@example.com}}](support@example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test15(self) -> None:
        """
        Test converting multiple URLs on same line.
        """
        # Prepare inputs.
        input_text = """
        Visit https://example.com and https://another.com
        """
        expected_text = r"""
        Visit [\textcolor{blue}{\underline{https://example.com}}](https://example.com) and [\textcolor{blue}{\underline{https://another.com}}](https://another.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test16(self) -> None:
        """
        Test converting multiple URLs on different lines.
        """
        # Prepare inputs.
        input_text = """
        Tutorial: https://ubuntu.com/tutorials/command-line-for-beginners

        Documentation: https://docs.python.org/3/
        """
        expected_text = r"""
        Tutorial: [\textcolor{blue}{\underline{https://ubuntu.com/tutorials/command-line-for-beginners}}](https://ubuntu.com/tutorials/command-line-for-beginners)

        Documentation: [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test17(self) -> None:
        """
        Test handling mixed plain and backtick URLs.
        """
        # Prepare inputs.
        input_text = """
        Plain: https://example.com
        Backtick: `https://docs.example.com`
        """
        expected_text = r"""
        Plain: [\textcolor{blue}{\underline{https://example.com}}](https://example.com)
        Backtick: [\textcolor{blue}{\underline{https://docs.example.com}}](https://docs.example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test18(self) -> None:
        """
        Test handling mixed plain URLs and markdown links.
        """
        # Prepare inputs.
        input_text = """
        Plain: https://example.com
        Markdown: [Click here](https://docs.example.com)
        """
        expected_text = r"""
        Plain: [\textcolor{blue}{\underline{https://example.com}}](https://example.com)
        Markdown: [\textcolor{blue}{\underline{Click here}}](https://docs.example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test19(self) -> None:
        """
        Test handling all link types in same content.
        """
        # Prepare inputs.
        input_text = r"""
        ## Resources

        - Plain URL: https://ubuntu.com/tutorials/command-line-for-beginners
        - Backtick URL: `https://docs.python.org/3/`
        - Markdown link: [Click here](https://github.com)
        - Email: [support@example.com](support@example.com)
        - Already formatted: [\textcolor{blue}{\underline{https://stackoverflow.com}}](https://stackoverflow.com)
        """
        expected_text = r"""
        ## Resources

        - Plain URL: [\textcolor{blue}{\underline{https://ubuntu.com/tutorials/command-line-for-beginners}}](https://ubuntu.com/tutorials/command-line-for-beginners)
        - Backtick URL: [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        - Markdown link: [\textcolor{blue}{\underline{Click here}}](https://github.com)
        - Email: [\textcolor{blue}{\underline{support@example.com}}](support@example.com)
        - Already formatted: [\textcolor{blue}{\underline{https://stackoverflow.com}}](https://stackoverflow.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test20(self) -> None:
        """
        Test URL pointing to file with extension.
        """
        # Prepare inputs.
        input_text = """
        Download: https://cdn.example.com/files/document.pdf
        """
        expected_text = r"""
        Download: [\textcolor{blue}{\underline{https://cdn.example.com/files/document.pdf}}](https://cdn.example.com/files/document.pdf)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test21(self) -> None:
        """
        Test that already formatted links are preserved.
        """
        # Prepare inputs.
        input_text = r"""
        Link: [\textcolor{blue}{\underline{Example Site}}](https://example.com)
        """
        expected_text = r"""
        Link: [\textcolor{blue}{\underline{Example Site}}](https://example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test22(self) -> None:
        """
        Test that simple image links are left untouched.
        """
        # Prepare inputs.
        input_text = """
        Check this image: ![](path/to/image.png)
        """
        expected_text = """
        Check this image: ![](path/to/image.png)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test23(self) -> None:
        """
        Test that JPG image links are left untouched.
        """
        # Prepare inputs.
        input_text = """
        ![](lectures_source/images/lec_4_1_slide_5_image_1.jpg)
        """
        expected_text = """
        ![](lectures_source/images/lec_4_1_slide_5_image_1.jpg)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test24(self) -> None:
        """
        Test that image links are not processed while email links are.
        """
        # Prepare inputs.
        input_text = """
        Contact: [](support@example.com)
        Image: ![](path/to/image.png)
        Link: https://example.com
        """
        expected_text = r"""
        Contact: [\textcolor{blue}{\underline{support@example.com}}](support@example.com)
        Image: ![](path/to/image.png)
        Link: [\textcolor{blue}{\underline{https://example.com}}](https://example.com)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test25(self) -> None:
        """
        Test that image links with alt text are left untouched.
        """
        # Prepare inputs.
        input_text = """
        ![Alt text](path/to/image.png)
        """
        expected_text = """
        ![Alt text](path/to/image.png)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test26(self) -> None:
        """
        Test that multiple image links are left untouched.
        """
        # Prepare inputs.
        input_text = """
        ![](image1.png)
        ![](image2.jpg)
        ![](image3.gif)
        """
        expected_text = """
        ![](image1.png)
        ![](image2.jpg)
        ![](image3.gif)
        """
        # Run test.
        self.helper(input_text, expected_text)

    def test27(self) -> None:
        """
        Test markdown link with escaped underscores in the text.
        """
        # Prepare inputs.
        input_text = r"""
        [tutorial\_docker\_compose](https://github.com/gpsaggese/umd_classes/tree/main/data605/tutorials/tutorial_docker_compose)
        """
        expected_text = r"""
        [\textcolor{blue}{\underline{tutorial\_docker\_compose}}](https://github.com/gpsaggese/umd_classes/tree/main/data605/tutorials/tutorial_docker_compose)
        """
        # Run test.
        self.helper(input_text, expected_text)


# #############################################################################
# Test_add_prettier_ignore_to_div_blocks
# #############################################################################


class Test_add_prettier_ignore_to_div_blocks(hunitest.TestCase):
    """
    Test the function to add prettier-ignore comments around div blocks.
    """

    def test1(self) -> None:
        """
        Test simple div block with two colons.
        """
        # Prepare inputs.
        txt = """
        ::::
        :::
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        lines = txt.split("\n")
        # Run test.
        actual_lines = hmadiblo.add_prettier_ignore_to_div_blocks(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        expected = """
        <!-- prettier-ignore-start -->
        ::::
        :::
        <!-- prettier-ignore-end -->
        """
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test multiple div blocks in the same content.
        """
        # Prepare inputs.
        txt = """
        Some text before

        ::::
        ::::{.column width=40%}

        Middle text

        :::columns
        ::::{.column width=60%}

        Some text after
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        lines = txt.split("\n")
        # Run test.
        actual_lines = hmadiblo.add_prettier_ignore_to_div_blocks(lines)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = """Some text before


        <!-- prettier-ignore-start -->
        ::::
        ::::{.column width=40%}
        <!-- prettier-ignore-end -->


        Middle text


        <!-- prettier-ignore-start -->
        :::columns
        ::::{.column width=60%}
        <!-- prettier-ignore-end -->


        Some text after"""
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_remove_prettier_ignore_from_div_blocks
# #############################################################################


class Test_remove_prettier_ignore_from_div_blocks(hunitest.TestCase):
    """
    Test the function to remove prettier-ignore comments from div blocks.
    """

    def test1(self) -> None:
        """
        Test removing prettier-ignore from simple div block.
        """
        # Prepare inputs.
        txt = """

        <!-- prettier-ignore-start -->
        ::::
        :::
        <!-- prettier-ignore-end -->

        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        lines = txt.split("\n")
        # Run test.
        actual_lines = hmadiblo.remove_prettier_ignore_from_div_blocks(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        expected = """::::
:::"""
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test removing prettier-ignore from multiple div blocks.
        """
        # Prepare inputs.
        txt = """
        Text before

        <!-- prettier-ignore-start -->
        ::::
        ::::{.column width=40%}
        <!-- prettier-ignore-end -->

        Middle text

        <!-- prettier-ignore-start -->
        :::columns
        ::::{.column width=60%}
        <!-- prettier-ignore-end -->

        Text after
        """
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        lines = txt.split("\n")
        # Run test.
        actual_lines = hmadiblo.remove_prettier_ignore_from_div_blocks(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        expected = """Text before
::::
::::{.column width=40%}
Middle text
:::columns
::::{.column width=60%}
Text after"""
        self.assert_equal(actual, expected)


# #############################################################################
# _Format_md_TestCase
# #############################################################################


class _Format_md_TestCase(hunitest.TestCase):
    """
    Base class for testing format_md() function with different tools.

    Subclasses should set the tool and available_modes for their formatter.
    """

    tool: Optional[str] = None
    backend: Optional[str] = None

    def helper(self, input_txt: str, width: int = 80) -> str:
        """
        Test helper for format_md with different tools.

        :param input_txt: input markdown text
        :param width: line width for formatting
        :return: formatted text
        """
        hdbg.dassert_is_not(self.tool, None)
        hdbg.dassert_is_not(self.backend, None)
        formatted = hmarform.format_md(
            input_txt, self.tool, self.backend, width=width
        )
        return formatted

    def test1(self) -> None:
        """
        Test simple markdown formatting with dockerized prettier.
        """
        # Prepare inputs.
        input_txt = "# Hello\n\nThis is a test.\n"
        expected_txt = input_txt
        width = 80
        # Run test.
        actual = self.helper(input_txt, width)
        # Check outputs.
        self.assert_equal(actual, expected_txt)

    def test2(self) -> None:
        """
        Test empty input with dockerized prettier.
        """
        # Prepare inputs.
        input_txt = ""
        expected_txt = input_txt
        # Prepare outputs.
        width = 80
        # Run test.
        actual = self.helper(input_txt, width)
        # Check outputs.
        self.assert_equal(actual, expected_txt)

    def test3(self) -> None:
        """
        Test multiline markdown with dockerized prettier.
        """
        # Prepare inputs.
        input_txt = """
        # Section

        - Item 1
        - Item 2
        - Item 3
        """
        input_txt = hprint.dedent(input_txt)
        expected_txt = """
        # Section

        - Item 1
        - Item 2
        - Item 3
        """
        expected_txt = hprint.dedent(expected_txt)
        width = 80
        # Run test.
        actual = self.helper(input_txt, width)
        # Check outputs.
        self.assert_equal(actual, expected_txt)

    def test4(self) -> None:
        """
        Test that width parameter affects formatting.
        """
        # Prepare inputs.
        input_txt = "This is a very long line that should be wrapped at a shorter width to test the width parameter functionality."
        expected_txt = """
        This is a very long line that should be
        wrapped at a shorter width to test the
        width parameter functionality.
        """
        expected_txt = hprint.dedent(expected_txt)
        # Run test with different widths.
        actual = self.helper(input_txt, 40)
        # Check outputs.
        self.assert_equal(actual, expected_txt)

    def test5(self) -> None:
        """
        Test that width parameter affects formatting with wider width.
        """
        # Prepare inputs.
        input_txt = "This is a very long line that should be wrapped at a shorter width to test the width parameter functionality."
        expected_txt = """
        This is a very long line that should be wrapped at a shorter
        width to test the width parameter functionality.
        """
        expected_txt = hprint.dedent(expected_txt)
        # Run test with different widths.
        actual = self.helper(input_txt, 60)
        # Check outputs.
        self.assert_equal(actual, expected_txt)


# #############################################################################
# Test_format_md_prettier
# #############################################################################


class Test_format_md_prettier1(_Format_md_TestCase):
    """
    Test format_md() function with prettier tool.
    """

    tool = "prettier"
    backend = "dockerized"


@pytest.mark.skipif(
    not hmarform.is_prettier_available("global"),
    reason="prettier not installed globally",
)
class Test_format_md_prettier2(_Format_md_TestCase):
    """
    Test format_md() function with prettier tool (global backend).
    """

    tool = "prettier"
    backend = "global"


# #############################################################################
# Test_format_md_mdformat
# #############################################################################


@pytest.mark.skipif(
    not hmarform.is_mdformat_available("library"), reason="mdformat package not installed"
)
class Test_format_md_mdformat1(_Format_md_TestCase):
    """
    Test format_md() function with mdformat tool (library backend).
    """

    tool = "mdformat"
    backend = "library"


@pytest.mark.skipif(
    not hmarform.is_mdformat_available("uvx"), reason="mdformat package not installed"
)
class Test_format_md_mdformat2(_Format_md_TestCase):
    """
    Test format_md() function with mdformat tool (uvx backend).
    """

    tool = "mdformat"
    backend = "uvx"


@pytest.mark.skipif(
    not hmarform.is_mdformat_available("library"), reason="mdformat package not installed"
)
class Test_format_md_mdformat3(_Format_md_TestCase):
    """
    Test format_md() function with mdformat tool (uvx backend alternate).
    """

    tool = "mdformat"
    backend = "uvx"


# #############################################################################
# Test_format_md_flowmark
# #############################################################################


@pytest.mark.skipif(
    not hmarform.is_flowmark_available("library"), reason="flowmark package not installed"
)
class Test_format_md_flowmark1(_Format_md_TestCase):

    tool = "flowmark"
    backend = "library"


@pytest.mark.skipif(
    not hmarform.is_flowmark_available("uvx"), reason="flowmark package not installed"
)
class Test_format_md_flowmark2(_Format_md_TestCase):

    tool = "flowmark"
    backend = "uvx"


@pytest.mark.skipif(
    not hmarform.is_flowmark_available("global"), reason="flowmark package not installed"
)
class Test_format_md_flowmark3(_Format_md_TestCase):

    tool = "flowmark"
    backend = "global"


@pytest.mark.skipif(
    not hmarform.is_flowmark_available("uvx-rs"), reason="flowmark package not installed"
)
class Test_format_md_flowmark4(_Format_md_TestCase):

    tool = "flowmark"
    backend = "uvx-rs"


@pytest.mark.skipif(
    not hmarform.is_flowmark_available("global-rs"), reason="flowmark package not installed"
)
class Test_format_md_flowmark5(_Format_md_TestCase):

    tool = "flowmark"
    backend = "global-rs"

# #############################################################################
# Test_format_md_comparison_and_performance
# #############################################################################


class Test_format_md_comparison_and_performance(hunitest.TestCase):
    """
    Test format_md() comparison across tools and collect performance metrics.
    """

    def test1(self) -> None:
        """
        Test all available tools produce valid markdown output.

        This test compares output from multiple tools, collects timing data,
        and saves results to output directory. Results are both printed to logs
        and saved to a JSON file in the output directory for analysis.
        """
        # Prepare inputs.
        input_txt = """
        # Test Document

        This is a test markdown document.

        - Item 1 with a long description that might wrap
        - Item 2 with another long description
        - Item 3

        ## Subsection

        Some more text here to test formatting.

        Here is more content with formatting issues:
        -   Inconsistent list spacing
        -    Extra spaces

        **Bold text**  and *italic text* should be properly formatted.

        ```python
        def example():
            return "Code should be preserved"
        ```
        """
        input_txt = hprint.dedent(input_txt)
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        # Test data for each tool/backend combination.
        test_cases = [
            ("prettier", "dockerized"),
        ]
        # Add optional tools if available.
        tools = ["global"]
        for tool in tools:
            if hmarform.is_prettier_available(tool):
                test_cases.append(("prettier", tool))
        #
        tools = ["library", "uvx", "global"]
        for tool in tools:
            if hmarform.is_mdformat_available(tool):
                test_cases.append(("mdformat", tool))
        #
        tools = ["library", "uvx", "uvx-rs", "global", "global-rs"]
        for tool in tools:
            if hmarform.is_flowmark_available(tool):
                test_cases.append(("flowmark", tool))
        #
        _LOG.debug("test_cases=%s", str(test_cases))
        results = []
        for tool, backend in test_cases:
            error_msg = None
            output = None
            elapsed_time = None
            try:
                timer_ = htimer.Timer()
                output = hmarform.format_md(input_txt, tool, backend, width=80)
                timer_.stop()
                elapsed_time = str(timer_)
                success = True
            except Exception as e:
                success = False
                error_msg = str(e)
                elapsed_time = None
            results.append(
                {
                    "tool": tool,
                    "backend": backend,
                    "time": elapsed_time,
                    "output_length": len(output) if output else 0,
                    "success": success,
                    "error": error_msg,
                }
            )
            if success and output is not None:
                self.assertGreater(len(output), 0, f"{tool}/{backend} produced empty output")
        # Save results to JSON file for analysis.
        results_file = os.path.join(output_dir, "comparison_results.json")
        hio.to_file(results_file, json.dumps(results, indent=2))
        # Print results
        _LOG.info("Comparison results saved to %s", results_file)
        for result in results:
            if result["success"]:
                _LOG.info(
                    "%s/%s completed in %s",
                    result["tool"],
                    result["backend"],
                    result["time"],
                )
            else:
                error_msg = result.get("error", "Unknown error")
                _LOG.info(
                    "%s/%s failed: %s",
                    result["tool"],
                    result["backend"],
                    error_msg,
                )
        # At least some tests should succeed
        successful = sum(1 for r in results if r["success"])
        self.assertGreater(successful, 0, "At least one tool should succeed")
