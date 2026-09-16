#!/usr/bin/env python
"""
Unit tests for hdaemon.py.

Tests utility functions for file operations and hashing.
"""

import contextlib
import hashlib
import os
import time
import unittest.mock as umock
from typing import Callable, Dict, Iterator, Tuple

import helpers.hdaemon as hdaemon
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# _StopDaemonLoop
# #############################################################################


class _StopDaemonLoop(Exception):
    """
    Sentinel raised from a mocked `time.sleep()` to break out of
    `_daemon_watch()`'s `while True` after a bounded number of polls.
    """


# #############################################################################
# Test__file_hash
# #############################################################################


class Test__file_hash(hunitest.TestCase):
    """
    Test `_file_hash()` function that computes MD5 hashes of files.
    """

    def helper(self, content: str) -> None:
        """
        Test helper for `_file_hash()`.

        :param content: File content to hash
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "test.txt")
        hio.to_file(test_file, content)
        # Prepare outputs.
        expected_hash = hashlib.md5(content.encode()).hexdigest()
        # Run test.
        actual = hdaemon._file_hash(test_file)
        # Check outputs.
        self.assert_equal(actual, expected_hash)

    def test1(self) -> None:
        """
        Test hash of empty file.
        """
        # Prepare inputs.
        content = ""
        # Run test.
        self.helper(content)

    def test2(self) -> None:
        """
        Test hash of file with known content.
        """
        # Prepare inputs.
        content = "Hello, World!"
        # Run test.
        self.helper(content)

    def test3(self) -> None:
        """
        Test that different files produce different hashes.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "file1.txt")
        file2 = os.path.join(scratch_dir, "file2.txt")
        content1 = "Content A"
        content2 = "Content B"
        hio.to_file(file1, content1)
        hio.to_file(file2, content2)
        # Prepare outputs.
        expected_hash1 = hashlib.md5(content1.encode()).hexdigest()
        expected_hash2 = hashlib.md5(content2.encode()).hexdigest()
        # Run test.
        hash1 = hdaemon._file_hash(file1)
        hash2 = hdaemon._file_hash(file2)
        # Check outputs.
        self.assert_equal(hash1, expected_hash1)
        self.assert_equal(hash2, expected_hash2)

    def test4(self) -> None:
        """
        Test hash of large file (>65536 bytes to exercise chunking).
        """
        # Prepare inputs.
        content = "x" * 100000
        # Run test.
        self.helper(content)

    def test5(self) -> None:
        """
        Test that same file produces same hash consistently.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "consistent.txt")
        content = "Consistent content"
        hio.to_file(test_file, content)
        # Run test.
        hash1 = hdaemon._file_hash(test_file)
        hash2 = hdaemon._file_hash(test_file)
        # Check outputs.
        self.assert_equal(hash1, hash2)


# #############################################################################
# Test__fmt_mtime
# #############################################################################


class Test__fmt_mtime(hunitest.TestCase):
    """
    Test `_fmt_mtime()` function that formats a file mtime for debug logs.
    """

    def test1(self) -> None:
        """
        Test that the fractional second is rendered as zero-padded ms.
        """
        # Prepare inputs. `.5` is exactly representable in binary floating
        # point, so the millisecond component is exact (no rounding noise).
        mtime = 1700000000.5
        # Prepare outputs.
        expected = time.strftime("%H:%M:%S", time.localtime(mtime)) + ".500"
        # Run test.
        actual = hdaemon._fmt_mtime(mtime)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a whole-second mtime gets ".000".
        """
        # Prepare inputs.
        mtime = 1700000000.0
        # Prepare outputs.
        expected = time.strftime("%H:%M:%S", time.localtime(mtime)) + ".000"
        # Run test.
        actual = hdaemon._fmt_mtime(mtime)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that the output matches the "HH:MM:SS.mmm" shape.
        """
        # Prepare inputs.
        mtime = time.time()
        # Run test.
        actual = hdaemon._fmt_mtime(mtime)
        # Check outputs.
        self.assertRegex(actual, r"^\d{2}:\d{2}:\d{2}\.\d{3}$")


# #############################################################################
# Test__daemon_watch
# #############################################################################


class Test__daemon_watch(hunitest.TestCase):
    """
    Test `_daemon_watch()` function: poll, debounce, regenerate, and
    conflict detection logic.
    """

    def _create_fake_time_infrastructure(
        self,
    ) -> Tuple[Dict[str, float], Callable[[], float]]:
        """
        Create a fake clock and a `time.time()` replacement.

        :return:`(fake_clock, fake_time)` where `fake_clock["t"]` holds the
            current fake time and `fake_time()` reads it
        """
        fake_clock = {"t": 0.0}

        def fake_time() -> float:
            return fake_clock["t"]

        return fake_clock, fake_time

    def _create_fake_sleep_for_daemon(
        self,
        fake_clock: Dict[str, float],
        test_file: str,
        stop_threshold: int,
    ) -> Callable[[float], None]:
        """
        Create a fake `time.sleep()` that drives `_daemon_watch()`'s loop.

        Advances `fake_clock` on every poll, overwrites `test_file` with
        "v1" on the first poll to simulate a user edit, and raises
        `_StopDaemonLoop` once `stop_threshold` polls have elapsed to break
        out of the daemon's `while True` loop.

        :param fake_clock: clock dict shared with the corresponding
            `fake_time()`
        :param test_file: file to overwrite with "v1" on the first poll
        :param stop_threshold: poll count at which to raise
            `_StopDaemonLoop`
        :return: `fake_sleep` function to use as `time.sleep()`'s side
            effect
        """
        poll_count = {"n": 0}

        def fake_sleep(_: float) -> None:
            poll_count["n"] += 1
            fake_clock["t"] += 1.0
            if poll_count["n"] == 1:
                # Simulate the user's edit landing on the first poll.
                hio.to_file(test_file, "v1")
            if poll_count["n"] >= stop_threshold:
                raise _StopDaemonLoop

        return fake_sleep

    @contextlib.contextmanager
    def _mock_daemon_dependencies(
        self,
        fake_system: Callable[..., None],
        fake_sleep: Callable[[float], None],
        fake_time: Callable[[], float],
    ) -> Iterator[None]:
        """
        Patch `hdaemon`'s `hsystem.system()`, `time.sleep()`, and `time.time()`.

        :param fake_system: side effect for `hsystem.system()`
        :param fake_sleep: side effect for `time.sleep()`
        :param fake_time: side effect for `time.time()`
        """
        with (
            umock.patch.object(
                hdaemon.hsystem, "system", side_effect=fake_system
            ),
            umock.patch.object(hdaemon.time, "sleep", side_effect=fake_sleep),
            umock.patch.object(hdaemon.time, "time", side_effect=fake_time),
        ):
            yield

    def test1(self) -> None:
        """
        Test a plain edit: change detected, debounced, regenerated once,
        re-baselined, with hash/mtime present in the logs at every step.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "watched.smd")
        hio.to_file(test_file, "v0")
        system_cmds = []
        watch_cmd = "my_cmd"
        wait_in_sec = 0
        debounce_sec = 2

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del abort_on_error
            system_cmds.append(cmd)

        fake_clock, fake_time = self._create_fake_time_infrastructure()
        stop_threshold = 6
        fake_sleep = self._create_fake_sleep_for_daemon(
            fake_clock, test_file, stop_threshold
        )
        # Prepare outputs.
        hash_v0 = hashlib.md5(b"v0").hexdigest()[:8]
        hash_v1 = hashlib.md5(b"v1").hexdigest()[:8]
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with self._mock_daemon_dependencies(
                    fake_system, fake_sleep, fake_time
                ):
                    hdaemon._daemon_watch(
                        test_file,
                        watch_cmd,
                        wait_in_sec=wait_in_sec,
                        debounce_sec=debounce_sec,
                    )
        # Check outputs.
        log_text = "\n".join(cm.output)
        # Expected: log contains hash change, debounce, regeneration, and
        # re-baseline messages; mtime formatted as HH:MM:SS.mmm; no conflicts.
        self.assertIn(f"hash {hash_v0} -> {hash_v1}", log_text)
        self.assertIn("Debounce complete", log_text)
        self.assertIn("Regeneration complete", log_text)
        self.assertIn(f"Re-baselined: hash {hash_v1}", log_text)
        self.assertRegex(log_text, r"mtime \d{2}:\d{2}:\d{2}\.\d{3}")
        self.assertNotIn("Output NOT applied", log_text)
        # Invariant: initial run and one watch-run regenerate with unmodified
        # command (no suffix).
        expected_cmds = ["my_cmd", "my_cmd"]
        self.assertEqual(system_cmds, expected_cmds)

    def test2(self) -> None:
        """
        Test the conflict-marker path: the file changes again while the
        watch-run command is "running" (simulated), so the regenerated
        output must not be treated as settled, and a second regenerate must
        follow.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "watched.smd")
        hio.to_file(test_file, "v0")
        conflict_marker = hdaemon.get_conflict_marker_path(test_file)
        call_count = {"n": 0}
        watch_cmd = "my_cmd"
        wait_in_sec = 0
        debounce_sec = 2

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del cmd, abort_on_error
            call_count["n"] += 1
            if call_count["n"] == 2:
                # The first watch-run regenerate: simulate the watched
                # command detecting a newer edit mid-run and, instead of
                # overwriting it, touching the conflict marker (mirrors
                # `render_images.py`'s guard).
                hio.to_file(test_file, "v2-mid-run")
                hio.to_file(conflict_marker, "")

        fake_clock, fake_time = self._create_fake_time_infrastructure()
        stop_threshold = 10
        fake_sleep = self._create_fake_sleep_for_daemon(
            fake_clock, test_file, stop_threshold
        )
        # Prepare outputs.
        hash_mid_run = hashlib.md5(b"v2-mid-run").hexdigest()[:8]
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with self._mock_daemon_dependencies(
                    fake_system, fake_sleep, fake_time
                ):
                    hdaemon._daemon_watch(
                        test_file,
                        watch_cmd,
                        wait_in_sec=wait_in_sec,
                        debounce_sec=debounce_sec,
                    )
        # Check outputs.
        log_text = "\n".join(cm.output)
        # Expected: log shows conflict detection and hash of edited version.
        self.assertIn("Output NOT applied", log_text)
        self.assertIn(hash_mid_run, log_text)
        # Invariant: initial run, conflict regenerate, and second regenerate.
        expected_call_count = 3
        self.assertEqual(call_count["n"], expected_call_count)
        # Invariant: conflict marker is consumed after handling.
        self.assertFalse(os.path.exists(conflict_marker))

    def test3(self) -> None:
        """
        Test that `watch_cmd_suffix` is applied to watch runs only, not to
        the initial run.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "watched.smd")
        hio.to_file(test_file, "v0")
        system_cmds = []
        watch_cmd = "my_cmd"
        wait_in_sec = 0
        debounce_sec = 2
        watch_cmd_suffix = " --skip_action=open_pdf"

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del abort_on_error
            system_cmds.append(cmd)

        fake_clock, fake_time = self._create_fake_time_infrastructure()
        stop_threshold = 6
        fake_sleep = self._create_fake_sleep_for_daemon(
            fake_clock, test_file, stop_threshold
        )
        # Run test.
        with self.assertRaises(_StopDaemonLoop):
            with self._mock_daemon_dependencies(
                fake_system, fake_sleep, fake_time
            ):
                hdaemon._daemon_watch(
                    test_file,
                    watch_cmd,
                    wait_in_sec=wait_in_sec,
                    debounce_sec=debounce_sec,
                    watch_cmd_suffix=watch_cmd_suffix,
                )
        # Check outputs.
        self.assertEqual(
            system_cmds, ["my_cmd", "my_cmd --skip_action=open_pdf"]
        )

    def test4(self) -> None:
        """
        Test the bug this was written for: the watched command does not
        rewrite `file_path` (the default), and a real user edit lands while
        the command is "running" (simulated inside `fake_system`), with no
        conflict marker (the command has no idea `file_path` even exists).
        The edit must not be silently absorbed into the post-run baseline:
        it must trigger a second regenerate.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "watched.smd")
        hio.to_file(test_file, "v0")
        call_count = {"n": 0}
        watch_cmd = "my_cmd"
        wait_in_sec = 0
        debounce_sec = 2

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del cmd, abort_on_error
            call_count["n"] += 1
            if call_count["n"] == 2:
                # The first watch-run regenerate: simulate the user's edit
                # landing mid-run. Unlike test2, the command never touches
                # `file_path` and so never raises the conflict marker.
                hio.to_file(test_file, "v2-during-run")

        fake_clock, fake_time = self._create_fake_time_infrastructure()
        stop_threshold = 10
        fake_sleep = self._create_fake_sleep_for_daemon(
            fake_clock, test_file, stop_threshold
        )
        # Prepare outputs.
        hash_during_run = hashlib.md5(b"v2-during-run").hexdigest()[:8]
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with self._mock_daemon_dependencies(
                    fake_system, fake_sleep, fake_time
                ):
                    hdaemon._daemon_watch(
                        test_file,
                        watch_cmd,
                        wait_in_sec=wait_in_sec,
                        debounce_sec=debounce_sec,
                    )
        # Check outputs.
        log_text = "\n".join(cm.output)
        # Expected: log shows file not rewritten in place, hash of mid-run edit,
        # no conflict message, and triggers second regenerate.
        self.assertIn("does not rewrite it in place", log_text)
        self.assertIn(hash_during_run, log_text)
        self.assertNotIn("Output NOT applied", log_text)
        # Invariant: initial run, missed edit regenerate, and second regenerate.
        expected_call_count = 3
        self.assertEqual(call_count["n"], expected_call_count)

    def test5(self) -> None:
        """
        Test the `rewrites_file_in_place=True` opt-out: the watched command
        rewrites `file_path` itself on every run (e.g., `render_images.py`
        invoked from `run_typst.py`), so the resulting hash change must be
        trusted as that self-rewrite and treated as settled, not as a new
        edit, since no conflict marker was raised.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "watched.typ")
        hio.to_file(test_file, "v0")
        call_count = {"n": 0}

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del cmd, abort_on_error
            call_count["n"] += 1
            if call_count["n"] == 2:
                # Simulate the command rewriting its own input in place.
                hio.to_file(test_file, "v1-rewritten")

        fake_clock, fake_time = self._create_fake_time_infrastructure()
        stop_threshold = 10
        fake_sleep = self._create_fake_sleep_for_daemon(
            fake_clock, test_file, stop_threshold
        )
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with self._mock_daemon_dependencies(
                    fake_system, fake_sleep, fake_time
                ):
                    hdaemon._daemon_watch(
                        test_file,
                        "my_cmd",
                        wait_in_sec=0,
                        debounce_sec=2,
                        rewrites_file_in_place=True,
                    )
        # Check outputs.
        log_text = "\n".join(cm.output)
        # Expected: log shows only trusted self-rewrite, no conflict or edit
        # detection messages.
        self.assertNotIn("does not rewrite it in place", log_text)
        self.assertNotIn("Output NOT applied", log_text)
        # Invariant: only initial run and one regenerate when file is
        # rewritten in place; self-rewrite is trusted.
        expected_call_count = 2
        self.assertEqual(call_count["n"], expected_call_count)
