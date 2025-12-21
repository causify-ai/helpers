import logging

import numpy as np
import pandas as pd
import pytest

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"

# #############################################################################
# Type Conversion Tests
# #############################################################################


class Test_to_series1(hunitest.TestCase):
    def helper(self, n: int, expected: str) -> None:
        vals = list(range(n))
        df = pd.DataFrame([vals], columns=[f"a{i}" for i in vals])
        df = df.T
        _LOG.debug("df=\n%s", df)
        srs = hpandas.to_series(df)
        _LOG.debug("srs=\n%s", srs)
        actual = str(srs)
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test1(self) -> None:
        n = 0
        expected = r"""
        Series([], dtype: float64)
        """
        self.helper(n, expected)

    def test2(self) -> None:
        n = 1
        expected = r"""
        a0    0
        dtype: int64"""
        self.helper(n, expected)

    def test3(self) -> None:
        n = 5
        expected = r"""
        a0    0
        a1    1
        a2    2
        a3    3
        a4    4
        Name: 0, dtype: int64"""
        self.helper(n, expected)


class Test_cast_series_to_type(hunitest.TestCase):
    """
    Test converting a series into a given type.
    """

    def test1(self) -> None:
        series = pd.Series(["1", "2", "3"])
        series_type = int
        actual = hpandas.cast_series_to_type(series, series_type)
        self.assertEqual(actual.dtype.type, np.int64)

    def test2(self) -> None:
        series = pd.Series(["0.1", "0.2", "0.3"])
        series_type = float
        actual = hpandas.cast_series_to_type(series, series_type)
        self.assertEqual(actual.dtype.type, np.float64)

    def test3(self) -> None:
        series = pd.Series(["None", "None", "None"])
        series_type = None
        actual = hpandas.cast_series_to_type(series, series_type)
        for i in range(len(actual)):
            self.assertIsNone(actual.iloc[i])

    def test4(self) -> None:
        series = pd.Series(["2020-01-01", "2020-02-02", "2020-03-03"])
        series_type = pd.Timestamp
        actual = hpandas.cast_series_to_type(series, series_type)
        self.assertEqual(actual.dtype.type, np.datetime64)

    def test5(self) -> None:
        series = pd.Series(["{}", "{1: 2, 3: 4}", "{'a': 'b'}"])
        series_type = dict
        actual = hpandas.cast_series_to_type(series, series_type)
        for i in range(len(actual)):
            self.assertEqual(type(actual.iloc[i]), dict)


class Test_convert_to_type(hunitest.TestCase):
    def test_convert_to_type_bool(self) -> None:
        """
        Check converting to bool column.
        """
        # Mix of booleans, truthy/falsy strings, numerics, and invalid values
        data = [True, False, "True", "false", 1, 0, "1", "0", "yes", None]
        series = pd.Series(data)
        result = hpandas.convert_to_type(series, "is_bool")
        expected = pd.Series(
            [True, False, True, False, True, False, True, False, None, None]
        )
        pd.testing.assert_series_equal(result, expected)

    def test_convert_to_type_int_and_numeric(self) -> None:
        """
        Check converting to numeric and int column.
        """
        # Strings that parse to numbers, floats, invalid strings, and ints
        series = pd.Series(["1", "2", "3.5", "abc", 4], dtype=object)
        # is_int should coerce numeric strings to numbers, invalid -> NaN
        result_int = hpandas.convert_to_type(series, "is_int")
        expected_int = pd.to_numeric(series, errors="coerce")
        pd.testing.assert_series_equal(result_int, expected_int)
        # is_numeric is the same as to_numeric
        result_numeric = hpandas.convert_to_type(series, "is_numeric")
        pd.testing.assert_series_equal(result_numeric, expected_int)

    def test_convert_to_type_string(self) -> None:
        """
        Check converting to string column.
        """
        # Strings vs non-strings
        data = ["a", 1, None, "hello", True, 3.14]
        series = pd.Series(data, dtype=object)
        result = hpandas.convert_to_type(series, "is_string")
        expected = pd.Series(["a", "1", "None", "hello", "True", "3.14"])
        pd.testing.assert_series_equal(result, expected)

    def test_convert_to_type_unknown(self) -> None:
        "Check converting to invalid datatype column."
        series = pd.Series([1, 2, 3], dtype=object)
        with pytest.raises(ValueError) as exc:
            hpandas.convert_to_type(series, "invalid_type")
        self.assertIn("Unknown column type: invalid_type", str(exc.value))


class Test_infer_column_types(hunitest.TestCase):
    def test_numeric_dominance(self) -> None:
        """
        Check with numeric dominant column.
        """
        # 5 elements: '1','2',3 (numeric), 'a', None
        col = pd.Series(["1", "2", 3, "a", None], dtype=object)
        vals = hpandas.infer_column_types(col)
        # is_numeric: True for "1","2",3 → 3/5 = 0.6
        assert pytest.approx(vals["is_numeric"], rel=1e-6) == 0.6
        # is_bool: none are bool → 0.0
        assert vals["is_bool"] == 0.0
        # is_string: "1","2","a" are str → 3/5 = 0.6
        assert pytest.approx(vals["is_string"], rel=1e-6) == 0.6
        # numeric ≥ string, and bool < numeric ⇒ type is numeric
        self.assert_equal(vals["type"], "is_numeric")

    def test_bool_dominance(self) -> None:
        """
        Check with bool dominant column.
        """
        # 4 elements: True, False, True (bool), "x"
        col = pd.Series([True, False, True, "x"], dtype=object)
        vals = hpandas.infer_column_types(col)
        # is_bool: 3/4 = 0.75
        assert pytest.approx(vals["is_bool"], rel=1e-6) == 0.75
        # is_numeric: True→1, False→0, True→1, "x"→NaN  → notna → 3/4 = 0.75
        assert pytest.approx(vals["is_numeric"], rel=1e-6) == 0.75
        # is_string: only "x" → 1/4 = 0.25
        assert pytest.approx(vals["is_string"], rel=1e-6) == 0.25
        # bool ≥ numeric ⇒ type is bool
        self.assert_equal(vals["type"], "is_bool")

    def test_string_dominance(self) -> None:
        """
        Check with string dominant column.
        """
        # 3 elements: 1.5 (numeric), "a","b" (strings)
        col = pd.Series([1.5, "a", "b"], dtype=object)
        vals = hpandas.infer_column_types(col)
        # is_bool: none are bool → 0/3 = 0.0
        assert pytest.approx(vals["is_bool"], rel=1e-6) == 0.0
        # is_numeric: 1/3 ≈ 0.333...
        assert pytest.approx(vals["is_numeric"], rel=1e-6) == pytest.approx(
            1 / 3, rel=1e-6
        )
        # is_string: 2/3 ≈ 0.666...
        assert pytest.approx(vals["is_string"], rel=1e-6) == pytest.approx(
            2 / 3, rel=1e-6
        )
        # bool < numeric < string ⇒ type is string
        self.assert_equal(vals["type"], "is_string")


class Test_convert_df(hunitest.TestCase):
    def test_convert_df_all_bool(self) -> None:
        """
        A column of pure booleans should stay booleans.
        """
        df = pd.DataFrame({"flag": [True, False, True, False]})
        df_out = hpandas.convert_df(df)
        # Expect a DataFrame back
        assert isinstance(df_out, pd.DataFrame)
        # Column dtype must be bool
        self.assert_equal(df_out["flag"].dtype.name, "bool")
        # Values preserved
        self.assert_equal(
            str(df_out["flag"].tolist()), str([True, False, True, False])
        )

    def test_convert_df_all_numeric(self) -> None:
        """
        A column of numeric strings and ints should become floats.
        """
        df = pd.DataFrame({"score": ["1", 2, "3.5", 4]}, dtype=object)
        df_out = hpandas.convert_df(df)
        assert isinstance(df_out, pd.DataFrame)
        # dtype should be float64
        assert df_out["score"].dtype == float
        # Values converted correctly
        assert df_out["score"].tolist() == [1.0, 2.0, 3.5, 4.0]

    def test_convert_df_all_string(self) -> None:
        """
        A column of strings (and mixed non-numeric non-bool) stays as-is.
        """
        df = pd.DataFrame(
            {"name": ["alice", "bob", "", "charlie"]}, dtype=object
        )
        df_out = hpandas.convert_df(df)
        print(df_out.head(5))
        assert isinstance(df_out, pd.DataFrame)
        # dtype remains object (strings)
        self.assert_equal(df_out["name"].dtype.name, "object")
        self.assert_equal(
            str(df_out["name"].tolist()), str(["alice", "bob", "", "charlie"])
        )

    def test_convert_df_mixed_columns(self) -> None:
        """
        Different datatype columns should convert accordingly.
        """
        df = pd.DataFrame(
            {
                "flag": [True, False, False],
                "value": [10, 20, "xyz"],
                "text": ["one", "hello", 2],
            },
            dtype=object,
        )
        df_out = hpandas.convert_df(df)
        # flag → bool
        self.assert_equal(df_out["flag"].dtype.name, "bool")
        self.assertIn("float", df_out["value"].dtype.name)
        self.assert_equal(df_out["text"].dtype.name, "object")
