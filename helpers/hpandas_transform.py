"""
Import as:

import helpers.hpandas_transform as hpantran
"""

import csv
import random
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pandas as pd

import helpers.hdatetime as hdateti
import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hpandas_conversion as hpanconv
import helpers.hpandas_dassert as hpandass
import helpers.hpandas_utils as hpanutil
import helpers.hprint as hprint

_LOG = hloggin.getLogger(__name__)

# Enable extra verbose debugging. Do not commit.
_TRACE = False

RowsValues = List[List[str]]

# #############################################################################
# Resampling & Time Series Operations
# #############################################################################


def resample_index(index: pd.DatetimeIndex, frequency: str) -> pd.DatetimeIndex:
    """
    Resample `DatetimeIndex`.

    :param index: `DatetimeIndex` to resample
    :param frequency: frequency from `pd.date_range()` to resample to
    :return: resampled `DatetimeIndex`
    """
    _LOG.debug(hprint.to_str("index frequency"))
    hdbg.dassert_isinstance(index, pd.DatetimeIndex)
    hpandass.dassert_unique_index(
        index, msg="Index must have only unique values"
    )
    min_date = index.min()
    max_date = index.max()
    _LOG.debug("min_date=%s max_date=%s", min_date, max_date)
    # TODO(gp): Preserve the index name.
    # index_name = index.name
    resampled_index = pd.date_range(
        start=min_date,
        end=max_date,
        freq=frequency,
    )
    # Enable detailed debugging.
    if False:
        if len(resampled_index) > len(index):
            # Downsample.
            _LOG.debug(
                "Index length increased by %s = %s - %s",
                len(resampled_index) - len(index),
                len(resampled_index),
                len(index),
            )
        elif len(resampled_index) < len(index):
            # Upsample.
            _LOG.debug(
                "Index length decreased by %s = %s - %s",
                len(index) - len(resampled_index),
                len(index),
                len(resampled_index),
            )
        else:
            _LOG.debug("Index length=%s has not changed", len(index))
    # resampled_index.name = index_name
    return resampled_index


def resample_df(df: pd.DataFrame, frequency: str) -> pd.DataFrame:
    """
    Resample `DataFrame` by placing NaN in missing locations in the index.

    :param df: `DataFrame` to resample
    :param frequency: frequency from `pd.date_range()` to resample to
    :return: resampled `DataFrame`
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    # Preserve the index name.
    index_name = df.index.name
    resampled_index = resample_index(df.index, frequency)
    df_reindex = df.reindex(resampled_index)
    df_reindex.index.name = index_name
    return df_reindex


def reindex_on_unix_epoch(
    df: pd.DataFrame, in_col_name: str, unit: str = "s"
) -> pd.DataFrame:
    """
    Transform the column `in_col_name` into a datetime index. `in_col_name`
    contains Unix epoch (e.g., 1638194400) and it is converted into a UTC time.

    :param df: dataframe with a unix epoch
    :param in_col_name: column containing unix epoch
    :param unit: the unit of unix epoch
    """
    # Convert.
    temp_col_name = in_col_name + "_tmp"
    hdbg.dassert_in(in_col_name, df.columns)
    hdbg.dassert_not_in(temp_col_name, df.columns)
    # Save.
    df[temp_col_name] = pd.to_datetime(df[in_col_name], unit=unit, utc=True)
    df.set_index(temp_col_name, inplace=True, drop=True)
    df.index.name = None
    return df


def find_gaps_in_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Find data present in one dataframe and missing in the other one.

    :param df1: first dataframe for comparison
    :param df2: second dataframe for comparison
    :return: two dataframes with missing data
    """
    # Get data present in first, but not present in second dataframe.
    first_missing_indices = df2.index.difference(df1.index)
    first_missing_data = df2.loc[first_missing_indices]
    # Get data present in second, but not present in first dataframe.
    second_missing_indices = df1.index.difference(df2.index)
    second_missing_data = df1.loc[second_missing_indices]
    return first_missing_data, second_missing_data


# TODO(Grisha): use this idiom everywhere in the codebase, e.g., in `compare_dfs()`.


def find_gaps_in_time_series(
    time_series: pd.Series,
    start_timestamp: pd.Timestamp,
    end_timestamp: pd.Timestamp,
    freq: str,
) -> pd.Series:
    """
    Find missing points on a time interval specified by [start_timestamp,
    end_timestamp], where point distribution is determined by <step>.

    If the passed time series is of a unix epoch format. It is
    automatically tranformed to pd.Timestamp.

    :param time_series: time series to find gaps in
    :param start_timestamp: start of the time interval to check
    :param end_timestamp: end of the time interval to check
    :param freq: distance between two data points on the interval.
        Aliases correspond to pandas.date_range's freq parameter, i.e.
        "S" -> second, "T" -> minute.
    :return: pd.Series representing missing points in the source time
        series.
    """
    _time_series = time_series
    if str(time_series.dtype) in ["int32", "int64"]:
        _time_series = _time_series.map(hdateti.convert_unix_epoch_to_timestamp)
    correct_time_series = pd.date_range(
        start=start_timestamp, end=end_timestamp, freq=freq
    )
    return correct_time_series.difference(_time_series)


# #############################################################################
# DataFrame Transformation
# #############################################################################


def apply_index_mode(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    mode: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process DataFrames according to the index mode.

    :param df1: first input df
    :param df2: second input df
    :param mode: method of processing indices
        - "assert_equal": check that both indices are equal, assert otherwise
        - "intersect": restrict both dfs to a common index
        - "leave_unchanged": ignore any indices mismatch and return dfs as-is
    :return: transformed copy of the inputs
    """
    _LOG.debug("mode=%s", mode)
    hdbg.dassert_isinstance(df1, pd.DataFrame)
    hdbg.dassert_isinstance(df2, pd.DataFrame)
    hdbg.dassert_isinstance(mode, str)
    # Copy in order not to modify the inputs.
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    if mode == "assert_equal":
        hpandass.dassert_indices_equal(df1_copy, df2_copy)
    elif mode == "intersect":
        # TODO(Grisha): Add sorting on demand.
        common_index = df1_copy.index.intersection(df2_copy.index)
        df1_copy = df1_copy[df1_copy.index.isin(common_index)]
        df2_copy = df2_copy[df2_copy.index.isin(common_index)]
    elif mode == "leave_unchanged":
        _LOG.debug(
            "Ignoring any index missmatch as per user's request.\n"
            "df1.index.difference(df2.index)=\n%s\ndf2.index.difference(df1.index)=\n%s",
            df1_copy.index.difference(df2_copy.index),
            df2_copy.index.difference(df1_copy.index),
        )
    else:
        raise ValueError(f"Unsupported index_mode={mode}")
    return df1_copy, df2_copy


def apply_columns_mode(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    mode: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process DataFrames according to the column mode.

    :param df1: first input df
    :param df2: second input df
    :param mode: method of processing columns
        - "assert_equal": check that both dfs have equal columns, assert otherwise
        - "intersect": restrict both dfs to only include common columns
        - "leave_unchanged": ignore any column mismatches and return dfs as-is
    :return: transformed copy of the inputs
    """
    _LOG.debug("mode=%s", mode)
    # Input validation.
    hdbg.dassert_isinstance(df1, pd.DataFrame)
    hdbg.dassert_isinstance(df2, pd.DataFrame)
    hdbg.dassert_isinstance(mode, str)
    # Copy in order not to modify the inputs.
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    if mode == "assert_equal":
        # Check if columns are equal or not.
        hpandass.dassert_columns_equal(df1_copy, df2_copy)
    elif mode == "intersect":
        # Filter dataframes based on its common columns.
        common_columns = df1_copy.columns.intersection(df2_copy.columns)
        df1_copy = df1_copy[common_columns]
        df2_copy = df2_copy[common_columns]
        # Log the string representation of 2 dfs.
        _LOG.debug("df1 after filtering=\n%s", hpanutil.df_to_str(df1))
        _LOG.debug("df2 after filtering=\n%s", hpanutil.df_to_str(df2))
    elif mode == "leave_unchanged":
        # Ignore mismatch.
        _LOG.debug(
            "Ignoring any column missmatch as per user's request.\n"
            "df1.columns.difference(df2.columns)=\n%s\ndf2.columns.difference(df1.columns)=\n%s",
            df1.columns.difference(df2.columns),
            df2.columns.difference(df1.columns),
        )
    else:
        raise ValueError(f"Unsupported column mode: {mode}")
    return df1_copy, df2_copy


def trim_df(
    df: pd.DataFrame,
    ts_col_name: Optional[str],
    start_ts: Optional[pd.Timestamp],
    end_ts: Optional[pd.Timestamp],
    left_close: bool,
    right_close: bool,
) -> pd.DataFrame:
    """
    Trim the dataframe using values in `ts_col_name`.

    The dataframe is trimmed in the interval bounded by `start_ts` and `end_ts`.

    :param df: the dataframe to trim
    :param ts_col_name: the name of the column; `None` means index
    :param start_ts: the start boundary for trimming
    :param end_ts: the end boundary for trimming
    :param left_close: whether to include the start boundary of the interval
        - True: [start_ts, ...
        - False: (start_ts, ...
    :param right_close: whether to include the end boundary of the interval
        - True: ..., end_ts]
        - False: ..., end_ts)
    :return: the trimmed dataframe
    """
    if _TRACE:
        _LOG.trace(
            hpanutil.df_to_str(
                df, print_dtypes=True, print_shape_info=True, tag="df"
            )
        )
    _LOG.debug(
        hprint.to_str("ts_col_name start_ts end_ts left_close right_close")
    )
    if _TRACE:
        _LOG.trace("df=\n%s", hpanutil.df_to_str(df))
    if df.empty:
        # If the df is empty, there is nothing to trim.
        return df
    if start_ts is None and end_ts is None:
        # If no boundaries are specified, there are no points of reference to trim
        # to.
        return df
    num_rows_before = df.shape[0]
    if start_ts is not None and end_ts is not None:
        # Confirm that the interval boundaries are valid.
        hdateti.dassert_tz_compatible(start_ts, end_ts)
        hdbg.dassert_lte(start_ts, end_ts)
    # Get the values to filter by.
    if ts_col_name is None:
        values_to_filter_by = pd.Series(df.index, index=df.index)
    else:
        hdbg.dassert_in(ts_col_name, df.columns)
        values_to_filter_by = df[ts_col_name]
    if values_to_filter_by.is_monotonic_increasing:
        _LOG.trace("df is monotonic")
        # The values are sorted; using the `pd.Series.searchsorted()` method.
        # Find the index corresponding to the left boundary of the interval.
        if start_ts is not None:
            side = "left" if left_close else "right"
            left_idx = values_to_filter_by.searchsorted(start_ts, side)
        else:
            # There is nothing to filter, so the left index is the first one.
            left_idx = 0
        _LOG.debug(hprint.to_str("start_ts left_idx"))
        # Find the index corresponding to the right boundary of the interval.
        if end_ts is not None:
            side = "right" if right_close else "left"
            right_idx = values_to_filter_by.searchsorted(end_ts, side)
        else:
            # There is nothing to filter, so the right index is None.
            right_idx = df.shape[0]
        _LOG.debug(hprint.to_str("end_ts right_idx"))
        #
        hdbg.dassert_lte(0, left_idx)
        hdbg.dassert_lte(left_idx, right_idx)
        hdbg.dassert_lte(right_idx, df.shape[0])
        _LOG.debug(hprint.to_str("start_ts left_idx"))
        if right_idx < df.shape[0]:
            _LOG.debug(hprint.to_str("end_ts right_idx"))
        df = df.iloc[left_idx:right_idx]
    else:
        _LOG.trace("df is not monotonic")
        # The values are not sorted; using the `pd.Series.between` method.
        if left_close and right_close:
            inclusive = "both"
        elif left_close:
            inclusive = "left"
        elif right_close:
            inclusive = "right"
        else:
            inclusive = "neither"
        epsilon = pd.DateOffset(minutes=1)
        if start_ts is None:
            start_ts = values_to_filter_by.min() - epsilon
        if end_ts is None:
            end_ts = values_to_filter_by.max() + epsilon
        df = df[
            values_to_filter_by.between(start_ts, end_ts, inclusive=inclusive)
        ]
    # Report the changes.
    num_rows_after = df.shape[0]
    if num_rows_before != num_rows_after:
        _LOG.debug(
            "Removed %s rows",
            hprint.perc(num_rows_before - num_rows_after, num_rows_before),
        )
    return df


def _assemble_df_rows(rows_values: RowsValues) -> RowsValues:
    """
    Organize dataframe values into a column-row structure.

    - Indentation artifacts are removed
    - The index placement is handled, i.e.
      - if the index is named, the name is located and moved to the same
        row as the column names
      - if the index is not named, the row with the column names receives
        a placeholder empty value in its place
    - Empty columns are dropped

    :param rows_values: row values extracted from a string df representation
    :return: row values assembled into a valid column-row structure
    """
    # Clean up indentation artifacts.
    if all(row[0] == "" for row in rows_values):
        # Remove the first empty cell in each row.
        for row in rows_values:
            del row[0]
    # If the index is named, its name is located in the second row,
    # with an optional extra empty value cell value next to it.
    if len(rows_values[1]) == 1 or (
        len(rows_values[1]) == 2 and rows_values[1][1] == ""
    ):
        # Move the index name to the row with all the column names.
        if rows_values[0][0] == "":
            rows_values[0][0] = rows_values[1][0]
        else:
            rows_values[0].insert(0, rows_values[1][0])
        # Drop the former index name row.
        del rows_values[1]
    else:
        # Add an empty cell for the absent index name.
        rows_values[0].insert(0, "")
    # Identify and remove empty columns.
    min_len_row = min(len(row) for row in rows_values)
    idxs_to_delete = []
    for i in range(min_len_row):
        if all(row[i] == "" for row in rows_values):
            idxs_to_delete.append(i)
    for idx in idxs_to_delete:
        for row in rows_values:
            del row[idx]
    # Confirm that all the rows have the same number of values.
    hdbg.dassert_eq(len({len(row) for row in rows_values}), 1)
    return rows_values


# TODO(Nina): Add `filter_data_mode`.


def str_to_df(
    df_as_str: str,
    col_to_type: Dict[str, Optional[type]],
    col_to_name_type: Dict[str, type],
) -> pd.DataFrame:
    """
    Convert a string representation of a dataframe into a Pandas df.

    :param df_as_str: a df as a string
        - the format of the string is the same as the output of
          `hpandas.df_to_str()` on a pd.DataFrame, e.g.
          ```
              col1 col2   col3   col4
          0   0.1  a      None   2020-01-01
          1   0.2  "b c"  None   2021-05-05
          ```
        - values (including column names) that contain spaces need
          to be enclosed in double quotation marks, e.g.
          "2023-03-15 16:35:41.205000+00:00"
    :param col_to_type: a mapping between the column names and the
        types of the values in these columns
        - if a column is not present in the mapping, its values will
          remain strings
        - to indicate the type of index values, use {"__index__": ...}
          mapping, e.g. {"__index__": pd.Timestamp}
    :param col_to_name_type: a mapping between the column names and
        the required types of these column names
        - same conventions apply as for `col_to_type` (see above)
    :return: a converted Pandas dataframe
    """
    # Separate the rows.
    rows = df_as_str.split("\n")
    # Clean up extra spaces.
    rows_merged_space = [re.sub(" +", " ", row) for row in rows if len(row)]
    # Identify individual values in the rows.
    rows_values = list(csv.reader(rows_merged_space, delimiter=" "))
    # Remove the placeholder ["..."] row.
    rows_values = [row for row in rows_values if row != ["..."]]
    # Organize values into a proper column-row structure.
    rows_values = _assemble_df_rows(rows_values)
    # Get the column names.
    column_names = rows_values[0][1:]
    # Get the index.
    index_values = [row[0] for row in rows_values[1:]]
    index_name = rows_values[0][0]
    # Construct the df.
    df = pd.DataFrame(
        [row[1:] for row in rows_values[1:]],
        columns=column_names,
        index=index_values,
    )
    if index_name != "":
        df.index.name = index_name
    # Cast the columns into appropriate types.
    for col, col_type in col_to_type.items():
        if col == "__index__":
            df.index = hpanconv.cast_series_to_type(df.index, col_type)
        else:
            df[col] = hpanconv.cast_series_to_type(df[col], col_type)
    # Cast the column names into appropriate types.
    for col, col_name_type in col_to_name_type.items():
        if col == "__index__":
            df.index = df.index.rename(col_name_type(df.index.name))
        else:
            df = df.rename(columns={col: col_name_type(col)})
    return df


# #############################################################################
# Column Operations
# #############################################################################


def check_and_filter_matching_columns(
    df: pd.DataFrame, required_columns: List[str], filter_data_mode: str
) -> pd.DataFrame:
    """
    Check that columns are the required ones and if not filter data depending
    on `filter_data_mode`.

    :param df: data to check columns for
    :param required_columns: columns to return, skipping columns that are not required
    :param filter_data_mode: control behaviour with respect to extra or missing columns
        - "assert": raise an error if required columns do not match received columns
        - "warn_and_trim": return the intersection of required and received columns and
           issue a warning
    :return: input data as it is if required columns match received columns otherwise
        processed data, see `filter_data_mode`
    """
    received_columns = df.columns.to_list()
    hdbg.dassert_lte(1, len(received_columns))
    #
    if filter_data_mode == "assert":
        # Raise an assertion.
        only_warning = False
    elif filter_data_mode == "warn_and_trim":
        # Just issue a warning.
        only_warning = True
        # Get columns intersection while preserving the order of the columns.
        columns_intersection = [
            col_name
            for col_name in required_columns
            if col_name in received_columns
        ]
        hdbg.dassert_lte(1, len(columns_intersection))
        df = df[columns_intersection]
    else:
        raise ValueError(f"Invalid filter_data_mode='{filter_data_mode}'")
    hdbg.dassert_set_eq(
        required_columns,
        received_columns,
        only_warning=only_warning,
        msg="Received columns do not match required columns.",
    )
    return df


# TODO(Grisha): finish the function.
# TODO(Grisha): merge with the one in `dataflow.model.correlation.py`?


# #############################################################################
# Merge
# #############################################################################


def merge_dfs(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    threshold_col_name: str,
    *,
    threshold: float = 0.9,
    intersecting_columns: Optional[List[str]] = None,
    **pd_merge_kwargs: Any,
) -> pd.DataFrame:
    """
    Wrap `pd.merge`.

    :param threshold_col_name: a column's name to check the minimum
        overlap on
    :param threshold: minimum overlap of unique values in a specified
        column to perform the merge
    :param intersecting_columns: allow certain columns to appear in both
        dataframes; store both in the resulting df with corresponding
        suffixes
    """
    _LOG.debug(
        hprint.to_str(
            "threshold_col_name threshold intersecting_columns pd_merge_kwargs"
        )
    )
    # Sanity check column types.
    threshold_col1 = df1[threshold_col_name]
    threshold_col2 = df2[threshold_col_name]
    only_first_elem = False
    hdbg.dassert_array_has_same_type_element(
        threshold_col1, threshold_col2, only_first_elem
    )
    # TODO(Grisha): @Dan Implement asserts for each asset id.
    # Check that an overlap of unique values is above the specified threshold.
    threshold_unique_values1 = set(threshold_col1)
    threshold_unique_values2 = set(threshold_col2)
    threshold_common_values = set(threshold_unique_values1) & set(
        threshold_unique_values2
    )
    threshold_common_values_share1 = len(threshold_common_values) / len(
        threshold_unique_values1
    )
    threshold_common_values_share2 = len(threshold_common_values) / len(
        threshold_unique_values2
    )
    hdbg.dassert_lte(threshold, threshold_common_values_share1)
    hdbg.dassert_lte(threshold, threshold_common_values_share2)
    # Use an empty set instead of None to perform set difference further.
    intersecting_columns_set = (
        set() if intersecting_columns is None else set(intersecting_columns)
    )
    # Check that there are no common columns except for the ones in `intersecting_columns`.
    df1_cols = (
        set(df1.columns.to_list())
        - set(pd_merge_kwargs["on"])
        - intersecting_columns_set
    )
    df2_cols = (
        set(df2.columns.to_list())
        - set(pd_merge_kwargs["on"])
        - intersecting_columns_set
    )
    hdbg.dassert_not_intersection(df1_cols, df2_cols)
    #
    res_df = df1.merge(df2, **pd_merge_kwargs)
    return res_df


# TODO(gp): Is this (ironically) a duplicate of drop_duplicates?


def get_df_from_iterator(
    iter_: Iterator[pd.DataFrame],
    *,
    sort_index: bool = True,
) -> pd.DataFrame:
    """
    Concat all the dataframes in the iterator in one dataframe.

    :param iter_: dataframe iterator
    :param sort_index: whether to sort output index or not
    :return: combined iterator data
    """
    # TODO(gp): @all make a copy of `iter_` so we don't consume it.
    dfs = list(iter_)
    df_res = pd.concat(dfs)
    if sort_index:
        df_res = df_res.sort_index()
    return df_res


# #############################################################################
# Filter
# #############################################################################


def subset_df(df: pd.DataFrame, nrows: int, seed: int = 42) -> pd.DataFrame:
    """
    Remove N rows from the input data and shuffle the remaining ones.

    :param df: input data
    :param nrows: the number of rows to remove from the original data
    :param seed: see `random.seed()`
    :return: shuffled data with removed rows
    """
    hdbg.dassert_lte(1, nrows)
    hdbg.dassert_lte(nrows, df.shape[0])
    idx = list(range(df.shape[0]))
    random.seed(seed)
    random.shuffle(idx)
    idx = sorted(idx[nrows:])
    return df.iloc[idx]


def filter_df(
    df: pd.DataFrame,
    col_name: str,
    value: Any,
    *,
    invert: bool = False,
    check_value: bool = True,
    # TODO(gp): -> verbose
    print_info: bool = True,
) -> pd.DataFrame:
    """
    Filter a dataframe based on a column value.

    :param df: dataframe to filter
    :param col_name: column name to filter on
    :param value: value to filter on
    :param invert: whether to invert the filter
    :param check_value: whether to check that the value is in the column
    :param print_info: whether to print information about the filter
    :return: filtered dataframe
    """
    hdbg.dassert_in(col_name, df.columns)
    if isinstance(value, list):
        mask = df[col_name].isin(value)
    else:
        if check_value:
            hdbg.dassert_in(value, df[col_name].unique())
        mask = df[col_name] == value
    if invert:
        mask = ~mask
    if print_info:
        _LOG.info("selected=%s", hprint.perc(mask.sum(), df.shape[0]))
    return df[mask]


def remove_empty_columns(
    df: pd.DataFrame, *, verbose: bool = True
) -> pd.DataFrame:
    """
    Remove empty columns from a dataframe.

    :param df: dataframe to remove empty columns from
    :return: dataframe with empty columns removed
    """
    mask = df.apply(lambda col: col.notna() & (col != "")).any()
    non_empty_columns = df.columns[mask]
    empty_columns = df.columns[~mask]
    if verbose:
        _LOG.info(
            "kept %s columns: %s",
            hprint.perc(len(non_empty_columns), len(df.columns)),
            hprint.list_to_str(non_empty_columns),
        )
        _LOG.info(
            "removed %s columns: %s",
            hprint.perc(len(empty_columns), len(df.columns)),
            hprint.list_to_str(empty_columns),
        )
    df = df[non_empty_columns]
    return df


def remove_stable_columns(
    df: pd.DataFrame, *, threshold: float = 0.9, verbose: bool = True
) -> pd.DataFrame:
    """
    Remove columns from a dataframe that have less than threshold unique values.

    :param df: dataframe to remove stable columns from
    :param threshold: threshold for the percentage of stable columns to remove
    :return: dataframe with stable columns removed
    """
    high_variability_columns = []
    for col in df.columns:
        unique_values = df[col].unique()
        if len(unique_values) / len(df) >= threshold:
            high_variability_columns.append(col)
    # Compute the columns to remove.
    columns_to_remove = df.columns[~df.columns.isin(high_variability_columns)]
    if verbose:
        _LOG.info(
            "kept %s columns: %s",
            hprint.perc(len(high_variability_columns), len(df.columns)),
            hprint.list_to_str(high_variability_columns),
        )
        _LOG.info(
            "removed %s columns: %s",
            hprint.perc(len(columns_to_remove), len(df.columns)),
            hprint.list_to_str(columns_to_remove),
        )
    df = df[high_variability_columns]
    return df
