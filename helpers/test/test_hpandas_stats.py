import logging
from typing import Dict, List

import pandas as pd

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# Test_compute_duration_df
# #############################################################################


class Test_compute_duration_df(hunitest.TestCase):
    """
    Compute timestamp stats from dfs and check the intersection.
    """

    @staticmethod
    def get_dict_with_dfs() -> Dict[str, pd.DataFrame]:
        timestamp_index1 = [
            pd.Timestamp("2022-01-01 21:00:00+00:00"),
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
            pd.Timestamp("2022-01-01 21:05:00+00:00"),
            pd.Timestamp("2022-01-01 21:06:00+00:00"),
            pd.Timestamp("2022-01-01 21:06:00+00:00"),
        ]
        timestamp_index2 = [
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
            pd.Timestamp("2022-01-01 21:05:00+00:00"),
        ]
        timestamp_index3 = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
        ]
        #
        value1 = {"value1": [None, None, 1, 2, 3, 4, 5, None]}
        value2 = {"value2": [1, 2, 3, None]}
        value3 = {"value3": [None, None, 1, 2]}
        #
        df1 = pd.DataFrame(value1, index=timestamp_index1)
        df2 = pd.DataFrame(value2, index=timestamp_index2)
        df3 = pd.DataFrame(value3, index=timestamp_index3)
        #
        tag_to_df = {
            "tag1": df1,
            "tag2": df2,
            "tag3": df3,
        }
        return tag_to_df

    def intersection_helper(
        self,
        valid_intersect: bool,
        expected_start_timestamp: pd.Timestamp,
        expected_end_timestamp: pd.Timestamp,
    ) -> None:
        """
        Checks if the intersection is valid and the same amongst all dfs.
        """
        tag_to_df = self.get_dict_with_dfs()
        _, tag_dfs = hpandas.compute_duration_df(
            tag_to_df, valid_intersect=valid_intersect, intersect_dfs=True
        )
        # Collect all start timestamps.
        start_timestamps = [tag_dfs[tag].index.min() for tag in tag_dfs]
        # Check that all start timestamps are equal.
        start_equal = all(
            element == start_timestamps[0] for element in start_timestamps
        )
        self.assertTrue(start_equal)
        # Check that start intersection is correct.
        required_start_intersection = expected_start_timestamp
        self.assertEqual(start_timestamps[0], required_start_intersection)
        # Collect all end timestamps.
        end_timestamps = [tag_dfs[tag].index.max() for tag in tag_dfs]
        # Check that all end timestamps are equal.
        end_equal = all(
            element == end_timestamps[0] for element in end_timestamps
        )
        self.assertTrue(end_equal)
        # Check that end intersection is correct.
        required_end_intersection = expected_end_timestamp
        self.assertEqual(end_timestamps[0], required_end_intersection)

    def test1(self) -> None:
        """
        Check only timestamp stats.
        """
        tag_to_df = self.get_dict_with_dfs()
        df_stats, _ = hpandas.compute_duration_df(tag_to_df)
        expected_length = 3
        expected_column_names = [
            "max_index",
            "max_valid_index",
            "min_index",
            "min_valid_index",
        ]
        expected_column_unique_values = None
        expected_signature = r"""# df=
        index=[tag1, tag3]
        columns=min_index,max_index,min_valid_index,max_valid_index
        shape=(3, 4)
                            min_index                  max_index            min_valid_index            max_valid_index
        tag1  2022-01-01 21:00:00+00:00  2022-01-01 21:06:00+00:00  2022-01-01 21:02:00+00:00  2022-01-01 21:06:00+00:00
        tag2  2022-01-01 21:02:00+00:00  2022-01-01 21:05:00+00:00  2022-01-01 21:02:00+00:00  2022-01-01 21:04:00+00:00
        tag3  2022-01-01 21:01:00+00:00  2022-01-01 21:04:00+00:00  2022-01-01 21:03:00+00:00  2022-01-01 21:04:00+00:00
        """
        self.check_df_output(
            df_stats,
            expected_length,
            expected_column_names,
            expected_column_unique_values,
            expected_signature,
        )

    def test_intersection1(self) -> None:
        """
        Modify initial DataFrames in dictionary with non-valid intersection
        (incl NaNs).
        """
        valid_intersect = False
        expected_start_timestamp = pd.Timestamp("2022-01-01 21:02:00+00:00")
        expected_end_timestamp = pd.Timestamp("2022-01-01 21:04:00+00:00")
        self.intersection_helper(
            valid_intersect, expected_start_timestamp, expected_end_timestamp
        )

    def test_intersection2(self) -> None:
        """
        Modify initial DataFrames in dictionary with valid intersection
        (excluding NaNs).
        """
        valid_intersect = True
        expected_start_timestamp = pd.Timestamp("2022-01-01 21:03:00+00:00")
        expected_end_timestamp = pd.Timestamp("2022-01-01 21:04:00+00:00")
        self.intersection_helper(
            valid_intersect, expected_start_timestamp, expected_end_timestamp
        )


# #############################################################################
# Test_compute_weighted_sum
# #############################################################################


class Test_compute_weighted_sum(hunitest.TestCase):
    def helper(
        self,
        index1: List[int],
        index2: List[int],
        weights_data: Dict[str, List[float]],
        index_mode: str,
        expected_signature: str,
    ) -> None:
        """
        Build inputs and check that function output is correct.
        """
        # Create test data.
        data1 = {"A": [1, 2], "B": [3, 4]}
        df1 = pd.DataFrame(data1, index=index1)
        data2 = {"A": [5, 6], "B": [7, 8]}
        df2 = pd.DataFrame(data2, index=index2)
        dfs = {"df1": df1, "df2": df2}
        # Create weights DataFrame.
        weights = pd.DataFrame(weights_data, index=dfs.keys())
        # Run the function.
        weighted_sums = hpandas.compute_weighted_sum(
            dfs=dfs, weights=weights, index_mode=index_mode
        )
        actual_signature = str(weighted_sums)
        self.assert_equal(actual_signature, expected_signature, fuzzy_match=True)

    def test_compute_weighted_sum1(self) -> None:
        """
        Check that weighted sums are computed correctly.

        index_mode = "assert_equal".
        """
        index1 = [0, 1]
        index2 = [0, 1]
        weights_data = {"w1": [0.2, 0.8]}
        index_mode = "assert_equal"
        expected_signature = r"""
            {'w1':      A    B
            0  4.2  6.2
            1  5.2  7.2}
            """
        self.helper(index1, index2, weights_data, index_mode, expected_signature)

    def test_compute_weighted_sum2(self) -> None:
        """
        Check that weighted sums are computed correctly.

        index_mode = "intersect".
        """
        index1 = [0, 1]
        index2 = [0, 2]
        weights_data = {"w1": [0.2, 0.8], "w2": [0.5, 0.5]}
        index_mode = "intersect"
        expected_signature = r"""
            {'w1':      A    B
            0  4.2  6.2
            1  NaN  NaN
            2  NaN  NaN, 'w2':      A    B
            0  3.0  5.0
            1  NaN  NaN
            2  NaN  NaN}
            """
        self.helper(index1, index2, weights_data, index_mode, expected_signature)

    def test_compute_weighted_sum3(self) -> None:
        """
        Check that weighted sums are computed correctly.

        index_mode = "leave_unchanged".
        """
        index1 = [0, 1]
        index2 = [2, 3]
        weights_data = {"w1": [0.2, 0.8]}
        index_mode = "leave_unchanged"
        expected_signature = r"""
            {'w1':      A    B
                0  NaN  NaN
                1  NaN  NaN
                2  NaN  NaN
                3  NaN  NaN}
            """
        self.helper(index1, index2, weights_data, index_mode, expected_signature)

    def test_compute_weighted_sum4(self) -> None:
        """
        Check that an assertion is raised if input is an empty dict.
        """
        dfs: Dict[str, pd.DataFrame] = {}
        weights_data = {"w1": [0.2, 0.8]}
        index_mode = "assert_equal"
        with self.assertRaises(AssertionError) as cm:
            hpandas.compute_weighted_sum(
                dfs=dfs,
                weights=pd.DataFrame(weights_data),
                index_mode=index_mode,
            )
        actual_signature = str(cm.exception)
        expected_signature = r"""
            * Failed assertion *
            cond={}
            dictionary of dfs must be nonempty
            """
        self.assert_equal(actual_signature, expected_signature, fuzzy_match=True)


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
        result_df = hpandas.get_value_counts_stats_df(df, "category", num_rows=10)
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
        result_df = hpandas.get_value_counts_stats_df(df, "category", num_rows=2)
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
        result_df = hpandas.get_value_counts_stats_df(df, "category", num_rows=0)
        # Check output - should return all unique values.
        self.assertEqual(result_df.shape[0], 3)
