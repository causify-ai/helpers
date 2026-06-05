import logging

import numpy as np
import pandas as pd

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# Test_dassert_is_unique1
# #############################################################################


class Test_dassert_is_unique1(hunitest.TestCase):
    def get_df1(self) -> pd.DataFrame:
        """
        Return a df without duplicated index.
        """
        num_rows = 5
        idx = [
            pd.Timestamp("2000-01-01 9:00") + pd.Timedelta(minutes=i)
            for i in range(num_rows)
        ]
        values = [[i] for i in range(len(idx))]
        df = pd.DataFrame(values, index=idx)
        _LOG.debug("df=\n%s", df)
        #
        actual = hpandas.df_to_str(df)
        expected = r"""
                             0
        2000-01-01 09:00:00  0
        2000-01-01 09:01:00  1
        2000-01-01 09:02:00  2
        2000-01-01 09:03:00  3
        2000-01-01 09:04:00  4"""
        self.assert_equal(actual, expected, fuzzy_match=True)
        return df

    def test_dassert_is_unique1(self) -> None:
        df = self.get_df1()
        hpandas.dassert_unique_index(df)

    def get_df2(self) -> pd.DataFrame:
        """
        Return a df with duplicated index.
        """
        num_rows = 4
        idx = [
            pd.Timestamp("2000-01-01 9:00") + pd.Timedelta(minutes=i)
            for i in range(num_rows)
        ]
        idx.append(idx[0])
        values = [[i] for i in range(len(idx))]
        df = pd.DataFrame(values, index=idx)
        _LOG.debug("df=\n%s", df)
        #
        actual = hpandas.df_to_str(df)
        expected = r"""
                             0
        2000-01-01 09:00:00  0
        2000-01-01 09:01:00  1
        2000-01-01 09:02:00  2
        2000-01-01 09:03:00  3
        2000-01-01 09:00:00  4"""
        self.assert_equal(actual, expected, fuzzy_match=True)
        return df

    def test_dassert_is_unique2(self) -> None:
        df = self.get_df2()
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_unique_index(df)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        cond=False
        Duplicated rows are:
                             0
        2000-01-01 09:00:00  0
        2000-01-01 09:00:00  4
        """
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_dassert_valid_remap
# #############################################################################


class Test_dassert_valid_remap(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check that the function works with correct inputs.
        """
        # Set inputs.
        to_remap = ["dummy_value_1", "dummy_value_2", "dummy_value_3"]
        remap_dict = {
            "dummy_value_1": "1, 2, 3",
            "dummy_value_2": "A, B, C",
        }
        # Check.
        hpandas.dassert_valid_remap(to_remap, remap_dict)

    def test2(self) -> None:
        """
        Check that an assertion is raised if dictionary keys are not a subset.
        """
        # Set inputs.
        to_remap = ["dummy_value_1", "dummy_value_2"]
        remap_dict = {
            "dummy_value_1": "1, 2, 3",
            "dummy_value_2": "A, B, C",
            "dummy_value_3": "A1, A2, A3",
        }
        # Run.
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_valid_remap(to_remap, remap_dict)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        val1=['dummy_value_1', 'dummy_value_2', 'dummy_value_3']
        issubset
        val2=['dummy_value_1', 'dummy_value_2']
        val1 - val2=['dummy_value_3']
        Keys to remap should be a subset of existing columns"""
        # Check.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Check that an assertion is raised if the duplicate values are present
        in the dict.
        """
        # Set inputs.
        to_remap = ["dummy_value_1", "dummy_value_2", "dummy_value_3"]
        remap_dict = {
            "dummy_value_1": 1,
            "dummy_value_2": "A, B, C",
            "dummy_value_3": "A, B, C",
        }
        # Run.
        with self.assertRaises(AttributeError) as cm:
            hpandas.dassert_valid_remap(to_remap, remap_dict)
        actual = str(cm.exception)
        expected = r"""
        'dict_values' object has no attribute 'count'"""
        # Check.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test4(self) -> None:
        """
        Check that an assertion is raised if the input is not a list.
        """
        # Set inputs.
        to_remap = {"dummy_value_1"}
        remap_dict = {
            "dummy_value_1": "1, 2, 3",
        }
        # Run.
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_valid_remap(to_remap, remap_dict)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        Instance of '{'dummy_value_1'}' is '<class 'set'>' instead of '<class 'list'>'
        """
        # Check.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test5(self) -> None:
        """
        Check that an assertion is raised if the input is not a dictionary.
        """
        # Set inputs.
        to_remap = ["dummy_value_1"]
        remap_dict = [
            "dummy_value_1 : 1, 2, 3",
        ]
        # Run.
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_valid_remap(to_remap, remap_dict)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        Instance of '['dummy_value_1 : 1, 2, 3']' is '<class 'list'>' instead of '<class 'dict'>'
        """
        # Check.
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_dassert_increasing_index
# #############################################################################


class Test_dassert_increasing_index(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check that a monotonically increasing index passes the assert.
        """
        # Build test dataframe.
        idx = [
            pd.Timestamp("2000-01-01 9:01"),
            pd.Timestamp("2000-01-01 9:02"),
            pd.Timestamp("2000-01-01 9:03"),
            pd.Timestamp("2000-01-01 9:04"),
        ]
        values = [0, 0, 0, 0]
        df = pd.DataFrame(values, index=idx)
        # Run.
        hpandas.dassert_increasing_index(df)

    def test2(self) -> None:
        """
        Check that an assert is raised when index is not monotonically
        increasing.
        """
        # Build test dataframe.
        idx = [
            pd.Timestamp("2000-01-01 9:01"),
            pd.Timestamp("2000-01-01 9:02"),
            pd.Timestamp("2000-01-01 9:04"),
            pd.Timestamp("2000-01-01 9:03"),
        ]
        values = [0, 0, 0, 0]
        df = pd.DataFrame(values, index=idx)
        # Run.
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_increasing_index(df)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        cond=False
        Not increasing indices are:
                                0
        2000-01-01 09:04:00  0
        2000-01-01 09:03:00  0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Check that a monotonically increasing index with duplicates passes the
        assert.
        """
        # Build test dataframe.
        idx = [
            pd.Timestamp("2000-01-01 9:00"),
            pd.Timestamp("2000-01-01 9:00"),
            pd.Timestamp("2000-01-01 9:01"),
            pd.Timestamp("2000-01-01 9:01"),
        ]
        values = [0, 0, 0, 0]
        df = pd.DataFrame(values, index=idx)
        # Run.
        hpandas.dassert_increasing_index(df)


# #############################################################################
# Test_dassert_strictly_increasing_index
# #############################################################################


class Test_dassert_strictly_increasing_index(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check that unique and monotonically increasing index passes the assert.
        """
        # Build test dataframe.
        idx = [
            pd.Timestamp("2000-01-01 9:01"),
            pd.Timestamp("2000-01-01 9:02"),
            pd.Timestamp("2000-01-01 9:03"),
            pd.Timestamp("2000-01-01 9:04"),
        ]
        values = [0, 0, 0, 0]
        df = pd.DataFrame(values, index=idx)
        # Run.
        hpandas.dassert_strictly_increasing_index(df)

    def test2(self) -> None:
        """
        Check that an assert is raised for an increasing index with duplicates.
        """
        # Build test dataframe.
        idx = [
            pd.Timestamp("2000-01-01 9:01"),
            pd.Timestamp("2000-01-01 9:01"),
            pd.Timestamp("2000-01-01 9:02"),
            pd.Timestamp("2000-01-01 9:03"),
        ]
        values = [0, 0, 0, 0]
        df = pd.DataFrame(values, index=idx)
        # Run.
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_strictly_increasing_index(df)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        cond=False
        Duplicated rows are:
                            0
        2000-01-01 09:01:00  0
        2000-01-01 09:01:00  0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Check that an assert is raised for a not monotonically increasing
        index.
        """
        # Build test dataframe.
        idx = [
            pd.Timestamp("2000-01-01 9:01"),
            pd.Timestamp("2000-01-01 9:03"),
            pd.Timestamp("2000-01-01 9:02"),
            pd.Timestamp("2000-01-01 9:04"),
        ]
        values = [0, 0, 0, 0]
        df = pd.DataFrame(values, index=idx)
        # Run.
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_strictly_increasing_index(df)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        cond=False
        Not increasing indices are:
                                0
        2000-01-01 09:03:00  0
        2000-01-01 09:02:00  0"""
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_dassert_index_is_datetime
# #############################################################################


class Test_dassert_index_is_datetime(hunitest.TestCase):
    @staticmethod
    def get_multiindex_df(
        index_is_datetime: bool,
    ) -> pd.DataFrame:
        """
        Helper function to get test multi-index dataframe. Example of dataframe
        returned when `index_is_datetime = True`:

        ```
                                            column1     column2
        index   timestamp
        index1  2022-01-01 21:00:00+00:00   -0.122140   -1.949431
                2022-01-01 21:10:00+00:00   1.303778    -0.288235
        index2  2022-01-01 21:00:00+00:00   1.237079    1.168012
                2022-01-01 21:10:00+00:00   1.333692    1.708455
        ```

        Example of dataframe returned when `index_is_datetime = False`:

        ```
                            column1     column2
        index   timestamp
        index1  string1     -0.122140   -1.949431
                string2     1.303778    -0.288235
        index2  string1     1.237079    1.168012
                string2     1.333692    1.708455
        ```
        """
        if index_is_datetime:
            index_inner = [
                pd.Timestamp("2022-01-01 21:00:00", tz="UTC"),
                pd.Timestamp("2022-01-01 21:10:00", tz="UTC"),
            ]
        else:
            index_inner = ["string1", "string2"]
        index_outer = ["index1", "index2"]
        iterables = [index_outer, index_inner]
        index = pd.MultiIndex.from_product(
            iterables, names=["index", "timestamp"]
        )
        columns = ["column1", "column2"]
        nums = np.random.uniform(-2, 2, size=(4, 2))
        df = pd.DataFrame(nums, index=index, columns=columns)
        return df

    def test1(self) -> None:
        """
        Check that multi-index dataframe index is datetime type.
        """
        index_is_datetime = True
        df = self.get_multiindex_df(index_is_datetime)
        hpandas.dassert_index_is_datetime(df)

    def test2(self) -> None:
        """
        Check that multi-index dataframe index is not datetime type.
        """
        index_is_datetime = False
        df = self.get_multiindex_df(index_is_datetime)
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_index_is_datetime(df)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        cond=False
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Check for empty dataframe.
        """
        df = pd.DataFrame()
        with self.assertRaises(AssertionError) as cm:
            hpandas.dassert_index_is_datetime(df)
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        Instance of 'RangeIndex(start=0, stop=0, step=1)' is '<class 'pandas.core.indexes.range.RangeIndex'>' instead of '<class 'pandas.core.indexes.datetimes.DatetimeIndex'>'
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test4(self) -> None:
        """
        Check that single-indexed dataframe index is datetime type.
        """
        index_is_datetime = True
        df = self.get_multiindex_df(index_is_datetime)
        df = df.loc["index1"]
        hpandas.dassert_index_is_datetime(df)


# #############################################################################
# Test_dassert_approx_eq1
# #############################################################################


class Test_dassert_approx_eq1(hunitest.TestCase):
    def test1(self) -> None:
        hpandas.dassert_approx_eq(1, 1.0000001)

    def test2(self) -> None:
        srs1 = pd.Series([1, 2.0000001])
        srs2 = pd.Series([0.999999, 2.0])
        hpandas.dassert_approx_eq(srs1, srs2, msg="hello world")
