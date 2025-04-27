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
        line = "# ---"
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


def _get_markdown_example5() -> str:
    content = r"""
    - Functions can be declared in the body of another function
    - E.g., to hide utility functions in the scope of the function that uses them
        ```python
        def print_integers(values):

            def _is_integer(value):
                try:
                    return value == int(value)
                except:
                    return False

            for v in values:
                if _is_integer(v):
                    print(v)
        ```
    - Hello
    """
    content = hprint.dedent(content)
    return content


def _get_markdown_example6() -> hmarkdo.HeaderList:
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
        txt_in = _get_markdown_example5()
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        act = self.process_code_block(txt_in)
        exp = r"""
        - Functions can be declared in the body of another function
        - E.g., to hide utility functions in the scope of the function that uses them


                ```python
                def print_integers(values):

                    def _is_integer(value):
                        try:
                            return value == int(value)
                        except:
                            return False

                    for v in values:
                        if _is_integer(v):
                            print(v)
                ```


        - Hello
        """
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )


# #############################################################################
# Test_process_lines1
# #############################################################################


class Test_process_lines1(hunitest.TestCase):

    # TODO(gp): This doesn't seem correct.
    def test1(self) -> None:
        txt = _get_markdown_example5()
        lines = txt.split("\n")
        out = []
        for i, line in hmarkdo.process_lines(lines):
            _LOG.debug(hprint.to_str("line"))
            out.append(f"{i}:{line}")
        act = "\n".join(out)
        exp = r"""
        0:- Functions can be declared in the body of another function
        1:- E.g., to hide utility functions in the scope of the function that uses them
        2:

        3:        ```python
        4:        def print_integers(values):
        5:
        6:            def _is_integer(value):
        7:                try:
        8:                    return value == int(value)
        9:                except:
        10:                    return False
        11:
        12:            for v in values:
        13:                if _is_integer(v):
        14:                    print(v)
        15:        ```
        16:

        17:- Hello
        """
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )


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
        Create navigation bar from Markdown text `_get_markdown_example6()`.
        """
        txt = _get_markdown_example6()
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
        txt = _get_markdown_example6()
        _test_full_navigation_flow(self, txt)


# #############################################################################
# Test_colorize_first_level_bullets1
# #############################################################################


class Test_colorize_first_level_bullets1(hunitest.TestCase):

    def test1(self) -> None:
        # Prepare inputs.
        content = r"""
        - Item 1
          - Subitem 1.1
          - Subitem 1.2
        - Item 2
          - Subitem 2.1
        """
        content = hprint.dedent(content)
        # Call tested function.
        act = hmarkdo.colorize_first_level_bullets(content)
        # Check output.
        exp = r"""
        - \textcolor{red}{Item 1}
          - Subitem 1.1
          - Subitem 1.2
        - \textcolor{orange}{Item 2}
          - Subitem 2.1
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_fix_chatgpt_output
# #############################################################################


class Test_fix_chatgpt_output1(hunitest.TestCase):

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
        act = hmarkdo.fix_chatgpt_output(txt)
        act = hprint.dedent(act)
        exp = r"""
        **States**:
        - $S = \{\text{Sunny}, \text{Rainy}\}$
        **Observations**:
        - $O = \{\text{Yes}, \text{No}\}$ (umbrella)

        ### Initial Probabilities:
        $$\Pr(\text{Sunny}) = 0.6, \quad \Pr(\text{Rainy}) = 0.4$$### Transition Probabilities:$$
        \begin{aligned}
        \Pr(\text{Sunny} \to \text{Sunny}) &= 0.7, \quad \Pr(\text{Sunny} \to \text{Rainy}) = 0.3 \\
        \Pr(\text{Rainy} \to \text{Sunny}) &= 0.4, \quad \Pr(\text{Rainy} \to \text{Rainy}) = 0.6
        \end{aligned}
        $$### Observation (Emission) Probabilities:$$
        \begin{aligned}
        \Pr(\text{Yes} | \text{Sunny}) &= 0.1, \quad \Pr(\text{No} | \text{Sunny}) = 0.9 \\
        \Pr(\text{Yes} | \text{Rainy}) &= 0.8, \quad \Pr(\text{No} | \text{Rainy}) = 0.2
        \end{aligned}
        $$
        """
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
        content = r"""

        ```python

        def check_empty_lines():
            print("Check empty lines are present!")

        ```

        """
        content = hprint.dedent(content)
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
        content = _get_markdown_example5()
        # Call function.
        act = hmarkdo.remove_code_delimiters(content)
        # Check output.
        exp = r"""
        - Functions can be declared in the body of another function
        - E.g., to hide utility functions in the scope of the function that uses them

            def print_integers(values):

                def _is_integer(value):
                    try:
                        return value == int(value)
                    except:
                        return False

                for v in values:
                    if _is_integer(v):
                        print(v)

        - Hello
        """
        self.assert_equal(str(act), exp, dedent=True)

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
        content = r"""
        ```python
        def no_start_python():
            print("No mention of python at the start")```
        ```

        ```
            A markdown paragraph contains
            delimiters that needs to be removed.
        ```
        """
        content = hprint.dedent(content)
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
