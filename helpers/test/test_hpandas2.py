"""
Tests for helpers.hpandas2 module.
"""

import io
import logging

import numpy as np
import pandas as pd
import pytest

import helpers.hpandas2 as hpandas2
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


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
        result_df = hpandas2.impute_nans(df, "col1", "")
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
        result_df = hpandas2.impute_nans(df, "col2", "MISSING")
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
        result_df = hpandas2.impute_nans(df, "col1", "")
        # Check output - should be unchanged.
        self.assertEqual(result_df["col1"].tolist(), ["value1", "value2", "value3"])


# #############################################################################
# Test_get_value_counts_stats_df
# #############################################################################


class Test_get_value_counts_stats_df(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test basic value counts with default parameters.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "category": [
                    "A",
                    "B",
                    "A",
                    "C",
                    "A",
                    "B",
                    "D",
                    "A",
                    "C",
                    "A",
                ]
            }
        )
        # Call function to test.
        result_df = hpandas2.get_value_counts_stats_df(df, "category", num_rows=10)
        # Check output.
        self.assertEqual(result_df.index.tolist(), ["A", "B", "C", "D"])
        self.assertEqual(result_df["count"].tolist(), [5, 2, 2, 1])
        expected_pcts = [50.0, 20.0, 20.0, 10.0]
        actual_pcts = result_df["pct [%]"].tolist()
        self.assertAlmostEqual(actual_pcts[0], expected_pcts[0])
        self.assertAlmostEqual(actual_pcts[1], expected_pcts[1])
        self.assertAlmostEqual(actual_pcts[2], expected_pcts[2])
        self.assertAlmostEqual(actual_pcts[3], expected_pcts[3])

    def test2(self) -> None:
        """
        Test limiting the number of rows returned.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "category": [
                    "A",
                    "B",
                    "A",
                    "C",
                    "A",
                    "B",
                    "D",
                    "A",
                    "C",
                    "A",
                ]
            }
        )
        # Call function to test.
        result_df = hpandas2.get_value_counts_stats_df(df, "category", num_rows=2)
        # Check output - should only return top 2.
        self.assertEqual(result_df.shape[0], 2)
        self.assertEqual(result_df.index.tolist(), ["A", "B"])

    def test3(self) -> None:
        """
        Test with num_rows=0 to return all rows.
        """
        # Prepare input.
        df = pd.DataFrame({"category": ["A", "B", "A", "C", "A", "B"]})
        # Call function to test.
        result_df = hpandas2.get_value_counts_stats_df(df, "category", num_rows=0)
        # Check output - should return all unique values.
        self.assertEqual(result_df.shape[0], 3)
