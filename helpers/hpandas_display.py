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

RowsValues = List[List[str]]


# TODO(gp): Maybe we can have a `_LOG_df_to_str(log_level, *args, **kwargs)` that
#  calls `_LOG.log(log_level, hpandas.df_to_str(*args, **kwargs, log_level=log_level))`.
# TODO(gp): We should make sure this works properly in a notebook, although
#  it's not easy to unit test.


def _display(log_level: int, df: pd.DataFrame) -> None:
    """
    Display a df in a notebook at the given log level.

    The behavior is similar to a command like `_LOG.log(log_level, ...)` but
    for a notebook `display` command.

    :param log_level: log level at which to display a df. E.g., if `log_level =
        logging.DEBUG`, then we display the df only if we are running with
        `-v DEBUG`. If `log_level = logging.INFO` then we don't display it
    """
    from IPython.display import display

    if (
        hsystem.is_running_in_ipynb()
        and log_level >= hdbg.get_logger_verbosity()
    ):
        display(df)


def _df_to_str(
    df: pd.DataFrame,
    num_rows: Optional[int],
    max_columns: int,
    max_colwidth: int,
    max_rows: int,
    precision: int,
    display_width: int,
    use_tabulate: bool,
    log_level: int,
) -> str:
    is_in_ipynb = hsystem.is_running_in_ipynb()
    out = []
    # Set dataframe print options.
    with pd.option_context(
        "display.max_colwidth",
        max_colwidth,
        # "display.height", 1000,
        "display.max_rows",
        max_rows,
        "display.precision",
        precision,
        "display.max_columns",
        max_columns,
        "display.width",
        display_width,
    ):
        if use_tabulate:
            import tabulate

            out.append(tabulate.tabulate(df, headers="keys", tablefmt="psql"))
        # TODO(Grisha): Add an option to display all rows since if `num_rows`
        # is `None`, only first and last 5 rows are displayed. Consider using
        # `df.to_string()` instead of `str(df)`.
        if num_rows is None or df.shape[0] <= num_rows:
            # Print the entire data frame.
            if not is_in_ipynb:
                out.append(str(df))
            else:
                # Display dataframe.
                _display(log_level, df)
        else:
            nr = num_rows // 2
            if not is_in_ipynb:
                # Print top and bottom of df.
                out.append(str(df.head(nr)))
                out.append("...")
                tail_str = str(df.tail(nr))
                # Remove index and columns from tail_df.
                skipped_rows = 1
                if df.index.name:
                    skipped_rows += 1
                tail_str = "\n".join(tail_str.split("\n")[skipped_rows:])
                out.append(tail_str)
            else:
                # TODO(gp): @all use this approach also above and update all the
                #  unit tests.
                df = [
                    df.head(nr),
                    pd.DataFrame(
                        [["..."] * df.shape[1]], index=[" "], columns=df.columns
                    ),
                    df.tail(nr),
                ]
                df = pd.concat(df)
                # Display dataframe.
                _display(log_level, df)
    if not is_in_ipynb:
        txt = "\n".join(out)
    else:
        txt = ""
    return txt


# #############################################################################
# Functions
# #############################################################################


def df_to_str(
    df: Union[pd.DataFrame, pd.Series, pd.Index],
    *,
    # TODO(gp): Remove this hack in the integration.
    # handle_signed_zeros: bool = False,
    handle_signed_zeros: bool = True,
    num_rows: Optional[int] = 6,
    print_dtypes: bool = False,
    print_shape_info: bool = False,
    print_nan_info: bool = False,
    print_memory_usage: bool = False,
    memory_usage_mode: str = "human_readable",
    tag: Optional[str] = None,
    max_columns: int = 10000,
    max_colwidth: int = 2000,
    max_rows: int = 500,
    precision: int = 6,
    display_width: int = 10000,
    use_tabulate: bool = False,
    log_level: int = logging.DEBUG,
) -> str:
    """
    Print a dataframe to string reporting all the columns without trimming.

    Note that code like: `_LOG.info(hpandas.df_to_str(df, num_rows=3))` works
    properly when called from outside a notebook, i.e., the dataframe is printed
    But it won't display the dataframe in a notebook, since the default level at
    which the dataframe is displayed is `logging.DEBUG`.

    In this case to get the correct behavior one should do:

    ```
    log_level = ...
    _LOG.log(log_level, hpandas.df_to_str(df, num_rows=3, log_level=log_level))
    ```

    :param: handle_signed_zeros: convert `-0.0` to `0.0`
    :param: num_rows: max number of rows to print (half from the top and half from
        the bottom of the dataframe)
        - `None` to print the entire dataframe
    :param print_dtypes: report dataframe types and information about the type of
        each column by looking at the first value
    :param print_shape_info: report dataframe shape, index and columns
    :param print_memory_usage: report memory use for each
    """
    if df is None:
        return ""
    if isinstance(df, pd.Series):
        df = pd.DataFrame(df)
    elif isinstance(df, pd.Index):
        df = df.to_frame(index=False)
    hdbg.dassert_isinstance(df, pd.DataFrame)
    # For some reason there are so-called "negative zeros", but we consider
    # them equal to `0.0`.
    df = df.copy()
    if handle_signed_zeros:
        for col_name in df.select_dtypes(include=[np.float64, float]).columns:
            df[col_name] = df[col_name].where(df[col_name] != -0.0, 0.0)
    out = []
    # Print the tag.
    if tag is not None:
        out.append(f"# {tag}=")
    if not df.empty:
        # Print information about the shape and index.
        # TODO(Nikola): Revisit and rename print_shape_info to print_axes_info
        if print_shape_info:
            # TODO(gp): Unfortunately we can't improve this part of the output
            # since there are many golden inside the code that would need to be
            # updated. Consider automating updating the expected values in the code.
            txt = f"index=[{df.index.min()}, {df.index.max()}]"
            out.append(txt)
            txt = f"columns={','.join(map(str, df.columns))}"
            out.append(txt)
            txt = f"shape={str(df.shape)}"
            out.append(txt)
        # Print information about the types.
        if print_dtypes:
            out.append("* type=")

            table = []

            def _report_srs_stats(srs: pd.Series) -> List[Any]:
                """
                Report dtype, the first element, and its type of series.
                """
                row: List[Any] = []
                first_elem = srs.values[0]
                num_unique = srs.nunique()
                num_nans = srs.isna().sum()
                row.extend(
                    [
                        srs.dtype,
                        hprint.perc(num_unique, len(srs)),
                        hprint.perc(num_nans, len(srs)),
                        first_elem,
                        type(first_elem),
                    ]
                )
                return row

            row = []
            col_name = "index"
            row.append(col_name)
            row.extend(_report_srs_stats(df.index))
            row = map(str, row)
            table.append(row)
            for col_name in df.columns:
                row_: List[Any] = []
                row_.append(col_name)
                row_.extend(_report_srs_stats(df[col_name]))
                row_ = map(str, row_)
                table.append(row_)
            #
            columns = [
                "col_name",
                "dtype",
                "num_unique",
                "num_nans",
                "first_elem",
                "type(first_elem)",
            ]
            df_stats = pd.DataFrame(table, columns=columns)
            stats_num_rows = None
            df_stats_as_str = _df_to_str(
                df_stats,
                stats_num_rows,
                max_columns,
                max_colwidth,
                max_rows,
                precision,
                display_width,
                use_tabulate,
                log_level,
            )
            out.append(df_stats_as_str)
        # Print info about memory usage.
        if print_memory_usage:
            out.append("* memory=")
            mem_use_df = pd.concat(
                [df.memory_usage(deep=False), df.memory_usage(deep=True)],
                axis=1,
                keys=["shallow", "deep"],
            )
            # Add total row.
            mem_use_df_total = pd.DataFrame({"total": mem_use_df.sum(axis=0)})
            mem_use_df = pd.concat([mem_use_df, mem_use_df_total.T])
            # Convert into the desired format.
            if memory_usage_mode == "bytes":
                pass
            elif memory_usage_mode == "human_readable":
                import helpers.hintrospection as hintros

                mem_use_df = mem_use_df.applymap(hintros.format_size)
            else:
                raise ValueError(
                    f"Invalid memory_usage_mode='{memory_usage_mode}'"
                )
            memory_num_rows = None
            memory_usage_as_txt = _df_to_str(
                mem_use_df,
                memory_num_rows,
                max_columns,
                max_colwidth,
                max_rows,
                precision,
                display_width,
                use_tabulate,
                log_level,
            )
            out.append(memory_usage_as_txt)
        # Print info about nans.
        if print_nan_info:
            num_elems = df.shape[0] * df.shape[1]
            num_nans = df.isna().sum().sum()
            txt = f"num_nans={hprint.perc(num_nans, num_elems)}"
            out.append(txt)
            #
            num_zeros = df.isnull().sum().sum()
            txt = f"num_zeros={hprint.perc(num_zeros, num_elems)}"
            out.append(txt)
            # TODO(gp): np can't do isinf on objects like strings.
            # num_infinite = np.isinf(df).sum().sum()
            # txt = "num_infinite=" + hprint.perc(num_infinite, num_elems)
            # out.append(txt)
            #
            num_nan_rows = df.dropna().shape[0]
            txt = f"num_nan_rows={hprint.perc(num_nan_rows, num_elems)}"
            out.append(txt)
            #
            num_nan_cols = df.dropna(axis=1).shape[1]
            txt = f"num_nan_cols={hprint.perc(num_nan_cols, num_elems)}"
            out.append(txt)
    if hsystem.is_running_in_ipynb():
        if len(out) > 0 and log_level >= hdbg.get_logger_verbosity():
            print("\n".join(out))
        txt = None
    # Print the df.
    df_as_str = _df_to_str(
        df,
        num_rows,
        max_columns,
        max_colwidth,
        max_rows,
        precision,
        display_width,
        use_tabulate,
        log_level,
    )
    if not hsystem.is_running_in_ipynb():
        out.append(df_as_str)
        txt = "\n".join(out)
    return txt


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
