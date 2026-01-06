"""
Import as:

import helpers.hpandas_utils as hpanutil
"""

import logging
from typing import Any, List, Optional, Tuple, Union, cast

import numpy as np
import pandas as pd
import tqdm.autonotebook as tauton

import helpers.hdbg as hdbg
import helpers.hlogging as hloggin
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = hloggin.getLogger(__name__)

# Import add_pct for use in this module.


# TODO(gp): -> AxisNameSet
ColumnSet = Optional[Union[str, List[str]]]


# #############################################################################


# TODO(gp): Maybe we can have a `_LOG_df_to_str(log_level, *args, **kwargs)` that
#  calls `_LOG.log(log_level, hpandas.df_to_str(*args, **kwargs, log_level=log_level))`.
# TODO(gp): We should make sure this works properly in a notebook, although
#  it's not easy to unit test.


def _display(log_level: int, df: pd.DataFrame) -> None:
    """
    Display a dataframe in a notebook at the given log level.

    The behavior is similar to a command like `_LOG.log(log_level, ...)` but
    for a notebook `display` command.

    :param log_level: log level at which to display a df. E.g., if `log_level =
        logging.DEBUG`, then we display the df only if we are running with
        `-v DEBUG`. If `log_level = logging.INFO` then we don't display it
    :param df: dataframe to display
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
    """
    Convert a DataFrame to a string representation.

    :param df: The DataFrame to convert to a string.
    :param num_rows: The number of rows to display.
    :param max_columns: The maximum number of columns to display.
    :param max_colwidth: The maximum width of each column.
    :param max_rows: The maximum number of rows to display.
    :param precision: The precision of the numbers.
    :param display_width: The width of the display.
    :param use_tabulate: Whether to use the tabulate library to format the DataFrame.
    :param log_level: The log level to use.
    :return: A string representation of the DataFrame.
    """
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


def _report_srs_stats(srs: pd.Series) -> List[Any]:
    """
    Report dtype, the first element, and its type of series.

    :param srs: The series to report the stats of.
    :return: A list of the stats.
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
    # Convert "negative zeros" to `0.0`.
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


# #############################################################################


def head(
    df: pd.DataFrame,
    *,
    print_columns: bool = False,
    num_rows: int = 2,
    seed: Union[int, None] = None,
) -> str:
    """
    Display a sample of rows from a DataFrame.

    By default shows the first `num_rows` rows. When a seed is provided,
    randomly samples `num_rows` rows instead.

    :param df: The DataFrame to sample from.
    :param num_rows: Number of rows to display.
    :param seed: Optional random seed for reproducible sampling. If None, shows
        first rows.
    """
    txt = ""
    if print_columns:
        txt += "columns=%s\n" % ",".join(df.columns.tolist())
    txt += "shape=%s\n" % str(df.shape)
    #
    if seed is not None:
        np.random.seed(seed)
        index = np.random.choice(df.index, num_rows, replace=False)
        index = sorted(index)
        df = df.loc[index]
    else:
        df = df.head(num_rows)
    with pd.option_context(
        "display.width",
        200,
        "display.max_columns",
        None,
        "display.max_colwidth",
        None,
    ):
        txt += "\n" + str(df)
    return txt


# #############################################################################


def resolve_column_names(
    column_set: ColumnSet,
    columns: Union[List[str], pd.Index],
    *,
    keep_order: bool = False,
) -> List[str]:
    """
    Change format of the columns and perform some sanity checks.

    :param column_set: columns to proceed
    :param columns: all columns available
    :param keep_order: preserve the original order or allow sorting
    """
    # Ensure that `columns` is well-formed.
    if isinstance(columns, pd.Index):
        columns = columns.to_list()
    hdbg.dassert_isinstance(columns, list)
    hdbg.dassert_lte(1, len(columns))
    #
    if column_set is None:
        # Columns were not specified, thus use the list of all the columns.
        column_set = columns
    else:
        if isinstance(column_set, str):
            column_set = [column_set]
        hdbg.dassert_isinstance(column_set, list)
        hdbg.dassert_lte(1, len(column_set))
        hdbg.dassert_is_subset(column_set, columns)
        if keep_order:
            # Keep the selected columns in the same order as in the original
            # `columns`.
            column_set = [c for c in columns if c in column_set]
    return column_set


def _get_unique_elements_in_column(df: pd.DataFrame, col_name: str) -> List[Any]:
    """
    Get unique elements in a column, handling unhashable types.

    :param df: dataframe containing the column
    :param col_name: name of the column to get unique elements from
    :return: list of unique elements
    """
    try:
        vals = df[col_name].unique()
    except TypeError:
        # TypeError: unhashable type: 'list'
        _LOG.error("Column '%s' has unhashable types", col_name)
        vals = list(set(map(str, df[col_name])))
    cast(List[Any], vals)
    return vals


def _get_variable_cols(
    df: pd.DataFrame, threshold: int = 1
) -> Tuple[List[str], List[str]]:
    """
    Return columns of a df that contain less than <threshold> unique values.

    :return: (variable columns, constant columns)
    """
    var_cols = []
    const_cols = []
    for col_name in df.columns:
        unique_elems = _get_unique_elements_in_column(df, col_name)
        num_unique_elems = len(unique_elems)
        if num_unique_elems <= threshold:
            const_cols.append(col_name)
        else:
            var_cols.append(col_name)
    return var_cols, const_cols


def remove_columns_with_low_variability(
    df: pd.DataFrame, threshold: int = 1, log_level: int = logging.DEBUG
) -> pd.DataFrame:
    """
    Remove columns of a df that contain less than <threshold> unique values.

    :return: df with only columns with sufficient variability
    """
    var_cols, const_cols = _get_variable_cols(df, threshold=threshold)
    _LOG.log(log_level, "# Constant cols")
    for col_name in const_cols:
        unique_elems = _get_unique_elements_in_column(df, col_name)
        _LOG.log(
            log_level,
            "  %s: %s",
            col_name,
            hprint.list_to_str(list(map(str, unique_elems))),
        )
    _LOG.log(log_level, "# Var cols")
    _LOG.log(log_level, hprint.list_to_str(var_cols))
    return df[var_cols]


def print_column_variability(
    df: pd.DataFrame,
    max_num_vals: int = 3,
    num_digits: int = 2,
    use_thousands_separator: bool = True,
) -> pd.DataFrame:
    """
    Print statistics about the values in each column of a data frame.

    This is useful to get a sense of which columns are interesting.
    """
    print(("# df.columns=%s" % hprint.list_to_str(df.columns)))
    res = []
    for c in tauton.tqdm(df.columns, desc="Computing column variability"):
        vals = _get_unique_elements_in_column(df, c)
        try:
            min_val = min(vals)
        except TypeError as e:
            _LOG.debug("Column='%s' reported %s", c, e)
            min_val = "nan"
        try:
            max_val = max(vals)
        except TypeError as e:
            _LOG.debug("Column='%s' reported %s", c, e)
            max_val = "nan"
        if len(vals) <= max_num_vals:
            txt = ", ".join(map(str, vals))
        else:
            txt = ", ".join(map(str, [min_val, "...", max_val]))
        row = ["%20s" % c, len(vals), txt]
        res.append(row)
    res = pd.DataFrame(res, columns=["col_name", "num", "elems"])
    res.sort_values("num", inplace=True)
    # TODO(gp): Fix this.
    # res = add_count_as_idx(res)
    # Import locally to avoid circular dependency.
    from helpers.hpandas_transform import add_pct as hpantran_add_pct

    res = hpantran_add_pct(
        res,
        "num",
        df.shape[0],
        "[diff %]",
        num_digits=num_digits,
        use_thousands_separator=use_thousands_separator,
    )
    res.reset_index(drop=True, inplace=True)
    return res


def breakdown_table(
    df: pd.DataFrame,
    col_name: str,
    num_digits: int = 2,
    use_thousands_separator: bool = True,
    verbosity: bool = False,
) -> pd.DataFrame:
    """
    Create a breakdown table showing value counts and percentages for a column.

    :param df: dataframe to analyze
    :param col_name: column name to create breakdown for
    :param num_digits: number of decimal digits for percentages
    :param use_thousands_separator: whether to use thousands separator in counts
    :param verbosity: whether to print additional details
    :return: breakdown table with counts and percentages
    """
    if isinstance(col_name, list):
        for c in col_name:
            print(("\n" + hprint.frame(c).rstrip("\n")))
            res = breakdown_table(df, c)
            print(res)
        return None
    #
    if verbosity:
        print(("# col_name=%s" % col_name))
    first_col_name = df.columns[0]
    res = df.groupby(col_name)[first_col_name].count()
    res = pd.DataFrame(res)
    res.columns = ["count"]
    res.sort_values(["count"], ascending=False, inplace=True)
    res = pd.concat(
        [res, pd.DataFrame([df.shape[0]], index=["Total"], columns=["count"])]
    )
    res["pct"] = (100.0 * res["count"]) / df.shape[0]
    # Format.
    res["count"] = [
        hprint.round_digits(
            v, num_digits=None, use_thousands_separator=use_thousands_separator
        )
        for v in res["count"]
    ]
    res["pct"] = [
        hprint.round_digits(
            v, num_digits=num_digits, use_thousands_separator=False
        )
        for v in res["pct"]
    ]
    if verbosity:
        for k, df_tmp in df.groupby(col_name):
            print((hprint.frame("%s=%s" % (col_name, k))))
            cols = [col_name, "description"]
            with pd.option_context(
                "display.max_colwidth", 100000, "display.width", 130
            ):
                print((df_tmp[cols]))
    return res
