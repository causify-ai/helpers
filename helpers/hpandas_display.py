"""
Import as:

import helpers.hpandas as hpandas
"""

import logging
import helpers.hlogging as hlogging
from typing import Any, List, Optional, Union

import numpy as np
import pandas as pd


import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hsystem as hsystem


_LOG = hlogging.getLogger(__name__)


def get_df_signature(df: pd.DataFrame, num_rows: int = 6) -> str:
    """
    Compute a simple signature of a dataframe in string format.

    The signature contains metadata about dataframe size and certain
    amount of rows from start and end of a dataframe. It is used for
    testing purposes.
    """
    hdbg.dassert_isinstance(df, pd.DataFrame)
    text: List[str] = [f"df.shape={str(df.shape)}"]
    with pd.option_context(
        "display.max_colwidth", int(1e6), "display.max_columns", None
    ):
        # If dataframe size exceeds number of rows, show only subset in form of
        # first and last rows. Otherwise, whole dataframe is shown.
        if len(df) > num_rows:
            text.append(f"df.head=\n{df.head(num_rows // 2)}")
            text.append(f"df.tail=\n{df.tail(num_rows // 2)}")
        else:
            text.append(f"df.full=\n{df}")
    text: str = "\n".join(text)
    return text


# #############################################################################


def convert_df_to_json_string(
    df: pd.DataFrame,
    n_head: Optional[int] = 10,
    n_tail: Optional[int] = 10,
    columns_order: Optional[List[str]] = None,
) -> str:
    """
    Convert dataframe to pretty-printed JSON string.

    To select all rows of the dataframe, pass `n_head` as None.

    :param df: dataframe to convert
    :param n_head: number of printed top rows
    :param n_tail: number of printed bottom rows
    :param columns_order: order for the KG columns sort
    :return: dataframe converted to JSON string
    """
    # Append shape of the initial dataframe.
    shape = f"original shape={df.shape}"
    # Reorder columns.
    if columns_order is not None:
        hdbg.dassert_set_eq(columns_order, df.cols)
        df = df[columns_order]
    # Select head.
    if n_head is not None:
        head_df = df.head(n_head)
    else:
        # If no n_head provided, append entire dataframe.
        head_df = df
    # Transform head to json.
    head_json = head_df.to_json(
        orient="index",
        force_ascii=False,
        indent=4,
        default_handler=str,
        date_format="iso",
        date_unit="s",
    )
    if n_tail is not None:
        # Transform tail to json.
        tail = df.tail(n_tail)
        tail_json = tail.to_json(
            orient="index",
            force_ascii=False,
            indent=4,
            default_handler=str,
            date_format="iso",
            date_unit="s",
        )
    else:
        # If no tail specified, append an empty string.
        tail_json = ""
    # Join shape and dataframe to single string.
    output_str = "\n".join([shape, "Head:", head_json, "Tail:", tail_json])
    return output_str


def list_to_str(
    vals: List[Any],
    *,
    sep_char: str = ", ",
    enclose_str_char: str = "'",
    max_num: Optional[int] = 10,
) -> str:
    """
    Convert a list of values into a formatted string representation.

    E.g., [1, "two", 3, 4, 5] -> "5 ['1', 'two', '3', '4', '5']"

    :param vals: values to be converted
    :param sep_char: separator to use between elements
    :param enclose_str_char: character to enclose each element's string
        representation; if empty, elements are not enclosed
    :param max_num: maximum number of elements to display in the output
    :return: the formatted string representing the list
    """
    vals_as_str = list(map(str, vals))
    # Add a str around.
    if enclose_str_char:
        vals_as_str = [
            enclose_str_char + v + enclose_str_char for v in vals_as_str
        ]
    #
    ret = f"{len(vals)} ["
    if max_num is not None and len(vals) > max_num:
        hdbg.dassert_lt(1, max_num)
        ret += sep_char.join(vals_as_str[: int(max_num / 2)])
        ret += sep_char + "..." + sep_char
        ret += sep_char.join(vals_as_str[-int(max_num / 2) :])
    else:
        ret += sep_char.join(vals_as_str)
    ret += "]"
    return ret
