"""
Import as:

import helpers.hpandas as hpandas
"""

import logging
from typing import List

import numpy as np
import pandas as pd

import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hpandas_dassert as hpandass
import helpers.hpandas_utils as hpanutil

_LOG = hloggin.getLogger(__name__)

RowsValues = List[List[str]]


def compare_dataframe_rows(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    Compare contents of rows with same indices.

    Index is set to default sequential integer values because compare is
    sensitive to multi index (probably because new multi indexes are created
    for each difference in `compare`). Multi index columns are regular columns now.
    Excess columns are removed so both dataframes are always same shape because
    `compare` expects identical dataframes (same number of rows, columns, etc.).

    :param df1: first dataframe for comparison
    :param df2: second dataframe for comparison
    :return: dataframe with data with same indices and different contents
    """
    # Get rows on which the two dataframe indices match.
    idx_intersection = df1.index.intersection(df2.index)
    # Remove excess columns and reset indexes.
    trimmed_second = df2.loc[idx_intersection].reset_index()
    trimmed_first = df1.loc[idx_intersection].reset_index()
    # Get difference between second and first dataframe.
    data_difference = trimmed_second.compare(trimmed_first)
    # Update data difference with original dataframe index names
    # for easier identification.
    index_names = tuple(df2.index.names)
    # If index or multi index is named, it will be visible in data difference.
    if index_names != (None,):
        for index in data_difference.index:
            for column in index_names:
                data_difference.loc[index, column] = trimmed_second.loc[index][
                    column
                ]
        data_difference = data_difference.convert_dtypes()
    return data_difference


def compare_nans_in_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> pd.DataFrame:
    """
    Compare equality of DataFrames in terms of NaNs.

    For example:
    - `5 vs np.nan` is a mismatch
    - `np.nan vs 5` is a mismatch
    - `np.nan vs np.nan` is a match
    - `np.nan vs np.inf` is a mismatch

    :param df1: dataframe to compare
    :param df2: dataframe to compare with
    :return: dataframe that shows the differences stacked side by side, see
        `pandas.DataFrame.compare()` for an example
    """
    hpandass.dassert_axes_equal(df1, df2)
    # Keep rows where df1's value is NaN and df2's value is not NaN and vice versa.
    mask1 = df1.isna() & ~df2.isna()
    mask2 = ~df1.isna() & df2.isna()
    mask3 = mask1 | mask2
    # Compute a dataframe with the differences.
    nan_diff_df = df1[mask3].compare(df2[mask3], result_names=("df1", "df2"))
    return nan_diff_df


# TODO(Grisha): -> `compare_dataframes()`?
def compare_dfs(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    *,
    row_mode: str = "equal",
    column_mode: str = "equal",
    # TODO(Grisha): should be True by default?
    compare_nans: bool = False,
    diff_mode: str = "diff",
    assert_diff_threshold: float = 1e-3,
    close_to_zero_threshold: float = 1e-6,
    zero_vs_zero_is_zero: bool = True,
    remove_inf: bool = True,
    log_level: int = logging.DEBUG,
    only_warning: bool = True,
) -> pd.DataFrame:
    """
    Compare two dataframes.

    This works for dataframes with and without multi-index.

    :param row_mode: control how the rows are handled
        - "equal": rows need to be the same for the two dataframes
        - "inner": compute the common rows for the two dataframes
    :param column_mode: same as `row_mode`
    :param compare_nans: include NaN comparison if True otherwise just
        compare non-NaN values
    :param diff_mode: control how the dataframes are compared in terms of
        corresponding elements
        - "diff": use the difference
        - "pct_change": use the percentage difference
    :param assert_diff_threshold: maximum allowed total difference
        - do not assert if `None`
        - works when `diff_mode` is "pct_change"
    :param close_to_zero_threshold: round numbers below the threshold to 0
    :param zero_vs_zero_is_zero: replace the diff with 0 when comparing 0 to 0
        if True, otherwise keep the actual result
    :param remove_inf: replace +-inf with `np.nan`
    :param log_level: logging level
    :param only_warning: when `True` the function issues a warning instead of aborting
    :return: a singe dataframe with differences as values
    """
    hdbg.dassert_isinstance(df1, pd.DataFrame)
    hdbg.dassert_isinstance(df2, pd.DataFrame)
    # Check value of `assert_diff_threshold`, if it was passed.
    if assert_diff_threshold:
        hdbg.dassert_lte(assert_diff_threshold, 1.0)
        hdbg.dassert_lte(0.0, assert_diff_threshold)
    # TODO(gp): Factor out this logic and use it for both compare_visually_dfs
    #  and
    if row_mode == "equal":
        hpandass.dassert_indices_equal(df1, df2)
    elif row_mode == "inner":
        # TODO(gp): Add sorting on demand, otherwise keep the columns in order.
        same_rows = list((set(df1.index)).intersection(set(df2.index)))
        df1 = df1[df1.index.isin(same_rows)]
        df2 = df2[df2.index.isin(same_rows)]
    else:
        raise ValueError(f"Invalid row_mode='{row_mode}'")
    #
    if column_mode == "equal":
        hdbg.dassert_eq(sorted(df1.columns), sorted(df2.columns))
    elif column_mode == "inner":
        # TODO(gp): Add sorting on demand, otherwise keep the columns in order.
        col_names = sorted(list(set(df1.columns).intersection(set(df2.columns))))
        df1 = df1[col_names]
        df2 = df2[col_names]
    else:
        raise ValueError(f"Invalid column_mode='{column_mode}'")
    # Round small numbers to 0 to exclude them from the diff computation.
    close_to_zero_threshold_mask = lambda x: abs(x) < close_to_zero_threshold
    df1[close_to_zero_threshold_mask] = df1[close_to_zero_threshold_mask].round(0)
    df2[close_to_zero_threshold_mask] = df2[close_to_zero_threshold_mask].round(0)
    # Compute the difference df.
    if diff_mode == "diff":
        # Test and convert the assertion into a boolean.
        is_ok = True
        try:
            pd.testing.assert_frame_equal(
                df1, df2, check_like=True, check_dtype=False
            )
        except AssertionError as e:
            is_ok = False
            _ = e
        # Check `is_ok` and raise an assertion depending on `only_warning`.
        if not is_ok:
            hdbg._dfatal(
                _,
                "df1=\n%s\n and df2=\n%s\n are not equal.",
                hpanutil.df_to_str(df1, log_level=log_level),
                hpanutil.df_to_str(df2, log_level=log_level),
                only_warning=only_warning,
            )
        # Calculate the difference.
        df_diff = df1 - df2
        if remove_inf:
            df_diff = df_diff.replace([np.inf, -np.inf], np.nan)
    elif diff_mode == "pct_change":
        # Compare NaN values in dataframes.
        nan_diff_df = compare_nans_in_dataframes(df1, df2)
        _LOG.debug(
            "Dataframe with NaN differences=\n%s",
            hpanutil.df_to_str(nan_diff_df),
        )
        msg = "There are NaN values in one of the dataframes that are not in the other one."
        hdbg.dassert_eq(
            0, nan_diff_df.shape[0], msg=msg, only_warning=only_warning
        )
        # Compute pct_change.
        df_diff = 100 * (df1 - df2) / df2.abs()
        if zero_vs_zero_is_zero:
            # When comparing 0 to 0 set the diff (which is NaN by default) to 0.
            df1_mask = df1 == 0
            df2_mask = df2 == 0
            zero_vs_zero_mask = df1_mask & df2_mask
            df_diff[zero_vs_zero_mask] = 0
        if remove_inf:
            df_diff = df_diff.replace([np.inf, -np.inf], np.nan)
        # Check if `df_diff` values are less than `assert_diff_threshold`.
        if assert_diff_threshold is not None:
            nan_mask = df_diff.isna()
            within_threshold = (df_diff.abs() <= assert_diff_threshold) | nan_mask
            expected = pd.DataFrame(
                True,
                index=within_threshold.index,
                columns=within_threshold.columns,
            )
            # Test and convert the assertion into boolean.
            is_ok = True
            try:
                pd.testing.assert_frame_equal(
                    within_threshold, expected, check_exact=True
                )
            except AssertionError as e:
                is_ok = False
                _ = e
            # Check `is_ok` and raise assertion depending on `only_warning`.
            if not is_ok:
                hdbg._dfatal(
                    _,
                    "df1=\n%s\n and df2=\n%s\n have pct_change more than `assert_diff_threshold`.",
                    hpanutil.df_to_str(df1, log_level=log_level),
                    hpanutil.df_to_str(df2, log_level=log_level),
                    only_warning=only_warning,
                )
        # Report max diff.
        max_diff = df_diff.abs().max().max()
        _LOG.log(
            log_level,
            "Maximum percentage difference between the two dataframes = %s",
            max_diff,
        )
    else:
        raise ValueError(f"diff_mode={diff_mode}")
    df_diff = df_diff.add_suffix(f".{diff_mode}")
    return df_diff
