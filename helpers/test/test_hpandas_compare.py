import logging
from typing import Tuple

import numpy as np
import pandas as pd
import pytest

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"

# #############################################################################
# DataFrame Comparison Tests
# #############################################################################


class TestCompareDataframeRows(hunitest.TestCase):
    def get_test_data(self) -> pd.DataFrame:
        test_data = {
            "dummy_value_1": [0, 1, 3, 2, 0],
            "dummy_value_2": ["0", "A", "C", "B", "D"],
            "dummy_value_3": [0, 0, 0, 0, 0],
        }
        df = pd.DataFrame(data=test_data)
        df.index.name = "test"
        return df

    def test_compare_dataframe_rows1(self) -> None:
        """
        Verify that differences are caught and displayed properly.
        """
        # Prepare inputs.
        test_data = self.get_test_data()
        edited_test_data = test_data.copy()[1:-1]
        edited_test_data.loc[1, "dummy_value_2"] = "W"
        edited_test_data.loc[2, "dummy_value_2"] = "Q"
        edited_test_data.loc[2, "dummy_value_3"] = "1"
        # Run.
        data_difference = hpandas.compare_dataframe_rows(
            test_data, edited_test_data
        )
        # Check output.
        actual = hpandas.df_to_str(data_difference)
        expected = r"""  dummy_value_2       dummy_value_3       test
                   self other          self other
        0             W     A          <NA>  <NA>    1
        1             Q     C             1     0    2"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_compare_dataframe_rows2(self) -> None:
        """
        Verify that differences are caught and displayed properly without
        original index.
        """
        # Prepare inputs.
        test_data = self.get_test_data()
        test_data.index.name = None
        edited_test_data = test_data.copy()[1:-1]
        edited_test_data.loc[1, "dummy_value_2"] = "W"
        edited_test_data.loc[2, "dummy_value_2"] = "Q"
        edited_test_data.loc[2, "dummy_value_3"] = "1"
        # Run.
        data_difference = hpandas.compare_dataframe_rows(
            test_data, edited_test_data
        )
        # Check output.
        actual = hpandas.df_to_str(data_difference)
        expected = r"""  dummy_value_2       dummy_value_3
                   self other          self other
        0             W     A           NaN   NaN
        1             Q     C             1   0.0"""
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# TestReadDataFromS3
# #############################################################################


@pytest.mark.requires_ck_infra
@pytest.mark.requires_aws
class Test_compare_dfs(hunitest.TestCase):
    """
    - Define two DataFrames that can be either equal or different in terms of columns or rows
    - Compare its values by calculating the difference
    """

    @staticmethod
    def get_test_dfs_equal() -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Both DataFrames have only equal rows and columns names.
        """
        timestamp_index1 = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
        ]
        values1 = {
            "tsA": pd.Series([1, 2, 3]),
            "tsB": pd.Series([4, 5, 6]),
            "tsC": pd.Series([7, 8, 9]),
            "timestamp": timestamp_index1,
        }
        df1 = pd.DataFrame(data=values1)
        df1 = df1.set_index("timestamp")
        #
        timestamp_index2 = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
        ]
        values2 = {
            "tsA": pd.Series([1.1, 1.9, 3.15]),
            "tsB": pd.Series([0, 5, 5.8]),
            "tsC": pd.Series([6.5, 8.6, 9.07]),
            "timestamp": timestamp_index2,
        }
        df2 = pd.DataFrame(data=values2)
        df2 = df2.set_index("timestamp")
        return df1, df2

    @staticmethod
    def get_test_dfs_close_to_zero() -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        DataFrames with values that are close to 0.
        """
        timestamp_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
        ]
        values1 = {
            "tsA": [3e-9, -3e-9],
            "tsB": [6e-3, 4e-9],
            "timestamp": timestamp_index,
        }
        df1 = pd.DataFrame(data=values1)
        df1 = df1.set_index("timestamp")
        #
        values2 = {
            "tsA": [15e-3, -5e-9],
            "tsB": [5e-9, 3e-9],
            "timestamp": timestamp_index,
        }
        df2 = pd.DataFrame(data=values2)
        df2 = df2.set_index("timestamp")
        return df1, df2

    def get_test_dfs_different(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        DataFrames have both unique and equal rows and columns.
        """
        df1, df2 = self.get_test_dfs_equal()
        df2 = df2.rename(
            columns={"tsC": "extra_col"},
            index={
                pd.Timestamp("2022-01-01 21:03:00+00:00"): pd.Timestamp(
                    "2022-01-01 21:04:00+00:00"
                )
            },
        )
        return df1, df2

    def test1(self) -> None:
        """
        - DataFrames are equal
        - Column and row modes are `equal`
        - diff_mode = "diff"
        """
        df1, df2 = self.get_test_dfs_equal()
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            row_mode="equal",
            column_mode="equal",
            diff_mode="diff",
            assert_diff_threshold=None,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                           tsA.diff  tsB.diff  tsC.diff
        timestamp
        2022-01-01 21:01:00+00:00     -0.10       4.0      0.50
        2022-01-01 21:02:00+00:00      0.10       0.0     -0.60
        2022-01-01 21:03:00+00:00     -0.15       0.2     -0.07
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        - DataFrames are equal
        - Column and row modes are `equal`
        - diff_mode = "pct_change"
        - zero_vs_zero_is_zero = False
        - remove_inf = False
        """
        df1, df2 = self.get_test_dfs_equal()
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            row_mode="equal",
            column_mode="equal",
            diff_mode="pct_change",
            assert_diff_threshold=None,
            zero_vs_zero_is_zero=False,
            remove_inf=False,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                  tsA.pct_change  tsB.pct_change  tsC.pct_change
        timestamp
        2022-01-01 21:01:00+00:00       -9.090909             inf        7.692308
        2022-01-01 21:02:00+00:00        5.263158        0.000000       -6.976744
        2022-01-01 21:03:00+00:00       -4.761905        3.448276       -0.771775
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        - DataFrames are not equal
        - Column and row modes are `inner`
        - diff_mode = "diff"
        """
        df1, df2 = self.get_test_dfs_different()
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            row_mode="inner",
            column_mode="inner",
            diff_mode="diff",
            assert_diff_threshold=None,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""               tsA.diff  tsB.diff
        timestamp
        2022-01-01 21:01:00+00:00      -0.1       4.0
        2022-01-01 21:02:00+00:00       0.1       0.0
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test4(self) -> None:
        """
        - DataFrames are not equal
        - Column and row modes are `inner`
        - diff_mode = "pct_change"
        """
        df1, df2 = self.get_test_dfs_different()
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            row_mode="inner",
            column_mode="inner",
            diff_mode="pct_change",
            assert_diff_threshold=None,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                     tsA.pct_change  tsB.pct_change
        timestamp
        2022-01-01 21:01:00+00:00       -9.090909             NaN
        2022-01-01 21:02:00+00:00        5.263158             0.0
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test5(self) -> None:
        """
        - DataFrames are equal
        - Column and row modes are `equal`
        - diff_mode = "diff"
        - All values of the second DataFrame are zeros

        Check that if the second DataFrame consists of zeros,
        the function will perform comparison to the initial DataFrame.
        """
        df1, df2 = self.get_test_dfs_different()
        # Create DataFrame with zeros.
        df2 = df1 * 0
        # Compare.
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            row_mode="equal",
            column_mode="equal",
            diff_mode="diff",
            assert_diff_threshold=None,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                  tsA.diff  tsB.diff  tsC.diff
        timestamp
        2022-01-01 21:01:00+00:00         1         4         7
        2022-01-01 21:02:00+00:00         2         5         8
        2022-01-01 21:03:00+00:00         3         6         9
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test6(self) -> None:
        """
        - DataFrames are equal
        - Column and row modes are `equal`
        - diff_mode = "pct_change"
        - close_to_zero_threshold = 1e-6
        - zero_vs_zero_is_zero = True
        - remove_inf = True

        The second DataFrame has numbers below the close_to_zero_threshold.
        """
        df1, df2 = self.get_test_dfs_close_to_zero()
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            row_mode="equal",
            column_mode="equal",
            diff_mode="pct_change",
            assert_diff_threshold=None,
            zero_vs_zero_is_zero=True,
            remove_inf=True,
        )
        #
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                    tsA.pct_change  tsB.pct_change
        timestamp
        2022-01-01 21:01:00+00:00          -100.0             NaN
        2022-01-01 21:02:00+00:00             0.0             0.0
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test7(self) -> None:
        """
        - DataFrames are equal
        - Column and row modes are `equal`
        - diff_mode = "pct_change"
        - close_to_zero_threshold = 1e-6
        - zero_vs_zero_is_zero = False
        - remove_inf = False

        The second DataFrame has numbers below the close_to_zero_threshold.
        """
        df1, df2 = self.get_test_dfs_close_to_zero()
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            row_mode="equal",
            column_mode="equal",
            diff_mode="pct_change",
            assert_diff_threshold=None,
            zero_vs_zero_is_zero=False,
            remove_inf=False,
        )
        #
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                    tsA.pct_change  tsB.pct_change
        timestamp
        2022-01-01 21:01:00+00:00          -100.0             inf
        2022-01-01 21:02:00+00:00             NaN             NaN
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test8(self) -> None:
        """
        Test NaN comparison with NaNs present at different location in two
        dataframes.
        """
        # Build test dataframes.
        df1 = pd.DataFrame(
            data={
                "A": [1.1, np.nan, 3.1, np.nan, np.inf, np.inf],
                "B": [0, 0, 0, 0, 0, 0],
            }
        )
        df2 = pd.DataFrame(
            data={
                "A": [3.0, 2.2, np.nan, np.nan, np.nan, np.inf],
                "B": [0, 0, 0, 0, 0, 0],
            }
        )
        # Check.
        with self.assertRaises(AssertionError) as cm:
            compare_nans = True
            hpandas.compare_dfs(
                df1, df2, compare_nans=compare_nans, only_warning=False
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        DataFrame.iloc[:, 0] (column name="A") are different

        DataFrame.iloc[:, 0] (column name="A") values are different (66.66667 %)
        [index]: [0, 1, 2, 3, 4, 5]
        [left]:  [1.1, nan, 3.1, nan, inf, inf]
        [right]: [3.0, 2.2, nan, nan, nan, inf]
        At positional index 0, first diff: 1.1 != 3.0
        df1=
             A  B
        0  1.1  0
        1  NaN  0
        2  3.1  0
        3  NaN  0
        4  inf  0
        5  inf  0
        and df2=
             A  B
        0  3.0  0
        1  2.2  0
        2  NaN  0
        3  NaN  0
        4  NaN  0
        5  inf  0
        are not equal.
        """
        self.assert_equal(actual, expected, purify_text=True, fuzzy_match=True)

    def test9(self) -> None:
        """
        Test to verify the error when df1 and df2 have different index types.
        """
        df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        # Create df2 with a DatetimeIndex.
        dates = pd.date_range("2021-01-01", periods=3)
        df2 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "timestamp": dates})
        df2 = df2.set_index("timestamp")
        with self.assertRaises(AssertionError) as cm:
            hpandas.compare_dfs(
                df1,
                df2,
                row_mode="equal",
                column_mode="equal",
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        cond=False
        df1.index.difference(df2.index)=
        RangeIndex(start=0, stop=3, step=1)
        df2.index.difference(df1.index)=
        DatetimeIndex(['2021-01-01', '2021-01-02', '2021-01-03'], dtype='datetime64[ns]', freq=None)
        """
        self.assert_equal(actual, expected, purify_text=True, fuzzy_match=True)

    def test10(self) -> None:
        """
        Check `assert_diff_threshold` functionality in presence of NaN values
        in df_diff.
        """
        timestamp_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
        ]
        df2 = pd.DataFrame(
            {
                "tsA": [100, 200, 300],
                "tsB": [400, 500, 600],
                "tsC": [700, 800, 900],
                "timestamp": timestamp_index,
            }
        )
        df2 = df2.set_index("timestamp")
        adjustment_factor = 1.000001
        df1 = df2 * adjustment_factor
        df1.iloc[1, 2] = np.nan
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            diff_mode="pct_change",
            only_warning=True,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                  tsA.pct_change  tsB.pct_change  tsC.pct_change
        timestamp
        2022-01-01 21:01:00+00:00         0.0001           0.0001            0.0001
        2022-01-01 21:02:00+00:00         0.0001           0.0001            NaN
        2022-01-01 21:03:00+00:00         0.0001           0.0001            0.0001
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test11(self) -> None:
        """
        Check functionality for `remove_inf = False` in presence of `diff_mode
        = 'pct_change'`.
        """
        timestamp_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
        ]
        df2 = pd.DataFrame(
            {
                "tsA": [100, 200, 300],
                "tsB": [400, 500, 600],
                "tsC": [700, 800, 900],
                "timestamp": timestamp_index,
            }
        )
        df2 = df2.set_index("timestamp")
        adjustment_factor = 1.00001
        df1 = df2 * adjustment_factor
        df1.iloc[1, 2] = np.inf
        with self.assertRaises(AssertionError) as cm:
            hpandas.compare_dfs(
                df1,
                df2,
                diff_mode="pct_change",
                remove_inf=False,
                only_warning=False,
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        DataFrame.iloc[:, 0] (column name="tsA") are different

        DataFrame.iloc[:, 0] (column name="tsA") values are different (100.0 %)
        [index]: [2022-01-01 21:01:00+00:00, 2022-01-01 21:02:00+00:00, 2022-01-01 21:03:00+00:00]
        [left]:  [False, False, False]
        [right]: [True, True, True]
        df1=
                                       tsA      tsB      tsC
        timestamp
        2022-01-01 21:01:00+00:00  100.001  400.004  700.007
        2022-01-01 21:02:00+00:00  200.002  500.005      inf
        2022-01-01 21:03:00+00:00  300.003  600.006  900.009
        and df2=
                                   tsA  tsB  tsC
        timestamp
        2022-01-01 21:01:00+00:00  100  400  700
        2022-01-01 21:02:00+00:00  200  500  800
        2022-01-01 21:03:00+00:00  300  600  900
        have pct_change more than `assert_diff_threshold`.
        """
        self.assert_equal(actual, expected, purify_text=True, fuzzy_match=True)

    def test12(self) -> None:
        """
        Check functionality for `remove_inf = True` in presence of `diff_mode =
        'pct_change'`.
        """
        timestamp_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
        ]
        df2 = pd.DataFrame(
            {
                "tsA": [100, 200, 300],
                "tsB": [400, 500, 600],
                "tsC": [700, 800, 900],
                "timestamp": timestamp_index,
            }
        )
        df2 = df2.set_index("timestamp")
        adjustment_factor = 1.00001
        df1 = df2 * adjustment_factor
        df1.iloc[1, 2] = np.inf
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            diff_mode="pct_change",
            only_warning=True,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                  tsA.pct_change  tsB.pct_change  tsC.pct_change
        timestamp
        2022-01-01 21:01:00+00:00         0.001           0.001            0.001
        2022-01-01 21:02:00+00:00         0.001           0.001            NaN
        2022-01-01 21:03:00+00:00         0.001           0.001            0.001
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test13(self) -> None:
        """
        Check test case when negative values in df2.
        """
        timestamp_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
        ]
        df2 = pd.DataFrame(
            {
                "tsA": [100, 200, -300],
                "tsB": [400, -500, 600],
                "tsC": [700, -800, 900],
                "timestamp": timestamp_index,
            }
        )
        df2 = df2.set_index("timestamp")
        adjustment_factor = 1.00001
        df1 = df2 * adjustment_factor
        df_diff = hpandas.compare_dfs(
            df1,
            df2,
            diff_mode="pct_change",
            only_warning=True,
        )
        actual = hpandas.df_to_str(df_diff)
        expected = r"""                  tsA.pct_change  tsB.pct_change  tsC.pct_change
        timestamp
        2022-01-01 21:01:00+00:00         0.001           0.001             0.001
        2022-01-01 21:02:00+00:00         0.001          -0.001            -0.001
        2022-01-01 21:03:00+00:00        -0.001           0.001             0.001
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_invalid_input(self) -> None:
        """
        Put two different DataFrames with `equal` mode.
        """
        df1, df2 = self.get_test_dfs_different()
        with self.assertRaises(AssertionError):
            hpandas.compare_dfs(
                df1,
                df2,
                row_mode="equal",
                column_mode="equal",
                diff_mode="pct_change",
            )


class Test_compare_nans_in_dataframes(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check that NaN differences are identified correctly.
        """
        # Build test dataframes.
        df1 = pd.DataFrame(
            data={
                "A": [1.1, np.nan, 3.1, np.nan, np.inf, np.inf],
                "B": [0, 0, 0, 0, 0, 0],
            }
        )
        df2 = pd.DataFrame(
            data={
                "A": [3.0, 2.2, np.nan, np.nan, np.nan, np.inf],
                "B": [0, 0, 0, 0, 0, 0],
            }
        )
        df = hpandas.compare_nans_in_dataframes(df1, df2)
        actual = hpandas.df_to_str(df)
        expected = r"""
            A
           df1  df2
        1  NaN  2.2
        2  3.1  NaN
        4  inf  NaN
        """
        self.assert_equal(actual, expected, fuzzy_match=True)
