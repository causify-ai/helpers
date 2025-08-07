import logging
import os
import textwrap

import pandas as pd

import dev_scripts_helpers.documentation.generate_EDA_context as dshdgedco
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _write_input_file(
    test_case: hunitest.TestCase, txt: str, file_name: str
) -> str:
    """
    Write test content to a file in the scratch space.

    :param txt: the content of the file
    :param file_name: the name of the file
    :return: the path to the file with the test content
    """
    txt = txt.strip()
    # Get file path to write.
    dir_name = test_case.get_scratch_space()
    file_path = os.path.join(dir_name, file_name)
    file_path = os.path.abspath(file_path)
    # Create the file.
    hio.to_file(file_path, txt)
    return file_path


# #############################################################################
# Test_read_function_table
# #############################################################################


class Test_read_function_table(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test convert a table from a Markdown file into a DataFrame.
        """
        # Prepare inputs.
        content = """
        | Function Type   | Script Path     | Function Name             |
        |-----------------|-----------------|---------------------------|
        | data conversion | helpers/hcsv.py | convert_csv_to_pq         |
        """
        file_path = _write_input_file(self, content, "input_table.md")
        # Run function.
        actual = dshdgedco._read_function_table(file_path)
        # Check output.
        expected = pd.DataFrame(
            {
                "Function Type": ["data conversion"],
                "Script Path": ["helpers/hcsv.py"],
                "Function Name": ["convert_csv_to_pq"],
            }
        )
        self.assert_equal(
            actual.to_string(index=False), expected.to_string(index=False)
        )


# #############################################################################
# Test_get_function_line_range_and_docstring
# #############################################################################


class Test_get_function_line_range_and_docstring(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test extracting line range and docstring from a function.
        """
        # Prepare inputs.
        content = '''
        def sample_function() -> None:
            """
            This is a test docstring.
            """
            return None
        '''
        file_path = _write_input_file(self, content, "sample.py")
        # Run function.
        actual = dshdgedco._get_function_line_range_and_docstring(
            file_path, "sample_function"
        )
        # Check output.
        expected = ("1-5", "This is a test docstring.")
        self.assertEqual(actual, expected)


# #############################################################################
# Test_enrich_function_table
# #############################################################################


class Test_enrich_function_table(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test enriching a function table with line range and docstring.
        """
        # Prepare inputs.
        content = '''
        def sample_function() -> None:
            """
            This is a test docstring.
            """
            return None
        '''
        file_path = _write_input_file(self, content, "sample.py")
        df = pd.DataFrame(
            {
                "Function Type": ["data conversion"],
                "Script Path": [file_path],
                "Function Name": ["sample_function"],
            }
        )
        # Run function.
        actual = dshdgedco._enrich_function_table(df)
        # Check output.
        expected = pd.DataFrame(
            {
                "Function Type": ["data conversion"],
                "Script Path": [file_path],
                "Function Name": ["sample_function"],
                "Line Range": ["1-5"],
                "Docstring": ["This is a test docstring."],
            }
        )
        self.assert_equal(
            actual.to_string(index=False), expected.to_string(index=False)
        )


# #############################################################################
# Test_write_markdown_table
# #############################################################################


class Test_write_markdown_table(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test that the Markdown file output matches the expected table format.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "Function Type": ["data conversion"],
                "Script Path": ["sample.py"],
                "Function Name": ["sample_function"],
                "Line Range": ["1-5"],
                "Docstring": ["This is a test docstring."],
            }
        )
        file_path = _write_input_file(self, "", "output.md")
        # Run function.
        dshdgedco._write_markdown_table(df, file_path)
        actual = hio.from_file(file_path)
        # Check output.
        expected = textwrap.dedent(
            """\
        | Function Type | Script Path | Function Name | Line Range | Docstring |
        | ------------- | ----------- | ------------- | ---------- | --------- |
        | data conversion | sample.py | sample_function | 1-5 | This is a test docstring. |
        """
        )
        self.assert_equal(actual.strip(), expected.strip())
