import logging

import numpy as np
import pandas as pd

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# TestDropNa
# #############################################################################


class TestDropNa(hunitest.TestCase):
    def test_dropna1(self) -> None:
        """
        Test if all types of NaNs are dropped.
        """
        # Prepare actual result.
        test_data = {
            "dummy_value_1": [np.nan, 1, 3, 2, 0],
            "dummy_value_2": ["0", "A", "B", None, "D"],
            "dummy_value_3": [0, 0, pd.NA, 0, 0],
        }
        test_df = pd.DataFrame(data=test_data)
        # Drop NA.
        actual = hpandas.dropna(test_df, drop_infs=False)
        # Prepare expected result.
        expected = {
            "dummy_value_1": [1, 0],
            "dummy_value_2": ["A", "D"],
            "dummy_value_3": [0, 0],
        }
        # Set the dtype of numeral columns to float to match the dataframe after NA dropping.
        expected = pd.DataFrame(data=expected).astype(
            {"dummy_value_1": "float64", "dummy_value_3": "object"}
        )
        # Set the index of the rows that remained.
        expected = expected.set_index(pd.Index([1, 4]))
        # Check.
        hunitest.compare_df(actual, expected)

    def test_dropna2(self) -> None:
        """
        Test if infs are dropped.
        """
        # Prepare actual result.
        test_data = {
            "dummy_value_1": [-np.inf, 1, 3, 2, 0],
            "dummy_value_2": ["0", "A", "B", "C", "D"],
            "dummy_value_3": [0, 0, np.inf, 0, 0],
        }
        test_df = pd.DataFrame(data=test_data)
        # Drop NA.
        actual = hpandas.dropna(test_df, drop_infs=True)
        # Prepare expected result.
        expected = {
            "dummy_value_1": [1, 2, 0],
            "dummy_value_2": ["A", "C", "D"],
            "dummy_value_3": [0, 0, 0],
        }
        # Set the dtype of numeral columns to float to match the dataframe after NA dropping.
        expected = pd.DataFrame(data=expected).astype(
            {"dummy_value_1": "float64", "dummy_value_3": "float64"}
        )
        # Set the index of the rows that remained.
        expected = expected.set_index(pd.Index([1, 3, 4]))
        # Check.
        hunitest.compare_df(actual, expected)


# #############################################################################
# TestDropAxisWithAllNans
# #############################################################################


class TestDropAxisWithAllNans(hunitest.TestCase):
    def test_drop_rows1(self) -> None:
        """
        Test if row full of nans is dropped.
        """
        # Prepare actual result.
        test_data = {
            "dummy_value_1": [np.nan, 2, 3],
            "dummy_value_2": [pd.NA, "B", "C"],  # type: ignore
            "dummy_value_3": [None, 1.0, 1.0],
        }
        test_df = pd.DataFrame(data=test_data)
        # Drop NA.
        actual = hpandas.drop_axis_with_all_nans(test_df, drop_rows=True)
        # Prepare expected result.
        expected = {
            "dummy_value_1": [2, 3],
            "dummy_value_2": ["B", "C"],
            "dummy_value_3": [1.0, 1.0],
        }
        # Set the dtype of numeral columns to float to match the dataframe after NA dropping.
        expected = pd.DataFrame(data=expected).astype(
            {"dummy_value_1": "float64"}
        )
        # Set the index of the rows that remained.
        expected = expected.set_index(pd.Index([1, 2]))
        # Check.
        hunitest.compare_df(actual, expected)

    def test_drop_rows2(self) -> None:
        """
        Test if non fully nan row is not dropped.
        """
        # Prepare actual result.
        test_data = {
            "dummy_value_1": [np.nan, 2, 3],
            "dummy_value_2": ["A", "B", "C"],  # type: ignore
            "dummy_value_3": [None, 1.0, 1.0],
        }
        test_df = pd.DataFrame(data=test_data)
        # Drop NA.
        actual = hpandas.drop_axis_with_all_nans(test_df, drop_rows=True)
        # Prepare expected result.
        expected = {
            "dummy_value_1": [np.nan, 2, 3],
            "dummy_value_2": ["A", "B", "C"],  # type: ignore
            "dummy_value_3": [None, 1.0, 1.0],
        }
        # Set the dtype of numeral columns to float to match the dataframe after NA dropping.
        expected = pd.DataFrame(data=expected).astype(
            {"dummy_value_1": "float64"}
        )
        # Set the index of the rows that remained.
        expected = expected.set_index(pd.Index([0, 1, 2]))
        # Check.
        hunitest.compare_df(actual, expected)

    def test_drop_columns1(self) -> None:
        """
        Test if column full of nans is dropped.
        """
        # Prepare actual result.
        test_data = {
            "dummy_value_1": [np.nan, pd.NA, None],
            "dummy_value_2": ["A", "B", "C"],
            "dummy_value_3": [1.0, 1.0, 1.0],
        }
        test_df = pd.DataFrame(data=test_data)
        # Drop NA.
        actual = hpandas.drop_axis_with_all_nans(test_df, drop_columns=True)
        # Prepare expected result.
        expected = {
            "dummy_value_2": ["A", "B", "C"],
            "dummy_value_3": [1.0, 1.0, 1.0],
        }
        expected = pd.DataFrame(data=expected)
        # Check.
        hunitest.compare_df(actual, expected)

    def test_drop_columns2(self) -> None:
        """
        Test if column that is not full of nans is not dropped.
        """
        # Prepare actual result.
        test_data = {
            "dummy_value_1": [np.nan, 2, None],
            "dummy_value_2": ["A", "B", "C"],
            "dummy_value_3": [1.0, 1.0, 1.0],
        }
        test_df = pd.DataFrame(data=test_data)
        # Drop NA.
        actual = hpandas.drop_axis_with_all_nans(test_df, drop_columns=True)
        # Prepare expected result.
        expected = {
            "dummy_value_1": [np.nan, 2, None],
            "dummy_value_2": ["A", "B", "C"],
            "dummy_value_3": [1.0, 1.0, 1.0],
        }
        expected = pd.DataFrame(data=expected)
        # Check.
        hunitest.compare_df(actual, expected)


# #############################################################################
# TestDropDuplicates
# #############################################################################


class TestDropDuplicates(hunitest.TestCase):
    """
    Test that duplicates are dropped correctly.
    """

    @staticmethod
    def get_test_data() -> pd.DataFrame:
        test_data = [
            (1, "A", 3.2),
            (1, "A", 3.2),
            (10, "B", 3.2),
            (8, "A", 3.2),
            (4, "B", 8.2),
            (10, "B", 3.2),
        ]
        index = [
            "dummy_value1",
            "dummy_value3",
            "dummy_value2",
            "dummy_value1",
            "dummy_value1",
            "dummy_value2",
        ]
        columns = ["int", "letter", "float"]
        df = pd.DataFrame(data=test_data, index=index, columns=columns)
        return df

    def test_drop_duplicates1(self) -> None:
        """
        - use_index = True
        - column_subset is not None
        """
        # Prepare test data.
        df = self.get_test_data()
        use_index = True
        column_subset = ["float"]
        no_duplicates_df = hpandas.drop_duplicates(
            df, use_index, column_subset=column_subset
        )
        no_duplicates_df = hpandas.df_to_str(no_duplicates_df)
        # Prepare expected result.
        expected_signature = r"""
                      int letter  float
        dummy_value1    1      A    3.2
        dummy_value3    1      A    3.2
        dummy_value2   10      B    3.2
        dummy_value1    4      B    8.2
        """
        # Check.
        self.assert_equal(no_duplicates_df, expected_signature, fuzzy_match=True)

    def test_drop_duplicates2(self) -> None:
        """
        - use_index = True
        - column_subset = None
        """
        # Prepare test data.
        df = self.get_test_data()
        use_index = True
        no_duplicates_df = hpandas.drop_duplicates(df, use_index)
        no_duplicates_df = hpandas.df_to_str(no_duplicates_df)
        # Prepare expected result.
        expected_signature = r"""
                      int letter  float
        dummy_value1    1      A    3.2
        dummy_value3    1      A    3.2
        dummy_value2   10      B    3.2
        dummy_value1    8      A    3.2
        dummy_value1    4      B    8.2
        """
        # Check.
        self.assert_equal(no_duplicates_df, expected_signature, fuzzy_match=True)

    def test_drop_duplicates3(self) -> None:
        """
        - use_index = False
        - column_subset = None
        """
        # Prepare test data.
        df = self.get_test_data()
        use_index = False
        no_duplicates_df = hpandas.drop_duplicates(df, use_index)
        no_duplicates_df = hpandas.df_to_str(no_duplicates_df)
        # Prepare expected result.
        expected_signature = r"""
                      int letter  float
        dummy_value1    1      A    3.2
        dummy_value2   10      B    3.2
        dummy_value1    8      A    3.2
        dummy_value1    4      B    8.2
        """
        # Check.
        self.assert_equal(no_duplicates_df, expected_signature, fuzzy_match=True)

    def test_drop_duplicates4(self) -> None:
        """
        - use_index = False
        - column_subset is not None
        """
        # Prepare test data.
        df = self.get_test_data()
        use_index = False
        column_subset = ["letter", "float"]
        no_duplicates_df = hpandas.drop_duplicates(
            df, use_index, column_subset=column_subset
        )
        no_duplicates_df = hpandas.df_to_str(no_duplicates_df)
        # Prepare expected result.
        expected_signature = r"""
                      int letter  float
        dummy_value1    1      A    3.2
        dummy_value2   10      B    3.2
        dummy_value1    4      B    8.2
        """
        # Check.
        self.assert_equal(no_duplicates_df, expected_signature, fuzzy_match=True)


# #############################################################################
# Test_impute_nans
# #############################################################################


class Test_impute_nans(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test basic imputation of "nan" strings with empty string.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "col1": ["value1", "nan", "value3"],
                "col2": ["a", "b", "c"],
            }
        )
        # Call function to test.
        result_df = hpandas.impute_nans(df, "col1", "")
        # Check output.
        self.assertEqual(result_df["col1"].tolist(), ["value1", "", "value3"])
        self.assertEqual(result_df["col2"].tolist(), ["a", "b", "c"])

    def test2(self) -> None:
        """
        Test imputation with a custom value.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "col1": ["value1", "nan", "value3"],
                "col2": ["a", "nan", "c"],
            }
        )
        # Call function to test.
        result_df = hpandas.impute_nans(df, "col2", "MISSING")
        # Check output.
        self.assertEqual(result_df["col1"].tolist(), ["value1", "nan", "value3"])
        self.assertEqual(result_df["col2"].tolist(), ["a", "MISSING", "c"])

    def test3(self) -> None:
        """
        Test with no "nan" values present.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "col1": ["value1", "value2", "value3"],
                "col2": ["a", "b", "c"],
            }
        )
        # Call function to test.
        result_df = hpandas.impute_nans(df, "col1", "")
        # Check output - should be unchanged.
        self.assertEqual(result_df["col1"].tolist(), ["value1", "value2", "value3"])
