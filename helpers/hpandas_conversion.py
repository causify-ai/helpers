"""
Import as:

import helpers.hpandas as hpandas
"""

from typing import List, Optional, Union

import numpy as np
import pandas as pd

import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hpandas_dassert as hpandass

_LOG = hloggin.getLogger(__name__)

RowsValues = List[List[str]]

# #############################################################################
# DataFrame/Series Conversion
# #############################################################################


def to_series(df: pd.DataFrame, *, series_dtype: str = "float64") -> pd.Series:
    """
    Convert a pd.DataFrame with a single column into a pd.Series. The problem
    is that empty df or df with a single row are not converted correctly to a
    pd.Series.

    :param df: dataframe with a single column to convert to a series
    :param series_dtype: dtype of the desired series in case a DataFrame
        is empty, otherwise inherit dtype from a DataFrame
    """
    # See https://stackoverflow.com/questions/33246771
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_eq(df.shape[1], 1, "df=%s doesn't have a single column", df)
    if df.empty:
        srs = pd.Series(dtype=series_dtype)
    elif df.shape[0] > 1:
        srs = df.squeeze()
    else:
        srs = pd.Series(df.iloc[0, 0], index=[df.index.values[0]])
        srs.name = df.index.name
    hdbg.dassert_isinstance(srs, pd.Series)
    return srs


def as_series(data: Union[pd.DataFrame, pd.Series]) -> pd.Series:
    """
    Convert a single-column dataframe to a series or no-op if already a series.
    """
    if isinstance(data, pd.Series):
        return data
    return to_series(data)


# #############################################################################
# Infer type
# #############################################################################


def infer_column_types(col: pd.Series):
    """
    Determine which data type is most prevalent in a column.

    Examine the values in the given pandas Series and decides whether
    the majority of entries are strings, numeric values, or booleans.

    :param col: The column to inspect.
    :return: One of `"is_string"`, `"is_numeric"`, or `"is_bool"`,
        representing the predominant type.
    """
    vals = {
        "is_numeric": pd.to_numeric(col, errors="coerce").notna(),
        #'is_datetime': pd.to_datetime(col, errors='coerce').notna(),
        "is_bool": col.map(lambda x: isinstance(x, bool)),
        "is_string": col.map(lambda x: isinstance(x, str)),
    }
    vals = {k: float(v.mean()) for k, v in vals.items()}
    # type_ = np.where(vals["is_bool"] >= vals["is_numeric"], "is_bool",
    #                  (vals["is_numeric"] >= vals["is_string"], "is_numeric",
    #                  "is_string"))
    if vals["is_bool"] >= vals["is_numeric"] and (vals["is_bool"] != 0):
        type_ = "is_bool"
    elif vals["is_numeric"] >= vals["is_string"] and (vals["is_numeric"] != 0):
        type_ = "is_numeric"
    else:
        type_ = "is_string"
    vals["type"] = type_
    return vals


def infer_column_types_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify the predominant data type for each column in a DataFrame.

    :param df: The DataFrame whose columns will be analyzed.
    :return: A DataFrame with two columns:
        - `column`: the name of each original column.
        - `predominant_type`: the most frequent type in that column,
          one of `"string"`, `"numeric"`, or `"bool"`.
    """
    return df.apply(lambda x: pd.Series(infer_column_types(x))).T


def convert_to_type(col: pd.Series, type_: str) -> pd.Series:
    """
    Convert a pandas Series to a specified data type.

    :param col: The input column to be converted.
    :param type_: The target data type. Expected values include:
        - `"is_bool"`: convert values to booleans.
        - `"is_int"`: convert values to integers.
        - `"is_numeric"`: convert values to float.
        - `"is_string"`: convert values to strings.
    :return: A new Series with the same index as `col`, cast to the requested
        type.
    """
    if type_ == "is_bool":
        return col.map(
            lambda x: (
                True
                if x in ["True", 1, "1", "true", True]
                else False if x in [0, "0", "False", False, "false"] else None
            )
        )
    elif type_ == "is_int":
        return pd.to_numeric(col, errors="coerce", downcast="integer")
    elif type_ == "is_numeric":
        return pd.to_numeric(col, errors="coerce")
    elif type_ == "is_string":
        return col.astype(str)
    else:
        raise ValueError(f"Unknown column type: {type_}")


def convert_col_to_int(
    df: pd.DataFrame,
    col: str,
) -> pd.DataFrame:
    """
    Convert a column to an integer column.

    Example use case: Parquet uses categoricals. If supplied with a
    categorical-type column, this function will convert it to an integer
    column.
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_isinstance(col, str)
    hdbg.dassert_in(col, df.columns)
    # Attempt the conversion.
    df[col] = df[col].astype("int64")
    # Trust, but verify.
    hpandass.dassert_series_type_is(df[col], np.int64)
    return df


def cast_series_to_type(
    series: pd.Series, series_type: Optional[type]
) -> pd.Series:
    """
    Convert a Pandas series to a given type.

    :param series: the input series
    :param series_type: the type to convert the series into
        - if None, then the series values are turned into Nones
    :return: the series in the required type
    """
    if series_type is None:
        # Turn the series values into None.
        series[:] = None
    elif series_type is pd.Timestamp:
        # Convert to timestamp.
        series = pd.to_datetime(series)
    elif series_type is dict:
        # Convert to dict.
        series = series.apply(eval)
    else:
        # Convert to the specified type.
        series = series.astype(series_type)
    return series


def convert_df(
    df: pd.DataFrame, *, print_invalid_values: bool = False
) -> pd.DataFrame:
    """
    Convert each DataFrame column to its predominant type.

    This function inspects every column in `df`, determines whether the
    majority of its values are boolean, numeric, or string, and then
    casts the column to that type using `convert_to_type`.

    :param df: The input DataFrame whose columns will be converted.
    :param print_invalid_values: If True, print any original values that could
        not be converted (they become NaN after conversion)
    :return: a new DataFrame with each column cast to its detected predominant
        type.
    """
    df_out = pd.DataFrame(index=df.index)
    for col in df.columns:
        series = df[col]
        # Determine the dominant datatype.
        col_type = infer_column_types(series)["type"]
        hdbg.dassert_in(col_type, ("is_bool", "is_numeric", "is_string"))
        # Convert the column to dominant datatype.
        converted = convert_to_type(series, col_type)
        if print_invalid_values:
            invalid_mask = series.notna() & converted.isna()
            if invalid_mask.any():
                invalid = series[invalid_mask].tolist()
                print(f"Column {col} dropped invalid values: {invalid}")
        df_out[col] = converted
    return df_out
