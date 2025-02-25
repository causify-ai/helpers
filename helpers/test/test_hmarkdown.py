import logging
import pprint
from typing import List, Tuple

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

    def test_valid_separator(self) -> None:
        # Prepare inputs.
        line = "-----------------------"
        # Call function.
        act = hmarkdo.is_markdown_line_separator(line)
        # Check output.
        exp = True
        self.assertEqual(act, exp)

    def test_invalid_separator(self) -> None:
        # Prepare inputs.
        line = "Not a separator"
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
        act = hmarkdo.extract_headers_from_markdown(content)
        # Check output.
        exp = r"""[(1, 'Header1', 1), (2, 'Header2', 3), (1, 'Header3', 5)]"""
        self.assert_equal(str(act), exp)

    def test_single_header(self) -> None:
        # Prepare inputs.
        content = _get_markdown_example2()
        # Call function.
        act = hmarkdo.extract_headers_from_markdown(content)
        # Check output.
        exp = r"""[(1, 'Header1', 1), (2, 'Header2', 3)]"""
        self.assert_equal(str(act), exp)

    def test_no_headers(self) -> None:
        # Prepare inputs.
        content = r"""
        This is some content without any headers.
        """
        content = hprint.dedent(content)
        # Call function.
        act = hmarkdo.extract_headers_from_markdown(content)
        # Check output.
        exp = []
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
        # txt_in = r"""
        # - Functions can be declared in the body of another function
        # - E.g., to hide utility functions in the scope of the function that uses them
        #     ```python
        #     def print_integers(values):

        #         def _is_integer(value):
        #             try:
        #                 return value == int(value)
        #             except:
        #                 return False

        #         for v in values:
        #             if _is_integer(v):
        #                 print(v)
        #     ```
        # - Hello
        # """
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
        #exp = hprint.dedent(exp, remove_lead_trail_empty_lines_=True)
        self.assert_equal(act, exp, dedent=True, remove_lead_trail_empty_lines=True)


# #############################################################################
# Test_process_lines1
# #############################################################################


class Test_process_lines1(hunitest.TestCase):

    def test1(self) -> None:
        txt = _get_markdown_example5()
        lines = txt.split("\n")
        out = []
        for i, line in hmarkdo.process_lines(lines):
            _LOG.debug(hprint.to_str("line"))
            out.append(f"{i}:{line}")
        act = "\n".join(out)
        exp = """
        1:- Functions can be declared in the body of another function
        2:- E.g., to hide utility functions in the scope of the function that uses them
        16:- Hello
        """
        self.assert_equal(act, exp, dedent=True, remove_lead_trail_empty_lines=True)


class Test_selected_navigation_to_str1(hunitest.TestCase):

    def test1(self) -> None:
        res = []
        txt = _get_markdown_example4()
        res.append("txt=\n" + txt)
        #
        header_list = hmarkdo.extract_headers_from_markdown(txt)
        act = pprint.pformat(header_list)
        exp = """
        [(1, 'Chapter 1', 1),
         (2, 'Section 1.1', 6),
         (3, 'Subsection 1.1.1', 11),
         (3, 'Subsection 1.1.2', 23),
         (2, 'Section 1.2', 31),
         (1, 'Chapter 2', 38),
         (2, 'Section 2.1', 43),
         (3, 'Subsection 2.1.1', 48),
         (2, 'Section 2.2', 56)]
        """
        self.assert_equal(act, exp, dedent=True, remove_lead_trail_empty_lines=True)
        #
        tree = hmarkdo.build_header_tree(header_list)
        act = hmarkdo.header_tree_to_str(tree, ancestry=None)
        exp = """
        - Chapter 1
        - Chapter 2
        """
        self.assert_equal(act, exp, dedent=True, remove_lead_trail_empty_lines=True)
        #
        level = 3
        description = "Subsection 1.1.2"
        act = hmarkdo.selected_navigation_to_str(tree, level, description)
        exp = """
        - Chapter 1
          - Section 1.1
            - Subsection 1.1.1
            - *Subsection 1.1.2*
          - Section 1.2
        - Chapter 2
        """
        self.assert_equal(act, exp, dedent=True, remove_lead_trail_empty_lines=True)

    def test2(self) -> None:
        res = []
        txt = _get_markdown_example4()
        header_list = hmarkdo.extract_headers_from_markdown(txt)
        tree = hmarkdo.build_header_tree(header_list)
        # Create a navigation map for any header.
        for level, description, _ in header_list:
            res_tmp = hprint.frame(hprint.to_str("level description"))
            res.append(res_tmp)
            #
            res_tmp = hmarkdo.selected_navigation_to_str(tree, level, description)
            res.append(res_tmp)
        # Check.
        act = "\n".join(res)
        self.check_string(act)