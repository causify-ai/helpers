import logging
import pprint
from typing import Dict, List

import helpers.hmarkdown_tables as hmartabl
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_replace_tables_with_tags1
# #############################################################################


class Test_replace_tables_with_tags1(hunitest.TestCase):
    def helper(
        self, text: str, expected_lines: List[str], expected_map: Dict[str, str]
    ) -> None:
        """
        Test replacing markdown tables with tags.
        """
        lines = hprint.dedent(text, remove_lead_trail_empty_lines_=True)
        lines = lines.split("\n")
        # Call function.
        actual_lines, table_map = hmartabl.replace_tables_with_tags(lines)
        # Check output.
        table_map_as_str = pprint.pformat(table_map)
        expected_map_as_str = pprint.pformat(expected_map)
        self.assert_equal(table_map_as_str, expected_map_as_str)
        #
        actual_lines = "\n".join(actual_lines)
        expected_lines = hprint.dedent(
            expected_lines, remove_lead_trail_empty_lines_=True
        )
        self.assert_equal(actual_lines, expected_lines)

    def helper_round_trip(self, text: str) -> None:
        """
        Test the round trip.
        """
        # Do the round trip.
        lines = text.split("\n")
        actual_lines, table_map = hmartabl.replace_tables_with_tags(lines)
        act_text = hmartabl.replace_tags_with_tables(actual_lines, table_map)
        # Check output.
        act_text = "\n".join(act_text)
        self.assert_equal(act_text, text)

    def test1(self) -> None:
        """
        Test replacing simple markdown table with tags.
        """
        # Prepare inputs.
        text = """
        Some text before
        | Column 1 | Column 2 |
        |----------|----------|
        | Value 1  | Value 2  |
        | Value 3  | Value 4  |
        Text between tables
        | Name | Age | City |
        |------|-----|------|
        | John | 25  | NYC  |
        Some text after
        """
        # Prepare outputs.
        expected_lines = """
        Some text before
        <table1>
        Text between tables
        <table2>
        Some text after
        """
        # Check table map.
        expected_map = {
            "1": "| Column 1 | Column 2 |\n|----------|----------|\n| Value 1  | Value 2  |\n| Value 3  | Value 4  |",
            "2": "| Name | Age | City |\n|------|-----|------|\n| John | 25  | NYC  |",
        }
        self.helper(text, expected_lines, expected_map)

    def test2(self) -> None:
        """
        Test table with alignment indicators.
        """
        text = """
        | Left | Center | Right |
        |:-----|:------:|------:|
        | L1   |   C1   |    R1 |
        | L2   |   C2   |    R2 |
        """
        expected_lines = """
        <table1>
        """
        expected_map = {
            "1": "| Left | Center | Right |\n|:-----|:------:|------:|\n| L1   |   C1   |    R1 |\n| L2   |   C2   |    R2 |"
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test3(self) -> None:
        """
        Test table with minimal structure.
        """
        text = """
        Before
        | A | B |
        |---|---|
        | 1 | 2 |
        After
        """
        expected_lines = """
        Before
        <table1>
        After
        """
        expected_map = {"1": "| A | B |\n|---|---|\n| 1 | 2 |"}
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test4(self) -> None:
        """
        Test table with empty cells.
        """
        text = """
        | Col1 | Col2 | Col3 |
        |------|------|------|
        | A    |      | C    |
        |      | B    |      |
        """
        expected_lines = """
        <table1>
        """
        expected_map = {
            "1": "| Col1 | Col2 | Col3 |\n|------|------|------|\n| A    |      | C    |\n|      | B    |      |"
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test5(self) -> None:
        """
        Test multiple tables with different column counts.
        """
        text = """
        First table:
        | A | B |
        |---|---|
        | 1 | 2 |

        Second table:
        | X | Y | Z | W |
        |---|---|---|---|
        | a | b | c | d |
        | e | f | g | h |
        """
        expected_lines = """
        First table:
        <table1>

        Second table:
        <table2>
        """
        expected_map = {
            "1": "| A | B |\n|---|---|\n| 1 | 2 |",
            "2": "| X | Y | Z | W |\n|---|---|---|---|\n| a | b | c | d |\n| e | f | g | h |",
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test6(self) -> None:
        """
        Test table with indentation.
        """
        text = """
        Outside
            | Col1 | Col2 |
            |------|------|
            | Val1 | Val2 |
        End
        """
        expected_lines = """
        Outside
        <table1>
        End
        """
        expected_map = {
            "1": "    | Col1 | Col2 |\n    |------|------|\n    | Val1 | Val2 |"
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)
