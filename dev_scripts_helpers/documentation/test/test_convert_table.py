import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.convert_table as dsconttbl


class Test_convert_table_parsing(hunitest.TestCase):
    """
    Test table parsing functions.
    """

    def test_parse_md_table_simple(self) -> None:
        """
        Test parsing a simple markdown table.
        """
        lines = [
            "| Name | Age | City |",
            "|------|-----|------|",
            "| Alice | 30 | NYC |",
            "| Bob | 25 | LA |",
        ]
        header, rows = dsconttbl._parse_md_table(lines)
        assert header == ["Name", "Age", "City"]
        assert len(rows) == 2
        assert rows[0] == ["Alice", "30", "NYC"]
        assert rows[1] == ["Bob", "25", "LA"]

    def test_parse_md_table_with_padding(self) -> None:
        """
        Test parsing markdown table with extra padding.
        """
        lines = [
            "|  Name  |  Age  |  City  |",
            "| ------ | ----- | ------ |",
            "|  Alice | 30    |  NYC   |",
        ]
        header, rows = dsconttbl._parse_md_table(lines)
        assert header == ["Name", "Age", "City"]
        assert rows[0] == ["Alice", "30", "NYC"]

    def test_parse_delimited_csv(self) -> None:
        """
        Test parsing CSV format.
        """
        lines = [
            "Name,Age,City",
            "Alice,30,NYC",
            "Bob,25,LA",
        ]
        header, rows = dsconttbl._parse_delimited(lines, ",")
        assert header == ["Name", "Age", "City"]
        assert len(rows) == 2
        assert rows[0] == ["Alice", "30", "NYC"]
        assert rows[1] == ["Bob", "25", "LA"]

    def test_parse_delimited_tsv(self) -> None:
        """
        Test parsing TSV format.
        """
        lines = [
            "Name\tAge\tCity",
            "Alice\t30\tNYC",
            "Bob\t25\tLA",
        ]
        header, rows = dsconttbl._parse_delimited(lines, "\t")
        assert header == ["Name", "Age", "City"]
        assert len(rows) == 2
        assert rows[0] == ["Alice", "30", "NYC"]


class Test_convert_table_formatting(hunitest.TestCase):
    """
    Test table formatting functions.
    """

    def test_format_as_md_simple(self) -> None:
        """
        Test formatting table as markdown.
        """
        header = ["Name", "Age"]
        rows = [["Alice", "30"], ["Bob", "25"]]
        result = dsconttbl._format_as_md(header, rows)
        expected_lines = [
            "| Name  | Age |",
            "| ----- | --- |",
            "| Alice | 30  |",
            "| Bob   | 25  |",
        ]
        expected = "\n".join(expected_lines)
        assert result == expected

    def test_format_as_md_column_width(self) -> None:
        """
        Test markdown formatting with varying column widths.
        """
        header = ["Product", "Price"]
        rows = [["Apple", "1.50"], ["Banana", "0.75"]]
        result = dsconttbl._format_as_md(header, rows)
        lines = result.split("\n")
        assert len(lines) == 4
        assert "|" in lines[0]
        assert "---" in lines[1]

    def test_format_as_csv(self) -> None:
        """
        Test formatting table as CSV.
        """
        header = ["Name", "Age", "City"]
        rows = [["Alice", "30", "NYC"], ["Bob", "25", "LA"]]
        result = dsconttbl._format_as_delimited(header, rows, ",")
        expected = "Name,Age,City\nAlice,30,NYC\nBob,25,LA"
        assert result == expected

    def test_format_as_tsv(self) -> None:
        """
        Test formatting table as TSV.
        """
        header = ["Product", "Price", "Qty"]
        rows = [["Apple", "1.50", "10"], ["Banana", "0.75", "20"]]
        result = dsconttbl._format_as_delimited(header, rows, "\t")
        expected = "Product\tPrice\tQty\nApple\t1.50\t10\nBanana\t0.75\t20"
        assert result == expected


class Test_convert_table_roundtrip(hunitest.TestCase):
    """
    Test roundtrip conversions (format A -> format B -> format A).
    """

    def test_csv_to_markdown_to_csv(self) -> None:
        """
        Test CSV -> Markdown -> CSV roundtrip.
        """
        csv_input = ["Name,Age,City", "Alice,30,NYC", "Bob,25,LA"]
        header, rows = dsconttbl._parse_delimited(csv_input, ",")
        md_output = dsconttbl._format_as_md(header, rows)
        md_lines = md_output.split("\n")
        header2, rows2 = dsconttbl._parse_md_table(md_lines)
        csv_output = dsconttbl._format_as_delimited(header2, rows2, ",")
        expected = "Name,Age,City\nAlice,30,NYC\nBob,25,LA"
        assert csv_output == expected

    def test_markdown_to_csv_to_markdown(self) -> None:
        """
        Test Markdown -> CSV -> Markdown roundtrip.
        """
        md_input = [
            "| Product | Price |",
            "|---------|-------|",
            "| Apple | 1.50 |",
        ]
        header, rows = dsconttbl._parse_md_table(md_input)
        csv_output = dsconttbl._format_as_delimited(header, rows, ",")
        csv_lines = csv_output.split("\n")
        header2, rows2 = dsconttbl._parse_delimited(csv_lines, ",")
        md_output = dsconttbl._format_as_md(header2, rows2)
        assert "Product" in md_output
        assert "Price" in md_output
        assert "Apple" in md_output


class Test_convert_table_edge_cases(hunitest.TestCase):
    """
    Test edge cases and special characters.
    """

    def test_parse_md_table_with_empty_cells(self) -> None:
        """
        Test parsing markdown table with empty cells.
        """
        lines = [
            "| Name | Note |",
            "|------|------|",
            "| Alice |  |",
            "| Bob | Good |",
        ]
        header, rows = dsconttbl._parse_md_table(lines)
        assert header == ["Name", "Note"]
        assert rows[0] == ["Alice", ""]
        assert rows[1] == ["Bob", "Good"]

    def test_parse_csv_with_quotes(self) -> None:
        """
        Test parsing CSV with quoted fields.
        """
        lines = [
            'Name,City,Note',
            'Alice,New York,"Has spaces"',
            'Bob,Los Angeles,"A, with comma"',
        ]
        header, rows = dsconttbl._parse_delimited(lines, ",")
        assert header == ["Name", "City", "Note"]
        assert rows[0] == ["Alice", "New York", "Has spaces"]
        assert rows[1] == ["Bob", "Los Angeles", "A, with comma"]

    def test_detect_mode_csv(self) -> None:
        """
        Test format detection for CSV files.
        """
        mode = dsconttbl._detect_mode("table.csv")
        assert mode == "csv"

    def test_detect_mode_tsv(self) -> None:
        """
        Test format detection for TSV files.
        """
        mode = dsconttbl._detect_mode("table.tsv")
        assert mode == "tsv"

    def test_detect_mode_md(self) -> None:
        """
        Test format detection for Markdown files.
        """
        mode = dsconttbl._detect_mode("table.md")
        assert mode == "md"
