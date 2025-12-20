"""
Import as:

import helpers.hpandas2 as hpandas2
"""

import logging
from typing import Any, Union

import numpy as np
import pandas as pd
from IPython.display import display

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


def impute_nans(df: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
    """
    Assign `value` to the `column` of `df` where the value is "nan".

    :param df: The DataFrame to modify.
    :param column: The column in which to replace "nan" values.
    :param value: The value to assign to "nan" entries.
    :return: The DataFrame with the "nan" values assigned.
    """
    df[column] = df[column].astype(str)
    mask = df[column] == "nan"
    # Assign the new value or keep the original value.
    df[column] = np.where(mask, value, df[column])
    # There should be no more nans.
    mask = df[column] == "nan"
    hdbg.dassert_eq(mask.sum(), 0)
    #
    return df


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


def head(
    df: pd.DataFrame, *, seed: Union[int, None] = None, num_rows: int = 2
) -> None:
    """
    Display a sample of rows from a DataFrame.

    By default shows the first `num_rows` rows. When a seed is provided,
    randomly samples `num_rows` rows instead.

    :param df: The DataFrame to sample from.
    :param seed: Optional random seed for reproducible sampling. If None, shows
        first rows.
    :param num_rows: Number of rows to display.
    """
    print("columns=", df.columns.tolist())
    print("shape=", df.shape)
    if seed is not None:
        np.random.seed(seed)
        index = np.random.choice(df.index, num_rows, replace=False)
        index = sorted(index)
        df = df.loc[index]
    else:
        df = df.head(num_rows)
    display(df)
