import logging
import os
import pprint
from typing import Any, Dict, List, Tuple, cast

import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _to_header_list(data: List[Tuple[int, str]]) -> hmarkdo.HeaderList:
    res = [
        hmarkdo.HeaderInfo(level, text, 5 * i + 1)
        for i, (level, text) in enumerate(data)
    ]
    return res


def get_header_list1() -> hmarkdo.HeaderList:
    data = [
        (1, "Chapter 1"),
        (2, "Section 1.1"),
        (3, "Subsection 1.1.1"),
        (3, "Subsection 1.1.2"),
        (2, "Section 1.2"),
        (1, "Chapter 2"),
        (2, "Section 2.1"),
        (3, "Subsection 2.1.1"),
        (2, "Section 2.2"),
    ]
    header_list = _to_header_list(data)
    return header_list


def get_header_list2() -> hmarkdo.HeaderList:
    data = [
        (1, "Module Alpha"),
        (2, "Lesson Alpha-1"),
        (3, "Topic Alpha-1.a"),
        (3, "Topic Alpha-1.b"),
        (2, "Lesson Alpha-2"),
        (3, "Topic Alpha-2.a"),
        (1, "Module Beta"),
        (2, "Lesson Beta-1"),
        (3, "Topic Beta-1.a"),
        (2, "Lesson Beta-2"),
        (1, "Module Gamma"),
        (2, "Lesson Gamma-1"),
        (3, "Topic Gamma-1.a"),
        (3, "Topic Gamma-1.b"),
    ]
    header_list = _to_header_list(data)
    return header_list


def get_header_list3() -> hmarkdo.HeaderList:
    data = [
        (1, "Topic A"),
        (2, "Subtopic A.1"),
        (3, "Detail A.1.i"),
        (3, "Detail A.1.ii"),
        (2, "Subtopic A.2"),
        (1, "Topic B"),
        (2, "Subtopic B.1"),
        (3, "Detail B.1.i"),
        (2, "Subtopic B.2"),
        (3, "Detail B.2.i"),
        (3, "Detail B.2.ii"),
        (2, "Subtopic B.3"),
        (1, "Topic C"),
        (2, "Subtopic C.1"),
        (3, "Detail C.1.i"),
    ]
    header_list = _to_header_list(data)
    return header_list


def get_header_list4() -> hmarkdo.HeaderList:
    data = [
        (1, "Chapter 1"),
        (3, "Subsection 1.1.1"),
    ]
    header_list = _to_header_list(data)
    return header_list


def get_header_list5() -> hmarkdo.HeaderList:
    data = [
        (1, "Chapter 1"),
        (2, "Section 1.1"),
        (3, "Subsection 1.1.1"),
        (1, "Chapter 2"),
    ]
    header_list = _to_header_list(data)
    return header_list


# #############################################################################
# Test_header_list_to_vim_cfile1
# #############################################################################


class Test_header_list_to_vim_cfile1(hunitest.TestCase):
    def test_get_header_list1(self) -> None:
        # Prepare inputs.
        markdown_file = "test.py"
        headers = get_header_list1()
        # Call function.
        act = hmarkdo.header_list_to_vim_cfile(markdown_file, headers)
        # Check output.
        exp = r"""
        test.py:1:Chapter 1
        test.py:6:Section 1.1
        test.py:11:Subsection 1.1.1
        test.py:16:Subsection 1.1.2
        test.py:21:Section 1.2
        test.py:26:Chapter 2
        test.py:31:Section 2.1
        test.py:36:Subsection 2.1.1
        test.py:41:Section 2.2
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_header_list_to_markdown1
# #############################################################################


class Test_header_list_to_markdown1(hunitest.TestCase):
    def test_mode_list1(self) -> None:
        # Prepare inputs.
        headers = get_header_list1()
        mode = "list"
        # Call function.
        act = hmarkdo.header_list_to_markdown(headers, mode)
        # Check output.
        exp = r"""
        - Chapter 1
          - Section 1.1
            - Subsection 1.1.1
            - Subsection 1.1.2
          - Section 1.2
        - Chapter 2
          - Section 2.1
            - Subsection 2.1.1
          - Section 2.2
        """
        self.assert_equal(act, exp, dedent=True)

    def test_mode_headers1(self) -> None:
        # Prepare inputs.
        headers = get_header_list1()
        mode = "headers"
        # Call function.
        act = hmarkdo.header_list_to_markdown(headers, mode)
        # Check output.
        exp = r"""
        # Chapter 1
        ## Section 1.1
        ### Subsection 1.1.1
        ### Subsection 1.1.2
        ## Section 1.2
        # Chapter 2
        ## Section 2.1
        ### Subsection 2.1.1
        ## Section 2.2
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_replace_fenced_blocks_with_tags1
# #############################################################################


class Test_replace_fenced_blocks_with_tags1(hunitest.TestCase):
    def helper(
        self, text: str, expected_lines: List[str], expected_map: Dict[str, str]
    ) -> None:
        """
        Test replacing fenced code blocks with tags.
        """
        lines = hprint.dedent(text, remove_lead_trail_empty_lines_=True)
        lines = lines.split("\n")
        # Call function.
        actual_lines, fence_map = hmarkdo.replace_fenced_blocks_with_tags(lines)
        # Check output.
        fence_map_as_str = pprint.pformat(fence_map)
        expected_map_as_str = pprint.pformat(expected_map)
        self.assert_equal(fence_map_as_str, expected_map_as_str)
        #
        actual_lines = "\n".join(actual_lines)
        expected_lines = hprint.dedent(
            expected_lines, remove_lead_trail_empty_lines_=True
        )
        self.assert_equal(actual_lines, expected_lines)

    def helper_round_trip(self, text: str) -> None:
        """
        Test the round trip.
        """
        # Do the round trip.
        lines = text.split("\n")
        actual_lines, fence_map = hmarkdo.replace_fenced_blocks_with_tags(lines)
        act_text = hmarkdo.replace_tags_with_fenced_blocks(
            actual_lines, fence_map
        )
        # Check output.
        act_text = "\n".join(act_text)
        self.assert_equal(act_text, text)

    def test1(self) -> None:
        """
        Test replacing fenced code blocks with tags.
        """
        # Prepare inputs.
        text = """
        Some text before
        ```python
        def foo():
            return 42
        ```
        Text between blocks
        ````
        Plain code block
        ````
        Some text after
        """
        # Prepare outputs.
        expected_lines = """
        Some text before
        <fenced_block1>
        Text between blocks
        <fenced_block2>
        Some text after
        """
        # Check fence map.
        expected_map = {
            "1": "```python\ndef foo():\n    return 42\n```",
            "2": "````\nPlain code block\n````",
        }
        self.helper(text, expected_lines, expected_map)

    def test2(self) -> None:
        """
        Test nested fenced blocks.
        """
        text = """
        ````
        Outer block
        ```python
        def nested():
            pass
        ```
        Still outer
        ````
        """
        expected_lines = """
        <fenced_block1>
        """
        expected_map = {
            "1": "````\nOuter block\n```python\ndef nested():\n    pass\n```\nStill outer\n````"
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test3(self) -> None:
        """
        Test empty fenced blocks.
        """
        text = """
        Before
        ```
        ```
        After
        ```python
        ```
        End
        """
        expected_lines = """
        Before
        <fenced_block1>
        After
        <fenced_block2>
        End
        """
        expected_map = {"1": "```\n```", "2": "```python\n```"}
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test4(self) -> None:
        """
        Test blocks with different fence lengths.
        """
        text = """
        Start
        ```
        Three
        ```
        Middle
        `````
        Five
        `````
        End
        """
        expected_lines = """
        Start
        <fenced_block1>
        Middle
        <fenced_block2>
        End
        """
        expected_map = {"1": "```\nThree\n```", "2": "`````\nFive\n`````"}
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test5(self) -> None:
        """
        Test blocks with language specifiers.
        """
        text = """
        ```python
        def foo(): pass
        ```
        ```bash
        echo hello
        ```
        ```javascript
        console.log('hi');
        ```
        """
        expected_lines = """
        <fenced_block1>
        <fenced_block2>
        <fenced_block3>
        """
        expected_map = {
            "1": "```python\ndef foo(): pass\n```",
            "2": "```bash\necho hello\n```",
            "3": "```javascript\nconsole.log('hi');\n```",
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test6(self) -> None:
        """
        Test blocks with indentation.
        """
        text = """
        Outside
         ```
         Indented block
          More indent
         ```
           ```python
           def foo():
               pass
           ```
        End
        """
        expected_lines = """
        Outside
        <fenced_block1>
        <fenced_block2>
        End
        """
        expected_map = {
            "1": " ```\n Indented block\n  More indent\n ```",
            "2": "   ```python\n   def foo():\n       pass\n   ```",
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)


# #############################################################################
# Test_colorize_bullet_points1
# #############################################################################


class Test_colorize_bullet_points_in_slide1(hunitest.TestCase):
    def test1(self) -> None:
        text = """
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
        expected = """
        * Machine Learning Flow

        ::: columns
        :::: {.column width=90%}
        - Question
        - E.g., "How can we predict house prices?"
        - Input data
        - E.g., historical data of house sales

        - _"If I were given one hour to save the planet, I would spend 59 minutes
        defining the problem and one minute resolving it"_ (Albert Einstein)

        - **\\red{Not all phases are equally important!}**
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
        act = hmarkdo.colorize_bullet_points_in_slide(text)
        # Check output.
        self.assert_equal(act, expected)


# #############################################################################
# Test_SlideProcessor1
# #############################################################################


class Test_process_slides(hunitest.TestCase):

    @staticmethod
    def _transform(slide_text: List[str]) -> str:
        """
        Add a @ to the beginning of each line of the slide.
        """
        # Print input.
        _LOG.debug("input=\n%s", "\n".join(slide_text))
        # Transform.
        text_out = [f"@{line}" for line in slide_text]
        # Print output.
        _LOG.debug("output=\n%s", "\n".join(text_out))
        return text_out

    def helper(self, text: str, expected: str) -> None:
        # Prepare inputs.
        text = hprint.dedent(text, remove_lead_trail_empty_lines_=False)
        # Process.
        actual = hmarkdo.process_slides(text, self._transform)
        # Check output.
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=False)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test multiple slides.
        """
        text = """
        * Slide 1
            - Point 1
            - Point 2

        * Slide 2
            - Point A 
            - Point B
        """
        expected = """
        @* Slide 1
        @    - Point 1
        @    - Point 2
        @
        @* Slide 2
        @    - Point A
        @    - Point B
        """
        self.helper(text, expected)

    def test2(self) -> None:
        """
        Test single line slide.
        """
        text = """
        * Single line slide
        """
        expected = """
        @* Single line slide
        """
        self.helper(text, expected)

    def test3(self) -> None:
        """
        Test slide with inline comment.
        """
        text = """
        * Slide with comment
            # This is a comment
            - Point 1
        """
        expected = """
        @* Slide with comment
        @    # This is a comment
        @    - Point 1
        """
        self.helper(text, expected)

    def test4(self) -> None:
        """
        Test slide with comment block.
        """
        text = """
        * Slide with block
            <!--
            This is a comment block
            spanning multiple lines
            -->
            - Point 1
        """
        expected = """
        @* Slide with block
        @    <!--
        @    This is a comment block
        @    spanning multiple lines
        @    -->
        @    - Point 1
        """
        self.helper(text, expected)

    def test5(self) -> None:
        text = """
        * Slide 1
        * Slide 2
        """
        expected = """
        @* Slide 1
        @* Slide 2
        """
        self.helper(text, expected)

    def test6(self) -> None:
        text = """

        * Slide 1
        * Slide 2
        """
        expected = """

        @* Slide 1
        @* Slide 2
        """
        self.helper(text, expected)

    def test7(self) -> None:
        text = """

        * Slide 1
        * Slide 2

        """
        expected = """

        @* Slide 1
        @* Slide 2
        @
        """
        self.helper(text, expected)

    def test8(self) -> None:
        text = """
        //* Slide 1
        * Slide 2

        """
        expected = """
        //* Slide 1
        @* Slide 2
        @
        """
        self.helper(text, expected)


# #############################################################################
# Test_is_markdown_line_separator1
# #############################################################################


class Test_is_markdown_line_separator1(hunitest.TestCase):
    def test_valid_separator1(self) -> None:
        # Prepare inputs.
        line = "-----------------------"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = True
        self.assertEqual(act, exp)

    def test_valid_separator2(self) -> None:
        # Prepare inputs.
        line = "# ------"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = True
        self.assertEqual(act, exp)

    def test_valid_separator3(self) -> None:
        # Prepare inputs.
        line = "# #########"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = True
        self.assertEqual(act, exp)

    def test_valid_separator4(self) -> None:
        # Prepare inputs.
        line = "### ====="
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = True
        self.assertEqual(act, exp)

    def test_valid_separator5(self) -> None:
        # Prepare inputs.
        line = "#//////"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = True
        self.assertEqual(act, exp)

    def test_valid_separator6(self) -> None:
        # Prepare inputs.
        line = "#  //////"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = True
        self.assertEqual(act, exp)

    def test_invalid_separator1(self) -> None:
        # Prepare inputs.
        line = "Not a separator"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = False
        self.assertEqual(act, exp)

    def test_invalid_separator2(self) -> None:
        # Prepare inputs.
        line = "# --"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = False
        self.assertEqual(act, exp)

    def test_invalid_separator3(self) -> None:
        # Prepare inputs.
        line = "# ###---"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = False
        self.assertEqual(act, exp)

    def test_invalid_separator4(self) -> None:
        # Prepare inputs.
        line = "=="
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = False
        self.assertEqual(act, exp)

    def test_invalid_separator5(self) -> None:
        # Prepare inputs.
        line = "- //////"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = False
        self.assertEqual(act, exp)

    def test_invalid_separator6(self) -> None:
        # Prepare inputs.
        line = "=== Not a seperator"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = False
        self.assertEqual(act, exp)

    def test_invalid_separator7(self) -> None:
        # Prepare inputs.
        line = "--- Not a seperator ---"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = False
        self.assertEqual(act, exp)


# #############################################################################
# Test_extract_section_from_markdown1
# #############################################################################


def _get_markdown_example1() -> str:
    content = r"""
    # Header1
    Content under header 1.
    ## Header2
    Content under subheader 2.
    # Header3
    Content under header 3.
    """
    content = hprint.dedent(content)
    content = cast(str, content)
    return content


def _get_markdown_example2() -> str:
    content = r"""
    # Header1
    Content under header 1.
    ## Header2
    Content under subheader 2.
    """
    content = hprint.dedent(content)
    content = cast(str, content)
    return content


def _get_markdown_no_header_example1() -> str:
    content = r"""
    This is some content without any headers.
    """
    content = hprint.dedent(content)
    content = cast(str, content)
    return content


def _get_markdown_example4() -> str:
    content = r"""
    # Chapter 1

    Welcome to the first chapter. This chapter introduces fundamental concepts and
    lays the groundwork for further exploration.

    ## Section 1.1

    This section discusses the initial principles and key ideas that are crucial for
    understanding the topic.

    ### Subsection 1.1.1

    The first subsection dives deeper into the details, providing examples and
    insights that help clarify the concepts.

    Example:
    ```python
    def greet(name):
        return f"Hello, {name}!"
    print(greet("World"))
    ```

    ### Subsection 1.1.2

    Here, we examine alternative perspectives and additional considerations that
    were not covered in the previous subsection.

    - Key Point 1: Understanding different viewpoints enhances comprehension.
    - Key Point 2: Practical application reinforces learning.

    ## Section 1.2

    This section introduces new frameworks and methodologies that build upon the
    foundation established earlier.

    > "Knowledge is like a tree, growing stronger with each branch of understanding."

    # Chapter 2

    Moving forward, this chapter explores advanced topics and real-world
    applications.

    ## Section 2.1

    This section provides an in-depth analysis of core mechanisms that drive the
    subject matter.

    ### Subsection 2.1.1

    A deep dive into specific case studies and empirical evidence that support
    theoretical claims.

    - Case Study 1: Implementation in modern industry
    - Case Study 2: Comparative analysis of traditional vs. modern methods

    ## Section 2.2

    The final section of this chapter presents summary conclusions, key takeaways,
    and potential future developments.

    ```yaml
    future:
    - AI integration
    - Process optimization
    - Sustainable solutions
    ```

    Stay curious and keep exploring!
    """
    content = hprint.dedent(content)
    content = cast(str, content)
    return content


def _get_markdown_example5() -> hmarkdo.HeaderList:
    content = r"""
    # Models
    test
    ## Naive Bayes
    test2
    ## Decision trees
    test3
    ## Random forests
    ## Linear models
    """
    content = hprint.dedent(content)
    content = cast(str, content)
    return content


def _get_markdown_slides_example1() -> str:
    content = r"""
    # Header1

    * Slide 1
    Content 1.

    ## Header2

    * Slide 2
    Content 2.

    * Slide 3
    Content 3.
    """
    content = hprint.dedent(content)
    content = cast(str, content)
    return content


def _get_markdown_slides_example2() -> str:
    content = r"""
    # Header1

    * Slide1
    Content 1.
    """
    content = hprint.dedent(content)
    content = cast(str, content)
    return content


# #############################################################################
# Test_extract_section_from_markdown1
# #############################################################################


class Test_extract_section_from_markdown1(hunitest.TestCase):
    # TODO(gp): This doesn't seem correct.
    def test1(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example1()
        # Call functions.
        act = hmarkdo.extract_section_from_markdown(content, "Header1")
        # Check output.
        exp = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under subheader 2.
        """
        self.assert_equal(act, exp, dedent=True)

    def test2(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example1()
        content = hprint.dedent(content)
        # Call functions.
        act = hmarkdo.extract_section_from_markdown(content, "Header2")
        # Check output.
        exp = r"""
        ## Header2
        Content under subheader 2.
        """
        self.assert_equal(act, exp, dedent=True)

    def test3(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example1()
        content = hprint.dedent(content)
        # Call tested function.
        act = hmarkdo.extract_section_from_markdown(content, "Header3")
        # Check output.
        exp = r"""
        # Header3
        Content under header 3.
        """
        self.assert_equal(act, exp, dedent=True)

    def test4(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example2()
        # Call function.
        act = hmarkdo.extract_section_from_markdown(content, "Header1")
        # Check output.
        exp = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under subheader 2.
        """
        self.assert_equal(act, exp, dedent=True)

    def test_no_header(self) -> None:
        # Prepare inputs.
        content = _get_markdown_no_header_example1()
        # Call tested function.
        with self.assertRaises(ValueError) as fail:
            hmarkdo.extract_section_from_markdown(content, "Header4")
        # Check output.
        actual = str(fail.exception)
        expected = r"Header 'Header4' not found"
        self.assert_equal(actual, expected)


# #############################################################################
# Test_extract_headers_from_markdown1
# #############################################################################


class Test_extract_headers_from_markdown1(hunitest.TestCase):
    def test_multiple_headers(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example1()
        # Call function.
        act = hmarkdo.extract_headers_from_markdown(content, max_level=3)
        # Check output.
        exp = r"""[HeaderInfo(1, 'Header1', 1), HeaderInfo(2, 'Header2', 3), HeaderInfo(1, 'Header3', 5)]"""
        self.assert_equal(str(act), exp)

    def test_single_header(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example2()
        # Call function.
        act = hmarkdo.extract_headers_from_markdown(content, max_level=3)
        # Check output.
        exp = r"""[HeaderInfo(1, 'Header1', 1), HeaderInfo(2, 'Header2', 3)]"""
        self.assert_equal(str(act), exp)

    def test_no_headers(self) -> None:
        # Prepare inputs.
        content = r"""
        This is some content without any headers.
        """
        content = hprint.dedent(content)
        # Call function.
        act = hmarkdo.extract_headers_from_markdown(content, max_level=3)
        # Check output.
        exp: List[str] = []
        self.assert_equal(str(act), str(exp))


# #############################################################################
# Test_extract_slides_from_markdown1
# #############################################################################


class Test_extract_slides_from_markdown1(hunitest.TestCase):
    def test_multiple_slides(self) -> None:
        # Prepare inputs.
        content = _get_markdown_slides_example1()
        # Call function.
        act = hmarkdo.extract_slides_from_markdown(content)
        # Check output.
        exp = r"""([HeaderInfo(1, 'Slide 1', 3), HeaderInfo(1, 'Slide 2', 8), HeaderInfo(1, 'Slide 3', 11)], 12)"""
        self.assert_equal(str(act), exp)

    def test_single_slides(self) -> None:
        # Prepare inputs.
        content = _get_markdown_slides_example2()
        # Call function.
        act = hmarkdo.extract_slides_from_markdown(content)
        # Check output.
        exp = r"""([HeaderInfo(1, 'Slide1', 3)], 4)"""
        self.assert_equal(str(act), exp)

    def test_no_slides(self) -> None:
        # Prepare inputs.
        content = _get_markdown_no_header_example1()
        # Call function.
        act = hmarkdo.extract_slides_from_markdown(content)
        # Check output.
        exp = r"""([], 1)"""
        self.assert_equal(str(act), exp)


# #############################################################################
# Test_remove_end_of_line_periods1
# #############################################################################


class Test_remove_end_of_line_periods1(hunitest.TestCase):
    def test_standard_case(self) -> None:
        txt = "Hello.\nWorld.\nThis is a test."
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = "Hello\nWorld\nThis is a test"
        self.assertEqual(act, exp)

    def test_no_periods(self) -> None:
        txt = "Hello\nWorld\nThis is a test"
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = "Hello\nWorld\nThis is a test"
        self.assertEqual(act, exp)

    def test_multiple_periods(self) -> None:
        txt = "Line 1.....\nLine 2.....\nEnd."
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = "Line 1\nLine 2\nEnd"
        self.assertEqual(act, exp)

    def test_empty_string(self) -> None:
        txt = ""
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = ""
        self.assertEqual(act, exp)

    def test_leading_and_trailing_periods(self) -> None:
        txt = ".Line 1.\n.Line 2.\n..End.."
        act = hmarkdo.remove_end_of_line_periods(txt)
        exp = ".Line 1\n.Line 2\n..End"
        self.assertEqual(act, exp)


# #############################################################################
# Test_process_code_block1
# #############################################################################


class Test_process_code_block1(hunitest.TestCase):
    def helper_process_code_block(self, txt: str) -> str:
        out: List[str] = []
        in_code_block = False
        lines = txt.split("\n")
        for i, line in enumerate(lines):
            _LOG.debug("%s:line=%s", i, line)
            # Process the code block.
            do_continue, in_code_block, out_tmp = hmarkdo.process_code_block(
                line, in_code_block, i, lines
            )
            out.extend(out_tmp)
            if do_continue:
                continue
            #
            out.append(line)
        return "\n".join(out)

    def test1(self) -> None:
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        txt_in = hio.from_file(input_file_path)
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        act = self.helper_process_code_block(txt_in)
        self.check_string(act, dedent=True, remove_lead_trail_empty_lines=True)


# #############################################################################
# Test_selected_navigation_to_str1
# #############################################################################


def _test_navigation_flow(
    self_: Any,
    txt: str,
    header_list_exp: str,
    header_tree_exp: str,
    level: int,
    description: str,
    nav_str_exp: str,
) -> None:
    # 1) Extract headers.
    header_list = hmarkdo.extract_headers_from_markdown(txt, max_level=3)
    act = pprint.pformat(header_list)
    self_.assert_equal(
        act, header_list_exp, dedent=True, remove_lead_trail_empty_lines=True
    )
    # 2) Build header tree.
    tree = hmarkdo.build_header_tree(header_list)
    act = hmarkdo.header_tree_to_str(tree, ancestry=None)
    self_.assert_equal(
        act, header_tree_exp, dedent=True, remove_lead_trail_empty_lines=True
    )
    # 3) Compute the navigation bar for a specific header.
    act = hmarkdo.selected_navigation_to_str(tree, level, description)
    self_.assert_equal(
        act, nav_str_exp, dedent=True, remove_lead_trail_empty_lines=True
    )


def _test_full_navigation_flow(self_: Any, txt: str) -> None:
    res: List[str] = []
    # Extract headers.
    header_list = hmarkdo.extract_headers_from_markdown(txt, max_level=3)
    # Build header tree.
    tree = hmarkdo.build_header_tree(header_list)
    # Create a navigation map for any header.
    for node in header_list:
        level, description, _ = node.as_tuple()
        res_tmp = hprint.frame(hprint.to_str("level description"))
        res.append(res_tmp)
        #
        res_tmp = hmarkdo.selected_navigation_to_str(tree, level, description)
        res.append(res_tmp)
    # Check.
    act = "\n".join(res)
    self_.check_string(act)


# #############################################################################
# Test_selected_navigation_to_str1
# #############################################################################


class Test_selected_navigation_to_str1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Create navigation bar from Markdown text `_get_markdown_example4()`.
        """
        txt = _get_markdown_example4()
        header_list_exp = """
        [HeaderInfo(1, 'Chapter 1', 1),
         HeaderInfo(2, 'Section 1.1', 6),
         HeaderInfo(3, 'Subsection 1.1.1', 11),
         HeaderInfo(3, 'Subsection 1.1.2', 23),
         HeaderInfo(2, 'Section 1.2', 31),
         HeaderInfo(1, 'Chapter 2', 38),
         HeaderInfo(2, 'Section 2.1', 43),
         HeaderInfo(3, 'Subsection 2.1.1', 48),
         HeaderInfo(2, 'Section 2.2', 56)]
        """
        header_tree_exp = """
        - Chapter 1
        - Chapter 2
        """
        level = 3
        description = "Subsection 1.1.2"
        nav_str_exp = """
        - Chapter 1
          - Section 1.1
            - Subsection 1.1.1
            - **Subsection 1.1.2**
          - Section 1.2
        - Chapter 2
        """
        _test_navigation_flow(
            self,
            txt,
            header_list_exp,
            header_tree_exp,
            level,
            description,
            nav_str_exp,
        )

    def test2(self) -> None:
        txt = _get_markdown_example4()
        _test_full_navigation_flow(self, txt)


# #############################################################################
# Test_selected_navigation_to_str2
# #############################################################################


class Test_selected_navigation_to_str2(hunitest.TestCase):
    def test1(self) -> None:
        """
        Create navigation bar from Markdown text `_get_markdown_example5()`.
        """
        txt = _get_markdown_example5()
        header_list_exp = r"""
        [HeaderInfo(1, 'Models', 1),
         HeaderInfo(2, 'Naive Bayes', 3),
         HeaderInfo(2, 'Decision trees', 5),
         HeaderInfo(2, 'Random forests', 7),
         HeaderInfo(2, 'Linear models', 8)]
        """
        header_tree_exp = """
        - Models
        """
        level = 2
        description = "Decision trees"
        nav_str_exp = """
        - Models
          - Naive Bayes
          - **Decision trees**
          - Random forests
          - Linear models
        """
        _test_navigation_flow(
            self,
            txt,
            header_list_exp,
            header_tree_exp,
            level,
            description,
            nav_str_exp,
        )

    def test2(self) -> None:
        txt = _get_markdown_example5()
        _test_full_navigation_flow(self, txt)


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
        act = hmarkdo.md_clean_up(txt)
        act = hprint.dedent(act)
        exp = r"""
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
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_modify_header_level1
# #############################################################################


class Test_modify_header_level1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test the inputs to increase headings.
        """
        # Prepare inputs and outputs.
        input_lines = [
            "# Chapter 1",
            "## Section 1.1",
            "### Subsection 1.1.1",
            "#### Sub-subsection 1.1.1.1",
        ]
        level = 1
        expected_lines = [
            "## Chapter 1",
            "### Section 1.1",
            "#### Subsection 1.1.1",
            "##### Sub-subsection 1.1.1.1",
        ]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test2(self) -> None:
        """
        Test inputs to increase headings with level 5 becoming level 6.
        """
        # Prepare inputs and outputs.
        input_lines = ["# Chapter 1", "##### Sub-sub-subsection 1.1.1.1.1"]
        level = 1
        expected_lines = ["## Chapter 1", "###### Sub-sub-subsection 1.1.1.1.1"]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test3(self) -> None:
        """
        Test inputs to increase headings including a paragraph which remains
        unchanged.
        """
        # Prepare inputs and outputs.
        input_lines = ["# Chapter 1", "Paragraph 1"]
        level = 1
        expected_lines = ["## Chapter 1", "Paragraph 1"]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test4(self) -> None:
        """
        Test inputs of paragraphs which remain unchanged.
        """
        # Prepare inputs and outputs.
        input_lines = ["Paragraph 1", "Paragraph 2"]
        level = 1
        expected_lines = ["Paragraph 1", "Paragraph 2"]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test5(self) -> None:
        """
        Test to increase headings with mixed levels.
        """
        # Prepare inputs and outputs.
        input_lines = [
            "# Chapter 1",
            "##### Sub-sub-subsection 1.1.1.1.1",
            "# Chapter 2",
            "### Subsection 2.1",
            "# Chapter 3",
        ]
        level = 1
        expected_lines = [
            "## Chapter 1",
            "###### Sub-sub-subsection 1.1.1.1.1",
            "## Chapter 2",
            "#### Subsection 2.1",
            "## Chapter 3",
        ]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test6(self) -> None:
        """
        Test the inputs to decrease headings.
        """
        # Prepare inputs and outputs.
        input_lines = [
            "## Section 1.1",
            "### Subsection 1.1.1",
            "#### Sub-subsection 1.1.1.1",
            "##### Sub-sub-subsection 1.1.1.1.1",
        ]
        level = -1
        expected_lines = [
            "# Section 1.1",
            "## Subsection 1.1.1",
            "### Sub-subsection 1.1.1.1",
            "#### Sub-sub-subsection 1.1.1.1.1",
        ]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test7(self) -> None:
        """
        Test inputs to decrease headings by one level.
        """
        # Prepare inputs and outputs.
        input_lines = [
            "## Chapter 1",
            "##### Sub-subsection 1.1.1.1",
        ]
        level = -1
        expected_lines = [
            "# Chapter 1",
            "#### Sub-subsection 1.1.1.1",
        ]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test8(self) -> None:
        """
        Test inputs of paragraphs which remain unchanged.
        """
        # Prepare inputs and outputs.
        input_lines = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
        level = -1
        expected_lines = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test9(self) -> None:
        """
        Test increasing headers by 2 levels.
        """
        # Prepare inputs and outputs.
        input_lines = [
            "# Chapter 1",
            "## Section 1.1",
            "### Subsection 1.1.1",
        ]
        level = 2
        expected_lines = [
            "### Chapter 1",
            "#### Section 1.1",
            "##### Subsection 1.1.1",
        ]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test10(self) -> None:
        """
        Test decreasing headers by 2 levels.
        """
        # Prepare inputs and outputs.
        input_lines = [
            "### Chapter 1",
            "#### Section 1.1",
            "##### Subsection 1.1.1",
        ]
        level = -2
        expected_lines = [
            "# Chapter 1",  # 3-2=1
            "## Section 1.1",  # 4-2=2
            "### Subsection 1.1.1",  # 5-2=3
        ]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def test11(self) -> None:
        """
        Test increasing headers by 2 levels.
        """
        # Prepare inputs and outputs.
        input_lines = [
            "### Level 3",
            "#### Level 4",
        ]
        level = 2
        expected_lines = [
            "##### Level 3",  # 3+2=5
            "###### Level 4",  # 4+2=6
        ]
        # Call the helper.
        self._helper(input_lines, level, expected_lines)

    def _helper(
        self, input_lines: List[str], level: int, expected_lines: List[str]
    ) -> None:
        """
        Helper method to test `modify_header_level` function.

        :param input_lines: list of input text lines
        :param level: level adjustment to apply
        :param expected_lines: list of expected output lines
        """
        # Prepare inputs.
        input_text = "\n".join(input_lines)
        # Call tested function.
        actual = hmarkdo.modify_header_level(input_text, level)
        # Check output.
        expected = "\n".join(expected_lines)
        self.assertEqual(actual, expected)


# #############################################################################
# Test_format_headers1
# #############################################################################


class Test_format_headers1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test the inputs to check the basic formatting of headings.
        """
        input_text = [
            "# Chapter 1",
            "section text",
        ]
        expected = [
            "# #############################################################################",
            "# Chapter 1",
            "# #############################################################################",
            "section text",
        ]
        self._helper_process(input_text, expected, max_lev=1)

    def test2(self) -> None:
        """
        Test inputs with headings beyond the maximum level to ensure they are
        ignored during formatting.
        """
        input_text = [
            "# Chapter 1",
            "## Section 1.1",
            "### Section 1.1.1",
        ]
        expected = [
            "# #############################################################################",
            "# Chapter 1",
            "# #############################################################################",
            "## ############################################################################",
            "## Section 1.1",
            "## ############################################################################",
            "### Section 1.1.1",
        ]
        self._helper_process(input_text, expected, max_lev=2)

    def test3(self) -> None:
        """
        Test the inputs to check that markdown line separators are removed.
        """
        input_text = [
            "# Chapter 1",
            "-----------------",
            "Text",
            "############",
        ]
        expected = [
            "# #############################################################################",
            "# Chapter 1",
            "# #############################################################################",
            "Text",
        ]
        self._helper_process(input_text, expected, max_lev=1)

    def test4(self) -> None:
        """
        Test inputs where max_level is inferred from the file content.
        """
        input_text = [
            "# Chapter 1",
            "max_level=1",
            "## Section 1.1",
        ]
        expected = [
            "# #############################################################################",
            "# Chapter 1",
            "# #############################################################################",
            "max_level=1",
            "## Section 1.1",
        ]
        self._helper_process(input_text, expected, max_lev=2)

    def test5(self) -> None:
        """
        Test inputs with no headers to ensure they remain unchanged.
        """
        input_text = [
            "Only text",
            "No headings",
        ]
        expected = [
            "Only text",
            "No headings",
        ]
        self._helper_process(input_text, expected, max_lev=3)

    def _helper_process(
        self, input_text: List[str], expected: List[str], max_lev: int
    ) -> None:
        """
        Process the given text with a specified maximum level and compare the
        result with the expected output.

        :param input_text: the text to be processed
        :param expected: the expected output after processing the text
        :param max_lev: the maximum heading level to be formatted
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hio.to_file(read_file, "\n".join(input_text))
        # Call tested function.
        hmarkdo.format_headers(read_file, write_file, max_lev=max_lev)
        # Check output.
        actual = hio.from_file(write_file)
        self.assertEqual(actual, "\n".join(expected))


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
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        def hello_world():
            print("Hello, World!")
        """
        self.assert_equal(str(act), exp, dedent=True)

    def test2(self) -> None:
        """
        Test an example with empty lines at the start and end.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        def check_empty_lines():
            print("Check empty lines are present!")
        """
        self.assert_equal(str(act), exp, dedent=True)

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
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
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
        self.assert_equal(str(act), exp, dedent=True)

    def test4(self) -> None:
        """
        Test another markdown with headings and multiple indent Python blocks.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        content = hprint.dedent(content)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        self.check_string(act, dedent=True)

    def test5(self) -> None:
        """
        Test an empty string.
        """
        # Prepare inputs.
        content = ""
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = ""
        self.assert_equal(str(act), exp, dedent=True)

    def test6(self) -> None:
        """
        Test a Python and immediate markdown code block.
        """
        # Prepare inputs.
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        content = hio.from_file(input_file_path)
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        def no_start_python():
            print("No mention of python at the start")



            A markdown paragraph contains
            delimiters that needs to be removed.
        """
        self.assert_equal(str(act), exp, dedent=True)


# #############################################################################
# Test_sanity_check_header_list1
# #############################################################################


class Test_sanity_check_header_list1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the header list with valid level increase is accepted.
        """
        # Prepare inputs.
        header_list = get_header_list1()
        # Call function.
        hmarkdo.sanity_check_header_list(header_list)

    def test2(self) -> None:
        """
        Test that the header list with an increase of more than one level
        raises an error.
        """
        # Prepare inputs.
        header_list = get_header_list4()
        # Call function.
        with self.assertRaises(ValueError) as err:
            hmarkdo.sanity_check_header_list(header_list)
        # Check output.
        actual = str(err.exception)
        self.check_string(actual)

    def test3(self) -> None:
        """
        Test that the header list is accepted when heading levels decrease by
        more than one.
        """
        # Prepare inputs.
        header_list = get_header_list5()
        # Call function.
        hmarkdo.sanity_check_header_list(header_list)


# //////////////////////////////////////////////////////////////////////////////
# Rules processing.
# //////////////////////////////////////////////////////////////////////////////


def get_header_list6() -> hmarkdo.HeaderList:
    """
    - Spelling
      - All
        - LLM
        - Linter
    - Python
      - Naming
        - LLM
        - Linter
      - Docstrings
        - LLM
        - Linter
    - Unit_tests
      - All
        - LLM
        - Linter
    """
    data = [
        (1, "Spelling"),
        (2, "All"),
        (3, "LLM"),
        (3, "Linter"),
        (1, "Python"),
        (2, "Naming"),
        (3, "LLM"),
        (3, "Linter"),
        (2, "Docstrings"),
        (3, "LLM"),
        (3, "Linter"),
        (1, "Unit_tests"),
        (2, "All"),
        (3, "LLM"),
        (3, "Linter"),
    ]
    header_list = _to_header_list(data)
    return header_list


# #############################################################################
# Test_convert_header_list_into_guidelines1
# #############################################################################


class Test_convert_header_list_into_guidelines1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test converting a header list into guidelines.
        """
        # Prepare inputs.
        header_list = get_header_list6()
        # Call function.
        guidelines = hmarkdo.convert_header_list_into_guidelines(header_list)
        # Check output.
        act = "\n".join(map(str, guidelines))
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        HeaderInfo(1, 'Spelling:All:Linter', 16)
        HeaderInfo(1, 'Python:Naming:LLM', 31)
        HeaderInfo(1, 'Python:Naming:Linter', 36)
        HeaderInfo(1, 'Python:Docstrings:LLM', 46)
        HeaderInfo(1, 'Python:Docstrings:Linter', 51)
        HeaderInfo(1, 'Unit_tests:All:LLM', 66)
        HeaderInfo(1, 'Unit_tests:All:Linter', 71)
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_extract_rules1
# #############################################################################


class Test_extract_rules1(hunitest.TestCase):
    def helper(self, selection_rules: List[str], exp: str) -> None:
        """
        Test extracting rules from a markdown file.
        """
        # Prepare inputs.
        guidelines = get_header_list6()
        guidelines = hmarkdo.convert_header_list_into_guidelines(guidelines)
        # Call function.
        selected_guidelines = hmarkdo.extract_rules(guidelines, selection_rules)
        # Check output.
        act = "\n".join(map(str, selected_guidelines))
        self.assert_equal(act, exp, dedent=True)

    def test1(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:*:LLM"]
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        """
        self.helper(selection_rules, exp)

    def test2(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:NONE:LLM"]
        exp = """
        """
        self.helper(selection_rules, exp)

    def test3(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:All:*"]
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        HeaderInfo(1, 'Spelling:All:Linter', 16)
        """
        self.helper(selection_rules, exp)

    def test4(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:All:*", "Python:*:*"]
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        HeaderInfo(1, 'Spelling:All:Linter', 16)
        HeaderInfo(1, 'Python:Naming:LLM', 31)
        HeaderInfo(1, 'Python:Naming:Linter', 36)
        HeaderInfo(1, 'Python:Docstrings:LLM', 46)
        HeaderInfo(1, 'Python:Docstrings:Linter', 51)
        """
        self.helper(selection_rules, exp)


# #############################################################################
# Test_parse_rules_from_txt1
# #############################################################################


class Test_parse_rules_from_txt1(hunitest.TestCase):
    def helper(self, text: str, expected: str) -> None:
        # Prepare inputs.
        text = hprint.dedent(text)
        # Call function.
        actual = hmarkdo.parse_rules_from_txt(text)
        # Check output.
        act = "\n".join(actual)
        self.assert_equal(act, expected, dedent=True)

    def test_basic_list1(self) -> None:
        """
        Test extracting simple first-level bullet points.
        """
        text = """
        - Item 1
        - Item 2
        - Item 3
        """
        expected = """
        - Item 1
        - Item 2
        - Item 3
        """
        self.helper(text, expected)

    def test_nested_list1(self) -> None:
        """
        Test extracting bullet points with nested sub-items.
        """
        text = """
        - Item 1
        - Item 2
          - Sub-item 2.1
          - Sub-item 2.2
        - Item 3
        """
        expected = """
        - Item 1
        - Item 2
          - Sub-item 2.1
          - Sub-item 2.2
        - Item 3
        """
        self.helper(text, expected)

    def test_empty_list1(self) -> None:
        """
        Test handling empty input.
        """
        text = ""
        expected = ""
        self.helper(text, expected)


def get_guidelines_txt1() -> str:
    txt = r"""
    # General

    ## Spelling

    ### LLM

    ### Linter

    - Spell commands in lower case and programs with the first letter in upper case
    - E.g., `git` as a command, `Git` as a program
    - E.g., capitalize the first letter of `Python`
    - Capitalize `JSON`, `CSV`, `DB` and other abbreviations

    # Python

    ## Naming

    ### LLM

    - Name functions using verbs and verbs/actions
      - Good: `download_data()`, `process_input()`, `calculate_sum()`
      - Good: Python internal functions as `__repr__`, `__init__` are valid
      - Good: Functions names like `to_dict()`, `_parse()`, `_main()` are valid
    - Name classes using nouns
      - Good: `Downloader()`, `DataProcessor()`, `User()`
      - Bad: `DownloadStuff()`, `ProcessData()`, `UserActions()`

    ### Linter

    - Name executable Python scripts using verbs and actions
    - E.g., `download.py` and not `downloader.py`

    # Unit_tests

    ## Rules

    ### LLM

    - A test class should test only one function or class to help understanding
      test failures
    - A test method should only test a single case to ensures clarity and
      precision in testing
    - E.g., "for these inputs the function responds with this output"
    """
    txt = hprint.dedent(txt)
    txt = cast(str, txt)
    return txt


# #############################################################################
# Test_end_to_end_rules1
# #############################################################################


class Test_end_to_end_rules1(hunitest.TestCase):
    def test_get_header_list1(self) -> None:
        """
        Test extracting headers from a markdown file.
        """
        # Prepare inputs.
        txt = get_guidelines_txt1()
        max_level = 4
        # Run function.
        header_list = hmarkdo.extract_headers_from_markdown(txt, max_level)
        # Check output.
        act = "\n".join(map(str, header_list))
        exp = """
        HeaderInfo(1, 'General', 1)
        HeaderInfo(2, 'Spelling', 3)
        HeaderInfo(3, 'LLM', 5)
        HeaderInfo(3, 'Linter', 7)
        HeaderInfo(1, 'Python', 14)
        HeaderInfo(2, 'Naming', 16)
        HeaderInfo(3, 'LLM', 18)
        HeaderInfo(3, 'Linter', 28)
        HeaderInfo(1, 'Unit_tests', 33)
        HeaderInfo(2, 'Rules', 35)
        HeaderInfo(3, 'LLM', 37)
        """
        self.assert_equal(act, exp, dedent=True)
        # Run function.
        guidelines = hmarkdo.convert_header_list_into_guidelines(header_list)
        # Check output.
        act = "\n".join(map(str, guidelines))
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Python:Naming:Linter', 28)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.assert_equal(act, exp, dedent=True)

    def helper_extract_rules(self, selection_rules: List[str], exp: str) -> None:
        """
        Helper function to test extracting rules from a markdown file.
        """
        # Prepare inputs.
        txt = get_guidelines_txt1()
        max_level = 4
        header_list = hmarkdo.extract_headers_from_markdown(txt, max_level)
        guidelines = hmarkdo.convert_header_list_into_guidelines(header_list)
        # Call function.
        selected_guidelines = hmarkdo.extract_rules(guidelines, selection_rules)
        # Check output.
        act = "\n".join(map(str, selected_guidelines))
        self.assert_equal(act, exp, dedent=True)

    def test_extract_rules1(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["General:*:LLM"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules2(self) -> None:
        selection_rules = ["General:NONE:LLM"]
        exp = """
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules3(self) -> None:
        selection_rules = ["*:*:LLM"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules4(self) -> None:
        selection_rules = ["*:*:LLM", "General:*:*"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules5(self) -> None:
        selection_rules = ["*:*:*"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Python:Naming:Linter', 28)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules6(self) -> None:
        selection_rules = ["*:*:*", "General:*:*"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Python:Naming:Linter', 28)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)
