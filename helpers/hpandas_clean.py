"""
Import as:

import helpers.hpandas as hpandas
"""

from typing import Any, List, Optional, Union

import numpy as np
import pandas as pd

import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hpandas_utils as hpanutil
import helpers.hprint as hprint

_LOG = hloggin.getLogger(__name__)


def drop_duplicates(
    data: Union[pd.Series, pd.DataFrame],
    use_index: bool,
    column_subset: Optional[List[str]] = None,
    *args: Any,
    **kwargs: Any,
) -> Union[pd.Series, pd.DataFrame]:
    """
    Wrap `pandas.drop_duplicates()`.

    See the official docs:
    - https://pandas.pydata.org/docs/reference/api/pandas.Series.drop_duplicates.html
    - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop_duplicates.html

    :param use_index:
        - if `True`, use index values together with a column subset for
            identifying duplicates
        - if `False`, duplicated rows are with the exact same values in a subset
            and different indices
    :param column_subset: a list of columns to consider for identifying duplicates
    :return: data without duplicates
    """
    _LOG.debug(hprint.to_str("use_index column_subset args kwargs"))
    num_rows_before = data.shape[0]
    # Get all columns list for subset if no subset is passed.
    if column_subset is None:
        column_subset = data.columns.tolist()
    else:
        hdbg.dassert_lte(1, len(column_subset), "Columns subset cannot be empty")
    if use_index:
        # Add dummy index column to use it for duplicates detection.
        index_col_name = "use_index_col"
        hdbg.dassert_not_in(index_col_name, data.columns.tolist())
        column_subset.insert(0, index_col_name)
        data[index_col_name] = data.index
    # Drop duplicates based on the column subset.
    data_no_dups = data.drop_duplicates(subset=column_subset, *args, **kwargs)
    # Clean up the temporary index column if it was added.
    if use_index:
        # Remove dummy index column.
        data_no_dups = data_no_dups.drop([index_col_name], axis=1)
    # Report the change.
    num_rows_after = data_no_dups.shape[0]
    if num_rows_before != num_rows_after:
        _LOG.debug(
            "Removed %s rows",
            hprint.perc(num_rows_before - num_rows_after, num_rows_before),
        )
    return data_no_dups


def dropna(
    df: pd.DataFrame,
    *args: Any,
    drop_infs: bool = False,
    report_stats: bool = False,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Create a wrapper around pd.dropna() reporting information about the removed
    rows.

    :param df: dataframe to process
    :param drop_infs: if +/- np.inf should be considered as nans
    :param report_stats: if processing stats should be reported
    :return: dataframe with nans dropped
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    num_rows_before = df.shape[0]
    if drop_infs:
        df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(*args, **kwargs)
    if report_stats:
        num_rows_after = df.shape[0]
        pct_removed = hprint.perc(
            num_rows_before - num_rows_after, num_rows_before
        )
        _LOG.info("removed rows with nans: %s", pct_removed)
    return df


def drop_axis_with_all_nans(
    df: pd.DataFrame,
    drop_rows: bool = True,
    drop_columns: bool = False,
    drop_infs: bool = False,
    report_stats: bool = False,
) -> pd.DataFrame:
    """
    Remove columns and rows not containing information (e.g., with only nans).

    The operation is not performed in place and the resulting df is
    returned. Assume that the index is timestamps.

    :param df: dataframe to process
    :param drop_rows: remove rows with only nans
    :param drop_columns: remove columns with only nans
    :param drop_infs: remove also +/- np.inf
    :param report_stats: report the stats of the operations
    :return: dataframe with specific nan axis dropped
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    if drop_infs:
        df = df.replace([np.inf, -np.inf], np.nan)
    if drop_columns:
        # Remove columns with all nans, if any.
        cols_before = df.columns[:]
        df = df.dropna(axis=1, how="all")
        if report_stats:
            # Report results.
            cols_after = df.columns[:]
            removed_cols = set(cols_before).difference(set(cols_after))
            pct_removed = hprint.perc(
                len(cols_before) - len(cols_after), len(cols_after)
            )
            _LOG.info(
                "removed cols with all nans: %s %s",
                pct_removed,
                hprint.list_to_str(removed_cols),
            )
    if drop_rows:
        # Remove rows with all nans, if any.
        rows_before = df.index[:]
        df = df.dropna(axis=0, how="all")
        if report_stats:
            # Report results.
            rows_after = df.index[:]
            removed_rows = set(rows_before).difference(set(rows_after))
            if len(rows_before) == len(rows_after):
                # Nothing was removed.
                min_ts = max_ts = None
            else:
                # TODO(gp): Report as intervals of dates.
                min_ts = min(removed_rows)
                max_ts = max(removed_rows)
            pct_removed = hprint.perc(
                len(rows_before) - len(rows_after), len(rows_after)
            )
            _LOG.info(
                "removed rows with all nans: %s [%s, %s]",
                pct_removed,
                min_ts,
                max_ts,
            )
    return df


def drop_duplicated(
    df: pd.DataFrame, *, subset: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Implement `df.duplicated` but considering also the index and ignoring nans.
    """
    _LOG.debug("before df=\n%s", hpanutil.df_to_str(df))
    # Move the index to the df.
    old_index_name = df.index.name
    new_index_name = "_index.tmp"
    hdbg.dassert_not_in(new_index_name, df.columns)
    df.index.name = new_index_name
    df.reset_index(drop=False, inplace=True)
    # Remove duplicates by ignoring nans.
    if subset is not None:
        hdbg.dassert_isinstance(subset, list)
        subset = [new_index_name] + subset
    duplicated = df.fillna(0.0).duplicated(subset=subset, keep="first")
    # Report the result of the operation.
    if duplicated.sum() > 0:
        num_rows_before = df.shape[0]
        _LOG.debug(
            "Removing duplicates df=\n%s",
            hpanutil.df_to_str(df.loc[duplicated]),
        )
        df = df.loc[~duplicated]
        num_rows_after = df.shape[0]
        _LOG.warning(
            "Removed repeated rows num_rows=%s",
            hprint.perc(num_rows_before - num_rows_after, num_rows_before),
        )
    _LOG.debug("after removing duplicates df=\n%s", hpanutil.df_to_str(df))
    # Set the index back.
    df.set_index(new_index_name, inplace=True)
    df.index.name = old_index_name
    _LOG.debug("after df=\n%s", hpanutil.df_to_str(df))
    return df


# #############################################################################


def remove_outliers(
    df: pd.DataFrame,
    lower_quantile: float,
    *,
    column_set: hpanutil.ColumnSet,
    # TODO(Grisha): the params are not used.
    fill_value: float = np.nan,
    mode: str = "remove_outliers",
    axis: Any = 0,
    upper_quantile: Optional[float] = None,
) -> pd.DataFrame:
    hdbg.dassert_eq(len(df.shape), 2, "Multi-index dfs not supported")
    # Validate quantile parameters.
    hdbg.dassert_lte(0.0, lower_quantile)
    if upper_quantile is None:
        upper_quantile = 1.0 - lower_quantile
    hdbg.dassert_lte(lower_quantile, upper_quantile)
    hdbg.dassert_lte(upper_quantile, 1.0)
    # Create a copy of the dataframe to avoid modifying the original.
    df = df.copy()
    if axis == 0:
        all_columns = df.columns
        columns = hpanutil.resolve_column_names(column_set, all_columns)
        hdbg.dassert_is_subset(columns, df.columns)
        for column in all_columns:
            if column in columns:
                df[column] = df[column].quantile(
                    [lower_quantile, upper_quantile]
                )
    elif axis == 1:
        all_rows = df.rows
        rows = hpanutil.resolve_column_names(column_set, all_rows)
        hdbg.dassert_is_subset(rows, df.rows)
        for row in all_rows:
            if row in rows:
                df[row] = df[row].quantile([lower_quantile, upper_quantile])
    else:
        raise ValueError(f"Invalid axis='{axis}'")
    return df
