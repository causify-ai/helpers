import logging

import numpy as np
import pandas as pd

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# Test_subset_multiindex_df
# #############################################################################


class Test_subset_multiindex_df(hunitest.TestCase):
    """
    Filter Multiindex DataFrame with 2 column levels.
    """

    @staticmethod
    def get_multiindex_df() -> pd.DataFrame:
        timestamp_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
            pd.Timestamp("2022-01-01 21:05:00+00:00"),
        ]
        iterables = [["asset1", "asset2"], ["open", "high", "low", "close"]]
        index = pd.MultiIndex.from_product(iterables, names=[None, "timestamp"])
        nums = np.array(
            [
                [
                    0.77650806,
                    0.12492164,
                    -0.35929232,
                    1.04137784,
                    0.20099949,
                    1.4078602,
                    -0.1317103,
                    0.10023361,
                ],
                [
                    -0.56299812,
                    0.79105046,
                    0.76612895,
                    -1.49935339,
                    -1.05923797,
                    0.06039862,
                    -0.77652117,
                    2.04578691,
                ],
                [
                    0.77348467,
                    0.45237724,
                    1.61051308,
                    0.41800008,
                    0.20838053,
                    -0.48289112,
                    1.03015762,
                    0.17123323,
                ],
                [
                    0.40486053,
                    0.88037142,
                    -1.94567068,
                    -1.51714645,
                    -0.52759748,
                    -0.31592803,
                    1.50826723,
                    -0.50215196,
                ],
                [
                    0.17409714,
                    -2.13997243,
                    -0.18530403,
                    -0.48807381,
                    0.5621593,
                    0.25899393,
                    1.14069646,
                    2.07721856,
                ],
            ]
        )
        df = pd.DataFrame(nums, index=timestamp_index, columns=index)
        return df

    def test1(self) -> None:
        """
        Filter by:

        - Timestamp index range
        - Level 1 columns
        - Level 2 columns
        """
        df = self.get_multiindex_df()
        df_filtered = hpandas.subset_multiindex_df(
            df,
            start_timestamp=pd.Timestamp("2022-01-01 21:01:00+00:00"),
            end_timestamp=pd.Timestamp("2022-01-01 21:03:00+00:00"),
            columns_level0=["asset1"],
            columns_level1=["high", "low"],
        )
        expected_length = 3
        expected_column_names = [("asset1", "high"), ("asset1", "low")]
        expected_column_unique_values = None
        expected_signature = r"""# df=
        index=[2022-01-01 21:01:00+00:00, 2022-01-01 21:03:00+00:00]
        columns=('asset1', 'high'),('asset1', 'low')
        shape=(3, 2)
                                    asset1
        timestamp                      high       low
        2022-01-01 21:01:00+00:00  0.124922 -0.359292
        2022-01-01 21:02:00+00:00  0.791050  0.766129
        2022-01-01 21:03:00+00:00  0.452377  1.610513
        """
        self.check_df_output(
            df_filtered,
            expected_length,
            expected_column_names,
            expected_column_unique_values,
            expected_signature,
        )

    def test2(self) -> None:
        """
        Filter by:

        - Timestamp index range
        - Level 1 columns
        """
        df = self.get_multiindex_df()
        df_filtered = hpandas.subset_multiindex_df(
            df,
            start_timestamp=pd.Timestamp("2022-01-01 21:01:00+00:00"),
            end_timestamp=pd.Timestamp("2022-01-01 21:02:00+00:00"),
            columns_level1=["close"],
        )
        expected_length = 2
        expected_column_names = [("asset1", "close"), ("asset2", "close")]
        expected_column_unique_values = None
        expected_signature = r"""# df=
        index=[2022-01-01 21:01:00+00:00, 2022-01-01 21:02:00+00:00]
        columns=('asset1', 'close'),('asset2', 'close')
        shape=(2, 2)
                                    asset1    asset2
        timestamp                     close     close
        2022-01-01 21:01:00+00:00  1.041378  0.100234
        2022-01-01 21:02:00+00:00 -1.499353  2.045787
        """
        self.check_df_output(
            df_filtered,
            expected_length,
            expected_column_names,
            expected_column_unique_values,
            expected_signature,
        )

    def test3(self) -> None:
        """
        Filter by:

        - Timestamp index range
        - Level 2 columns
        """
        df = self.get_multiindex_df()
        df_filtered = hpandas.subset_multiindex_df(
            df,
            start_timestamp=pd.Timestamp("2022-01-01 21:01:00+00:00"),
            end_timestamp=pd.Timestamp("2022-01-01 21:02:00+00:00"),
            columns_level0=["asset2"],
        )
        expected_length = 2
        expected_column_names = [
            ("asset2", "close"),
            ("asset2", "high"),
            ("asset2", "low"),
            ("asset2", "open"),
        ]
        expected_column_unique_values = None
        expected_signature = r"""# df=
        index=[2022-01-01 21:01:00+00:00, 2022-01-01 21:02:00+00:00]
        columns=('asset2', 'close'),('asset2', 'high'),('asset2', 'low'),('asset2', 'open')
        shape=(2, 4)
                                    asset2
        timestamp                     close      high       low      open
        2022-01-01 21:01:00+00:00  0.100234  1.407860 -0.131710  0.200999
        2022-01-01 21:02:00+00:00  2.045787  0.060399 -0.776521 -1.059238
        """
        self.check_df_output(
            df_filtered,
            expected_length,
            expected_column_names,
            expected_column_unique_values,
            expected_signature,
        )

    def test4(self) -> None:
        """
        Filter by:

        - Level 1 columns
        - Level 2 columns
        """
        df = self.get_multiindex_df()
        df_filtered = hpandas.subset_multiindex_df(
            df,
            columns_level0=["asset2"],
            columns_level1=["low"],
        )
        expected_length = 5
        expected_column_names = [("asset2", "low")]
        expected_column_unique_values = None
        expected_signature = r"""# df=
        index=[2022-01-01 21:01:00+00:00, 2022-01-01 21:05:00+00:00]
        columns=('asset2', 'low')
        shape=(5, 1)
                                    asset2
        timestamp                       low
        2022-01-01 21:01:00+00:00 -0.131710
        2022-01-01 21:02:00+00:00 -0.776521
        2022-01-01 21:03:00+00:00  1.030158
        2022-01-01 21:04:00+00:00  1.508267
        2022-01-01 21:05:00+00:00  1.140696
        """
        self.check_df_output(
            df_filtered,
            expected_length,
            expected_column_names,
            expected_column_unique_values,
            expected_signature,
        )

    def test_columns_level0_invalid_input(self) -> None:
        df = self.get_multiindex_df()
        with self.assertRaises(AssertionError):
            hpandas.subset_multiindex_df(
                df,
                columns_level0=["invalid_input"],
            )

    def test_columns_level1_invalid_input(self) -> None:
        df = self.get_multiindex_df()
        with self.assertRaises(AssertionError):
            hpandas.subset_multiindex_df(
                df,
                columns_level1=["invalid_input"],
            )


# #############################################################################
# Test_compare_multiindex_dfs
# #############################################################################


class Test_compare_multiindex_dfs(hunitest.TestCase):
    """
    Subset Multiindex DataFrames with 2 column levels and compare its values.
    """

    @staticmethod
    def get_multiindex_dfs() -> pd.DataFrame:
        timestamp_index1 = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
            pd.Timestamp("2022-01-01 21:05:00+00:00"),
        ]
        iterables1 = [["asset1", "asset2"], ["open", "high", "low", "close"]]
        index1 = pd.MultiIndex.from_product(
            iterables1, names=[None, "timestamp"]
        )
        nums1 = np.array(
            [
                [
                    0.77650806,
                    0.12492164,
                    -0.35929232,
                    1.04137784,
                    0.20099949,
                    1.4078602,
                    -0.1317103,
                    0.10023361,
                ],
                [
                    -0.56299812,
                    0.79105046,
                    0.76612895,
                    -1.49935339,
                    -1.05923797,
                    0.06039862,
                    -0.77652117,
                    2.04578691,
                ],
                [
                    0.77348467,
                    0.45237724,
                    1.61051308,
                    0.41800008,
                    0.20838053,
                    -0.48289112,
                    1.03015762,
                    0.17123323,
                ],
                [
                    0.40486053,
                    0.88037142,
                    -1.94567068,
                    -1.51714645,
                    -0.52759748,
                    -0.31592803,
                    1.50826723,
                    -0.50215196,
                ],
                [
                    0.17409714,
                    -2.13997243,
                    -0.18530403,
                    -0.48807381,
                    0.5621593,
                    0.25899393,
                    1.14069646,
                    2.07721856,
                ],
            ]
        )
        df1 = pd.DataFrame(nums1, index=timestamp_index1, columns=index1)
        #
        timestamp_index2 = [
            pd.Timestamp("2022-01-01 21:00:00+00:00"),
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
            pd.Timestamp("2022-01-01 21:05:00+00:00"),
            pd.Timestamp("2022-01-01 21:06:00+00:00"),
            pd.Timestamp("2022-01-01 21:06:00+00:00"),
        ]
        iterables2 = [
            ["asset1", "asset2", "asset3"],
            ["open", "high", "low", "close", "volume"],
        ]
        index2 = pd.MultiIndex.from_product(
            iterables2, names=[None, "timestamp"]
        )
        nums2 = [
            [
                0.79095104,
                -0.10304008,
                -0.69848962,
                0.50078409,
                0.41756371,
                -1.33487885,
                1.04546138,
                0.191062,
                0.08841533,
                0.61717725,
                -2.15558483,
                1.21036169,
                2.60355386,
                0.07508052,
                1.00702849,
            ],
            [
                0.56223723,
                0.97433151,
                -1.40471182,
                0.53292355,
                0.24381913,
                0.64343069,
                -0.46733655,
                -1.20471491,
                -0.08347491,
                0.33365524,
                0.04370572,
                -0.53547653,
                -1.07622168,
                0.7318155,
                -0.47146482,
            ],
            [
                -0.48272741,
                1.17859032,
                -0.40816664,
                0.46684297,
                0.42518077,
                -1.52913855,
                1.09925095,
                0.48817537,
                1.2662552,
                -0.59757824,
                0.23724902,
                -0.00660826,
                0.09780482,
                -0.17166633,
                -0.54515917,
            ],
            [
                -0.37618442,
                -0.3086281,
                1.09168123,
                -1.1751162,
                0.38291194,
                1.80830268,
                1.28318855,
                0.75696503,
                -1.04042572,
                0.06493231,
                -0.10392893,
                1.89053412,
                -0.21200498,
                1.61212857,
                -2.00765278,
            ],
            [
                -0.19674075,
                -1.02532132,
                -0.22486018,
                0.37664998,
                0.35619408,
                -0.77304675,
                0.59053699,
                -1.53249898,
                0.57548424,
                -0.32093537,
                -0.52109972,
                1.70938034,
                -0.55419632,
                0.45531674,
                0.66878119,
            ],
            [
                0.05903553,
                1.2040308,
                0.62323671,
                -0.23639535,
                0.87270792,
                2.60253287,
                -0.77788842,
                0.80645833,
                1.85438743,
                -1.77561587,
                0.41469478,
                -0.29791883,
                0.75140743,
                0.50389702,
                0.55311024,
            ],
            [
                -0.97820763,
                -1.32155197,
                -0.6143911,
                0.01473404,
                0.87798665,
                0.1701048,
                -0.75376376,
                0.72503616,
                0.5791076,
                0.43942739,
                0.62505817,
                0.44998739,
                0.37350664,
                -0.73485633,
                -0.70406184,
            ],
            [
                -1.35719477,
                -1.82401288,
                0.77263763,
                2.36399552,
                -0.45353019,
                0.33983713,
                -0.62895329,
                1.34256611,
                0.2207564,
                0.24146184,
                0.90769186,
                0.57426869,
                -0.04587782,
                -1.6319128,
                0.38094798,
            ],
        ]
        df2 = pd.DataFrame(nums2, index=timestamp_index2, columns=index2)
        return df1, df2

    def test1(self) -> None:
        """
        - Subset by both columns and index
        - Make inner intersection and compute pct_change
        """
        df1, df2 = self.get_multiindex_dfs()
        subset_multiindex_df_kwargs = {
            "start_timestamp": pd.Timestamp("2022-01-01 21:02:00+00:00"),
            "end_timestamp": pd.Timestamp("2022-01-01 21:04:00+00:00"),
            "columns_level0": ["asset1", "asset2"],
            "columns_level1": ["low", "high"],
        }
        compare_dfs_kwargs = {
            "column_mode": "inner",
            "row_mode": "inner",
            "diff_mode": "pct_change",
            "assert_diff_threshold": None,
        }
        df_diff = hpandas.compare_multiindex_dfs(
            df1,
            df2,
            subset_multiindex_df_kwargs=subset_multiindex_df_kwargs,
            compare_dfs_kwargs=compare_dfs_kwargs,
        )
        expected_length = 3
        expected_column_names = [
            ("asset1.pct_change", "high.pct_change"),
            ("asset1.pct_change", "low.pct_change"),
            ("asset2.pct_change", "high.pct_change"),
            ("asset2.pct_change", "low.pct_change"),
        ]
        expected_column_unique_values = None
        expected_signature = r"""# df=
        index=[2022-01-01 21:02:00+00:00, 2022-01-01 21:04:00+00:00]
        columns=('asset1.pct_change', 'high.pct_change'),('asset1.pct_change', 'low.pct_change'),('asset2.pct_change', 'high.pct_change'),('asset2.pct_change', 'low.pct_change')
        shape=(3, 4)
                                asset1.pct_change                asset2.pct_change
        timestamp                   high.pct_change low.pct_change   high.pct_change low.pct_change
        2022-01-01 21:02:00+00:00        -32.881643     287.700041        -94.505475    -259.066028
        2022-01-01 21:03:00+00:00        246.576815      47.525948       -137.632125      36.090517
        2022-01-01 21:04:00+00:00        185.862978     -765.280229       -153.498432     198.418808
        """
        self.check_df_output(
            df_diff,
            expected_length,
            expected_column_names,
            expected_column_unique_values,
            expected_signature,
        )


# #############################################################################
# Test_multiindex_df_info1
# #############################################################################


class Test_multiindex_df_info1(hunitest.TestCase):
    @staticmethod
    def get_multiindex_df_with_datetime_index() -> pd.DataFrame:
        datetime_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:03:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
            pd.Timestamp("2022-01-01 21:05:00+00:00"),
        ]
        iterables = [["asset1", "asset2"], ["open", "high", "low", "close"]]
        index = pd.MultiIndex.from_product(iterables, names=[None, "timestamp"])
        nums = np.array(
            [
                [
                    0.77650806,
                    0.12492164,
                    -0.35929232,
                    1.04137784,
                    0.20099949,
                    1.4078602,
                    -0.1317103,
                    0.10023361,
                ],
                [
                    -0.56299812,
                    0.79105046,
                    0.76612895,
                    -1.49935339,
                    -1.05923797,
                    0.06039862,
                    -0.77652117,
                    2.04578691,
                ],
                [
                    0.77348467,
                    0.45237724,
                    1.61051308,
                    0.41800008,
                    0.20838053,
                    -0.48289112,
                    1.03015762,
                    0.17123323,
                ],
                [
                    0.40486053,
                    0.88037142,
                    -1.94567068,
                    -1.51714645,
                    -0.52759748,
                    -0.31592803,
                    1.50826723,
                    -0.50215196,
                ],
                [
                    0.17409714,
                    -2.13997243,
                    -0.18530403,
                    -0.48807381,
                    0.5621593,
                    0.25899393,
                    1.14069646,
                    2.07721856,
                ],
            ]
        )
        df = pd.DataFrame(nums, index=datetime_index, columns=index)
        return df

    @staticmethod
    def get_multiindex_df_with_non_datetime_index() -> pd.DataFrame:
        non_datetime_index = ["M", "N"]
        index = pd.MultiIndex.from_product([["A", "B"], ["X", "Y"]])
        data = [[1, 2, 3, 4], [5, 6, 7, 8]]
        df = pd.DataFrame(data, index=non_datetime_index, columns=index)
        return df

    def test1(self) -> None:
        """
        Test DataFrame with a datetime index.
        """
        df = self.get_multiindex_df_with_datetime_index()
        actual = hpandas.multiindex_df_info(df)
        # This is required by `pandas` >= 2.2.
        expected = """
            shape=2 x 4 x 5
            columns_level0=2 ['asset1', 'asset2']
            columns_level1=4 ['close', 'high', 'low', 'open']
            rows=5 ['2022-01-01 21:01:00+00:00', '2022-01-01 21:02:00+00:00', '2022-01-01 21:03:00+00:00', '2022-01-01 21:04:00+00:00', '2022-01-01 21:05:00+00:00']
            start_timestamp=2022-01-01 21:01:00+00:00
            end_timestamp=2022-01-01 21:05:00+00:00
            frequency=min
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test DataFrame with a non-frequency datetime index.
        """
        df = self.get_multiindex_df_with_datetime_index()
        non_frequency_datetime_index = [
            pd.Timestamp("2022-01-01 21:01:00+00:00"),
            pd.Timestamp("2022-01-01 21:02:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:00+00:00"),
            pd.Timestamp("2022-01-01 21:04:30+00:00"),
            pd.Timestamp("2022-01-01 21:06:00+00:00"),
        ]
        df.index = non_frequency_datetime_index
        actual = hpandas.multiindex_df_info(df)
        expected = """
            shape=2 x 4 x 5
            columns_level0=2 ['asset1', 'asset2']
            columns_level1=4 ['close', 'high', 'low', 'open']
            rows=5 ['2022-01-01 21:01:00+00:00', '2022-01-01 21:02:00+00:00', '2022-01-01 21:04:00+00:00', '2022-01-01 21:04:30+00:00', '2022-01-01 21:06:00+00:00']
            start_timestamp=2022-01-01 21:01:00+00:00
            end_timestamp=2022-01-01 21:06:00+00:00
            frequency=None
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test DataFrame with a non-datetime index.
        """
        df = self.get_multiindex_df_with_non_datetime_index()
        actual = hpandas.multiindex_df_info(df)
        expected = """
            shape=2 x 2 x 2
            columns_level0=2 ['A', 'B']
            columns_level1=2 ['X', 'Y']
            rows=2 ['M', 'N']
        """
        self.assert_equal(actual, expected, fuzzy_match=True)
