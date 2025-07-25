import helpers.hunit_test as hunitest
import linters.amp_check_import as lamchimp


class Test_check_import(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test long import shortcut: invalid.
        """
        shortcut = "very_long_name"
        line = f"import test as {shortcut}"
        expected = f"the import shortcut '{shortcut}' in '{line}' is longer than 8 characters"
        self._helper_check_import(line, expected, file_name="test.py")

    def test2(self) -> None:
        """
        Test from lib import something: invalid.
        """
        line = "from pandas import DataFrame"
        expected = f"do not use '{line}' use 'import foo.bar as fba'"
        self._helper_check_import(line, expected, file_name="test.py")

    def test3(self) -> None:
        """
        Test from typing import something: valid.
        """
        line = "from typing import List"
        expected = ""
        self._helper_check_import(line, expected, file_name="test.py")

    def test4(self) -> None:
        """
        Test wild import in __init__.py: valid.
        """
        line = "from test import *"
        expected = ""
        self._helper_check_import(line, expected, file_name="__init__.py")

    def test5(self) -> None:
        """
        Test import test.ab as tab: valid.
        """
        line = "import test.ab as tab"
        expected = ""
        self._helper_check_import(line, expected, file_name="test.py")

    def _helper_check_import(self, line: str, expected: str, file_name: str) -> None:
        file_name = file_name or "test.py"
        line_num = 1
        expected = f"{file_name}:{line_num}: {expected}" if expected else expected
        msg = lamchimp._check_import(file_name, line_num, line)
        self.assertEqual(expected, msg)
