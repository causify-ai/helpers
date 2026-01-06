"""
Import as:

import helpers.hpandas_dassert as hpandass
"""

from typing import Any, Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd

import helpers.hdatetime as hdateti
import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hpandas_utils as hpanutil

_LOG = hloggin.getLogger(__name__)


RowsValues = List[List[str]]

# #############################################################################
# Index/Axis Validation & Assertions
# #############################################################################


def _get_index(obj: Union[pd.Index, pd.DataFrame, pd.Series]) -> pd.Index:
    """
    Return the index of a Pandas object.

    :param obj: pandas Index, DataFrame, or Series
    :return: the index of the object
    """
    if isinstance(obj, pd.Index):
        index = obj
    else:
        hdbg.dassert_isinstance(obj, (pd.Series, pd.DataFrame))
        index = obj.index
    return index


# TODO(gp): Maybe for symmetry with the other functions, rename to
#  dassert_datetime_index


def dassert_index_is_datetime(
    obj: Union[pd.Index, pd.DataFrame, pd.Series],
    msg: Optional[str] = None,
    *args: Any,
) -> None:
    """
    Ensure that the dataframe has an index containing datetimes.

    It works for both single and multi-indexed dataframes.
    """
    index = _get_index(obj)
    if isinstance(index, pd.MultiIndex):
        # In case of multi index check that at least one level is a datetime.
        is_any_datetime = any(
            isinstance(level, pd.DatetimeIndex) for level in index.levels
        )
        hdbg.dassert(is_any_datetime, msg, *args)
    else:
        hdbg.dassert_isinstance(index, pd.DatetimeIndex, msg, *args)


def dassert_unique_index(
    obj: Union[pd.Index, pd.DataFrame, pd.Series],
    msg: Optional[str] = None,
    *args: Any,
) -> None:
    """
    Ensure that a Pandas object has a unique index.
    """
    index = _get_index(obj)
    if not index.is_unique:
        dup_indices = index.duplicated(keep=False)
        df_dup = obj[dup_indices]
        df_dup_as_str = hpanutil.df_to_str(df_dup)
        dup_msg = f"Duplicated rows are:\n{df_dup_as_str}\n"
        if msg is None:
            msg = dup_msg
        else:
            msg = dup_msg + msg
        hdbg.dassert(index.is_unique, msg=msg, *args)


# TODO(gp): @all Add unit tests.


def dassert_increasing_index(
    obj: Union[pd.Index, pd.DataFrame, pd.Series],
    msg: Optional[str] = None,
    *args: Any,
) -> None:
    """
    Ensure that a Pandas object has an increasing index.
    """
    index = _get_index(obj)
    if not index.is_monotonic_increasing:
        # Print information about the problematic indices like:
        # ```
        # Not increasing indices are:
        #                                  full_symbol         open         high
        # timestamp
        # 2018-08-17 01:39:00+00:00  binance::BTC_USDT  6339.250000  6348.910000
        # 2018-08-17 00:01:00+00:00   kucoin::ETH_USDT   286.712987   286.712987
        # ```
        # Find the problematic indices.
        mask = np.diff(index) <= pd.Timedelta(seconds=0)
        mask = np.insert(mask, 0, False)
        # TODO(gp): We might want to specify an integer with how many rows before
        #  after we want to show.
        # Shift back to get the previous index that was creating the issue.
        mask_shift = np.empty_like(mask)
        mask_shift[: len(mask) - 1] = mask[1 : len(mask)]
        mask_shift[len(mask) - 1] = False
        #
        mask = mask | mask_shift
        df_dup_as_str = hpanutil.df_to_str(obj[mask])
        dup_msg = f"Not increasing indices are:\n{df_dup_as_str}\n"
        if msg is None:
            msg = dup_msg
        else:
            msg = dup_msg + msg
        # Dump the data to file for further inspection.
        # obj.to_csv("index.csv")
        hdbg.dassert(index.is_monotonic_increasing, msg=msg, *args)


# TODO(gp): @all Add more info in case of failures and unit tests.


def dassert_strictly_increasing_index(
    obj: Union[pd.Index, pd.DataFrame, pd.Series],
    msg: Optional[str] = None,
    *args: Any,
) -> None:
    """
    Ensure that a Pandas object has a strictly increasing index.
    """
    dassert_unique_index(obj, msg, *args)
    dassert_increasing_index(obj, msg, *args)


# TODO(gp): Not sure it's used or useful?


def dassert_monotonic_index(
    obj: Union[pd.Index, pd.DataFrame, pd.Series],
    msg: Optional[str] = None,
    *args: Any,
) -> None:
    """
    Ensure that a Pandas object has a monotonic (i.e., strictly increasing or
    decreasing index).
    """
    dassert_unique_index(obj, msg, *args)
    index = _get_index(obj)
    cond = index.is_monotonic_increasing or index.is_monotonic_decreasing
    hdbg.dassert(cond, msg=msg, *args)


# TODO(Paul): @gp -> dassert_datetime_indexed_df


def dassert_time_indexed_df(
    df: pd.DataFrame, allow_empty: bool, strictly_increasing: bool
) -> None:
    """
    Validate that input dataframe is time indexed and well-formed.

    It works for both single and multi-indexed dataframes.

    :param df: dataframe to validate
    :param allow_empty: allow empty data frames
    :param strictly_increasing: if True the index needs to be strictly
        increasing, instead of just increasing
    """
    # Verify that Pandas dataframe is passed as input.
    hdbg.dassert_isinstance(df, pd.DataFrame)
    if not allow_empty:
        # Verify that a non-empty dataframe is passed as input.
        hdbg.dassert_lt(0, df.shape[0])
        # Verify that the dataframe has at least 1 column.
        hdbg.dassert_lte(1, len(df.columns))
    # Verify that the index is increasing.
    if strictly_increasing:
        dassert_strictly_increasing_index(df)
    else:
        dassert_increasing_index(df)
    # Check that the index is in datetime format.
    dassert_index_is_datetime(df)
    # Check that the passed timestamp has timezone info.
    index_item = df.index[0]
    if isinstance(index_item, tuple):
        # In case of multi index assume that the first level is a datetime.
        index_item = index_item[0]
    hdateti.dassert_has_tz(index_item)


def dassert_indices_equal(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    allow_series: bool = False,
    only_warning: bool = False,
) -> None:
    """
    Ensure that `df1` and `df2` share a common index.

    Print the symmetric difference of indices if equality does not hold.
    """
    if allow_series:
        if isinstance(df1, pd.Series):
            df1 = df1.to_frame()
        if isinstance(df2, pd.Series):
            df2 = df2.to_frame()
    hdbg.dassert_isinstance(df1, pd.DataFrame)
    hdbg.dassert_isinstance(df2, pd.DataFrame)
    hdbg.dassert(
        df1.index.equals(df2.index),
        "df1.index.difference(df2.index)=\n%s\ndf2.index.difference(df1.index)=\n%s",
        df1.index.difference(df2.index),
        df2.index.difference(df1.index),
        only_warning=only_warning,
    )


def dassert_columns_equal(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    sort_cols: bool = False,
    only_warning: bool = False,
) -> None:
    """
    Ensure that `df1` and `df2` have the same columns.

    Print the symmetric difference of columns if equality does not hold.
    """
    hdbg.dassert_isinstance(df1, pd.DataFrame)
    hdbg.dassert_isinstance(df2, pd.DataFrame)
    if sort_cols:
        _LOG.debug("Sorting dataframe columns.")
        df1 = df1.sort_index(axis=1)
        df2 = df2.sort_index(axis=1)
    hdbg.dassert(
        df1.columns.equals(df2.columns),
        "df1.columns.difference(df2.columns)=\n%s\ndf2.columns.difference(df1.columns)=\n%s",
        df1.columns.difference(df2.columns),
        df2.columns.difference(df1.columns),
        only_warning=only_warning,
    )


def dassert_axes_equal(
    df1: pd.DataFrame, df2: pd.DataFrame, *, sort_cols: bool = False
) -> None:
    """
    Ensure that `df1` and `df2` have the same index and same columns.
    """
    dassert_indices_equal(df1, df2)
    dassert_columns_equal(df1, df2, sort_cols=sort_cols)


# TODO(Grisha): instead of passing `rtol` and `atol` use `**allclose_kwargs: Dict[str, Any]`.


def dassert_series_type_is(
    srs: pd.Series,
    type_: type,
    msg: Optional[str] = None,
    *args: Any,
) -> None:
    """
    Ensure that the data type of `srs` is `type_`.

    Examples of valid series types are
      - np.float64
      - np.int64
      - pd.Timestamp
    """
    hdbg.dassert_isinstance(srs, pd.Series)
    hdbg.dassert_isinstance(type_, type)
    hdbg.dassert_eq(srs.dtype.type, type_, msg, *args)


def dassert_series_type_in(
    srs: pd.Series,
    types: List[type],
    msg: Optional[str] = None,
    *args: Any,
) -> None:
    """
    Ensure that the data type of `srs` is one of the types in `types`.
    """
    hdbg.dassert_isinstance(srs, pd.Series)
    hdbg.dassert_container_type(types, list, type)
    hdbg.dassert_in(srs.dtype.type, types, msg, *args)


def dassert_valid_remap(to_remap: List[str], remap_dict: Dict[str, str]) -> None:
    """
    Ensure that remapping rows / columns is valid.
    """
    hdbg.dassert_isinstance(to_remap, list)
    hdbg.dassert_isinstance(remap_dict, dict)
    # All the rows / columns to remap, should exist.
    hdbg.dassert_is_subset(
        remap_dict.keys(),
        to_remap,
        "Keys to remap should be a subset of existing columns",
    )
    # The mapping is invertible.
    hdbg.dassert_no_duplicates(remap_dict.keys())
    hdbg.dassert_no_duplicates(remap_dict.values())
    # Rows / columns should not be remapped on existing rows / columns.
    hdbg.dassert_not_intersection(remap_dict.values(), to_remap)


def dassert_approx_eq(
    val1: Any,
    val2: Any,
    rtol: float = 1e-05,
    atol: float = 1e-08,
    msg: Optional[str] = None,
    *args: Any,
    only_warning: bool = False,
) -> None:
    # Approximate comparison is not applicable for strings.
    hdbg.dassert_is_not(type(val1), str)
    hdbg.dassert_is_not(type(val2), str)
    # Convert iterable inputs to list in order to comply with numpy.
    if isinstance(val1, Iterable):
        val1 = list(val1)
    if isinstance(val2, Iterable):
        val2 = list(val2)
    cond = np.allclose(
        np.array(val1), np.array(val2), rtol=rtol, atol=atol, equal_nan=True
    )
    if not cond:
        txt = f"'{val1}'\n==\n'{val2}' rtol={rtol}, atol={atol}"
        hdbg._dfatal(txt, msg, *args, only_warning=only_warning)  # type: ignore


# #############################################################################


def dassert_is_days(
    timedelta: pd.Timedelta, *, min_num_days: Optional[int] = None
) -> None:
    """
    Assert that a timedelta represents an integer number of days.

    :param timedelta: the timedelta to check
    :param min_num_days: optional minimum number of days to enforce
    """
    hdbg.dassert(
        (timedelta / pd.Timedelta(days=1)).is_integer(),
        "timedelta='%s' is not an integer number of days",
        timedelta,
    )
    if min_num_days is not None:
        hdbg.dassert_lte(1, timedelta.days)


# #############################################################################
