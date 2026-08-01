import json
import os
import pprint
from io import StringIO
from typing import Any, Dict, List
from unittest import mock

import dev_scripts_helpers.ai.extract_cc_log as dshaecclo
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# Test_extract_statistics
# #############################################################################


class Test_extract_statistics(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_statistics()` function.
    """

    def _get_sample_input_file(self) -> str:
        """Get path to sample CC log file."""
        return os.path.join(self.get_input_dir(), "sample_cc_log.txt")

    def _parse_sample_records(self, input_file: str) -> List[Dict[str, Any]]:
        """Parse records from sample input file."""
        return dshaecclo._parse_records(input_file)

    def test1(self) -> None:
        """
        Extract statistics from sample CC log.
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        records = self._parse_sample_records(input_file)
        # Run test.
        actual = dshaecclo._extract_statistics(records)
        # Check outputs.
        actual_str = pprint.pformat(actual)
        expected = """
        {'num_messages_assistant': 2,
         'num_messages_user': 0,
         'num_requests': 1,
         'total_cost': 0.0241739,
         'total_input_tokens': 10,
         'total_output_tokens': 259,
         'total_thinking_tokens': 110}
        """
        self.assert_equal(actual_str, expected, dedent=True, fuzzy_match=True)


# #############################################################################
# Test_parse_records
# #############################################################################


class Test_parse_records(hunitest.TestCase):
    """
    Test `extract_cc_log._parse_records()` function.
    """

    def _get_sample_input_file(self) -> str:
        """Get path to sample CC log file."""
        return os.path.join(self.get_input_dir(), "sample_cc_log.txt")

    def _parse_sample_records(self, input_file: str) -> List[Dict[str, Any]]:
        """Parse records from sample input file."""
        return dshaecclo._parse_records(input_file)

    def test1(self) -> None:
        """
        Parse records from sample CC log file.
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        # Run test.
        records = self._parse_sample_records(input_file)
        # Prepare outputs.
        has_system = any(r.get("type") == "system" for r in records)
        has_stream = any(r.get("type") == "stream_event" for r in records)
        # Check outputs.
        actual = {
            "num_records": len(records),
            "has_system_records": has_system,
            "has_stream_event_records": has_stream,
        }
        expected = {
            "num_records": True,
            "has_system_records": True,
            "has_stream_event_records": True,
        }
        self.assert_equal(
            str(actual["num_records"] > 0),
            str(expected["num_records"]),
        )
        self.assert_equal(
            str(actual["has_system_records"]),
            str(expected["has_system_records"]),
        )
        self.assert_equal(
            str(actual["has_stream_event_records"]),
            str(expected["has_stream_event_records"]),
        )


# #############################################################################
# Test_extract_requests
# #############################################################################


class Test_extract_requests(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_requests()` function.
    """

    def _get_sample_input_file(self) -> str:
        """Get path to sample CC log file."""
        return os.path.join(self.get_input_dir(), "sample_cc_log.txt")

    def _parse_sample_records(self, input_file: str) -> List[Dict[str, Any]]:
        """Parse records from sample input file."""
        return dshaecclo._parse_records(input_file)

    def test1(self) -> None:
        """
        Extract request metadata from sample CC log.
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        records = self._parse_sample_records(input_file)
        # Run test.
        requests = dshaecclo._extract_requests(records)
        # Check outputs.
        actual = pprint.pformat(requests)
        expected = """
        [{'cost': 0,
          'input_tokens': 10,
          'message_id': 'msg_011CdYxEHPoMjy7CdDPza2YB',
          'model': 'claude-haiku-4-5-20251001',
          'output_tokens': 259,
          'provider': '',
          'speed': '',
          'thinking_tokens': 110,
          'ttft_ms': 1010}]
        """
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_extract_assistant_text_blocks
# #############################################################################


class Test_extract_assistant_text_blocks(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_assistant_text_blocks()` function.
    """

    def _get_sample_input_file(self) -> str:
        """Get path to sample CC log file."""
        return os.path.join(self.get_input_dir(), "sample_cc_log.txt")

    def _parse_sample_records(self, input_file: str) -> List[Dict[str, Any]]:
        """Parse records from sample input file."""
        return dshaecclo._parse_records(input_file)

    def test1(self) -> None:
        """
        Extract assistant text blocks from sample CC log.
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        records = self._parse_sample_records(input_file)
        # Run test.
        text_blocks = dshaecclo._extract_assistant_text_blocks(records)
        # Check outputs.
        all_text = "\n".join(b.get("text", "") for b in text_blocks)
        expected = r"""
        Recursion is when a function calls itself to solve a problem by breaking it into smaller instances of the same problem. Each recursive call operates on simpler input until reaching a base case—a condition that stops further recursion and returns a value.
        Key components: a base case(exit condition)and a recursive case(calls itself with reduced input). Without a base case,recursion loops infinitely.
        Examples: factorial(n! = n ×(n-1)!),tree traversal,binary search. Each call adds a stack frame; deep recursion risks stack overflow. Iteration often replaces recursion for performance,but recursion clarifies problems with inherent recursive structure.
        Recursion is when a function calls itself to solve a problem by breaking it into smaller instances of the same problem. Each recursive call operates on simpler input until reaching a base case—a condition that stops further recursion and returns a value.
        Key components: a base case(exit condition)and a recursive case(calls itself with reduced input). Without a base case,recursion loops infinitely.
        Examples: factorial(n! = n ×(n-1)!),tree traversal,binary search. Each call adds a stack frame; deep recursion risks stack overflow. Iteration often replaces recursion for performance,but recursion clarifies problems with inherent recursive structure.
        """
        expected = hprint.dedent(expected)
        self.assert_equal(all_text, expected, fuzzy_match=True)


# #############################################################################
# Test_extract_thinking_blocks
# #############################################################################


class Test_extract_thinking_blocks(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_thinking_blocks()` function.
    """

    def _get_sample_input_file(self) -> str:
        """Get path to sample CC log file."""
        return os.path.join(self.get_input_dir(), "sample_cc_log.txt")

    def _parse_sample_records(self, input_file: str) -> List[Dict[str, Any]]:
        """Parse records from sample input file."""
        return dshaecclo._parse_records(input_file)

    def test1(self) -> None:
        """
        Extract thinking blocks from sample CC log.
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        records = self._parse_sample_records(input_file)
        # Run test.
        thinking_blocks = dshaecclo._extract_thinking_blocks(records)
        # Check outputs.
        all_thinking = "\n".join(b.get("text", "") for b in thinking_blocks)
        expected = r"""
        User is asking for a 100-word description of recursion. This is a straightforward educational question. They want me to explain recursion concisely.
        Given the caveman mode instructions from CLAUDE.md,I should be terse - strip fluff,use fragments,keep it technical. But this is an educational explanation,so I need to be clear. I'll keep it direct and technical without filler.
        Let me write a clear,technical 100-word explanation of recursion.
        User is asking for a 100-word description of recursion. This is a straightforward educational question. They want me to explain recursion concisely.
        Given the caveman mode instructions from CLAUDE.md,I should be terse - strip fluff,use fragments,keep it technical. But this is an educational explanation,so I need to be clear. I'll keep it direct and technical without filler.
        Let me write a clear,technical 100-word explanation of recursion.
        """
        expected = hprint.dedent(expected)
        self.assert_equal(all_thinking, expected, fuzzy_match=True)


# #############################################################################
# Test_extract_cc_log_py
# #############################################################################


class Test_extract_cc_log_py(hunitest.TestCase):
    """
    End-to-end tests for extract_cc_log.py executable.
    """

    _EXPECTED_STATS = """
    {
        "total_input_tokens": 10,
        "total_output_tokens": 259,
        "total_thinking_tokens": 110,
        "total_cost": 0.0241739,
        "num_requests": 1,
        "num_messages_user": 0,
        "num_messages_assistant": 2
    }
    """

    def _get_sample_input_file(self) -> str:
        """Get path to sample CC log file."""
        return os.path.join(self.get_input_dir(), "sample_cc_log.txt")

    def _setup_test_input_file(
        self, source_filename: str = "sample_cc_log.txt"
    ) -> str:
        """
        Setup test input file by copying from fixture directory.

        :param source_filename: Name of source file in main input directory
        :return: Path to copied test input file
        """
        test_input_dir = self.get_input_dir()
        main_input_dir = os.path.dirname(__file__) + "/input"
        main_input_file = os.path.join(main_input_dir, source_filename)
        test_input_file = os.path.join(test_input_dir, source_filename)
        hio.to_file(test_input_file, hio.from_file(main_input_file))
        return test_input_file

    def _helper_check_stats_file(self, stats_file: str) -> None:
        """
        Verify stats file contains expected output.

        :param stats_file: Path to stats JSON file to verify
        """
        actual = hio.from_file(stats_file)
        self.assert_equal(
            actual, self._EXPECTED_STATS, dedent=True, fuzzy_match=True
        )

    def _run_extract_cc_log(
        self,
        log_file: str,
        *,
        output_dir: str = "",
        output_file: str = "",
        stats_file: str = "",
    ) -> None:
        """
        Run extract_cc_log.py with specified arguments.

        :param log_file: Path to CC log file to process
        :param output_dir: Optional output directory for narrative
        :param output_file: Optional output file for narrative
        :param stats_file: Optional output file for statistics
        """
        argv = ["extract_cc_log.py", "--input", log_file]
        if output_dir:
            argv.extend(["--output_dir", output_dir])
        if output_file:
            argv.extend(["--output", output_file])
        if stats_file:
            argv.extend(["--stats", stats_file])
        parser = dshaecclo._parse()
        with mock.patch("sys.argv", argv):
            dshaecclo._main(parser)

    def test1(self) -> None:
        """
        Extract log and generate statistics output file.
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        scratch_dir = self.get_scratch_space()
        stats_file = os.path.join(scratch_dir, "stats.json")
        # Run test.
        self._run_extract_cc_log(input_file, stats_file=stats_file)
        # Check outputs.
        self._helper_check_stats_file(stats_file)

    def test2(self) -> None:
        """
        Extract log and generate output narrative file.
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "narrative.txt")
        # Run test.
        self._run_extract_cc_log(input_file, output_file=output_file)
        # Check outputs.
        actual = hio.from_file(output_file)
        expected = """
        === Session: 6da1ffe9 | claude-haiku-4-5-20251001 | CC 2.1.220 ===
        ASSISTANT TEXT
        Recursion is when a function calls itself to solve a problem by breaking it into smaller instances of the same problem. Each recursive call operates on simpler input until reaching a base case—a condition that stops further recursion and returns a value.
        Key components: a base case(exit condition)and a recursive case(calls itself with reduced input). Without a base case,recursion loops infinitely.
        Examples: factorial(n! = n ×(n-1)!),tree traversal,binary search. Each call adds a stack frame; deep recursion risks stack overflow. Iteration often replaces recursion for performance,but recursion clarifies problems with inherent recursive structure.
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Extract multiple logs and verify statistics across batch.
        """
        # Prepare inputs: copy fixture multiple times to simulate batch processing.
        scratch_dir = self.get_scratch_space()
        batch_input_dir = os.path.join(scratch_dir, "batch_logs")
        os.makedirs(batch_input_dir, exist_ok=True)
        log_file1 = self._get_sample_input_file()
        batch_log1 = os.path.join(batch_input_dir, "log1.txt")
        batch_log2 = os.path.join(batch_input_dir, "log2.txt")
        hio.to_file(batch_log1, hio.from_file(log_file1))
        hio.to_file(batch_log2, hio.from_file(log_file1))
        # Process batch and collect statistics.
        stats_dir = os.path.join(scratch_dir, "batch_stats")
        os.makedirs(stats_dir, exist_ok=True)
        all_stats: List[Dict[str, Any]] = []
        for log_path in [batch_log1, batch_log2]:
            stats_file = os.path.join(
                stats_dir, os.path.basename(log_path) + ".stats.json"
            )
            self._run_extract_cc_log(log_path, stats_file=stats_file)
            with open(stats_file, "r") as f:
                stats = json.load(f)
            all_stats.append(stats)
        # Check outputs.
        actual = pprint.pformat(all_stats)
        expected = """
        [{'num_messages_assistant': 2,
          'num_messages_user': 0,
          'num_requests': 1,
          'total_cost': 0.0241739,
          'total_input_tokens': 10,
          'total_output_tokens': 259,
          'total_thinking_tokens': 110},
         {'num_messages_assistant': 2,
          'num_messages_user': 0,
          'num_requests': 1,
          'total_cost': 0.0241739,
          'total_input_tokens': 10,
          'total_output_tokens': 259,
          'total_thinking_tokens': 110}]
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test4(self) -> None:
        """
        Test statistics extraction with output directory (narrative output).
        """
        # Prepare inputs.
        input_file = self._get_sample_input_file()
        scratch_dir = self.get_scratch_space()
        output_dir = os.path.join(scratch_dir, "narrative_output")
        stats_file = os.path.join(scratch_dir, "stats.json")
        # Run test.
        self._run_extract_cc_log(
            input_file, output_dir=output_dir, stats_file=stats_file
        )
        # Check outputs.
        self._helper_check_stats_file(stats_file)

    def test5(self) -> None:
        """
        Test reading from stdin using `--input -`.
        """
        # Prepare inputs: copy sample log to test-specific input directory.
        test_input_file = self._setup_test_input_file()
        input_content = hio.from_file(test_input_file)
        scratch_dir = self.get_scratch_space()
        stats_file = os.path.join(scratch_dir, "stats.json")
        # Run test: mock stdin with log content.
        argv = ["extract_cc_log.py", "--input", "-", "--stats", stats_file]
        parser = dshaecclo._parse()
        with mock.patch("sys.argv", argv):
            with mock.patch("sys.stdin", StringIO(input_content)):
                dshaecclo._main(parser)
        # Check outputs.
        self._helper_check_stats_file(stats_file)

    def test6(self) -> None:
        """
        Test writing to stdout using `--output -`.
        """
        # Prepare inputs: copy sample log to test-specific input directory.
        test_input_file = self._setup_test_input_file()
        # Run test: capture stdout.
        argv = ["extract_cc_log.py", "--input", test_input_file, "--output", "-"]
        parser = dshaecclo._parse()
        captured_output = StringIO()
        with mock.patch("sys.argv", argv):
            with mock.patch("sys.stdout", new=captured_output):
                dshaecclo._main(parser)
        # Check outputs: verify both narrative and output file content are in stdout.
        actual = captured_output.getvalue()
        # Check for key narrative elements.
        self.assertIn("NARRATIVE", actual)
        # Check for output file content (ASSISTANT TEXT appears twice: once from
        # narrative, once from --output -).
        self.assertIn("ASSISTANT TEXT", actual)
        # Check for recursion content appears.
        self.assertIn("Recursion is when a function calls itself", actual)
