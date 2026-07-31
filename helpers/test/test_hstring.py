from typing import Tuple

import helpers.hstring as hstring
import helpers.hunit_test as hunitest


# #############################################################################
# TestExtractVersionFromFileName
# #############################################################################


class TestExtractVersionFromFileName(hunitest.TestCase):
    def _test_extract_version_from_file_name(
        self, version: str, expected: Tuple[int, int]
    ) -> None:
        """
        Verify function provides expected output on valid inputs.

        :param version: version in string format to input, e.g. 1.0
        :param expected: expected output version in (major, minor)
            format
        """
        fn = f"/app/datapull/ccxt/universe/download/universe_v{version}.json"
        self.assertEqual(hstring.extract_version_from_file_name(fn), expected)

    def test_extract_version_from_file_name1(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("1.1", (1, 1))

    def test_extract_version_from_file_name2(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("4", (4, 0))

    def test_extract_version_from_file_name3(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("1.0", (1, 0))

    def test_extract_version_from_file_name4(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("3.11", (3, 11))

    def test_extract_version_from_file_name5(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("16.2", (16, 2))

    def test_extract_version_from_file_name6(self) -> None:
        """
        Verify function provides expected output on valid input.
        """
        self._test_extract_version_from_file_name("25.11", (25, 11))

    def _test_extract_version_from_file_name_incorrect_format(
        self, file_name: str
    ) -> None:
        """
        Helper function to verify function raises AssertionError on incorrect
        input format.

        :param file_name: incorrect file_name to test
        """
        expected_fail = "Can't parse file"
        with self.assertRaises(AssertionError) as fail:
            _ = hstring.extract_version_from_file_name(file_name)
        self.assertIn(expected_fail, str(fail.exception))

    def test_extract_version_from_file_name_incorrect_format1(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format("incorrect")

    def test_extract_version_from_file_name_incorrect_format2(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format(
            "universe_vxx.json"
        )

    def test_extract_version_from_file_name_incorrect_format3(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format(
            "universe_v.1.json"
        )

    def test_extract_version_from_file_name_incorrect_format4(self) -> None:
        """
        Verify function raises AssertionError on incorrect input format.
        """
        self._test_extract_version_from_file_name_incorrect_format(
            "universe_11.json"
        )
