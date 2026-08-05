import logging
import re
from typing import List

import helpers.hprint as hprint
import helpers.htable as htable
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)



def _get_table() -> htable.Table:
    """
    Build a small `htable.Table` fixture for testing.

    :return: table with `status`, `outcome`, `descr`, `workflow` columns
    """
    # Prepare inputs.
    txt = """
    completed failure Lint Run_linter
    completed success Lint Fast_tests
    completed success Lint Slow_tests
    """
    txt = hprint.dedent(txt)
    cols = ["status", "outcome", "descr", "workflow"]
    # table = [line for line in csv.reader(txt.split("\n"), delimiter=' ')]
    # _LOG.debug(hprint.to_str("table"))
    # _LOG.debug("size=%s", str(htable.size(table)))
    table = htable.Table.from_text(cols, txt, delimiter=" ")
    return table


# #############################################################################
# Test_from_text
# #############################################################################


class Test_from_text(hunitest.TestCase):
    """
    Test `htable.Table.from_text()`.
    """

    def helper(self, cols: List[str], txt: str, expected: str) -> None:
        """
        Check that a malformed `txt` raises `AssertionError`.

        :param cols: column names to build the table with
        :param txt: CSV body to parse
        :param expected: expected assertion error message
        """
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            htable.Table.from_text(cols, txt, delimiter=" ")
        # Check outputs.
        actual = str(cm.exception)
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test building a table from valid input text.
        """
        # Run test.
        table = _get_table()
        # Check outputs.
        self.assertIsInstance(table, htable.Table)
        _LOG.debug(hprint.to_str("table"))

    def test2(self) -> None:
        """
        Test that a row with fewer fields than columns raises.
        """
        # Prepare inputs.
        txt = """
        completed failure Lint Run_linter
        completed success Lint
        completed success Lint Slow_tests
        """
        txt = hprint.dedent(txt)
        cols = ["status", "outcome", "descr", "workflow"]
        # Prepare outputs.
        expected = """
        * Failed assertion *
        '3'
        ==
        '4'
        Invalid row='['completed', 'success', 'Lint']' for cols='['status', 'outcome', 'descr', 'workflow']'
        """
        # Run test.
        self.helper(cols, txt, expected)

    def test3(self) -> None:
        """
        Test that a column list longer than the row width raises.
        """
        # Prepare inputs.
        txt = """
        completed failure Lint Run_linter
        completed success Lint Fast_tess
        completed success Lint Slow_tests
        """
        txt = hprint.dedent(txt)
        cols = ["status", "outcome", "descr", "workflow", "EXTRA"]
        # Prepare outputs.
        expected = """
        * Failed assertion *
        '4'
        ==
        '5'
        Invalid row='['completed', 'failure', 'Lint', 'Run_linter']' for cols='['status', 'outcome', 'descr', 'workflow', 'EXTRA']'
        """
        # Run test.
        self.helper(cols, txt, expected)


# #############################################################################
# Test_repr
# #############################################################################


class Test_repr(hunitest.TestCase):
    """
    Test `htable.Table.__repr__()`.
    """

    def test1(self) -> None:
        """
        Test the string representation of a table.
        """
        # Prepare inputs.
        table = _get_table()
        # Prepare outputs.
        expected = r"""
        cols=['status', 'outcome', 'descr', 'workflow']
        table=
        ['completed', 'failure', 'Lint', 'Run_linter']
        ['completed', 'success', 'Lint', 'Fast_tests']
        ['completed', 'success', 'Lint', 'Slow_tests']
        size=(3, 4)
        """
        # Run test.
        actual = repr(table)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_str
# #############################################################################


class Test_str(hunitest.TestCase):
    """
    Test `htable.Table.__str__()`.
    """

    def test1(self) -> None:
        """
        Test formatting a table with aligned columns.
        """
        # Prepare inputs.
        table = _get_table()
        # Prepare outputs.
        expected = r"""
        status    | outcome | descr | workflow   |
        --------- | ------- | ----- | ---------- |
        completed | failure | Lint  | Run_linter |
        completed | success | Lint  | Fast_tests |
        completed | success | Lint  | Slow_tests |
        """
        # Run test.
        actual = str(table)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test that cells colored with `hprint.color_highlight()` do not throw
        off the column alignment (the invisible ANSI escape bytes should not
        count towards the column width).
        """
        # Prepare inputs.
        table_data = [
            ["docker", hprint.color_highlight("NOT STARTED", "white"), "0"],
            ["apple", hprint.color_highlight("PASS", "green"), "3754"],
        ]
        table = htable.Table(table_data, ["Build", "Status", "Passed"])
        # Prepare outputs.
        expected = r"""
        Build  | Status      | Passed |
        ------ | ----------- | ------ |
        docker | NOT STARTED | 0      |
        apple  | PASS        | 3754   |
        """
        # Run test.
        actual = str(table)
        # Strip ANSI escape codes before comparing, since the color codes
        # themselves are environment-specific (see `_visible_len()`).
        actual = re.sub(r"\x1b\[[0-9;]*m", "", actual)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_filter_rows
# #############################################################################


class Test_filter_rows(hunitest.TestCase):
    """
    Test `htable.Table.filter_rows()`.
    """

    def test1(self) -> None:
        """
        Filter resulting in a single matching row.
        """
        # Prepare inputs.
        table = _get_table()
        # Prepare outputs.
        expected = r"""
        cols=['status', 'outcome', 'descr', 'workflow']
        table=
        ['completed', 'failure', 'Lint', 'Run_linter']
        size=(1, 4)
        """
        # Run test.
        table_filter = table.filter_rows("outcome", "failure")
        actual = repr(table_filter)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Filter resulting in no matches.
        """
        # Prepare inputs.
        table = _get_table()
        # Prepare outputs.
        expected = r"""
        cols=['status', 'outcome', 'descr', 'workflow']
        table=

        size=(0, 4)
        """
        # Run test.
        table_filter = table.filter_rows("status", "in progress")
        actual = repr(table_filter)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Filter with a column constant using the constant value.
        """
        # Prepare inputs.
        table = _get_table()
        # Run test.
        table_filter = table.filter_rows("descr", "Lint")
        actual = repr(table_filter)
        expected = repr(table)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_unique
# #############################################################################


class Test_unique(hunitest.TestCase):
    """
    Test `htable.Table.unique()`.
    """

    def test1(self) -> None:
        """
        Test unique values for a column with a single unique value.
        """
        # Prepare inputs.
        table = _get_table()
        # Prepare outputs.
        expected = ["Lint"]
        # Run test.
        actual = table.unique("descr")
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test unique values for a column with multiple unique values.
        """
        # Prepare inputs.
        table = _get_table()
        # Prepare outputs.
        expected = ["Fast_tests", "Run_linter", "Slow_tests"]
        # Run test.
        actual = table.unique("workflow")
        # Check outputs.
        self.assert_equal(str(actual), str(expected))
