import logging
import os
import pprint
from typing import Any, List, Tuple

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
    return content


def _get_markdown_example2() -> str:
    content = r"""
    # Header1
    Content under header 1.
    ## Header2
    Content under subheader 2.
    """
    content = hprint.dedent(content)
    return content


def _get_markdown_example3() -> str:
    content = r"""
    This is some content without any headers.
    """
    content = hprint.dedent(content)
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
        content = _get_markdown_example3()
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

    def process_code_block(self, txt: str) -> str:
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
        act = self.process_code_block(txt_in)
        self.check_string(act, dedent=True, remove_lead_trail_empty_lines=True)


# #############################################################################
# Test_process_lines1
# #############################################################################


class Test_process_lines1(hunitest.TestCase):

    # TODO(gp): This doesn't seem correct.
    def test1(self) -> None:
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        txt_in = hio.from_file(input_file_path)
        txt_in = hprint.dedent(txt_in)
        lines = txt_in.split("\n")
        out = []
        for i, line in hmarkdo.process_lines(lines):
            _LOG.debug(hprint.to_str("line"))
            out.append(f"{i}:{line}")
        act = "\n".join(out)
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
# Test_bold_first_level_bullets1
# #############################################################################


class Test_bold_first_level_bullets1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test basic first-level bullet bolding.
        """
        text = r"""
        - First item
          - Sub item
        - Second item
        """
        expected = r"""
        - **First item**
          - Sub item
        - **Second item**
        """
        self._test_bold_first_level_bullets(text, expected)

    def test2(self) -> None:
        """
        Test with mixed content including non-bullet text.
        """
        text = r"""
        Some text here
        - First bullet
        More text
        - Second bullet
          - Nested bullet
        Final text
        """
        expected = r"""
        Some text here
        - **First bullet**
        More text
        - **Second bullet**
          - Nested bullet
        Final text
        """
        self._test_bold_first_level_bullets(text, expected)

    def test3(self) -> None:
        """
        Test with multiple levels of nesting.
        """
        text = r"""
        - Top level
          - Second level
            - Third level
          - Back to second
        - Another top
        """
        expected = r"""
        - **Top level**
          - Second level
            - Third level
          - Back to second
        - **Another top**
        """
        self._test_bold_first_level_bullets(text, expected)

    def test4(self) -> None:
        """
        Test with empty lines between bullets.
        """
        text = r"""
        - First item

        - Second item
          - Sub item

        - Third item
        """
        expected = r"""
        - **First item**

        - **Second item**
          - Sub item

        - **Third item**
        """
        self._test_bold_first_level_bullets(text, expected)

    def test5(self) -> None:
        """
        Test with text that already contains some bold markers.
        """
        text = r"""
        - First **important** point
          - Sub point
        - Second point with emphasis
        """
        expected = r"""
        - First **important** point
          - Sub point
        - **Second point with emphasis**
        """
        self._test_bold_first_level_bullets(text, expected)

    def _test_bold_first_level_bullets(self, text: str, expected: str) -> None:
        """
        Helper to test bold_first_level_bullets function.
        """
        text = hprint.dedent(text)
        actual = hmarkdo.bold_first_level_bullets(text)
        self.assert_equal(actual, expected, dedent=True)


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
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = [
            "# Chapter 1",
            "## Section 1.1",
            "### Subsection 1.1.1",
            "#### Sub-subsection 1.1.1.1",
        ]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "increase")
        # Check output.
        expected = [
            "## Chapter 1",
            "### Section 1.1",
            "#### Subsection 1.1.1",
            "##### Sub-subsection 1.1.1.1",
        ]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test inputs to increase headings with more than four hashes which
        remain unchanged.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = ["# Chapter 1", "##### Sub-sub-subsection 1.1.1.1.1"]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "increase")
        # Check output.
        expected = ["## Chapter 1", "##### Sub-sub-subsection 1.1.1.1.1"]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test inputs to increase headings including a paragraph which remains
        unchanged.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = ["# Chapter 1", "Paragraph 1"]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "increase")
        # Check output.
        expected = ["## Chapter 1", "Paragraph 1"]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test inputs of paragraphs which remain unchanged.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = ["Paragraph 1", "Paragraph 2"]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "increase")
        # Check output.
        expected = ["Paragraph 1", "Paragraph 2"]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test to increase headings with less than five hashes.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = [
            "# Chapter 1",
            "##### Sub-sub-subsection 1.1.1.1.1",
            "# Chapter 2",
            "### Subsection 2.1",
            "# Chapter 3",
        ]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "increase")
        # Check output.
        expected = [
            "## Chapter 1",
            "##### Sub-sub-subsection 1.1.1.1.1",
            "## Chapter 2",
            "#### Subsection 2.1",
            "## Chapter 3",
        ]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
        self.assertEqual(actual, expected)

    def test6(self) -> None:
        """
        Test the inputs to decrease headings.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = [
            "## Section 1.1",
            "### Subsection 1.1.1",
            "#### Sub-subsection 1.1.1.1",
            "##### Sub-sub-subsection 1.1.1.1.1",
        ]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "decrease")
        # Check output.
        expected = [
            "# Section 1.1",
            "## Subsection 1.1.1",
            "### Sub-subsection 1.1.1.1",
            "#### Sub-sub-subsection 1.1.1.1.1",
        ]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
        self.assertEqual(actual, expected)

    def test7(self) -> None:
        """
        Test inputs to decrease headings with one hash which remains unchanged.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = [
            "# Chapter 1",
            "##### Sub-subsection 1.1.1.1",
        ]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "decrease")
        # Check output.
        expected = [
            "# Chapter 1",
            "#### Sub-subsection 1.1.1.1",
        ]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
        self.assertEqual(actual, expected)

    def test8(self) -> None:
        """
        Test inputs of paragraphs which remain unchanged.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        read_file = os.path.join(scratch_dir, "read_file.txt")
        input_text = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
        input_text = "\n".join(input_text)
        hio.to_file(read_file, input_text)
        # Call tested function.
        write_file = os.path.join(scratch_dir, "write_file.txt")
        hmarkdo.modify_header_level(read_file, write_file, "decrease")
        # Check output.
        expected = ["Paragraph 1", "Paragraph 2", "Paragraph 3"]
        expected = "\n".join(expected)
        actual = hio.from_file(write_file)
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
# Test_check_header_list1
# #############################################################################


class Test_check_header_list1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test that the header list with valid level increase is accepted.
        """
        # Prepare inputs.
        header_list = get_header_list1()
        # Call function.
        hmarkdo.check_header_list(header_list)
        self.assertTrue(True)

    def test2(self) -> None:
        """
        Test that the header list with an increase of more than one level
        raises an error.
        """
        # Prepare inputs.
        header_list = get_header_list4()
        # Call function.
        with self.assertRaises(ValueError) as err:
            hmarkdo.check_header_list(header_list)
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
        hmarkdo.check_header_list(header_list)
        self.assertTrue(True)


# #############################################################################
# Test_colorize_bold_text1
# #############################################################################


class Test_colorize_bold_text1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test basic case with single bold text.
        """
        text = "This is **bold** text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"This is **\red{bold}** text"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test multiple bold sections get different colors.
        """
        text = "**First** normal **Second** text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"**\red{First}** normal **\teal{Second}** text"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test underscore style bold text.
        """
        text = "This is __bold__ text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"This is **\red{bold}** text"
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test text with no bold sections returns unchanged.
        """
        text = "This is plain text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = "This is plain text"
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test mixed bold styles in same text.
        """
        text = "**First** and __Second__ bold"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"**\red{First}** and **\teal{Second}** bold"
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test with abbreviations=False uses full \textcolor syntax.
        """
        text = "This is **bold** text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=False)
        expected = r"This is **\textcolor{red}{bold}** text"
        self.assert_equal(actual, expected)

    def test7(self) -> None:
        """
        Test with multiple bullet lists and different colors.
        """
        text = """
        **List 1:**
        - First item
        - Second item

        **List 2:**
        - Another item
        - Final item
        """
        text = hprint.dedent(text)
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"""
        **\red{List 1:}**
        - First item
        - Second item

        **\teal{List 2:}**
        - Another item
        - Final item
        """
        self.assert_equal(actual, expected, dedent=True)

    def test8(self) -> None:
        text = r"""
        - **\red{Objective}**
          - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **\orange{Key Components}**
          - Model learning: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
          - Utility update: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **\blue{Learning Process}**
          - Collect transitions $(s, \pi(s), r, s')$ during execution
          - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
          - Use dynamic programming to compute $U^\pi(s)$

        - **\violet{Advantages}**
          - More sample-efficient than direct utility estimation
          - Leverages structure of the MDP to generalize better

        - **\pink{Challenges}**
          - Requires accurate model estimation
          - Computational cost of solving Bellman equations repeatedly

        - **\olive{Example}**
          - A thermostat estimates room temperature dynamics and uses them to predict
            comfort level under a fixed heating schedule

        - **\darkgray{Use Case}**
          - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        text = hprint.dedent(text)
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"""
        - **\red{Objective}**
          - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **\orange{Key Components}**
          - Model learning: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
          - Utility update: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **\olive{Learning Process}**
          - Collect transitions $(s, \pi(s), r, s')$ during execution
          - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
          - Use dynamic programming to compute $U^\pi(s)$

        - **\green{Advantages}**
          - More sample-efficient than direct utility estimation
          - Leverages structure of the MDP to generalize better

        - **\cyan{Challenges}**
          - Requires accurate model estimation
          - Computational cost of solving Bellman equations repeatedly

        - **\blue{Example}**
          - A thermostat estimates room temperature dynamics and uses them to predict
            comfort level under a fixed heating schedule

        - **\darkgray{Use Case}**
          - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_format_compressed_markdown1
# #############################################################################


class Test_format_compressed_markdown1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test basic case with single first level bullet.
        """
        text = """
        Some text
        - First bullet
        More text"""
        expected = """
        Some text

        - First bullet
        More text"""
        self._format_and_compare_markdown(text, expected)

    def test2(self) -> None:
        """
        Test multiple first level bullets.
        """
        text = """
        - First bullet
        - Second bullet
        - Third bullet"""
        expected = """
        - First bullet

        - Second bullet

        - Third bullet"""
        self._format_and_compare_markdown(text, expected)

    def test3(self) -> None:
        """
        Test mixed first level and indented bullets.
        """
        text = """
        - First level

          - Second level
          - Another second
        - Back to first"""
        expected = """
        - First level
          - Second level
          - Another second

        - Back to first"""
        self._format_and_compare_markdown(text, expected)

    def test4(self) -> None:
        """
        Test mixed content with text and bullets.
        """
        text = """
        Some initial text
        - First bullet
        Some text in between
        - Second bullet
        Final text"""
        expected = """
        Some initial text

        - First bullet
        Some text in between

        - Second bullet
        Final text"""
        self._format_and_compare_markdown(text, expected)

    def test5(self) -> None:
        """
        Test nested bullets with multiple levels.
        """
        text = """
        - Level 1
            - Level 2
                - Level 3
        - Another level 1
            - Level 2 again"""
        expected = """
        - Level 1
            - Level 2
                - Level 3

        - Another level 1
            - Level 2 again"""
        self._format_and_compare_markdown(text, expected)

    def test6(self) -> None:
        """
        Test empty lines handling.
        """
        text = """
        - First bullet

        - Second bullet

        - Third bullet"""
        expected = """
        - First bullet

        - Second bullet

        - Third bullet"""
        self._format_and_compare_markdown(text, expected)

    def test7(self) -> None:
        """
        Test mixed content with bullets and text.
        """
        text = """
        Some text here
        - First bullet
        More text
        - Second bullet
            - Nested bullet
        Final paragraph
        - Last bullet"""
        expected = """
        Some text here

        - First bullet
        More text

        - Second bullet
            - Nested bullet
        Final paragraph

        - Last bullet"""
        self._format_and_compare_markdown(text, expected)

    def test8(self) -> None:
        """
        Test bullets with inline formatting.
        """
        text = """
        - **Bold bullet** point
            - *Italic nested* bullet
        - `Code bullet` here
            - **_Mixed_** formatting"""
        expected = """
        - **Bold bullet** point
            - *Italic nested* bullet

        - `Code bullet` here
            - **_Mixed_** formatting"""
        self._format_and_compare_markdown(text, expected)

    def test9(self) -> None:
        """
        Test bullets with special characters.
        """
        text = """
        - Bullet with (parentheses)
            - Bullet with [brackets]
        - Bullet with {braces}
            - Bullet with $math$"""
        expected = """
        - Bullet with (parentheses)
            - Bullet with [brackets]

        - Bullet with {braces}
            - Bullet with $math$"""
        self._format_and_compare_markdown(text, expected)

    def test10(self) -> None:
        text = r"""
        - **Objective**

          - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **Key Components**

          - **Model learning**: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
          - **Utility update**: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **Learning Process**

          - Collect transitions $(s, \pi(s), r, s')$ during execution
          - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
          - Use dynamic programming to compute $U^\pi(s)$

        - **Use Case**
          - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        expected = r"""
        - **Objective**
          - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **Key Components**
          - **Model learning**: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
          - **Utility update**: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **Learning Process**
          - Collect transitions $(s, \pi(s), r, s')$ during execution
          - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
          - Use dynamic programming to compute $U^\pi(s)$

        - **Use Case**
          - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        self._format_and_compare_markdown(text, expected)

    def _format_and_compare_markdown(self, text: str, expected: str) -> None:
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        #
        actual = hmarkdo.remove_empty_lines_from_markdown(text)
        self.assert_equal(actual, expected)
