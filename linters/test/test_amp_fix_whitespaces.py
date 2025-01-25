import helpers.hunit_test as hunitest
import linters.amp_fix_whitespaces as lamfiwhi


class Test_replace_tabs_with_spaces(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test replacing tabs with spaces.
        """
        in_out_dict = {
            "\tinitial tab": "    initial tab",
            "final tab\t": "final tab   ",
            "\t initial tab with space": "     initial tab with space",
            "Many\ttabs\tsome \twith\t spaces\t\tor \t\t double": "Many    tabs    some    with     spaces     or       double",
        }
        num_spaces = 4
        for line, exp in in_out_dict.items():
            actual = lamfiwhi._replace_tabs_with_spaces(
                line, num_spaces=num_spaces
            )
            self.assertEqual(exp, actual)


class Test_remove_trailing_whitespaces(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test removing trailing whitespaces.
        """
        in_out_dict = {
            "trailing spaces  ": "trailing spaces",
            "trailing carriage return\r": "trailing carriage return",
            "trailing space and carriage return \r": "trailing space and carriage return",
            "\r text with non-trailing whitespaces": "\r text with non-trailing whitespaces",
        }
        for line, exp in in_out_dict.items():
            actual = lamfiwhi._remove_trailing_whitespaces(line)
            self.assertEqual(exp, actual)


class Test_format_end_of_file(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test formatting the end of file.
        """
        in_out_lst = [
            (["", "\r", " "], []),
            (["first", "second"], ["first", "second", ""]),
            (["first", "second", "", ""], ["first", "second", ""]),
            (["first", "second", "", "\r", ""], ["first", "second", ""]),
        ]
        for lines, exp in in_out_lst:
            actual = lamfiwhi._format_end_of_file(lines)
            self.assertEqual(exp, actual)
