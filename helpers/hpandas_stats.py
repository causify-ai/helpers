"""
Import as:

import helpers.hpandas_stats as hpanstat
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
import pandas as pd
import IPython.display

import helpers.hdatetime as hdateti
import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hpandas as hpandas
import helpers.hpandas_dassert as hpandass
import helpers.hpandas_transform as hpantran
import helpers.hprint as hprint

_LOG = hloggin.getLogger(__name__)


def compute_duration_df(
    tag_to_df: Dict[str, pd.DataFrame],
    *,
    intersect_dfs: bool = False,
    valid_intersect: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Compute a df with some statistics about the time index.

    E.g.,
    ```
                   min_index   max_index   min_valid_index   max_valid_index
    tag1
    tag2
    ```

    :param intersect_dfs: return a transformed dict with the intersection of
        indices of all the dfs if True, otherwise return the input data as is
    :param valid_intersect: intersect indices without NaNs if True, otherwise
        intersect indices as is
    :return: timestamp stats and updated dict of dfs, see `intersect_dfs` param
    """
    hdbg.dassert_isinstance(tag_to_df, Dict)
    # Create df and assign columns.
    data_stats = pd.DataFrame()
    min_col = "min_index"
    max_col = "max_index"
    min_valid_index_col = "min_valid_index"
    max_valid_index_col = "max_valid_index"
    # Collect timestamp info from all dfs.
    for tag in tag_to_df.keys():
        # Check that the passed timestamp has timezone info.
        hdateti.dassert_has_tz(tag_to_df[tag].index[0])
        hpandass.dassert_index_is_datetime(tag_to_df[tag])
        # Compute timestamp stats.
        data_stats.loc[tag, min_col] = tag_to_df[tag].index.min()
        data_stats.loc[tag, max_col] = tag_to_df[tag].index.max()
        data_stats.loc[tag, min_valid_index_col] = (
            tag_to_df[tag].dropna().index.min()
        )
        data_stats.loc[tag, max_valid_index_col] = (
            tag_to_df[tag].dropna().index.max()
        )
    # Make a copy so we do not modify the original data.
    tag_to_df_updated = tag_to_df.copy()
    # Change the initial dfs with intersection.
    if intersect_dfs:
        if valid_intersect:
            # Assign start, end date column according to specs.
            min_col = min_valid_index_col
            max_col = max_valid_index_col
        # The start of the intersection will be the max value amongt all start dates.
        intersection_start_date = data_stats[min_col].max()
        # The end of the intersection will be the min value amongt all end dates.
        intersection_end_date = data_stats[max_col].min()
        for tag in tag_to_df_updated.keys():
            df = hpantran.trim_df(
                tag_to_df_updated[tag],
                ts_col_name=None,
                start_ts=intersection_start_date,
                end_ts=intersection_end_date,
                left_close=True,
                right_close=True,
            )
            tag_to_df_updated[tag] = df
    return data_stats, tag_to_df_updated


# #############################################################################


# TODO(gp): Remove this since it's in Google API.


def compute_weighted_sum(
    dfs: Dict[str, pd.DataFrame],
    weights: pd.DataFrame,
    *,
    index_mode: str = "assert_equal",
) -> Dict[str, pd.DataFrame]:
    """
    Compute weighted sums of `dfs` using `weights`.

    :param dfs: dataframes keyed by id; all dfs should have the same cols,
        indices are handled based on the `index_mode`
    :param weights: float weights indexed by id with unique col names
    :param index_mode: same as `mode` in `apply_index_mode()`
    :return: weighted sums keyed by weight col names
    """
    hdbg.dassert_isinstance(dfs, dict)
    hdbg.dassert(dfs, "dictionary of dfs must be nonempty")
    # Get a dataframe from the dictionary and record its index and columns.
    id_ = list(dfs)[0]
    hdbg.dassert_isinstance(id_, str)
    df = dfs[id_]
    hdbg.dassert_isinstance(df, pd.DataFrame)
    cols = df.columns
    # Sanity-check dataframes in dictionary.
    for key, value in dfs.items():
        hdbg.dassert_isinstance(key, str)
        hdbg.dassert_isinstance(value, pd.DataFrame)
        # The reference df is not modified.
        _, value = hpantran.apply_index_mode(df, value, index_mode)
        hdbg.dassert(
            value.columns.equals(cols),
            "Column equality fails for keys=%s, %s",
            id_,
            key,
        )
    # Sanity-check weights.
    hdbg.dassert_isinstance(weights, pd.DataFrame)
    hdbg.dassert_eq(weights.columns.nlevels, 1)
    hdbg.dassert(not weights.columns.has_duplicates)
    hdbg.dassert_set_eq(weights.index.to_list(), list(dfs))
    # Create a multiindexed dataframe to facilitate computing the weighted sums.
    weighted_dfs = {}
    combined_df = pd.concat(dfs.values(), axis=1, keys=dfs.keys())
    # TODO(Paul): Consider relaxing the NaN-handling.
    for col in weights.columns:
        weighted_combined_df = combined_df.multiply(weights[col], level=0)
        weighted_sums = weighted_combined_df.groupby(axis=1, level=1).sum(
            min_count=len(dfs)
        )
        weighted_dfs[col] = weighted_sums
    return weighted_dfs


def remap_obj(
    obj: Union[pd.Series, pd.Index],
    map_: Dict[Any, Any],
    **kwargs: Any,
) -> pd.Series:
    """
    Substitute each value of an object with another value from a dictionary.

    :param obj: an object to substitute value in
    :param map_: values to substitute with
    :return: remapped pandas series
    """
    hdbg.dassert_lte(1, obj.shape[0])
    # TODO(Grisha): consider extending for other mapping types supported by
    #  `pd.Series.map`.
    hdbg.dassert_isinstance(map_, dict)
    # Check that every element of the object is in the mapping.
    hdbg.dassert_is_subset(obj, map_.keys())
    new_srs = obj.map(map_, **kwargs)
    return new_srs


def get_random_df(
    num_cols: int,
    seed: Optional[int] = None,
    date_range_kwargs: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Compute df with random data with `num_cols` columns and index obtained by
    calling `pd.date_range(**kwargs)`.

    :param num_cols: the number of columns in a DataFrame to generate
    :param seed: see `random.seed()`
    :param date_range_kwargs: kwargs for `pd.date_range()`
    """
    if seed:
        np.random.seed(seed)
    dt = pd.date_range(**date_range_kwargs)
    df = pd.DataFrame(np.random.rand(len(dt), num_cols), index=dt)
    return df


# #############################################################################


def heatmap_df(df: pd.DataFrame, *, axis: Any = None) -> pd.DataFrame:
    """
    Colorize a df with a heatmap depending on the numeric values.

    :param axis: along which axis to compute the heatmap
        - 0 colorize along rows
        - 1 colorize along columns
        - None: colorize everything
    """
    # Keep it here to avoid long start up times.
    import seaborn as sns

    cm = sns.diverging_palette(5, 250, as_cmap=True)
    df = df.style.background_gradient(axis=axis, cmap=cm)
    return df


def to_perc(vals: Union[List, pd.Series], **perc_kwargs: Dict[str, Any]) -> str:
    """
    Report percentage of True for a list / series.
    """
    if isinstance(vals, list):
        vals = pd.Series(vals)
    ret = hprint.perc(vals.sum(), len(vals), **perc_kwargs)
    return ret


def add_end_download_timestamp(
    obj: Union[pd.DataFrame, Dict], *, timezone: str = "UTC"
) -> Union[pd.DataFrame, Dict]:
    """
    Add a column 'end_download_timestamp' to the DataFrame with the current
    time.

    :param obj: The DataFrame to which the column will be added.
    :param timezone: The timezone for the current time. Defaults to
        'UTC'.
    """
    # Get current timestamp.
    current_ts = hdateti.get_current_time(timezone)
    # Set value of end_download_timestamp.
    obj["end_download_timestamp"] = current_ts
    return obj


def get_value_counts_stats_df(
    df: pd.DataFrame, col_name: str, *, num_rows: int = 10
) -> pd.DataFrame:
    """
    Get the value counts of `col_name` in `df`.

    :param df: The DataFrame to get the value counts of `col_name` from.
    :param col_name: The column name to get the value counts of.
    :param num_rows: The number of rows to return.
    :return: A DataFrame with the value counts of `col_name` in `df`. E.g.,
    ```
                                        count  pct [%]
    Venture Fund                        1004   25.100
    Financial Services                   274    6.850
    Venture Capital & Private Equity     176    4.400
    Computer Software                    163    4.075
    Higher Education                     133    3.325
    Information Technology & Services     73    1.825
    ```
    """
    hdbg.dassert_in(col_name, df.columns)
    stats_df = df[col_name].value_counts().to_frame()
    stats_df["pct [%]"] = stats_df["count"] / len(df) * 100
    if num_rows > 0:
        stats_df = stats_df.head(num_rows)
    return stats_df


def display_value_counts_stats_df(
    df: pd.DataFrame, col_names: Union[str, List[str]], *, num_rows: int = 10
) -> None:
    if isinstance(col_names, list):
        for col_name in col_names:
            display_value_counts_stats_df(df, col_name, num_rows=num_rows)
        return
    hdbg.dassert_isinstance(col_names, str)
    _LOG.info("# %s", col_names)
    stats_df = get_value_counts_stats_df(df, col_names, num_rows=num_rows)
    IPython.display.display(stats_df)


# #############################################################################
# Functions moved from core/explore.py
# #############################################################################


def report_zero_nan_inf_stats(
    df: pd.DataFrame,
    zero_threshold: float = 1e-9,
    verbose: bool = False,
    as_txt: bool = False,
) -> pd.DataFrame:
    """
    Report count and percentage about zeros, nans, infs for a df.
    """
    # Convert Series to DataFrame if needed.
    if isinstance(df, pd.Series):
        df = pd.DataFrame(df)
    _LOG.info("index in [%s, %s]", df.index.min(), df.index.max())
    #
    num_rows = df.shape[0]
    _LOG.info("num_rows=%s", hprint.thousand_separator(num_rows))
    _LOG.info("data=")
    hpandas.display_df(df, max_lines=5, as_txt=as_txt)
    #
    num_days = len(set(df.index.date))
    _LOG.info("num_days=%s", num_days)
    #
    num_weekdays = len(set(d for d in df.index.date if d.weekday() < 5))
    _LOG.info("num_weekdays=%s", num_weekdays)
    #
    stats_df = pd.DataFrame(None, index=df.columns)
    if False:
        # Find the index of the first non-nan value.
        df = df.applymap(lambda x: not np.isnan(x))
        min_idx = df.idxmax(axis=0)
        min_idx.name = "min_idx"
        # Find the index of the last non-nan value.
        max_idx = df.reindex(index=df.index[::-1]).idxmax(axis=0)
        max_idx.name = "max_idx"
    stats_df["num_rows"] = num_rows
    #
    num_zeros = (np.abs(df) < zero_threshold).sum(axis=0)
    if verbose:
        stats_df["num_zeros"] = num_zeros
    stats_df["zeros [%]"] = (100.0 * num_zeros / num_rows).apply(
        hprint.round_digits
    )
    #
    num_nans = np.isnan(df).sum(axis=0)
    if verbose:
        stats_df["num_nans"] = num_nans
    stats_df["nans [%]"] = (100.0 * num_nans / num_rows).apply(
        hprint.round_digits
    )
    #
    num_infs = np.isinf(df).sum(axis=0)
    if verbose:
        stats_df["num_infs"] = num_infs
    stats_df["infs [%]"] = (100.0 * num_infs / num_rows).apply(
        hprint.round_digits
    )
    #
    num_valid = df.shape[0] - num_zeros - num_nans - num_infs
    if verbose:
        stats_df["num_valid"] = num_valid
    stats_df["valid [%]"] = (100.0 * num_valid / num_rows).apply(
        hprint.round_digits
    )
    #
    hpandas.display_df(stats_df, as_txt=as_txt)
    return stats_df


def pvalue_to_stars(pval: Optional[float]) -> str:
    """
    Convert p-value to star notation for statistical significance.

    :param pval: p-value to convert
    :return: star notation (* to ****) or ? for non-significant, NA for NaN
    """
    if np.isnan(pval):
        stars = "NA"
    else:
        hdbg.dassert_lte(0.0, pval)
        hdbg.dassert_lte(pval, 1.0)
        pval = cast(float, pval)
        if pval < 0.005:
            # More than 99.5% confidence.
            stars = "****"
        elif pval < 0.01:
            # More than 99% confidence.
            stars = "***"
        elif pval < 0.05:
            # More than 95% confidence.
            stars = "**"
        elif pval < 0.1:
            # More than 90% confidence.
            stars = "*"
        else:
            stars = "?"
    return stars


def format_ols_regress_results(regr_res: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Format OLS regression results into a readable DataFrame.

    :param regr_res: regression results dictionary with coeffs, pvals, rsquared, etc.
    :return: formatted DataFrame with coefficients and statistics
    """
    if regr_res is None:
        _LOG.warning("regr_res=None: skipping")
        df = pd.DataFrame(None)
        return df
    row: List[Union[float, str]] = [
        "%.3f (%s)" % (coeff, pvalue_to_stars(pval))
        for (coeff, pval) in zip(regr_res["coeffs"], regr_res["pvals"])
    ]
    row.append(float("%.2f" % (regr_res["rsquared"] * 100.0)))
    row.append(float("%.2f" % (regr_res["adj_rsquared"] * 100.0)))
    col_names = regr_res["param_names"] + ["R^2 [%]", "Adj R^2 [%]"]
    df = pd.DataFrame([row], columns=col_names)
    return df


def describe_df(
    df: pd.DataFrame,
    ts_col: Optional[str] = None,
    max_col_width: int = 30,
    max_thr: int = 15,
    sort_by_uniq_num: bool = False,
    log_level: int = logging.INFO,
) -> None:
    """
    Improved version of pd.DataFrame.describe()

    :param ts_col: timestamp column
    """
    if ts_col is None:
        _LOG.log(
            log_level,
            "[%s, %s], count=%s",
            min(df.index),
            max(df.index),
            len(df.index.unique()),
        )
    else:
        _LOG.log(
            log_level,
            "%s: [%s, %s], count=%s",
            ts_col,
            min(df[ts_col]),
            max(df[ts_col]),
            len(df[ts_col].unique()),
        )
    _LOG.log(log_level, "num_cols=%s", df.shape[1])
    _LOG.log(log_level, "num_rows=%s", df.shape[0])
    res_df = []
    for c in df.columns:
        uniq = df[c].unique()
        num = len(uniq)
        if num < max_thr:
            vals = " ".join(map(str, uniq))
        else:
            vals = " ".join(map(str, uniq[:10]))
        if len(vals) > max_col_width:
            vals = vals[:max_col_width] + " ..."
        type_str = df[c].dtype
        res_df.append([c, len(uniq), vals, type_str])
    #
    res_df = pd.DataFrame(res_df, columns=["column", "num uniq", "vals", "type"])
    res_df.set_index("column", inplace=True)
    if sort_by_uniq_num:
        res_df.sort("num uniq", inplace=True)
    _LOG.log(log_level, "res_df=\n%s", res_df)
