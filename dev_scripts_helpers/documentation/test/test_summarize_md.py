from typing import List, Optional
from unittest import mock

import helpers.hmarkdown_headers as hmarhead
import helpers.hunit_test as hunitest

import dev_scripts_helpers.documentation.summarize_md as sum_md


class Test_get_target_headers(hunitest.TestCase):
    """
    Test _get_target_headers function.
    """

    def helper(
        self,
        all_headers: hmarhead.HeaderList,
        md_level: int,
        start: Optional[str] = None,
        end: Optional[str] = None,
        expected_count: Optional[int] = None,
        expected_descriptions: Optional[List[str]] = None,
    ) -> None:
        """
        Test helper for _get_target_headers.

        :param all_headers: List of all headers
        :param md_level: Header level to filter
        :param start: Start header description
        :param end: End header description
        :param expected_count: Expected number of headers
        :param expected_descriptions: Expected header descriptions
        """
        # Run test.
        actual = sum_md._get_target_headers(
            all_headers, md_level=md_level, start=start, end=end
        )
        # Check outputs.
        self.assertEqual(len(actual), expected_count)
        if expected_descriptions:
            actual_descriptions = [h.description for h in actual]
            self.assertEqual(actual_descriptions, expected_descriptions)

    def test1(self) -> None:
        """
        Test filtering headers by level 1.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=2, description="Section 1.1", line_number=3),
            hmarhead.HeaderInfo(level=2, description="Section 1.2", line_number=5),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
        ]
        md_level = 1
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 1", "Chapter 2"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test2(self) -> None:
        """
        Test filtering headers by level 2.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=2, description="Section 1.1", line_number=3),
            hmarhead.HeaderInfo(level=2, description="Section 1.2", line_number=5),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
        ]
        md_level = 2
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Section 1.1", "Section 1.2"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test3(self) -> None:
        """
        Test filtering with start parameter.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(level=1, description="Chapter 3", line_number=13),
        ]
        md_level = 1
        start = "Chapter 2"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 2", "Chapter 3"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            start=start,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test4(self) -> None:
        """
        Test filtering with end parameter.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(level=1, description="Chapter 3", line_number=13),
        ]
        md_level = 1
        end = "Chapter 2"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 1", "Chapter 2"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            end=end,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test5(self) -> None:
        """
        Test filtering with both start and end parameters.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(level=1, description="Chapter 3", line_number=13),
            hmarhead.HeaderInfo(level=1, description="Chapter 4", line_number=19),
        ]
        md_level = 1
        start = "Chapter 2"
        end = "Chapter 3"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 2", "Chapter 3"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            start=start,
            end=end,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test6(self) -> None:
        """
        Test filtering with partial match on start.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
            hmarhead.HeaderInfo(level=1, description="Chapter 3", line_number=13),
        ]
        md_level = 1
        start = "Chapter 2"
        # Prepare outputs.
        expected_count = 2
        expected_descriptions = ["Chapter 2", "Chapter 3"]
        # Run test.
        self.helper(
            all_headers,
            md_level,
            start=start,
            expected_count=expected_count,
            expected_descriptions=expected_descriptions,
        )

    def test7(self) -> None:
        """
        Test error when no headers at specified level.
        """
        # Prepare inputs.
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=2, description="Section 1.1", line_number=3),
        ]
        md_level = 3
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            sum_md._get_target_headers(
                all_headers, md_level=md_level, start=None, end=None
            )
        actual = str(cm.exception)
        self.assertIn("No headers found at level 3", actual)


class Test_extract_section(hunitest.TestCase):
    """
    Test _extract_section function.
    """

    def test1(self) -> None:
        """
        Test extracting section with content until next header.
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 1", line_number=1
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=4),
        ]
        lines = [
            "# Chapter 1",
            "Content line 1",
            "Content line 2",
            "# Chapter 2",
            "Content line 3",
        ]
        md_level = 1
        # Prepare outputs.
        expected = [
            "# Chapter 1",
            "Content line 1",
            "Content line 2",
        ]
        # Run test.
        actual = sum_md._extract_section(
            header, all_headers, lines, md_level=md_level
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test extracting last section (no next header).
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 2", line_number=4
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=4),
        ]
        lines = [
            "# Chapter 1",
            "Content 1",
            "",
            "# Chapter 2",
            "Content 2a",
            "Content 2b",
        ]
        md_level = 1
        # Prepare outputs.
        expected = [
            "# Chapter 2",
            "Content 2a",
            "Content 2b",
        ]
        # Run test.
        actual = sum_md._extract_section(
            header, all_headers, lines, md_level=md_level
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test extracting section strips trailing empty lines.
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 1", line_number=1
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=6),
        ]
        lines = [
            "# Chapter 1",
            "Content",
            "",
            "",
            "",
            "# Chapter 2",
        ]
        md_level = 1
        # Prepare outputs.
        expected = [
            "# Chapter 1",
            "Content",
        ]
        # Run test.
        actual = sum_md._extract_section(
            header, all_headers, lines, md_level=md_level
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test extracting section respects nested headers.
        """
        # Prepare inputs.
        header = hmarhead.HeaderInfo(
            level=1, description="Chapter 1", line_number=1
        )
        all_headers = [
            hmarhead.HeaderInfo(level=1, description="Chapter 1", line_number=1),
            hmarhead.HeaderInfo(level=2, description="Section 1.1", line_number=3),
            hmarhead.HeaderInfo(level=2, description="Section 1.2", line_number=5),
            hmarhead.HeaderInfo(level=1, description="Chapter 2", line_number=7),
        ]
        lines = [
            "# Chapter 1",
            "",
            "## Section 1.1",
            "Content 1.1",
            "## Section 1.2",
            "Content 1.2",
            "# Chapter 2",
        ]
        md_level = 1
        # Prepare outputs.
        expected = [
            "# Chapter 1",
            "",
            "## Section 1.1",
            "Content 1.1",
            "## Section 1.2",
            "Content 1.2",
        ]
        # Run test.
        actual = sum_md._extract_section(
            header, all_headers, lines, md_level=md_level
        )
        # Check outputs.
        self.assertEqual(actual, expected)


class Test_summarize_section(hunitest.TestCase):
    """
    Test _summarize_section function.
    """

    @mock.patch("dev_scripts_helpers.documentation.summarize_md.hllmcli.apply_llm")
    def test1(self, mock_apply_llm) -> None:
        """
        Test basic summarization call.
        """
        # Prepare inputs.
        section_lines = [
            "# Chapter 1",
            "This is content about chapter 1.",
        ]
        system_prompt = "Summarize in bullet points."
        model = "gpt-4o-mini"
        use_llm_executable = False
        expected_result = "- Point 1\n- Point 2"
        expected_cost = 0.01
        mock_apply_llm.return_value = (expected_result, expected_cost)
        # Run test.
        actual_result, actual_cost = sum_md._summarize_section(
            section_lines,
            system_prompt,
            model=model,
            use_llm_executable=use_llm_executable,
        )
        # Check outputs.
        self.assertEqual(actual_result, expected_result)
        self.assertEqual(actual_cost, expected_cost)
        mock_apply_llm.assert_called_once()

    @mock.patch("dev_scripts_helpers.documentation.summarize_md.hllmcli.apply_llm")
    def test2(self, mock_apply_llm) -> None:
        """
        Test summarization with different model.
        """
        # Prepare inputs.
        section_lines = ["Content to summarize."]
        system_prompt = "Summarize."
        model = "claude-3-opus"
        use_llm_executable = True
        expected_result = "Summary"
        expected_cost = 0.05
        mock_apply_llm.return_value = (expected_result, expected_cost)
        # Run test.
        actual_result, actual_cost = sum_md._summarize_section(
            section_lines,
            system_prompt,
            model=model,
            use_llm_executable=use_llm_executable,
        )
        # Check outputs.
        self.assertEqual(actual_result, expected_result)
        self.assertEqual(actual_cost, expected_cost)
        call_kwargs = mock_apply_llm.call_args[1]
        self.assertEqual(call_kwargs["model"], model)
        self.assertEqual(call_kwargs["use_llm_executable"], use_llm_executable)

    @mock.patch("dev_scripts_helpers.documentation.summarize_md.hllmcli.apply_llm")
    def test3(self, mock_apply_llm) -> None:
        """
        Test summarization with empty section.
        """
        # Prepare inputs.
        section_lines = []
        system_prompt = "Summarize."
        model = "gpt-4o-mini"
        use_llm_executable = False
        expected_result = "No content to summarize"
        expected_cost = 0.0
        mock_apply_llm.return_value = (expected_result, expected_cost)
        # Run test.
        actual_result, actual_cost = sum_md._summarize_section(
            section_lines,
            system_prompt,
            model=model,
            use_llm_executable=use_llm_executable,
        )
        # Check outputs.
        self.assertEqual(actual_result, expected_result)
        self.assertEqual(actual_cost, 0.0)


class Test_parse(hunitest.TestCase):
    """
    Test _parse function.
    """

    def test1(self) -> None:
        """
        Test parser creates expected arguments.
        """
        # Prepare inputs.
        # Run test.
        parser = sum_md._parse()
        # Check outputs.
        self.assertIsNotNone(parser)
        self.assertTrue(hasattr(parser, "parse_args"))

    def test2(self) -> None:
        """
        Test parser with basic arguments.
        """
        # Prepare inputs.
        args_list = [
            "-i",
            "input.md",
            "-o",
            "output.md",
            "--md_level",
            "2",
        ]
        parser = sum_md._parse()
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.input_file, "input.md")
        self.assertEqual(args.output_file, "output.md")
        self.assertEqual(args.md_level, 2)

    def test3(self) -> None:
        """
        Test parser with default md_level.
        """
        # Prepare inputs.
        args_list = ["-i", "input.md", "-o", "output.md"]
        parser = sum_md._parse()
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.md_level, 1)

    def test4(self) -> None:
        """
        Test parser with start and end parameters.
        """
        # Prepare inputs.
        args_list = [
            "-i",
            "input.md",
            "-o",
            "output.md",
            "--start",
            "Chapter 1",
            "--end",
            "Chapter 2",
        ]
        parser = sum_md._parse()
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.start, "Chapter 1")
        self.assertEqual(args.end, "Chapter 2")

    def test5(self) -> None:
        """
        Test parser with dry_run flag.
        """
        # Prepare inputs.
        args_list = ["-i", "input.md", "-o", "output.md", "--dry_run"]
        parser = sum_md._parse()
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertTrue(args.dry_run)

    def test6(self) -> None:
        """
        Test parser with default dry_run is False.
        """
        # Prepare inputs.
        args_list = ["-i", "input.md", "-o", "output.md"]
        parser = sum_md._parse()
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertFalse(args.dry_run)

    def test7(self) -> None:
        """
        Test parser with custom model.
        """
        # Prepare inputs.
        args_list = [
            "-i",
            "input.md",
            "-o",
            "output.md",
            "--model",
            "claude-3-opus",
        ]
        parser = sum_md._parse()
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.model, "claude-3-opus")

    def test8(self) -> None:
        """
        Test parser with default model.
        """
        # Prepare inputs.
        args_list = ["-i", "input.md", "-o", "output.md"]
        parser = sum_md._parse()
        # Run test.
        args = parser.parse_args(args_list)
        # Check outputs.
        self.assertEqual(args.model, "gpt-4o-mini")


class Test_get_system_prompt(hunitest.TestCase):
    """
    Test _get_system_prompt function.
    """

    @mock.patch("dev_scripts_helpers.documentation.summarize_md.hgit.find_file_in_git_tree")
    @mock.patch("dev_scripts_helpers.documentation.summarize_md.hio.from_file")
    def test1(self, mock_from_file, mock_find_file) -> None:
        """
        Test system prompt contains expected content.
        """
        # Prepare inputs.
        rules_content = """
        - Rule 1
        - Rule 2
        """
        mock_find_file.return_value = "/path/to/rules.md"
        mock_from_file.return_value = rules_content
        # Run test.
        actual = sum_md._get_system_prompt()
        # Check outputs.
        self.assertIn("Keep the same structure", actual)
        self.assertIn("Bullet point rules", actual)
        self.assertIn("Rule 1", actual)
        self.assertIn("Rule 2", actual)

    @mock.patch("dev_scripts_helpers.documentation.summarize_md.hgit.find_file_in_git_tree")
    @mock.patch("dev_scripts_helpers.documentation.summarize_md.hio.from_file")
    def test2(self, mock_from_file, mock_find_file) -> None:
        """
        Test system prompt contains example output format.
        """
        # Prepare inputs.
        rules_content = "Rule content"
        mock_find_file.return_value = "/path/to/rules.md"
        mock_from_file.return_value = rules_content
        # Run test.
        actual = sum_md._get_system_prompt()
        # Check outputs.
        self.assertIn("Example", actual)
        self.assertIn("markdown headers", actual)
