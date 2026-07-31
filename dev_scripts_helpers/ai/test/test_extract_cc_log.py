#!/usr/bin/env python3

"""
Unit and end-to-end tests for extract_cc_log.py.
"""

import json
import os
import pprint
from typing import Any, Dict, List
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import extract_cc_log


class Test_extract_statistics(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_statistics()` function.
    """

    def test1(self) -> None:
        """
        Extract statistics from sample CC log.
        """
        # Prepare inputs.
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        records = extract_cc_log._parse_records(input_file)
        # Run test.
        actual = extract_cc_log._extract_statistics(records)
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


# TODO(ai_gp): This should be last
class Test_extract_cc_log_py(hunitest.TestCase):
    """
    End-to-end tests for extract_cc_log.py executable.
    """

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
        argv = ["extract_cc_log.py", "--file", log_file]
        if output_dir:
            argv.extend(["--output_dir", output_dir])
        if output_file:
            argv.extend(["--output", output_file])
        if stats_file:
            argv.extend(["--stats", stats_file])
        parser = extract_cc_log._parse()
        with mock.patch("sys.argv", argv):
            extract_cc_log._main(parser)

    def test1(self) -> None:
        """
        Extract log and generate statistics output file.
        """
        # Prepare inputs.
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        scratch_dir = self.get_scratch_space()
        stats_file = os.path.join(scratch_dir, "stats.json")
        # Run test.
        self._run_extract_cc_log(input_file, stats_file=stats_file)
        # Check outputs.
        actual = hio.from_file(stats_file)
        expected = """
        {
            "num_messages_assistant": 2,
            "num_messages_user": 0,
            "num_requests": 1,
            "total_cost": 0.0241739,
            "total_input_tokens": 10,
            "total_output_tokens": 259,
            "total_thinking_tokens": 110
        }
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test2(self) -> None:
        """
        Extract log and generate output narrative file.
        """
        # Prepare inputs.
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "narrative.txt")
        # Run test.
        self._run_extract_cc_log(input_file, output_file=output_file)
        # Check outputs.
        actual = hio.from_file(output_file)
        expected = """
        Recursion
        .*ASSISTANT TEXT.*
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Extract multiple logs and verify statistics across batch.
        """
        # Prepare inputs: copy fixture multiple times to simulate batch processing.
        input_dir = self.get_input_dir()
        scratch_dir = self.get_scratch_space()
        batch_input_dir = os.path.join(scratch_dir, "batch_logs")
        os.makedirs(batch_input_dir, exist_ok=True)
        log_file1 = os.path.join(input_dir, "sample_cc_log.txt")
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
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        scratch_dir = self.get_scratch_space()
        output_dir = os.path.join(scratch_dir, "narrative_output")
        stats_file = os.path.join(scratch_dir, "stats.json")
        # Run test.
        self._run_extract_cc_log(
            input_file, output_dir=output_dir, stats_file=stats_file
        )
        # Check outputs.
        actual = hio.from_file(stats_file)
        expected = """
        {
            "num_messages_assistant": 2,
            "num_messages_user": 0,
            "num_requests": 1,
            "total_cost": 0.0241739,
            "total_input_tokens": 10,
            "total_output_tokens": 259,
            "total_thinking_tokens": 110
        }
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)


class Test_parse_records(hunitest.TestCase):
    """
    Test `extract_cc_log._parse_records()` function.
    """

    def test1(self) -> None:
        """
        Parse records from sample CC log file.
        """
        # Prepare inputs.
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        # Run test.
        records = extract_cc_log._parse_records(input_file)
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


class Test_extract_requests(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_requests()` function.
    """

    def test1(self) -> None:
        """
        Extract request metadata from sample CC log.
        """
        # Prepare inputs.
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        records = extract_cc_log._parse_records(input_file)
        # Run test.
        requests = extract_cc_log._extract_requests(records)
        # Check outputs.
        actual = pprint.pformat(requests)
        expected = """
        [{'input_tokens': 10,
          'output_tokens': 259,
          'thinking_tokens': 110,
          'ttft_ms': [0-9.]+}]
        """
        self.assert_equal(actual, expected, fuzzy_match=True)


class Test_extract_assistant_text_blocks(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_assistant_text_blocks()` function.
    """

    def test1(self) -> None:
        """
        Extract assistant text blocks from sample CC log.
        """
        # Prepare inputs.
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        records = extract_cc_log._parse_records(input_file)
        # Run test.
        text_blocks = extract_cc_log._extract_assistant_text_blocks(records)
        # Check outputs.
        all_text = " ".join(b.get("text", "") for b in text_blocks)
        expected = """
        Recursion
        .*function.*
        """
        self.assert_equal(all_text, expected, fuzzy_match=True)


class Test_extract_thinking_blocks(hunitest.TestCase):
    """
    Test `extract_cc_log._extract_thinking_blocks()` function.
    """

    def test1(self) -> None:
        """
        Extract thinking blocks from sample CC log.
        """
        # Prepare inputs.
        input_file = os.path.join(self.get_input_dir(), "sample_cc_log.txt")
        records = extract_cc_log._parse_records(input_file)
        # Run test.
        thinking_blocks = extract_cc_log._extract_thinking_blocks(records)
        # Check outputs.
        all_thinking = " ".join(b.get("text", "") for b in thinking_blocks)
        expected = "recursion"
        self.assert_equal(
            all_thinking.lower(), expected, fuzzy_match=True
        )
