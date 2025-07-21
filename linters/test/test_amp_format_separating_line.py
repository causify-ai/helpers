import helpers.hunit_test as hunitest
import linters.amp_format_separating_line as lafoseli


class Test_format_separating_lines(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test seperator lines are formatted correctly.
        """
        min_num_chars = 6
        line_width = 78

        line = f"# {'#' * min_num_chars}"
        expected = f"# {'#' * (line_width - 1)}"
        actual = lafoseli._format_separating_line(
            line, min_num_chars=min_num_chars, line_width=line_width
        )
        self.assertEqual(expected, actual)

    def test2(self) -> None:
        """
        Test lines that don't meet the min number of chars aren't updated.
        """
        min_num_chars = 10

        line = f"# {'#' * (min_num_chars - 1)}"
        expected = line
        actual = lafoseli._format_separating_line(
            line,
            min_num_chars=min_num_chars,
        )
        self.assertEqual(expected, actual)

    def test3(self) -> None:
        """
        Test seperator lines can use different charachters.
        """
        min_num_chars = 6
        line_width = 78

        line = f"# {'=' * min_num_chars}"
        expected = f"# {'=' * (line_width - 1)}"
        actual = lafoseli._format_separating_line(
            line, min_num_chars=min_num_chars, line_width=line_width
        )
        self.assertEqual(expected, actual)

    def test4(self) -> None:
        """
        Check that it doesn't replace if the bar is not until the end of the
        line.
        """
        min_num_chars = 6
        line_width = 78

        line = f"# {'=' * min_num_chars} '''"
        expected = line
        actual = lafoseli._format_separating_line(
            line, min_num_chars=min_num_chars, line_width=line_width
        )
        self.assertEqual(expected, actual)
