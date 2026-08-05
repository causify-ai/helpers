import logging
import re

import helpers.hprint as hprint
import helpers.htable as htable
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestTable1
# #############################################################################

# TODO(ai_gp): Rename the testing methods -> test1, test2, ...

# TODO(ai_gp): Use vars with """, with text aligned and dedent

# TODO(ai_gp): Split in multiple classes, each testing a single method
class TestTable1(hunitest.TestCase):

    # TODO(ai_gp): Factor out a helper with an assert_equal inside

    @staticmethod
    def _get_table() -> htable.Table:
        txt = """completed failure Lint Run_linter
completed success Lint Fast_tests
completed success Lint Slow_tests"""
        cols = ["status", "outcome", "descr", "workflow"]
        # table = [line for line in csv.reader(txt.split("\n"), delimiter=' ')]
        # _LOG.debug(hprint.to_str("table"))
        # _LOG.debug("size=%s", str(htable.size(table)))
        table = htable.Table.from_text(cols, txt, delimiter=" ")
        return table

    def test_from_text1(self) -> None:
        table = self._get_table()
        self.assertIsInstance(table, htable.Table)
        _LOG.debug(hprint.to_str("table"))

    def test_from_text_invalid1(self) -> None:
        txt = """completed failure Lint Run_linter
completed success Lint
completed success Lint Slow_tests"""
        cols = ["status", "outcome", "descr", "workflow"]
        with self.assertRaises(AssertionError) as cm:
            htable.Table.from_text(cols, txt, delimiter=" ")
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '3'
        ==
        '4'
        Invalid row='['completed', 'success', 'Lint']' for cols='['status', 'outcome', 'descr', 'workflow']'
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_from_text_invalid2(self) -> None:
        txt = """completed failure Lint Run_linter
        completed success Lint Fast_tess
        completed success Lint Slow_tests"""
        cols = ["status", "outcome", "descr", "workflow", "EXTRA"]
        with self.assertRaises(AssertionError) as cm:
            htable.Table.from_text(cols, txt, delimiter=" ")
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '4'
        ==
        '5'
        Invalid row='['completed', 'failure', 'Lint', 'Run_linter']' for cols='['status', 'outcome', 'descr', 'workflow', 'EXTRA']'
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    # #########################################################################

    def test_repr1(self) -> None:
        table = self._get_table()
        actual = repr(table)
        expected = r"""
cols=['status', 'outcome', 'descr', 'workflow']
table=
['completed', 'failure', 'Lint', 'Run_linter']
['completed', 'success', 'Lint', 'Fast_tests']
['completed', 'success', 'Lint', 'Slow_tests']
size=(3, 4)
"""
        expected = expected.rstrip().lstrip()
        self.assert_equal(actual, expected, fuzzy_match=False)

    def test_str1(self) -> None:
        table = self._get_table()
        actual = str(table)
        expected = r"""
status    | outcome | descr | workflow   |
--------- | ------- | ----- | ---------- |
completed | failure | Lint  | Run_linter |
completed | success | Lint  | Fast_tests |
completed | success | Lint  | Slow_tests |
"""
        expected = expected.rstrip().lstrip()
        self.assert_equal(actual, expected, fuzzy_match=False)

    def test_str_color1(self) -> None:
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
        # Run test.
        actual = str(table)
        # Strip ANSI escape codes before comparing, since the color codes
        # themselves are environment-specific (see `_visible_len()`).
        actual = re.sub(r"\x1b\[[0-9;]*m", "", actual)
        # Check outputs.
        expected = r"""
        Build  | Status      | Passed |
        ------ | ----------- | ------ |
        docker | NOT STARTED | 0      |
        apple  | PASS        | 3754   |
        """
        expected = expected.rstrip().lstrip()
        self.assert_equal(actual, expected, fuzzy_match=False)

    # #########################################################################

    def test_filter_table1(self) -> None:
        """
        Filter resulting in a single matching row.
        """
        table = self._get_table()
        #
        table_filter = table.filter_rows("outcome", "failure")
        expected = r"""
cols=['status', 'outcome', 'descr', 'workflow']
table=
['completed', 'failure', 'Lint', 'Run_linter']
size=(1, 4)
"""
        actual = repr(table_filter)
        expected = expected.rstrip().lstrip()
        self.assert_equal(actual, expected, fuzzy_match=False)

    def test_filter_table2(self) -> None:
        """
        Filter resulting in no matches.
        """
        table = self._get_table()
        #
        table_filter = table.filter_rows("status", "in progress")
        expected = r"""
cols=['status', 'outcome', 'descr', 'workflow']
table=

size=(0, 4)
"""
        actual = repr(table_filter)
        expected = expected.rstrip().lstrip()
        self.assert_equal(actual, expected, fuzzy_match=False)

    def test_filter_table3(self) -> None:
        """
        Filter with a column constant using the constant value.
        """
        table = self._get_table()
        #
        table_filter = table.filter_rows("descr", "Lint")
        actual = repr(table_filter)
        expected = repr(table)
        self.assert_equal(actual, expected, fuzzy_match=False)

    # #########################################################################

    def test_unique1(self) -> None:
        table = self._get_table()
        #
        actual = table.unique("descr")
        expected = ["Lint"]
        self.assert_equal(str(actual), str(expected), fuzzy_match=False)

    def test_unique2(self) -> None:
        table = self._get_table()
        #
        actual = table.unique("workflow")
        expected = ["Fast_tests", "Run_linter", "Slow_tests"]
        self.assert_equal(str(actual), str(expected), fuzzy_match=False)
