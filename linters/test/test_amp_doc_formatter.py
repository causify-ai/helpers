import os

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
        test6_input_dir = self.get_input_dir()
        text_file_path = os.path.join(test6_input_dir, "test.txt")
        text = hio.from_file(text_file_path)
        expected = text
        actual = self._docformatter(text)
        self.assertEqual(expected, actual)

    def test7(self) -> None:
        """
        Test that unbalanced backticks are correctly flagged.
        """
        # Prepare inputs.
        text = '''def func1():
    """
    First function.

    ```
    Valid backticks. 
    ```
    """


def func2():
    """
    Second function.

    ```
    Missing closing backticks.
    """


def func3():
    """
    Third function.

    ```
    Missing closing backticks.
    """
'''
        scratch_dir = self.get_scratch_space()
        temp_file = os.path.join(scratch_dir, "temp_file.py")
        hio.to_file(temp_file, text)
        # Run.
        actual_warnings = lamdofor._DocFormatter().execute(
            file_name=temp_file, pedantic=0
        )[0]
        actual_content: str = hio.from_file(temp_file)
        # Check.
        expected_warnings = (
            f"{temp_file}:12: Found unbalanced triple backticks; make sure both opening and closing backticks are the leftmost element of their line"
            f"\n{temp_file}:21: Found unbalanced triple backticks; make sure both opening and closing backticks are the leftmost element of their line"
        )
        self.assertEqual(actual_warnings, expected_warnings) 
        self.assert_equal(actual_content, text, fuzzy_match=True)

    def test8(self) -> None:
        """
        Test that unbalanced backticks are correctly flagged.
        """
        # Prepare inputs.
        text = '''   """
    E.g., ```

    # Find all the dependency of a module from itself
    > i find_dependency --module-name "amp.dataflow.model" --mode "find_lev2_deps" --ignore-helpers --only-module dataflow
    amp/dataflow/model/stats_computer.py:16 dataflow.core
    amp/dataflow/model/model_plotter.py:4   dataflow.model
    ```

    :param module_name: the module path to analyze (e.g., `amp.dataflow.model`)
    :param mode:
        - `print_deps`: print the result of grepping for imports
        - `find_deps`: find all the dependencies
        - `find_lev1_deps`, `find_lev2_deps`: find all the dependencies
    :param only_module: keep only imports containing a certain module (e.g., `dataflow`)
    :param ignore_standard_libs: ignore the Python standard libs (e.g., `os`, `...`)
    :param ignore_helpers: ignore the `helper` lib
    :param remove_dups: remove the duplicated imports
    """
'''
        scratch_dir = self.get_scratch_space()
        temp_file = os.path.join(scratch_dir, "temp_file.py")
        hio.to_file(temp_file, text)
        # Run.
        actual_warnings = lamdofor._DocFormatter().execute(
            file_name=temp_file, pedantic=0
        )[0]
        actual_content: str = hio.from_file(temp_file)
        # Check.
        expected_warnings = (
            f"{temp_file}:1: Found unbalanced triple backticks; make sure both opening and closing backticks are the leftmost element of their line"
        )
        self.assertEqual(actual_warnings, expected_warnings) 
        self.assert_equal(actual_content, text, fuzzy_match=True)

    def _docformatter(self, text: str) -> str:
        """
        Run the docformatter on the temp file in scratch space.

        :param text: content to be formatted
        :return: modified content after formatting
        """
        scratch_dir = self.get_scratch_space()
        temp_file = os.path.join(scratch_dir, "temp_file.py")
        hio.to_file(temp_file, text)
        lamdofor._DocFormatter().execute(file_name=temp_file, pedantic=0)
        content: str = hio.from_file(temp_file)
        return content
