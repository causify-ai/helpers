import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# Test_extract_section_from_markdown1
# #############################################################################


class Test_extract_section_from_markdown1(hunitest.TestCase):

    def test1(self) -> None:
        # Prepare inputs.
        content = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under header 2.
        # Header3
        Content under header 3.
        """
        # Call functions.
        content = hprint.dedent(content)
        act = hmarkdo.extract_section_from_markdown(content, "Header1")
        # Check output.
        exp = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under header 2.
        """
        self.assert_equal(act, exp, dedent=True)

    def test2(self) -> None:
        # Prepare inputs.
        content = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under header 2.
        # Header3
        Content under header 3.
        """
        content = hprint.dedent(content)
        # Call functions.
        act = hmarkdo.extract_section_from_markdown(content, "Header2")
        # Check output.
        exp = r"""
        ## Header2
        Content under header 2.
        """
        self.assert_equal(act, exp, dedent=True)

    def test3(self) -> None:
        # Prepare inputs.
        content = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under header 2.
        # Header3
        Content under header 3.
        """
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
        content = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under header 2.
        """
        content = hprint.dedent(content)
        # Call function.
        act = hmarkdo.extract_section_from_markdown(content, "Header1")
        # Check output.
        exp = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under header 2.
        """
        self.assert_equal(act, exp, dedent=True)

    def test_no_header(self) -> None:
        # Prepare inputs.
        content = r"""
        # Header1
        Content under header 1.
        ## Header2
        Content under header 2.
        # Header3
        Content under header 3.
        """
        # Call tested function.
        content = hprint.dedent(content)
        with self.assertRaises(ValueError) as fail:
            hmarkdo.extract_section_from_markdown(content, "Header4")
        # Check output.
        actual = str(fail.exception)
        expected = r"Header 'Header4' not found"
        self.assert_equal(actual, expected)


# #############################################################################


def get_header_data1() -> hmarkdo.HeaderList:
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
    return data


def get_header_data2() -> hmarkdo.HeaderList:
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
    return data


def get_header_data3() -> hmarkdo.HeaderList:
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
    return data


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
