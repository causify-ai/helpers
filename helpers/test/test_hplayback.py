import logging
import os
from typing import Any, List

import helpers.hio as hio
import helpers.hplayback as hplayba
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_record_replay_storage1
# #############################################################################


class Test_record_replay_storage1(hunitest.TestCase):
    """
    Test the storage layer used by `@record` and the mock classes.
    """

    def test1(self) -> None:
        """
        Test round-trip of records with simple types.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        records = [
            {"args": ["cmd1"], "kwargs": {}, "result": [{"id": "1"}]},
            {"args": ["cmd2"], "kwargs": {"limit": 5}, "result": [{"id": "2"}]},
        ]
        # Run test.
        hplayba._save_records(file_path, records)
        actual = hplayba._load_records(file_path)
        # Check outputs.
        self.assert_equal(str(actual), str(records))

    def test2(self) -> None:
        """
        Test that the saved fixture file is human-readable JSON for simple
        types.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        records = [
            {"args": ["echo hi"], "kwargs": {}, "result": [{"id": "abc"}]},
        ]
        # Run test.
        hplayba._save_records(file_path, records)
        actual = hio.from_file(file_path)
        # Check outputs.
        # The saved file must contain the args/result inline as readable JSON.
        self.assertIn("echo hi", actual)
        self.assertIn("abc", actual)


# #############################################################################
# Test_recording1
# #############################################################################


class Test_recording1(hunitest.TestCase):
    """
    Test the `@record` decorator and the `recording()` context manager.
    """

    def test1(self) -> None:
        """
        Test that an undecorated call writes nothing and behaves normally.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        actual = add(2, 3)
        # Check outputs.
        self.assertEqual(actual, 5)
        # No file should have been written.
        self.assertFalse(os.path.exists(file_path))

    def test2(self) -> None:
        """
        Test that calls inside `recording()` are captured and flushed.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        with hplayba.recording(add):
            add(2, 3)
            add(10, 20)
        actual = hplayba._load_records(file_path)
        # Prepare outputs.
        expected = [
            {"args": [2, 3], "kwargs": {}, "result": 5},
            {"args": [10, 20], "kwargs": {}, "result": 30},
        ]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test that calls outside the context are not captured.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        # Before the context: not captured.
        add(1, 1)
        with hplayba.recording(add):
            add(2, 3)
        # After the context: not captured.
        add(5, 5)
        actual = hplayba._load_records(file_path)
        # Prepare outputs.
        expected = [{"args": [2, 3], "kwargs": {}, "result": 5}]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test that recording is turned off even if the block raises.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        with self.assertRaises(RuntimeError):
            with hplayba.recording(add):
                add(2, 3)
                raise RuntimeError("boom")
        # Subsequent calls outside the context must not be recorded.
        add(99, 99)
        actual = hplayba._load_records(file_path)
        # Prepare outputs.
        expected = [{"args": [2, 3], "kwargs": {}, "result": 5}]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# TestMockDict1
# #############################################################################


class TestMockDict1(hunitest.TestCase):
    """
    Test `MockDict` for order-independent replay.
    """

    def _write_fixture(self, records: List[Any]) -> hplayba.MockDict:
        """
        Persist `records` to a scratch fixture and return a `MockDict`.
        """
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        hplayba._save_records(file_path, records)
        return hplayba.MockDict(file_path)

    def test1(self) -> None:
        """
        Test lookup of a recorded call.
        """
        # Prepare inputs.
        records = [
            {"args": ["cmd1"], "kwargs": {}, "result": [{"id": "1"}]},
            {"args": ["cmd2"], "kwargs": {}, "result": [{"id": "2"}]},
        ]
        mock_dict = self._write_fixture(records)
        # Run test.
        actual1 = mock_dict("cmd1")
        actual2 = mock_dict("cmd2")
        # Check outputs.
        self.assertEqual(actual1, [{"id": "1"}])
        self.assertEqual(actual2, [{"id": "2"}])

    def test2(self) -> None:
        """
        Test that calls can be replayed in any order.
        """
        # Prepare inputs.
        records = [
            {"args": ["A"], "kwargs": {}, "result": 1},
            {"args": ["B"], "kwargs": {}, "result": 2},
        ]
        mock_dict = self._write_fixture(records)
        # Run test.
        # Call in the reverse order.
        actual_b = mock_dict("B")
        actual_a = mock_dict("A")
        # Check outputs.
        self.assertEqual(actual_a, 1)
        self.assertEqual(actual_b, 2)

    def test3(self) -> None:
        """
        Test that missing keys raise an assertion error.
        """
        # Prepare inputs.
        records = [{"args": ["cmd1"], "kwargs": {}, "result": "ok"}]
        mock_dict = self._write_fixture(records)
        # Run test and check output.
        with self.assertRaises(AssertionError):
            mock_dict("missing_cmd")


# #############################################################################
# TestMockSequence1
# #############################################################################


class TestMockSequence1(hunitest.TestCase):
    """
    Test `MockSequence` for ordered replay.
    """

    def _write_fixture(self, records: List[Any]) -> hplayba.MockSequence:
        """
        Persist `records` to a scratch fixture and return a `MockSequence`.
        """
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        hplayba._save_records(file_path, records)
        return hplayba.MockSequence(file_path)

    def test1(self) -> None:
        """
        Test that results are returned in the recorded order.
        """
        # Prepare inputs.
        records = [
            {"args": ["A"], "kwargs": {}, "result": 1},
            {"args": ["B"], "kwargs": {}, "result": 2},
            {"args": ["C"], "kwargs": {}, "result": 3},
        ]
        mock_seq = self._write_fixture(records)
        # Run test.
        actual_a = mock_seq("A")
        actual_b = mock_seq("B")
        actual_c = mock_seq("C")
        # Check outputs.
        self.assertEqual(actual_a, 1)
        self.assertEqual(actual_b, 2)
        self.assertEqual(actual_c, 3)

    def test2(self) -> None:
        """
        Test that out-of-order calls raise an assertion error.
        """
        # Prepare inputs.
        records = [
            {"args": ["A"], "kwargs": {}, "result": 1},
            {"args": ["B"], "kwargs": {}, "result": 2},
        ]
        mock_seq = self._write_fixture(records)
        # Run test and check output.
        with self.assertRaises(AssertionError):
            mock_seq("B")

    def test3(self) -> None:
        """
        Test that exhausting the sequence raises an assertion error.
        """
        # Prepare inputs.
        records = [{"args": ["A"], "kwargs": {}, "result": 1}]
        mock_seq = self._write_fixture(records)
        # Run test.
        mock_seq("A")
        # Check outputs.
        with self.assertRaises(AssertionError):
            mock_seq("A")

    def test4(self) -> None:
        """
        Test that `reset()` restarts the sequence.
        """
        # Prepare inputs.
        records = [{"args": ["A"], "kwargs": {}, "result": 1}]
        mock_seq = self._write_fixture(records)
        # Run test.
        first_call = mock_seq("A")
        mock_seq.reset()
        second_call = mock_seq("A")
        # Check outputs.
        self.assertEqual(first_call, 1)
        self.assertEqual(second_call, 1)
