"""
Import as:

import helpers.hpandas_display as hpandisp
"""

from typing import List, Optional

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hlist as hlist
import helpers.hlogging as hloggin

_LOG = hloggin.getLogger(__name__)


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


# #############################################################################


def display_df(
    df: pd.DataFrame,
    index: bool = True,
    inline_index: bool = False,
    max_lines: int = 5,
    as_txt: bool = False,
    tag: Optional[str] = None,
    mode: Optional[str] = None,
) -> None:
    """
    Display a pandas object (series, df, panel) in a better way than the
    ipython display, e.g.,

        - by printing head and tail of the dataframe
        - by formatting the code

    :param index: whether to show the index or not
    :param inline_index: make the index part of the dataframe. This is used
        when cutting and pasting to other applications, which are not happy
        with the output pandas html form
    :param max_lines: number of lines to print
    :param as_txt: print if True, otherwise render as usual html
    :param mode: use different formats temporarily overriding the default, e.g.,
        - "all_rows": print all the rows
        - "all_cols": print all the columns
        - "all": print the entire df (it could be huge)
    """
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
        print(tag)
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

    # Finally, print / display.
    def _print_display() -> None:
        if as_txt:
            print(df.to_string(index=index))
        else:
            import IPython.core.display

            IPython.core.display.display(
                IPython.core.display.HTML(df.to_html(index=index))
            )

    if mode is None:
        _print_display()
    elif mode == "all_rows":
        with pd.option_context(
            "display.max_rows", None, "display.max_columns", 3
        ):
            _print_display()
    elif mode == "all_cols":
        with pd.option_context(
            "display.max_colwidth", int(1e6), "display.max_columns", None
        ):
            _print_display()
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
            _print_display()
    else:
        _print_display()
        raise ValueError("Invalid mode=%s" % mode)
