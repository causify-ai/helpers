"""
Import as:

import helpers.hpandas as hpandas
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

import helpers.hdatetime as hdateti
import helpers.hdbg as hdbg
import helpers.hlogging as hlogging
import helpers.hpandas_dassert as hpandas_dassert
import helpers.hprint as hprint

_LOG = hlogging.getLogger(__name__)


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
        hpandas_dassert.dassert_index_is_datetime(tag_to_df[tag])
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
            df = trim_df(
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
        _, value = apply_index_mode(df, value, index_mode)
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
