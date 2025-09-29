import logging
import os

import pytest

import helpers.hio as hio
import helpers.hmarkdown_formatting as hmarform
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_remove_end_of_line_periods1
# #############################################################################


class Test_remove_end_of_line_periods1(hunitest.TestCase):

    def helper(self, input_text: str, expected_text: str) -> None:
        # Prepare inputs.
        input_text = hprint.dedent(input_text).strip()
        expected_text = hprint.dedent(expected_text).strip()
        lines = input_text.split("\n")
        # Run test.
        actual_lines = hmarform.remove_end_of_line_periods(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assertEqual(actual, expected_text)

    def test_standard_case(self) -> None:
        input_text = """
        Hello.
        World.
        This is a test.
        """
        expected_text = """
        Hello
        World
        This is a test
        """
        self.helper(input_text, expected_text)

    def test_no_periods(self) -> None:
        input_text = """
        Hello
        World
        This is a test
        """
        expected_text = """
        Hello
        World
        This is a test
        """
        self.helper(input_text, expected_text)

    def test_multiple_periods(self) -> None:
        input_text = """
        Line 1.....
        Line 2.....
        End.
        """
        expected_text = """
        Line 1
        Line 2
        End
        """
        self.helper(input_text, expected_text)

    def test_empty_string(self) -> None:
        input_text = ""
        expected_text = ""
        self.helper(input_text, expected_text)

    def test_leading_and_trailing_periods(self) -> None:
        input_text = """
        .Line 1.
        .Line 2.
        ..End..
        """
        expected_text = """
        .Line 1
        .Line 2
        ..End
        """
        self.helper(input_text, expected_text)


# #############################################################################
# Test_md_clean_up1
# #############################################################################


class Test_md_clean_up1(hunitest.TestCase):

    def test1(self) -> None:
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

    def test1(self) -> None:
        """
        Test a basic example.
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
        # Call function.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
        def hello_world():
            print("Hello, World!")
        """
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test an example with empty lines at the start and end.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        lines = content.split("\n")
        # Call function.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
        def check_empty_lines():
            print("Check empty lines are present!")
        """
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test a markdown with headings, Python and yaml blocks.
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
        # Call function.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check output.
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
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test another markdown with headings and multiple indent Python blocks.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        content = hprint.dedent(content)
        lines = content.split("\n")
        # Call function.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check output.
        self.check_string(actual, dedent=True)

    def test5(self) -> None:
        """
        Test an empty string.
        """
        # Prepare inputs.
        content = ""
        lines = content.split("\n") if content else []
        # Call function.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = ""
        self.assert_equal(actual, expected, dedent=True)

    def test6(self) -> None:
        """
        Test a Python and immediate markdown code block.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        lines = content.split("\n")
        # Call function.
        actual_lines = hmarform.remove_code_delimiters(lines)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
        def no_start_python():
            print("No mention of python at the start")



            A markdown paragraph contains
            delimiters that needs to be removed.
        """
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_format_markdown_slide
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_format_markdown_slide(hunitest.TestCase):

    def helper(self, input_text: str, expected_text: str) -> None:
        # Prepare inputs.
        lines = hprint.dedent(input_text).strip().split("\n")
        # Run test.
        actual = hmarform.format_markdown_slide(lines)
        actual = "\n".join(actual)
        # Check outputs.
        expected = hprint.dedent(expected_text).strip()
        _LOG.debug("actual=\n%s", actual)
        _LOG.debug("expected=\n%s", expected)
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test formatting a simple slide with bullets.
        """
        input_text = """
        * Slide title
        - First bullet
        - Second bullet
        """
        expected_text = """
        * Slide Title

        - First bullet

        - Second bullet
        """
        self.helper(input_text, expected_text)

    def test2(self) -> None:
        """
        Test formatting multiple slides.
        """
        input_text = """
        * First slide
        - Point A
        - Point B
        * Second slide
        - Point X
        - Point Y
        """
        expected_text = """
        * First Slide

        - Point A

        - Point B
        * Second Slide

        - Point X

        - Point Y
        """
        self.helper(input_text, expected_text)

    def test3(self) -> None:
        """
        Test formatting slides with nested bullets.
        """
        input_text = """
        * Main slide
        - First level
          - Nested point
          - Another nested
        - Second level
        """
        expected_text = """
        * Main Slide

        - First level
          - Nested point
          - Another nested

        - Second level
        """
        self.helper(input_text, expected_text)

    def test4(self) -> None:
        """
        Test formatting empty input.
        """
        # Prepare inputs.
        input_text = """
        """
        # Check outputs.
        expected_text = """
        """
        self.helper(input_text, expected_text)

    def test5(self) -> None:
        """
        Test formatting slide title capitalization.
        """
        input_text = """
        * mixed case slide title
        - Point one
        """
        expected_text = """
        * Mixed Case Slide Title

        - Point one
        """
        self.helper(input_text, expected_text)

    def test6(self) -> None:
        """
        Test formatting slide with only title, no bullet points.
        """
        input_text = """
        * Solo slide title
        """
        expected_text = """
        * Solo Slide Title
        """
        self.helper(input_text, expected_text)

    def test7(self) -> None:
        """
        Test formatting slide with deeply nested bullets.
        """
        input_text = """
        * Main slide
        - Level 1
          - Level 2
            - Level 3
              - Level 4
        - Back to level 1
        """
        expected_text = """
        * Main Slide

        - Level 1
          - Level 2
            - Level 3
              - Level 4

        - Back to level 1
        """
        self.helper(input_text, expected_text)

    def test8(self) -> None:
        """
        Test formatting slide with nested bullets and special formatting.
        """
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
        self.helper(input_text, expected_text)

    def test9(self) -> None:
        """
        This reproduces a broken behavior of prettier with fenced divs.
        """
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
        expected_text = r"""
        * Incremental vs Iterative
        ::: columns :::: {.column width=55%}

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
        :::: :::: {.column width=40%}
        ![](msml610/lectures_source/figures/Lesson02_Monalisa_incremental.png){width=90%}
        \small \_Incremental
        \vspace{0.5cm}
        ![](msml610/lectures_source/figures/Lesson02_Monalisa_iterative.png){width=90%}
        \small _Iterative_
        \vspace{0.5cm}
        ![](msml610/lectures_source/figures/Lesson02_Skateboard.png){width=90%}
        \small _Incremental vs Iterative_ :::: :::
        """
        self.helper(input_text, expected_text)


# #############################################################################
# Test_format_figures
# #############################################################################


class Test_format_figures(hunitest.TestCase):

    def helper(self, input_text: str, expected_text: str) -> None:
        # Prepare inputs.
        lines = hprint.dedent(input_text).strip().split("\n")
        # Run test.
        actual_lines = hmarform.format_figures(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        expected = hprint.dedent(expected_text).strip()
        self.assert_equal(actual, expected)

    def test_basic_text_with_figures(self) -> None:
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

    def test_no_figures_no_change(self) -> None:
        """
        Test that text without figures remains unchanged.
        """
        input_text = """
        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
        - **Columnar DBs**
          - E.g., Amazon Redshift, Snowflake
          - Better data compression
        """
        expected_text = """
        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
        - **Columnar DBs**
          - E.g., Amazon Redshift, Snowflake
          - Better data compression
        """
        self.helper(input_text, expected_text)

    def test_already_in_columns_format_no_change(self) -> None:
        """
        Test that text already in columns format remains unchanged.
        """
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
        self.helper(input_text, expected_text)

    def test_single_figure(self) -> None:
        """
        Test converting text with a single figure.
        """
        input_text = """
        - **Important concept**
          - This is the main point
          - Supporting detail

        ![](path/to/image.png)
        """
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
        self.helper(input_text, expected_text)

    def test_mixed_content_with_figures(self) -> None:
        """
        Test converting mixed content including text and figures.
        """
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
        self.helper(input_text, expected_text)

    def test_empty_input(self) -> None:
        """
        Test that empty input returns empty output.
        """
        input_text = ""
        expected_text = ""
        self.helper(input_text, expected_text)

    def test_with_slide_title(self) -> None:
        """
        Test that slide title is left unchanged.
        """
        input_text = """
        * VCS: How to Track Data

        - **Row-based DBs**
          - E.g., MySQL, Postgres
          - Optimized for reading / writing rows
          - Read / write small amounts of data frequently

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_1.png)

        ![](data605/lectures_source/images/lecture_2/lec_2_slide_47_image_2.png)
        """
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
        self.helper(input_text, expected_text)


# #############################################################################
# Test_format_links
# #############################################################################


class Test_format_links(hunitest.TestCase):

    def helper(self, input_text: str, expected_text: str) -> None:
        # Prepare inputs.
        lines = hprint.dedent(input_text).strip().split("\n")
        # Run test.
        actual_lines = hmarform.format_links(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        expected = hprint.dedent(expected_text).strip()
        self.assert_equal(actual, expected)

    def test_plain_url_conversion(self) -> None:
        """
        Test converting plain URLs to formatted links.
        """
        input_text = """
        Check out this tutorial:
        https://ubuntu.com/tutorials/command-line-for-beginners

        Another useful link:
        https://docs.python.org/3/
        """
        expected_text = r"""
        Check out this tutorial:
        [\textcolor{blue}{\underline{https://ubuntu.com/tutorials/command-line-for-beginners}}](https://ubuntu.com/tutorials/command-line-for-beginners)

        Another useful link:
        [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        """
        self.helper(input_text, expected_text)

    def test_backtick_url_conversion(self) -> None:
        """
        Test converting URLs in backticks to formatted links.
        """
        input_text = """
        Visit this site: `https://ubuntu.com/tutorials/command-line-for-beginners`

        Documentation: `https://docs.python.org/3/`
        """
        expected_text = r"""
        Visit this site: [\textcolor{blue}{\underline{https://ubuntu.com/tutorials/command-line-for-beginners}}](https://ubuntu.com/tutorials/command-line-for-beginners)

        Documentation: [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        """
        self.helper(input_text, expected_text)

    def test_fix_mismatched_formatted_links(self) -> None:
        """
        Test fixing formatted links where link text and URL don't match.
        """
        input_text = r"""
        Here's a link: [\textcolor{blue}{\underline{LINK1}}](https://example.com)

        Another: [\textcolor{blue}{\underline{Old Text}}](https://docs.python.org/3/)
        """
        expected_text = r"""
        Here's a link: [\textcolor{blue}{\underline{https://example.com}}](https://example.com)

        Another: [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        """
        self.helper(input_text, expected_text)

    def test_correctly_formatted_links_unchanged(self) -> None:
        """
        Test that correctly formatted links remain unchanged.
        """
        input_text = r"""
        Good link: [\textcolor{blue}{\underline{https://example.com}}](https://example.com)

        Another good link: [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        """
        expected_text = r"""
        Good link: [\textcolor{blue}{\underline{https://example.com}}](https://example.com)

        Another good link: [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        """
        self.helper(input_text, expected_text)

    def test_mixed_links_in_content(self) -> None:
        """
        Test handling mixed plain and formatted links in same content.
        """
        input_text = r"""
        ## Resources

        - Plain URL: https://ubuntu.com/tutorials/command-line-for-beginners
        - Backtick URL: `https://docs.python.org/3/`
        - Mismatched formatted: [\textcolor{blue}{\underline{Click here}}](https://github.com)
        - Correct formatted: [\textcolor{blue}{\underline{https://stackoverflow.com}}](https://stackoverflow.com)
        """
        expected_text = r"""
        ## Resources

        - Plain URL: [\textcolor{blue}{\underline{https://ubuntu.com/tutorials/command-line-for-beginners}}](https://ubuntu.com/tutorials/command-line-for-beginners)
        - Backtick URL: [\textcolor{blue}{\underline{https://docs.python.org/3/}}](https://docs.python.org/3/)
        - Mismatched formatted: [\textcolor{blue}{\underline{https://github.com}}](https://github.com)
        - Correct formatted: [\textcolor{blue}{\underline{https://stackoverflow.com}}](https://stackoverflow.com)
        """
        self.helper(input_text, expected_text)

    def test_no_links_no_change(self) -> None:
        """
        Test that content without links remains unchanged.
        """
        input_text = """
        # Important Notes

        - This is regular text
        - No links here
        - Just plain content

        ## Section 2

        More regular text without any URLs.
        """
        expected_text = """
        # Important Notes

        - This is regular text
        - No links here
        - Just plain content

        ## Section 2

        More regular text without any URLs.
        """
        self.helper(input_text, expected_text)

    def test_empty_input(self) -> None:
        """
        Test that empty input returns empty output.
        """
        input_text = ""
        expected_text = ""
        self.helper(input_text, expected_text)

    def test_http_and_https_urls(self) -> None:
        """
        Test handling both HTTP and HTTPS URLs.
        """
        input_text = """
        HTTP site: http://example.com
        HTTPS site: https://secure.example.com
        """
        expected_text = r"""
        HTTP site: [\textcolor{blue}{\underline{http://example.com}}](http://example.com)
        HTTPS site: [\textcolor{blue}{\underline{https://secure.example.com}}](https://secure.example.com)
        """
        self.helper(input_text, expected_text)
