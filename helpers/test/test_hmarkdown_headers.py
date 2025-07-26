import logging
import os
import pprint
from typing import Any, List, Tuple, cast

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
    lines = txt.split("\n")
    header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=3)
    actual = pprint.pformat(header_list)
    self_.assert_equal(
        actual, header_list_exp, dedent=True, remove_lead_trail_empty_lines=True
    )
    # 2) Build header tree.
    tree = hmarkdo.build_header_tree(header_list)
    actual = hmarkdo.header_tree_to_str(tree, ancestry=None)
    self_.assert_equal(
        actual, header_tree_exp, dedent=True, remove_lead_trail_empty_lines=True
    )
    # 3) Compute the navigation bar for a specific header.
    actual = hmarkdo.selected_navigation_to_str(tree, level, description)
    self_.assert_equal(
        actual, nav_str_exp, dedent=True, remove_lead_trail_empty_lines=True
    )


def _test_full_navigation_flow(self_: Any, txt: str) -> None:
    res: List[str] = []
    # Extract headers.
    lines = txt.split("\n")
    header_list = hmarkdo.extract_headers_from_markdown(lines, max_level=3)
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
    actual = "\n".join(res)
    self_.check_string(actual)


# #############################################################################
# Test_header_list_to_vim_cfile1
# #############################################################################


class Test_header_list_to_vim_cfile1(hunitest.TestCase):
    def test_get_header_list1(self) -> None:
        # Prepare inputs.
        markdown_file = "test.py"
        headers = get_header_list1()
        # Call function.
        actual = hmarkdo.header_list_to_vim_cfile(markdown_file, headers)
        # Check output.
        expected = r"""
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
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_header_list_to_markdown1
# #############################################################################


class Test_header_list_to_markdown1(hunitest.TestCase):
    def test_mode_list1(self) -> None:
        # Prepare inputs.
        headers = get_header_list1()
        mode = "list"
        # Call function.
        actual_lines = hmarkdo.header_list_to_markdown(headers, mode)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
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
        self.assert_equal(actual, expected, dedent=True)

    def test_mode_headers1(self) -> None:
        # Prepare inputs.
        headers = get_header_list1()
        mode = "headers"
        # Call function.
        actual_lines = hmarkdo.header_list_to_markdown(headers, mode)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
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
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_is_markdown_line_separator1
# #############################################################################


class Test_is_markdown_line_separator1(hunitest.TestCase):
    def test_valid_separator1(self) -> None:
        # Prepare inputs.
        line = "-----------------------"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = True
        self.assertEqual(actual, expected)

    def test_valid_separator2(self) -> None:
        # Prepare inputs.
        line = "# ------"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = True
        self.assertEqual(actual, expected)

    def test_valid_separator3(self) -> None:
        # Prepare inputs.
        line = "# #########"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = True
        self.assertEqual(actual, expected)

    def test_valid_separator4(self) -> None:
        # Prepare inputs.
        line = "### ====="
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = True
        self.assertEqual(actual, expected)

    def test_valid_separator5(self) -> None:
        # Prepare inputs.
        line = "#//////"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = True
        self.assertEqual(actual, expected)

    def test_valid_separator6(self) -> None:
        # Prepare inputs.
        line = "#  //////"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = True
        self.assertEqual(actual, expected)

    def test_invalid_separator1(self) -> None:
        # Prepare inputs.
        line = "Not a separator"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = False
        self.assertEqual(actual, expected)

    def test_invalid_separator2(self) -> None:
        # Prepare inputs.
        line = "# --"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = False
        self.assertEqual(actual, expected)

    def test_invalid_separator3(self) -> None:
        # Prepare inputs.
        line = "# ###---"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = False
        self.assertEqual(actual, expected)

    def test_invalid_separator4(self) -> None:
        # Prepare inputs.
        line = "=="
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = False
        self.assertEqual(actual, expected)

    def test_invalid_separator5(self) -> None:
        # Prepare inputs.
        line = "- //////"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = False
        self.assertEqual(actual, expected)

    def test_invalid_separator6(self) -> None:
        # Prepare inputs.
        line = "=== Not a seperator"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = False
        self.assertEqual(actual, expected)

    def test_invalid_separator7(self) -> None:
        # Prepare inputs.
        line = "--- Not a seperator ---"
        # Call function.
        actual = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        expected = False
        self.assertEqual(actual, expected)


# #############################################################################
# Test_extract_section_from_markdown1
# #############################################################################


class Test_extract_section_from_markdown1(hunitest.TestCase):
    # TODO(gp): This doesn't seem correct.
    def test1(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example1()
        # Call functions.
        lines = content.split("\n")
        actual_lines = hmarkdo.extract_section_from_markdown(lines, "Header1")
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under subheader 2.
        """
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example1()
        content = hprint.dedent(content)
        # Call functions.
        lines = content.split("\n")
        actual_lines = hmarkdo.extract_section_from_markdown(lines, "Header2")
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
        ## Header2
        Content under subheader 2.
        """
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example1()
        content = hprint.dedent(content)
        # Call tested function.
        lines = content.split("\n")
        actual_lines = hmarkdo.extract_section_from_markdown(lines, "Header3")
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
        # Header3
        Content under header 3.
        """
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example2()
        # Call function.
        lines = content.split("\n")
        actual_lines = hmarkdo.extract_section_from_markdown(lines, "Header1")
        actual = "\n".join(actual_lines)
        # Check output.
        expected = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under subheader 2.
        """
        self.assert_equal(actual, expected, dedent=True)

    def test_no_header(self) -> None:
        # Prepare inputs.
        content = _get_markdown_no_header_example1()
        # Call tested function.
        with self.assertRaises(ValueError) as fail:
            lines = content.split("\n")
            hmarkdo.extract_section_from_markdown(lines, "Header4")
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
        lines = content.split("\n")
        actual = hmarkdo.extract_headers_from_markdown(lines, max_level=3)
        # Check output.
        expected = r"""[HeaderInfo(1, 'Header1', 1), HeaderInfo(2, 'Header2', 3), HeaderInfo(1, 'Header3', 5)]"""
        self.assert_equal(str(actual), expected)

    def test_single_header(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example2()
        # Call function.
        lines = content.split("\n")
        actual = hmarkdo.extract_headers_from_markdown(lines, max_level=3)
        # Check output.
        expected = r"""[HeaderInfo(1, 'Header1', 1), HeaderInfo(2, 'Header2', 3)]"""
        self.assert_equal(str(actual), expected)

    def test_no_headers(self) -> None:
        # Prepare inputs.
        content = r"""
        This is some content without any headers.
        """
        content = hprint.dedent(content)
        # Call function.
        lines = content.split("\n")
        actual = hmarkdo.extract_headers_from_markdown(lines, max_level=3)
        # Check output.
        expected: List[str] = []
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_extract_slides_from_markdown1
# #############################################################################


class Test_extract_slides_from_markdown1(hunitest.TestCase):
    def test_multiple_slides(self) -> None:
        # Prepare inputs.
        content = _get_markdown_slides_example1()
        # Call function.
        lines = content.split("\n")
        actual = hmarkdo.extract_slides_from_markdown(lines)
        # Check output.
        expected = r"""([HeaderInfo(1, 'Slide 1', 3), HeaderInfo(1, 'Slide 2', 8), HeaderInfo(1, 'Slide 3', 11)], 12)"""
        self.assert_equal(str(actual), expected)

    def test_single_slides(self) -> None:
        # Prepare inputs.
        content = _get_markdown_slides_example2()
        # Call function.
        lines = content.split("\n")
        actual = hmarkdo.extract_slides_from_markdown(lines)
        # Check output.
        expected = r"""([HeaderInfo(1, 'Slide1', 3)], 4)"""
        self.assert_equal(str(actual), expected)

    def test_no_slides(self) -> None:
        # Prepare inputs.
        content = _get_markdown_no_header_example1()
        # Call function.
        lines = content.split("\n")
        actual = hmarkdo.extract_slides_from_markdown(lines)
        # Check output.
        expected = r"""([], 1)"""
        self.assert_equal(str(actual), expected)


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
# Test_modify_header_level1
# #############################################################################


class Test_modify_header_level1(hunitest.TestCase):
    def helper(
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
        actual_lines = hmarkdo.modify_header_level(input_lines, level)
        actual = "\n".join(actual_lines)
        # Check output.
        expected = "\n".join(expected_lines)
        self.assertEqual(actual, expected)

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
        self.helper(input_lines, level, expected_lines)

    def test2(self) -> None:
        """
        Test inputs to increase headings with level 5 becoming level 6.
        """
        # Prepare inputs and outputs.
        input_lines = ["# Chapter 1", "##### Sub-sub-subsection 1.1.1.1.1"]
        level = 1
        expected_lines = ["## Chapter 1", "###### Sub-sub-subsection 1.1.1.1.1"]
        # Call the helper.
        self.helper(input_lines, level, expected_lines)

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
        self.helper(input_lines, level, expected_lines)

    def test4(self) -> None:
        """
        Test inputs of paragraphs which remain unchanged.
        """
        # Prepare inputs and outputs.
        input_lines = ["Paragraph 1", "Paragraph 2"]
        level = 1
        expected_lines = ["Paragraph 1", "Paragraph 2"]
        # Call the helper.
        self.helper(input_lines, level, expected_lines)

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
        self.helper(input_lines, level, expected_lines)

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
        self.helper(input_lines, level, expected_lines)

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
        self.helper(input_lines, level, expected_lines)

    def test8(self) -> None:
        """
        Test inputs of paragraphs which remain unchanged.
        """
        # Prepare inputs and outputs.
        input_lines = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
        level = -1
        expected_lines = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
        # Call the helper.
        self.helper(input_lines, level, expected_lines)

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
        self.helper(input_lines, level, expected_lines)

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
        self.helper(input_lines, level, expected_lines)

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
        self.helper(input_lines, level, expected_lines)


# #############################################################################
# Test_format_headers1
# #############################################################################


class Test_format_headers1(hunitest.TestCase):
    def helper_process(
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
        self.helper_process(input_text, expected, max_lev=1)

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
        self.helper_process(input_text, expected, max_lev=2)

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
        self.helper_process(input_text, expected, max_lev=1)

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
        self.helper_process(input_text, expected, max_lev=2)

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
        self.helper_process(input_text, expected, max_lev=3)


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


# #############################################################################
# Test_capitalize_header1
# #############################################################################


class Test_capitalize_header1(hunitest.TestCase):
    def helper(self, txt: str, expected: str) -> None:
        # Prepare inputs.
        txt = hprint.dedent(txt)
        # Run function.
        lines = txt.split("\n")
        actual_lines = hmarkdo.capitalize_header(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        txt = r"""
        * ML theory
        """
        expected = r"""
        * ML Theory
        """
        self.helper(txt, expected)

    def test2(self) -> None:
        txt = r"""
        * A map of machine learning
        """
        expected = r"""
        * A Map of Machine Learning
        """
        self.helper(txt, expected)

    def test_backticks_preserved(self) -> None:
        """
        Test that strings inside backticks are preserved.
        """
        txt = r"""
        # Using `python` for Machine Learning
        """
        expected = r"""
        # Using `python` for Machine Learning
        """
        self.helper(txt, expected)

    def test_single_quotes_preserved(self) -> None:
        """
        Test that strings inside single quotes are preserved.
        """
        txt = r"""
        * Working with 'machine learning' algorithms
        """
        expected = r"""
        * Working with 'machine learning' Algorithms
        """
        self.helper(txt, expected)

    def test_double_quotes_preserved(self) -> None:
        """
        Test that strings inside double quotes are preserved.
        """
        txt = r"""
        # Understanding "deep learning" concepts
        """
        expected = r"""
        # Understanding "deep learning" Concepts
        """
        self.helper(txt, expected)

    def test_mixed_quotes_and_backticks(self) -> None:
        """
        Test mixed usage of quotes and backticks.
        """
        txt = r"""
        * Using `python` and "machine learning" for 'data science'
        """
        expected = r"""
        * Using `python` and "machine learning" for 'data science'
        """
        self.helper(txt, expected)

    def test_complex_title_with_quotes(self) -> None:
        """
        Test complex title with various quote types.
        """
        txt = r"""
        # Introduction to `sklearn` and "data preprocessing" in 'python'
        """
        expected = r"""
        # Introduction to `sklearn` and "data preprocessing" in 'python'
        """
        self.helper(txt, expected)
