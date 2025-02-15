import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


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
