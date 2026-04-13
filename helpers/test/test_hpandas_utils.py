import logging

import pandas as pd

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# Test_df_to_str
# #############################################################################


class Test_df_to_str(hunitest.TestCase):
    @staticmethod
    def get_test_data() -> pd.DataFrame:
        test_data = {
            "dummy_value_1": [1, 2, 3],
            "dummy_value_2": ["A", "B", "C"],
            "dummy_value_3": [0, 0, 0],
        }
        df = pd.DataFrame(data=test_data)
        return df

    def test_df_to_str1(self) -> None:
        """
        Test common call to `df_to_str` with basic df.
        """
        df = self.get_test_data()
        actual = hpandas.df_to_str(df)
        expected = r"""
            dummy_value_1 dummy_value_2  dummy_value_3
        0              1             A              0
        1              2             B              0
        2              3             C              0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str2(self) -> None:
        """
        Test common call to `df_to_str` with tag.
        """
        df = self.get_test_data()
        actual = hpandas.df_to_str(df, tag="df")
        expected = r"""# df=
           dummy_value_1 dummy_value_2  dummy_value_3
        0              1             A              0
        1              2             B              0
        2              3             C              0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str3(self) -> None:
        """
        Test common call to `df_to_str` with print_shape_info.
        """
        df = self.get_test_data()
        actual = hpandas.df_to_str(df, print_shape_info=True)
        expected = r"""
        index=[0, 2]
        columns=dummy_value_1,dummy_value_2,dummy_value_3
        shape=(3, 3)
           dummy_value_1 dummy_value_2  dummy_value_3
        0              1             A              0
        1              2             B              0
        2              3             C              0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str4(self) -> None:
        """
        Test common call to `df_to_str` with print_dtypes.
        """
        df = self.get_test_data()
        actual = hpandas.df_to_str(df, print_dtypes=True)
        expected = r"""
        * type=
                col_name   dtype       num_unique       num_nans first_elem       type(first_elem)
        0          index   int64  3 / 3 = 100.00%  0 / 3 = 0.00%          0  <class 'numpy.int64'>
        1  dummy_value_1   int64  3 / 3 = 100.00%  0 / 3 = 0.00%          1  <class 'numpy.int64'>
        2  dummy_value_2  object  3 / 3 = 100.00%  0 / 3 = 0.00%          A          <class 'str'>
        3  dummy_value_3   int64   1 / 3 = 33.33%  0 / 3 = 0.00%          0  <class 'numpy.int64'>
           dummy_value_1 dummy_value_2  dummy_value_3
        0              1             A              0
        1              2             B              0
        2              3             C              0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str5(self) -> None:
        """
        Test common call to `df_to_str` with multiple args.
        """
        df = self.get_test_data()
        actual = hpandas.df_to_str(
            df, print_shape_info=True, print_dtypes=True, tag="df"
        )
        expected = r"""
        # df=
        index=[0, 2]
        columns=dummy_value_1,dummy_value_2,dummy_value_3
        shape=(3, 3)
        * type=
                col_name   dtype       num_unique       num_nans first_elem       type(first_elem)
        0          index   int64  3 / 3 = 100.00%  0 / 3 = 0.00%          0  <class 'numpy.int64'>
        1  dummy_value_1   int64  3 / 3 = 100.00%  0 / 3 = 0.00%          1  <class 'numpy.int64'>
        2  dummy_value_2  object  3 / 3 = 100.00%  0 / 3 = 0.00%          A          <class 'str'>
        3  dummy_value_3   int64   1 / 3 = 33.33%  0 / 3 = 0.00%          0  <class 'numpy.int64'>
           dummy_value_1 dummy_value_2  dummy_value_3
        0              1             A              0
        1              2             B              0
        2              3             C              0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str6(self) -> None:
        """
        Test common call to `df_to_str` with `pd.Series`.
        """
        df = self.get_test_data()
        actual = hpandas.df_to_str(df["dummy_value_2"])
        expected = r"""
            dummy_value_2
        0             A
        1             B
        2             C
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str7(self) -> None:
        """
        Test common call to `df_to_str` with `pd.Index`.
        """
        df = self.get_test_data()
        index = df.index
        index.name = "index_name"
        actual = hpandas.df_to_str(index)
        expected = r"""
        index_name
        0  0
        1  1
        2  2
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str8(self) -> None:
        """
        Test that `-0.0` is replaced with `0.0`.
        """
        test_data = {
            "dummy_value_1": [1, 2, 3, 4],
            "dummy_value_2": ["A", "B", "C", "D"],
            "dummy_value_3": [0, 0, 0, 0],
            "dummy_value_4": [+0.0, -0.0, +0.0, -0.0],
        }
        df = pd.DataFrame(data=test_data)
        actual = hpandas.df_to_str(df, handle_signed_zeros=True)
        expected = r"""
            dummy_value_1 dummy_value_2  dummy_value_3  dummy_value_4
        0              1             A              0            0.0
        1              2             B              0            0.0
        2              3             C              0            0.0
        3              4             D              0            0.0"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str9(self) -> None:
        """
        Test that `-0.0` is replaced with `0.0` in a multi-index dataframe.
        """
        test_data = {
            ("A", "X"): [-0.0, 5.0, -0.0],
            ("A", "Y"): [2, 6, 0],
            ("B", "X"): [0, 7, 3],
            ("B", "Y"): [4.4, -0.0, 5.1],
        }
        df = pd.DataFrame(data=test_data)
        actual = hpandas.df_to_str(df, handle_signed_zeros=True)
        expected = r"""
             A     B
             X  Y  X    Y
        0  0.0  2  0  4.4
        1  5.0  6  7  0.0
        2  0.0  0  3  5.1"""
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_df_to_str10(self) -> None:
        """
        Test common call to `df_to_str` with `print_memory_usage = True`.
        """
        df = self.get_test_data()
        actual = hpandas.df_to_str(df, print_memory_usage=True)
        # This is required by `numpy` >= 2.1.0
        expected = r"""
        * memory=
                       shallow     deep
        Index          132.0 b  132.0 b
        dummy_value_1   24.0 b   24.0 b
        dummy_value_2   24.0 b  150.0 b
        dummy_value_3   24.0 b   24.0 b
        total          204.0 b  330.0 b
           dummy_value_1 dummy_value_2  dummy_value_3
        0              1             A              0
        1              2             B              0
        2              3             C              0
        """
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_head
# #############################################################################


class Test_head(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test basic head functionality without seed.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "col1": [1, 2, 3, 4, 5],
                "col2": ["a", "b", "c", "d", "e"],
            }
        )
        hpandas.head(df, num_rows=2)

    def test2(self) -> None:
        """
        Test head with a seed for reproducible sampling.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "col1": list(range(10)),
                "col2": list("abcdefghij"),
            }
        )
        hpandas.head(df, seed=42, num_rows=3)

    def test3(self) -> None:
        """
        Test head with different num_rows parameter.
        """
        # Prepare input.
        df = pd.DataFrame(
            {
                "col1": list(range(5)),
                "col2": list("abcde"),
            }
        )
        hpandas.head(df, num_rows=4)
