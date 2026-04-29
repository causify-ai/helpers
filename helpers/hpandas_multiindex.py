"""
Import as:

import helpers.hpandas_multiindex as hpanmult
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hpandas_compare as hpancomp
import helpers.hpandas_dassert as hpandass
import helpers.hpandas_transform as hpantran
import helpers.hpandas_utils as hpanutil
import helpers.hprint as hprint

_LOG = hloggin.getLogger(__name__)

RowsValues = List[List[str]]

# #############################################################################
# Functions
# #############################################################################


def add_multiindex_col(
    df: pd.DataFrame, multiindex_col: pd.DataFrame, col_name: str
) -> pd.DataFrame:
    """
    Add column to a multiindex DataFrame.

    Note: each column in a multiindex DataFrame is a DataFrame itself.

    :param df: multiindex df
    :param multiindex_col: column (i.e. singleindex df) of a multiindex df
    :param col_name: name of a new column
    :return: a multiindex DataFrame with a new column
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_isinstance(df.columns, pd.MultiIndex)
    hdbg.dassert_eq(2, len(df.columns.levels))
    hdbg.dassert_isinstance(multiindex_col, pd.DataFrame)
    hdbg.dassert_isinstance(col_name, str)
    hdbg.dassert_not_in(col_name, df.columns)
    for col in multiindex_col.columns:
        df[col_name, col] = multiindex_col[col]
    return df


def multiindex_df_info(
    df: pd.DataFrame,
    *,
    log_level: int = logging.INFO,
    **list_to_str_kwargs: Dict[str, Any],
) -> str:
    """
    Report information about a multi-index df.
    """
    hdbg.dassert_isinstance(df.columns, pd.MultiIndex)
    hdbg.dassert_eq(2, len(df.columns.levels))
    columns_level0 = df.columns.levels[0]
    columns_level1 = df.columns.levels[1]
    rows = df.index
    ret = []
    ret.append(
        f"shape={len(columns_level0)} x {len(columns_level1)} x {len(rows)}"
    )
    ret.append(
        "columns_level0="
        + hprint.list_to_str2(columns_level0, **list_to_str_kwargs)
    )
    ret.append(
        "columns_level1="
        + hprint.list_to_str2(columns_level1, **list_to_str_kwargs)
    )
    ret.append("rows=" + hprint.list_to_str2(rows, **list_to_str_kwargs))
    if isinstance(df.index, pd.DatetimeIndex):
        # Display timestamp info.
        start_timestamp = df.index.min()
        end_timestamp = df.index.max()
        frequency = df.index.freq
        if frequency is None:
            # Try to infer frequency.
            frequency = pd.infer_freq(df.index)
        ret.append(f"start_timestamp={start_timestamp}")
        ret.append(f"end_timestamp={end_timestamp}")
        ret.append(f"frequency={frequency}")
    ret = "\n".join(ret)
    _LOG.log(log_level, ret)
    return ret


def subset_multiindex_df(
    df: pd.DataFrame,
    *,
    # TODO(gp): Consider passing trim_df_kwargs as kwargs.
    start_timestamp: Optional[pd.Timestamp] = None,
    end_timestamp: Optional[pd.Timestamp] = None,
    columns_level0: hpanutil.ColumnSet = None,
    columns_level1: hpanutil.ColumnSet = None,
    keep_order: bool = False,
) -> pd.DataFrame:
    """
    Filter multi-index DataFrame by timestamp index and column levels.

    :param start_timestamp: see `trim_df()`
    :param end_timestamp: see `trim_df()`
    :param columns_level0: column names that corresponds to `df.columns.levels[0]`
        - `None` means no filtering
    :param columns_level1: column names that corresponds to `df.columns.levels[1]`
        - `None` means no filtering
    :param keep_order: see `hpandas_utils.resolve_column_names()`
    :return: filtered DataFrame
    """
    hdbg.dassert_isinstance(df.columns, pd.MultiIndex)
    hdbg.dassert_eq(2, len(df.columns.levels))
    # Filter by timestamp.
    allow_empty = False
    strictly_increasing = False
    hpandass.dassert_time_indexed_df(df, allow_empty, strictly_increasing)
    df = hpantran.trim_df(
        df,
        ts_col_name=None,
        start_ts=start_timestamp,
        end_ts=end_timestamp,
        left_close=True,
        right_close=True,
    )
    # Filter level 0.
    hdbg.dassert_isinstance(df.columns, pd.MultiIndex)
    all_columns_level0 = df.columns.levels[0]
    columns_level0 = hpanutil.resolve_column_names(
        columns_level0, all_columns_level0, keep_order=keep_order
    )
    hdbg.dassert_isinstance(df.columns, pd.MultiIndex)
    hdbg.dassert_is_subset(columns_level0, df.columns.levels[0])
    df = df[columns_level0]
    # Filter level 1.
    hdbg.dassert_isinstance(df.columns, pd.MultiIndex)
    all_columns_level1 = df.columns.levels[1]
    columns_level1 = hpanutil.resolve_column_names(
        columns_level1, all_columns_level1, keep_order=keep_order
    )
    hdbg.dassert_isinstance(df.columns, pd.MultiIndex)
    hdbg.dassert_is_subset(columns_level1, df.columns.levels[1])
    df = df.swaplevel(axis=1)[columns_level1].swaplevel(axis=1)
    return df


# #############################################################################


def compare_multiindex_dfs(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    subset_multiindex_df_kwargs: Optional[Dict[str, Any]] = None,
    compare_dfs_kwargs: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    - Subset both multi-index dfs, if needed
    - Compare dfs

    :param subset_multiindex_df: params for `subset_multiindex_df()`
    :param compare_dfs_kwargs: params for `compare_dfs()`
    :return: df with differences as values
    """
    # Subset dfs.
    if subset_multiindex_df_kwargs is None:
        subset_multiindex_df_kwargs = {}
    subset_df1 = subset_multiindex_df(df1, **subset_multiindex_df_kwargs)
    subset_df2 = subset_multiindex_df(df2, **subset_multiindex_df_kwargs)
    # Compare dfs.
    if compare_dfs_kwargs is None:
        compare_dfs_kwargs = {}
    diff_df = hpancomp.compare_dfs(subset_df1, subset_df2, **compare_dfs_kwargs)
    return diff_df


# #############################################################################
