import tempfile

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_doc_formatter as lamdofor


# #############################################################################
# Test_docformatter
# #############################################################################


class Test_docformatter(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test that the docstring should be dedented.
        """
        text = '''
"""     Test 1.

    Test 2."""
        '''
        expected = '''
"""
Test 1.

Test 2.
"""
'''
        actual = self._docformatter(text)
        self.assertEqual(expected.strip(), actual.strip())

    def test2(self) -> None:
        """
        Test docstring transformations.

        - A dot is added at the end
        - The first word is capitalized
        - The docstring is moved onto a separate line
        """
        text = '''
"""this is a test"""
        '''
        expected = '''
"""
This is a test.
"""
'''
        actual = self._docformatter(text)
        self.assertEqual(expected.strip(), actual.strip())

    def test3(self) -> None:
        """
        Test that single quotes are replaced by double quotes.
        """
        text = """
'''This is a test.'''
"""
        expected = '''
"""
This is a test.
"""
'''
        actual = self._docformatter(text)
        self.assertEqual(expected.strip(), actual.strip())

    def test4(self) -> None:
        """
        Test a well-formed docstring.
        """
        text = '''
def sample_method() -> None:
    """
    Process NaN values in a series according to the parameters.

    :param srs: pd.Series to process
    :param mode: method of processing NaNs
        - None - no transformation
        - "ignore" - drop all NaNs
        - "ffill" - forward fill not leading NaNs
        - "ffill_and_drop_leading" - do ffill and drop leading NaNs
        - "fill_with_zero" - fill NaNs with 0
        - "strict" - raise ValueError that NaNs are detected
    :param info: information storage
    :return: transformed copy of input series
    """
'''
        expected = text
        actual = self._docformatter(text)
        self.assertEqual(expected, actual)

    def test5(self) -> None:
        """
        Test that `# docformatter: ignore` keeps the docstring as-is.
        """
        text = '''
def sample_method1() -> None:
    # docformatter: ignore
    """
    this is a test
    """

def sample_method2() -> None:
    """
    this is a test
    """
'''
        expected = '''
def sample_method1() -> None:
    # docformatter: ignore
    """
    this is a test
    """

def sample_method2() -> None:
    """
    This is a test.
    """
'''
        actual = self._docformatter(text)
        self.assertEqual(expected, actual)

    def test6(self) -> None:
        """
        Test that code blocks remain as-is.
        """
        text = '''
def block_in_the_middle() -> None:
    """
    Test docstring.

    ```
    Code block.
    ```

    Some more text.
    """

def block_after_param(cmd: str) -> None:
    """
    Test docstring.

    Some more text.

    :param cmd: command, e.g.,
    ```
    > git pull
    ```
    """

def block_without_empty_lines(cmd: str) -> None:
    """
    Test docstring.

    Text before.
    ```
    > git pull
    ```
    Text after.
    """

def two_code_blocks(cmd: str) -> None:
    """
    Test docstring.

    ```
    > git pull
    ```
    Text in between.
    ```
    > git push
    ```
    """

def block_in_second_line(cmd: str) -> None:
    """
    Test docstring:
    ```
    > git pull
    ```
    """

def long_docstring_line(cmd: str) -> None:
    """
    Test docstring.

    Very very very very very very very very very very long line.
    ```
    > git pull
    ```
    """

def empty_lines_in_code_block(cmd: str) -> None:
    """
    Test docstring.

    ```
    # To lint the files modified in the current git client:
    > i lint --modified

    # To exclude certain paths from linting:
    > i lint --files="$(find . -name '*.py' -not -path './compute/*' -not -path './amp/*')"
    ```

    Text after.
    """
'''
        expected = text
        actual = self._docformatter(text)
        self.assertEqual(expected, actual)

    def _docformatter(self, text: str) -> str:
        """
        Run the docformatter on the temp file.

        :param text: content to be formatted
        :return: modified content after formatting
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".py")
        hio.to_file(tmp.name, text)
        lamdofor._DocFormatter().execute(file_name=tmp.name, pedantic=0)
        content: str = hio.from_file(tmp.name)
        tmp.close()
        return content
