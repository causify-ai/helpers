from typing import List

import pytest

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.convert_table as dshdcota

# Check if tabulate is available (required by _format_as_md which uses pandas.to_markdown)
try:
    import tabulate  # noqa: F401, pylint: disable=unused-import

    _TABULATE_AVAILABLE = True
except ImportError:
    _TABULATE_AVAILABLE = False


# #############################################################################
# Test_convert_table_parsing
# #############################################################################


class Test_convert_table_parsing(hunitest.TestCase):
    """
    Test table parsing functions.
    """

    def helper_parse_md_table(
        self,
        lines: List[str],
        expected_header: List[str],
        expected_rows: List[List[str]],
    ) -> None:
        """
        Test helper for _parse_md_table.

        :param lines: Input markdown table lines
        :param expected_header: Expected header row
        :param expected_rows: Expected data rows
        """
        # Run test.
        header, rows = dshdcota._parse_md_table(lines)
        # Check outputs.
        self.assertEqual(header, expected_header)
        self.assertEqual(rows, expected_rows)

    def helper_parse_delimited(
        self,
        lines: List[str],
        delimiter: str,
        expected_header: List[str],
        expected_rows: List[List[str]],
    ) -> None:
        """
        Test helper for _parse_delimited.

        :param lines: Input delimited lines
        :param delimiter: Delimiter character
        :param expected_header: Expected header row
        :param expected_rows: Expected data rows
        """
        # Run test.
        header, rows = dshdcota._parse_delimited(lines, delimiter)
        # Check outputs.
        self.assertEqual(header, expected_header)
        self.assertEqual(rows, expected_rows)

    def test1(self) -> None:
        """
        Test parsing a simple markdown table.
        """
        # Prepare inputs.
        lines_text = """
        | Name | Age | City |
        |------|-----|------|
        | Alice | 30 | NYC |
        | Bob | 25 | LA |
        """
        lines = hprint.dedent(lines_text).strip().split("\n")
        # Prepare outputs.
        expected_header = ["Name", "Age", "City"]
        expected_rows = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]
        # Run test.
        self.helper_parse_md_table(lines, expected_header, expected_rows)

    def test2(self) -> None:
        """
        Test parsing markdown table with extra padding.
        """
        # Prepare inputs.
        lines_text = """
        |  Name  |  Age  |  City  |
        | ------ | ----- | ------ |
        |  Alice | 30    |  NYC   |
        """
        lines = hprint.dedent(lines_text).strip().split("\n")
        # Prepare outputs.
        expected_header = ["Name", "Age", "City"]
        expected_rows = [
            ["Alice", "30", "NYC"],
        ]
        # Run test.
        self.helper_parse_md_table(lines, expected_header, expected_rows)

    def test3(self) -> None:
        """
        Test parsing CSV format.
        """
        # Prepare inputs.
        csv_text = """
        Name,Age,City
        Alice,30,NYC
        Bob,25,LA
        """
        lines = hprint.dedent(csv_text).strip().split("\n")
        delimiter = ","
        # Prepare outputs.
        expected_header = ["Name", "Age", "City"]
        expected_rows = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]
        # Run test.
        self.helper_parse_delimited(
            lines, delimiter, expected_header, expected_rows
        )

    def test4(self) -> None:
        """
        Test parsing TSV format.
        """
        # Prepare inputs.
        tsv_text = """
        Name\tAge\tCity
        Alice\t30\tNYC
        Bob\t25\tLA
        """
        lines = hprint.dedent(tsv_text).strip().split("\n")
        delimiter = "\t"
        # Prepare outputs.
        expected_header = ["Name", "Age", "City"]
        expected_rows = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]
        # Run test.
        self.helper_parse_delimited(
            lines, delimiter, expected_header, expected_rows
        )


# #############################################################################
# Test_convert_table_formatting
# #############################################################################


class Test_convert_table_formatting(hunitest.TestCase):
    """
    Test table formatting functions.
    """

    @pytest.mark.skipif(
        not _TABULATE_AVAILABLE,
        reason="Requires tabulate dependency for pandas.to_markdown(). "
        "Either test the executable, add tabulate to the container, "
        "or refactor code to not rely on tabulate.",
    )
    def test1(self) -> None:
        """
        Test formatting table as markdown.
        """
        # Prepare inputs.
        header = ["Name", "Age"]
        rows = [["Alice", "30"], ["Bob", "25"]]
        # Prepare outputs.
        expected = """
        | Name   |   Age |
        |:-------|------:|
        | Alice  |    30 |
        | Bob    |    25 |
        """
        # Run test.
        result = dshdcota._format_as_md(header, rows)
        # Check outputs.
        self.assert_equal(result, expected, dedent=True)

    @pytest.mark.skipif(
        not _TABULATE_AVAILABLE,
        reason="Requires tabulate dependency for pandas.to_markdown(). "
        "Either test the executable, add tabulate to the container, "
        "or refactor code to not rely on tabulate.",
    )
    def test2(self) -> None:
        """
        Test markdown formatting with varying column widths.
        """
        # Prepare inputs.
        header = ["Product", "Price"]
        rows = [["Apple", "1.50"], ["Banana", "0.75"]]
        # Prepare outputs.
        expected = """
        | Product   |   Price |
        |:----------|--------:|
        | Apple     |    1.5  |
        | Banana    |    0.75 |
        """
        # Run test.
        result = dshdcota._format_as_md(header, rows)
        # Check outputs.
        self.assert_equal(result, expected, dedent=True)

    def test3(self) -> None:
        """
        Test formatting table as CSV.
        """
        # Prepare inputs.
        header = ["Name", "Age", "City"]
        rows = [["Alice", "30", "NYC"], ["Bob", "25", "LA"]]
        # Prepare outputs.
        expected = """
        Name,Age,City
        Alice,30,NYC
        Bob,25,LA
        """
        # Run test.
        result = dshdcota._format_as_delimited(header, rows, ",")
        # Check outputs.
        self.assert_equal(result, expected, dedent=True)

    def test4(self) -> None:
        """
        Test formatting table as TSV.
        """
        # Prepare inputs.
        header = ["Product", "Price", "Qty"]
        rows = [["Apple", "1.50", "10"], ["Banana", "0.75", "20"]]
        # Prepare outputs.
        expected = """
        Product	Price	Qty
        Apple	1.50	10
        Banana	0.75	20
        """
        # Run test.
        result = dshdcota._format_as_delimited(header, rows, "\t")
        # Check outputs.
        self.assert_equal(result, expected, dedent=True)


# #############################################################################
# Test_convert_table_roundtrip
# #############################################################################


class Test_convert_table_roundtrip(hunitest.TestCase):
    """
    Test roundtrip conversions (format A -> format B -> format A).
    """

    @pytest.mark.skipif(
        not _TABULATE_AVAILABLE,
        reason="Requires tabulate dependency for pandas.to_markdown(). "
        "Either test the executable, add tabulate to the container, "
        "or refactor code to not rely on tabulate.",
    )
    def test1(self) -> None:
        """
        Test CSV -> Markdown -> CSV roundtrip.
        """
        # Prepare inputs.
        csv_text = """
        Name,Age,City
        Alice,30,NYC
        Bob,25,LA
        """
        csv_input = hprint.dedent(csv_text).strip().split("\n")
        # Prepare outputs.
        expected_text = csv_text
        expected = hprint.dedent(expected_text).strip()
        # Run test.
        header, rows = dshdcota._parse_delimited(csv_input, ",")
        md_output = dshdcota._format_as_md(header, rows)
        md_lines = md_output.split("\n")
        header2, rows2 = dshdcota._parse_md_table(md_lines)
        csv_output = dshdcota._format_as_delimited(header2, rows2, ",")
        # Check outputs.
        self.assertEqual(csv_output, expected)

    @pytest.mark.skipif(
        not _TABULATE_AVAILABLE,
        reason="Requires tabulate dependency for pandas.to_markdown(). "
        "Either test the executable, add tabulate to the container, "
        "or refactor code to not rely on tabulate.",
    )
    def test2(self) -> None:
        """
        Test Markdown -> CSV -> Markdown roundtrip.
        """
        # Prepare inputs.
        md_text = """
        | Product | Price |
        |---------|-------|
        | Apple | 1.50 |
        """
        md_input = hprint.dedent(md_text).strip().split("\n")
        # Run test.
        header, rows = dshdcota._parse_md_table(md_input)
        csv_output = dshdcota._format_as_delimited(header, rows, ",")
        csv_lines = csv_output.split("\n")
        header2, rows2 = dshdcota._parse_delimited(csv_lines, ",")
        md_output = dshdcota._format_as_md(header2, rows2)
        # Check outputs.
        self.assertIn("Product", md_output)
        self.assertIn("Price", md_output)
        self.assertIn("Apple", md_output)


# #############################################################################
# Test_convert_table_edge_cases
# #############################################################################


class Test_convert_table_edge_cases(hunitest.TestCase):
    """
    Test edge cases and special characters.
    """

    def helper_detect_mode(self, filename: str, expected_mode: str) -> None:
        """
        Test helper for _detect_mode.

        :param filename: Input filename
        :param expected_mode: Expected detected mode
        """
        # Run test.
        mode = dshdcota._detect_mode(filename)
        # Check outputs.
        self.assertEqual(mode, expected_mode)

    def test1(self) -> None:
        """
        Test parsing markdown table with empty cells.
        """
        # Prepare inputs.
        lines_text = """
        | Name | Note |
        |------|------|
        | Alice |  |
        | Bob | Good |
        """
        lines = hprint.dedent(lines_text).strip().split("\n")
        # Prepare outputs.
        expected_header = ["Name", "Note"]
        expected_rows = [
            ["Alice", ""],
            ["Bob", "Good"],
        ]
        # Run test.
        header, rows = dshdcota._parse_md_table(lines)
        # Check outputs.
        self.assertEqual(header, expected_header)
        self.assertEqual(rows, expected_rows)

    def test2(self) -> None:
        """
        Test parsing CSV with quoted fields.
        """
        # Prepare inputs.
        csv_text = """
        Name,City,Note
        Alice,New York,"Has spaces"
        Bob,Los Angeles,"A, with comma"
        """
        lines = hprint.dedent(csv_text).strip().split("\n")
        # Prepare outputs.
        expected_header = ["Name", "City", "Note"]
        expected_rows = [
            ["Alice", "New York", "Has spaces"],
            ["Bob", "Los Angeles", "A, with comma"],
        ]
        # Run test.
        header, rows = dshdcota._parse_delimited(lines, ",")
        # Check outputs.
        self.assertEqual(header, expected_header)
        self.assertEqual(rows, expected_rows)

    def test3(self) -> None:
        """
        Test format detection for CSV files.
        """
        # Prepare inputs.
        filename = "table.csv"
        # Prepare outputs.
        expected_mode = "csv"
        # Run test.
        self.helper_detect_mode(filename, expected_mode)

    def test4(self) -> None:
        """
        Test format detection for TSV files.
        """
        # Prepare inputs.
        filename = "table.tsv"
        # Prepare outputs.
        expected_mode = "tsv"
        # Run test.
        self.helper_detect_mode(filename, expected_mode)

    def test5(self) -> None:
        """
        Test format detection for Markdown files.
        """
        # Prepare inputs.
        filename = "table.md"
        # Prepare outputs.
        expected_mode = "md"
        # Run test.
        self.helper_detect_mode(filename, expected_mode)
