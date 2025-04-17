import os

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_remove_empty_lines_in_function as larelinfu


# #############################################################################
# Test_remove_empty_lines
# #############################################################################


class Test_remove_empty_lines(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test cleaning empty lines in a single function.
        """
        self._run_test()

    def test2(self) -> None:
        """
        Test cleaning empty lines in methods inside a class.
        """
        self._run_test()

    def test3(self) -> None:
        """
        Test cleaning empty lines in methods and functions.
        """
        self._run_test()

    def test4(self) -> None:
        """
        Test cleaning empty lines in methods and functions without any empty
        lines.
        """
        self._run_test()

    def _run_test(self) -> None:
        """
        Helper to run test cases.
        """
        # Prepare inputs.
        test_input_dir = self.get_input_dir()
        text_file_path = os.path.join(test_input_dir, "test.txt")
        text = hio.from_file(text_file_path)
        # Run.
        actual = larelinfu._remove_empty_lines(text)
        # Check.
        test_output_dir = self.get_output_dir()
        output_file_path = os.path.join(test_output_dir, "test.txt")
        expected = hio.from_file(output_file_path)
        self.assert_equal(expected, "\n".join(actual))
