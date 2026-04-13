import helpers.hunit_test as hunitest
import linters.amp_check_filename as lamchfil


class Test_check_notebook_dir(hunitest.TestCase):
    def test_check_notebook_dir1(self) -> None:
        """
        The notebook is not under 'notebooks': invalid.
        """
        file_name = "hello/world/notebook.ipynb"
        expected = (
            "hello/world/notebook.ipynb:1: "
            "each notebook should be under a 'notebooks' directory to not confuse pytest"
        )
        self._helper_check_notebook_dir(file_name, expected)

    def test_check_notebook_dir2(self) -> None:
        """
        The notebook is under 'notebooks': valid.
        """
        file_name = "hello/world/notebooks/notebook.ipynb"
        expected = ""
        self._helper_check_notebook_dir(file_name, expected)

    def test_check_notebook_dir3(self) -> None:
        """
        It's not a notebook: valid.
        """
        file_name = "hello/world/notebook.py"
        expected = ""
        self._helper_check_notebook_dir(file_name, expected)

    def _helper_check_notebook_dir(self, file_name: str, expected: str) -> None:
        msg = lamchfil._check_notebook_dir(file_name)
        self.assert_equal(msg, expected)


class Test_check_test_file_dir(hunitest.TestCase):
    def test_check_test_file_dir1(self) -> None:
        """
        Test is under `test`: valid.
        """
        file_name = "hello/world/test/test_all.py"
        expected = ""
        self._helper_check_test_file_dir(file_name, expected)

    def test_check_test_file_dir2(self) -> None:
        """
        Test is not under `test`: invalid.
        """
        file_name = "hello/world/test_all.py"
        expected = (
            "hello/world/test_all.py:1: "
            "test files should be under 'test' directory to be discovered by pytest"
        )
        self._helper_check_test_file_dir(file_name, expected)

    def test_check_test_file_dir3(self) -> None:
        """
        Test is not under `test`: invalid.
        """
        file_name = "hello/world/tests/test_all.py"
        expected = (
            "hello/world/tests/test_all.py:1: "
            "test files should be under 'test' directory to be discovered by pytest"
        )
        self._helper_check_test_file_dir(file_name, expected)

    def test_check_test_file_dir4(self) -> None:
        """
        It's a notebook: valid.
        """
        file_name = "hello/world/tests/test_all.ipynb"
        expected = ""
        self._helper_check_test_file_dir(file_name, expected)

    def _helper_check_test_file_dir(self, file_name: str, expected: str) -> None:
        msg = lamchfil._check_test_file_dir(file_name)
        self.assert_equal(msg, expected)


class Test_check_notebook_filename(hunitest.TestCase):
    def test1(self) -> None:
        r"""Check python files are not checked

        - Given python file
        - When function runs
        - Then no warning message is returned"""
        file_name = "linter/module.py"
        actual = lamchfil._check_notebook_filename(file_name)
        self.assertEqual("", actual)

    def test2(self) -> None:
        r"""Check filename rules

        - Given notebook filename starts with `Master_`
        - When function runs
        - Then no warning message is returned"""
        file_name = "linter/Master_notebook.ipynb"
        actual = lamchfil._check_notebook_filename(file_name)
        self.assertEqual("", actual)

    def test3(self) -> None:
        r"""Check filename rules

        - Given notebook filename matchs `\S+Task\d+_...`
        - When function runs
        - Then no warning message is returned"""
        file_name = "linter/PTask400_test.ipynb"
        actual = lamchfil._check_notebook_filename(file_name)
        self.assertEqual("", actual)

    def test4(self) -> None:
        r"""Check filename rules

        - Given notebook filename doesn't start with `Master_`
        - And notebook filename doesn't match `\S+Task\d+_...`
        - When function runs
        - Then a warning message is returned"""
        file_name = "linter/notebook.ipynb"
        expected = (
            f"{file_name}:1: "
            r"All notebook filenames start with `Master_` or match: `\S+Task\d+_...`"
        )
        actual = lamchfil._check_notebook_filename(file_name)
        self.assertEqual(expected, actual)

    def test5(self) -> None:
        r"""Check filename rules

        - Given notebook filename doesn't start with `Master_`
        - And notebook filename doesn't match `\S+Task\d+_...`
        - When function runs
        - Then a warning message is returned"""
        file_name = "linter/Task400.ipynb"
        expected = (
            f"{file_name}:1: "
            r"All notebook filenames start with `Master_` or match: `\S+Task\d+_...`"
        )
        actual = lamchfil._check_notebook_filename(file_name)
        self.assertEqual(expected, actual)

    def test6(self) -> None:
        r"""Check filename rules

        - Given notebook filename doesn't start with `Master_`
        - And notebook filename doesn't match `\S+Task\d+_...`
        - When function runs
        - Then a warning message is returned"""
        file_name = "linter/MegaTask200.ipynb"
        expected = (
            f"{file_name}:1: "
            r"All notebook filenames start with `Master_` or match: `\S+Task\d+_...`"
        )
        actual = lamchfil._check_notebook_filename(file_name)
        self.assertEqual(expected, actual)
