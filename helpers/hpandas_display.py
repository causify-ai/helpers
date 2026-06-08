"""
Import as:

import helpers.hpandas_display as hpandisp
"""

import logging
import os
from typing import List, Optional

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hlist as hlist
import helpers.hlogging as hloggin
import helpers.hsystem as hsystem

_LOG = hloggin.getLogger(__name__)


# Invariant:
# - When we are in a notebook we want to:
#   - Convert `_LOG.info()` in `print()` using `hnotebo.set_logger_to_print()`
#   - Display any dataframe using the `hpandas.display` function
#   - Do not return any value
#
# - When we are not in a notebook we want to:
#   - Use `_LOG.info()` and `_LOG.debug()` to log messages
#   - Print the dataframe with `_LOG.debug()`
#   - Return the result through a `return` statement
#
# - Each function should have a `log_level` parameter to control the logging level.
#   - If `log_level` is not provided, it should be set to `logging.DEBUG` if we are not in a notebook,
#     and `logging.INFO` if we are in a notebook.


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
        hdbg.dassert_set_eq(columns_order, df.columns)
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


# #############################################################################


def convert_df_to_png(
    df: pd.DataFrame,
    file_path: str,
    index: bool = True,
    table_conversion: str = "kaleido",
    dpi: int = 300,
    print_markdown: bool = False,
    markdown_path_prefix: Optional[str] = None,
) -> None:
    """
    Convert a dataframe to a PNG image file.

    Uses the dataframe_image library to render the DataFrame as an image
    with HTML styling.

    :param df: dataframe to convert
    :param file_path: path where the PNG image will be saved
    :param index: whether to include the index in the image
    :param table_conversion: conversion method ('kaleido', 'chrome', or 'playwright')
    :param dpi: resolution in dots per inch (default: 300 for print quality,
        higher values = higher resolution and larger file size)
    :param print_markdown: if True, print markdown image reference like
        ![](path/to/image.png)
    :param markdown_path_prefix: optional path to prepend to the image path in
        the markdown reference (e.g., '../figures/' or 'assets/')
    """
    # Keep this import here since it's an optional one.
    import dataframe_image as dfi

    hdbg.dassert_isinstance(df, pd.DataFrame)
    hdbg.dassert_isinstance(file_path, str)
    # Ensure the output directory exists.
    hio.create_enclosing_dir(file_path, incremental=True)
    # Prepare dataframe for export, handling index parameter.
    export_df = df
    if not index:
        # Reset index to exclude it from the image.
        export_df = df.reset_index(drop=True)
    dfi.export(export_df, file_path, table_conversion=table_conversion, dpi=dpi)
    # Use print instead of _LOG.info.
    print(f"PNG image saved to: '{file_path}'")
    if print_markdown:
        # Construct the markdown path.
        markdown_path = file_path
        if markdown_path_prefix:
            markdown_path = os.path.join(markdown_path_prefix, file_path)
        markdown_ref = f"![]({markdown_path})"
        # Use print instead of _LOG.info.
        print(markdown_ref)


# #############################################################################


def print_or_display(
    df: pd.DataFrame,
    *,
    index: bool = True,
    as_txt: bool = False,
    log_level: int = logging.INFO,
) -> None:
    """
    Print or display a dataframe in a notebook at the given log level.

    :param df: dataframe to print
    :param index: whether to show the index or not
    :param as_txt: print if True, otherwise render as usual HTML table
    :param log_level: log level at which to print the dataframe
    """
    # print(_LOG.getEffectiveLevel())
    # print(log_level)
    # print(_LOG.isEnabledFor(log_level))
    if hsystem.is_running_in_ipynb() and not as_txt:
        from IPython.display import display, HTML

        if _LOG.isEnabledFor(log_level):
            display(HTML(df.to_html(index=index)))
    else:
        _LOG.log(log_level, "%s", df.to_string(index=index))


def display_df(
    df: pd.DataFrame,
    *,
    index: bool = True,
    inline_index: bool = False,
    max_lines: Optional[int] = 5,
    tag: Optional[str] = None,
    mode: Optional[str] = None,
    as_txt: bool = False,
    log_level: int = logging.INFO,
) -> None:
    """
    Display a Pandas object (series, df, panel) in a better way than the
    ipython display, e.g., by printing head and tail of the dataframe, and
    other formatting options.

    :param index: whether to show the index or not
    :param inline_index: make the index part of the dataframe. This is used
        when cutting and pasting to other applications, which are not happy
        with the output pandas HTML form
    :param max_lines: number of lines to print
    :param mode: use different formats temporarily overriding the default, e.g.,
        - "all_rows": print all the rows
        - "all_cols": print all the columns
        - "all": print the entire df (it could be huge)
    :param as_txt: print if True, otherwise render as usual html table
    :param log_level: log level at which to print the dataframe
    """
    # Convert Series to DataFrame if needed.
    if isinstance(df, pd.Series):
        df = pd.DataFrame(df)
    #
    hdbg.dassert_type_is(df, pd.DataFrame)
    hdbg.dassert_eq(
        hlist.find_duplicates(df.columns.tolist()),
        [],
        msg="Find duplicated columns",
    )
    if tag is not None:
        _LOG.log(log_level, "tag=%s", tag)
    # Shrink the dataframe to the number of lines specified by `max_lines`,
    # if needed.
    if max_lines is not None:
        hdbg.dassert_lte(1, max_lines)
        if df.shape[0] > max_lines:
            # log.error("Printing only top / bottom %s out of %s rows",
            #        max_lines, df.shape[0])
            ellipses = pd.DataFrame(
                [["..."] * len(df.columns)], columns=df.columns, index=["..."]
            )
            df = pd.concat(
                [
                    df.head(int(max_lines / 2)),
                    ellipses,
                    df.tail(int(max_lines / 2)),
                ],
                axis=0,
            )
    # Inline the index, if needed.
    if inline_index:
        df = df.copy()
        # Copy the index to a column and don't print the index.
        if df.index.name is None:
            col_name = "."
        else:
            col_name = df.index.name
        df.insert(0, col_name, df.index)
        df.index.name = None
        index = False
    # Print or display the dataframe.
    if mode is None:
        print_or_display(df, index=index, as_txt=as_txt, log_level=log_level)
    elif mode == "all_rows":
        with pd.option_context(
            "display.max_rows", None, "display.max_columns", 3
        ):
            print_or_display(df, index=index, as_txt=as_txt, log_level=log_level)
    elif mode == "all_cols":
        with pd.option_context(
            "display.max_colwidth", int(1e6), "display.max_columns", None
        ):
            print_or_display(df, index=index, as_txt=as_txt, log_level=log_level)
    elif mode == "all":
        with pd.option_context(
            "display.max_rows",
            int(1e6),
            "display.max_columns",
            3,
            "display.max_colwidth",
            int(1e6),
            "display.max_columns",
            None,
        ):
            print_or_display(df, index=index, as_txt=as_txt, log_level=log_level)
    else:
        print_or_display(df, index=index, as_txt=as_txt, log_level=log_level)
        raise ValueError("Invalid mode=%s" % mode)
