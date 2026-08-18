"""
Import as:

import helpers.htable as htable
"""

import copy
import csv
import logging
from typing import Any, List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


TableType = List[List[str]]


# #############################################################################
# Table
# #############################################################################


class Table:
    """
    A simple (rectangular) table without introducing a dependency from Pandas.

    The element in the table can be anything.
    """

    @staticmethod
    def _check_table(table: TableType, column_names: List[str]) -> None:
        """
        Check that the table is well-formed (e.g., the list of lists is
        rectangular).
        """
        hdbg.dassert_isinstance(table, list)
        hdbg.dassert_isinstance(column_names, list)
        hdbg.dassert_no_duplicates(column_names)
        # Columns have no leading or trailing spaces.
        for column_name in column_names:
            hdbg.dassert_eq(column_name, column_name.rstrip().lstrip())
        # Check that the list of lists is rectangular.
        for row in table:
            hdbg.dassert_isinstance(table, list)
            hdbg.dassert_eq(
                len(row),
                len(column_names),
                "Invalid row='%s' for cols='%s'",
                row,
                column_names,
            )

    def __repr__(self) -> str:
        res = ""
        res += f"cols={str(self._column_names)}"
        res += "\ntable=\n" + "\n".join(map(str, self._table))
        res += "\n" + f"size={str(self.size())}"
        return res

    def __init__(self, table: TableType, column_names: List[str]) -> None:
        # Check that the inputs are well-formed.
        self._check_table(table, column_names)
        # Save state.
        self._table = table
        self._column_names = column_names
        _LOG.debug("%s", self.__repr__())
        # Map a column name to the index of the corresponding column, to allow
        # indexing by column.
        self._col_to_idx = {
            col: idx for idx, col in enumerate(self._column_names)
        }
        _LOG.debug("col_to_idx=%s", str(self._col_to_idx))

    @classmethod
    def from_text(cls, cols: List[str], txt: str, delimiter: str) -> "Table":
        """
        Build a table from a list of columns and the body of a CSV file.
        """
        hdbg.dassert_isinstance(txt, str)
        table = list(csv.reader(txt.split("\n"), delimiter=delimiter))
        return cls(table, cols)

    def size(self) -> Tuple[int, int]:
        """
        Return the size of the table.

        :return: number of rows x columns (i.e., numpy / Pandas convention)
        """
        return len(self._table), len(self._column_names)

    def filter_rows(self, column_name: str, value: str) -> "Table":
        """
        Return a Table filtered with rows filtered by the criteria "field ==
        value".
        """
        _LOG.debug("self=\n%s", repr(self))
        # Filter the rows.
        hdbg.dassert_in(column_name, self._col_to_idx.keys())
        rows_filter = [
            row
            for row in self._table
            if row[self._col_to_idx[column_name]] == value
        ]
        _LOG.debug(hprint.to_str("rows_filter"))
        # Build the resulting table.
        table_filter = Table(rows_filter, self._column_names)
        _LOG.debug("table_filter=\n%s", repr(table_filter))
        return table_filter

    def get_column(self, column_name: str) -> List[Any]:
        """
        Return the list of unique values for a row / field.
        """
        hdbg.dassert_in(column_name, self._column_names)
        column_idx = self._col_to_idx[column_name]
        # Scan the rows to extract the column.
        vals = []
        for row in self._table:
            vals.append(row[column_idx])
        return vals

    def unique(self, column_name: str) -> List[Any]:
        """
        Return a list of unique values for a field.
        """
        vals = self.get_column(column_name)
        vals = sorted(list(set(vals)))
        return vals

    def remove_column(self, column_name: str) -> "Table":
        """
        Return a new Table with the specified column removed.

        :param column_name: name of the column to remove
        :return: new Table without the specified column
        """
        hdbg.dassert_in(column_name, self._column_names)
        # Find the index of the column to remove.
        column_idx = self._col_to_idx[column_name]
        # Create new column names list without the removed column.
        new_column_names = [
            col for col in self._column_names if col != column_name
        ]
        # Create new table rows without the removed column.
        new_table = [
            [val for idx, val in enumerate(row) if idx != column_idx]
            for row in self._table
        ]
        # Build and return the new table.
        return Table(new_table, new_column_names)

    def __str__(self) -> str:
        """
        Return a string representing the table with columns aligned.
        """
        table = copy.deepcopy(self._table)
        table.insert(0, self._column_names)
        # Convert the cells to strings.
        table_as_str = [[str(cell) for cell in row] for row in table]

        def _visible_len(cell: str) -> int:
            """
            Compute the visible length of a cell, i.e., ignoring ANSI color codes
            (e.g., from `hprint.color_highlight()`).

            Using the raw `len()` would inflate the width of columns with
            colored cells (e.g., "Status") since escape codes count as
            characters but are not displayed, which misaligns the table when
            rendered.
            """
            return len(hprint.remove_non_printable_chars(cell))

        # Find the visible length of each column, looping over rows and
        # columns explicitly instead of transposing with `zip(*table_as_str)`.
        num_cols = len(self._column_names)
        lengths = [0] * num_cols
        for row in table_as_str:
            for col_idx, cell in enumerate(row):
                lengths[col_idx] = max(lengths[col_idx], _visible_len(cell))
        _LOG.debug(hprint.to_str("lengths"))
        # Add the row separating the column names.
        row_sep = ["-" * length for length in lengths]
        table_as_str.insert(1, row_sep)
        # Format rows, padding each cell to the column's visible length (rather
        # than relying on `str.format()`, which pads based on the raw, not
        # visible, length).
        rows_as_str = []
        for row in table_as_str:
            cells = []
            for cell, length in zip(row, lengths):
                padding = " " * (length - _visible_len(cell))
                cells.append(f"{cell}{padding} |")
            rows_as_str.append(" ".join(cells))
        # Remove trailing spaces.
        for idx, row_str in enumerate(rows_as_str):
            rows_as_str[idx] = row_str.rstrip()
        # Create string.
        res = "\n".join(rows_as_str)
        # res += "\nsize=" + str(self.size())
        return res


# #############################################################################


def csv_to_str(rows: TableType, *, max_rows: Optional[int] = None) -> str:
    """
    Render parsed CSV rows as an aligned table string.

    This is typically used to log a quick preview of a CSV file (e.g., the
    first 3 rows) right after it is read, written, or combined. The caller
    is responsible for reading the CSV file (or otherwise obtaining the
    rows), since this function only formats data it is given.

    :param rows: parsed CSV rows, including the header as the first row
    :param max_rows: max number of data rows to render (the header row is
        not counted); `None` renders all rows
    :return: table-formatted string, or a placeholder if there are no rows
    """
    if not rows:
        return "<empty CSV file>"
    column_names, data_rows = rows[0], rows[1:]
    if max_rows is not None:
        data_rows = data_rows[:max_rows]
    table = Table(data_rows, column_names)
    return str(table)
