#!/usr/bin/env python
"""
Unit tests for hdaemon.py.

Tests utility functions for file operations and hashing.
"""

import hashlib
import logging
import os
import time
import unittest.mock as umock

import helpers.hdaemon as hdaemon
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class _StopDaemonLoop(Exception):
    """
    Sentinel raised from a mocked `time.sleep()` to break out of
    `_daemon_watch()`'s `while True` after a bounded number of polls.
    """


# #############################################################################
# Test__file_hash
# #############################################################################


# TODO(ai_gp): Test public-facing behavior instead of private `_file_hash()`
# implementation; interface-level tests survive refactors
# (testing.rules.md:## Test From the Outside-In)
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
        # Run test.
        hash1 = hdaemon._file_hash(file1)
        hash2 = hdaemon._file_hash(file2)
        # TODO(ai_gp): Move expected_hash1 and expected_hash2 calculation to
        # "Prepare outputs" section before "Run test" to consolidate input/output
        # variables (testing.rules.md:## Consolidate Inputs and Outputs)
        # Check outputs.
        expected_hash1 = hashlib.md5(content1.encode()).hexdigest()
        expected_hash2 = hashlib.md5(content2.encode()).hexdigest()
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


# TODO(ai_gp): Test public-facing behavior instead of private `_fmt_mtime()`
# implementation; interface-level tests survive refactors
# (testing.rules.md:## Test From the Outside-In)
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
        # Run test.
        actual = hdaemon._fmt_mtime(mtime)
        # TODO(ai_gp): Move expected value calculation to "Prepare outputs"
        # section before "Run test" to consolidate input/output variables
        # (testing.rules.md:## Consolidate Inputs and Outputs)
        # Check outputs.
        expected = (
            time.strftime("%H:%M:%S", time.localtime(mtime)) + ".500"
        )
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a whole-second mtime gets ".000".
        """
        # Prepare inputs.
        mtime = 1700000000.0
        # Run test.
        actual = hdaemon._fmt_mtime(mtime)
        # Check outputs.
        self.assertTrue(actual.endswith(".000"))

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


# TODO(ai_gp): Test public-facing behavior instead of private `_daemon_watch()`
# implementation; interface-level tests survive refactors
# (testing.rules.md:## Test From the Outside-In)
class Test__daemon_watch(hunitest.TestCase):
    # TODO(ai_gp): Test class docstring should only document what is being
    # tested, not how or why; remove implementation details about mocking and
    # state machine (testing.rules.md:## Test Class Documentation)
    """
    Test `_daemon_watch()`'s poll / debounce / regenerate state machine and
    its debug logging, by mocking `time.sleep()`, `time.time()`, and
    `hsystem.system()` (the only external dependencies) so the `while True`
    loop runs deterministically and stops after a bounded number of polls.
    """

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
        # TODO(ai_gp): Move hash_v0 and hash_v1 computation to "Prepare
        # outputs" section; they are expected values used in assertions
        # (testing.rules.md:## Use Three Sections in Testing Methods)
        hash_v0 = hashlib.md5(b"v0").hexdigest()[:8]
        hash_v1 = hashlib.md5(b"v1").hexdigest()[:8]

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del abort_on_error
            system_cmds.append(cmd)

        fake_clock = {"t": 0.0}

        def fake_time() -> float:
            return fake_clock["t"]

        poll_count = {"n": 0}

        def fake_sleep(_: float) -> None:
            poll_count["n"] += 1
            fake_clock["t"] += 1.0
            if poll_count["n"] == 1:
                # Simulate the user's edit landing on the first poll.
                hio.to_file(test_file, "v1")
            if poll_count["n"] >= 6:
                raise _StopDaemonLoop
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with (
                    umock.patch.object(
                        hdaemon.hsystem, "system", side_effect=fake_system
                    ),
                    umock.patch.object(
                        hdaemon.time, "sleep", side_effect=fake_sleep
                    ),
                    umock.patch.object(
                        hdaemon.time, "time", side_effect=fake_time
                    ),
                ):
                    # TODO(ai_gp): Assign "my_cmd", 0, 2 to variables before
                    # calling _daemon_watch (testing.rules.md:## Assign Variables
                    # and Then Call Functions)
                    hdaemon._daemon_watch(
                        test_file,
                        "my_cmd",
                        wait_in_sec=0,
                        debounce_sec=2,
                    )
        # Check outputs.
        log_text = "\n".join(cm.output)
        # TODO(ai_gp): Use assert_equal() to compare whole log output instead
        # of multiple assertIn/assertRegex/assertNotIn calls; convert output
        # to string and compare with expected value
        # (testing.rules.md:## Compare Whole Output with assert_equal)
        # The initial run and one watch-run regenerate, both with the
        # unmodified command (no `watch_cmd_suffix` was given).
        self.assertEqual(system_cmds, ["my_cmd", "my_cmd"])
        # The change, debounce-complete, and re-baseline messages all carry
        # hash and a "HH:MM:SS.mmm" mtime.
        self.assertIn(f"hash {hash_v0} -> {hash_v1}", log_text)
        self.assertIn("Debounce complete", log_text)
        self.assertIn("Regeneration complete", log_text)
        self.assertIn(f"Re-baselined: hash {hash_v1}", log_text)
        self.assertRegex(log_text, r"mtime \d{2}:\d{2}:\d{2}\.\d{3}")
        # A conflict was never signaled, so no "not applied" message.
        self.assertNotIn("Output NOT applied", log_text)

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
        # TODO(ai_gp): Move hash_mid_run computation to "Prepare outputs"
        # section; it is an expected value used in assertions
        # (testing.rules.md:## Use Three Sections in Testing Methods)
        hash_mid_run = hashlib.md5(b"v2-mid-run").hexdigest()[:8]

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

        fake_clock = {"t": 0.0}

        def fake_time() -> float:
            return fake_clock["t"]

        poll_count = {"n": 0}

        def fake_sleep(_: float) -> None:
            poll_count["n"] += 1
            fake_clock["t"] += 1.0
            if poll_count["n"] == 1:
                hio.to_file(test_file, "v1")
            if poll_count["n"] >= 10:
                raise _StopDaemonLoop
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with (
                    umock.patch.object(
                        hdaemon.hsystem, "system", side_effect=fake_system
                    ),
                    umock.patch.object(
                        hdaemon.time, "sleep", side_effect=fake_sleep
                    ),
                    umock.patch.object(
                        hdaemon.time, "time", side_effect=fake_time
                    ),
                ):
                    # TODO(ai_gp): Assign "my_cmd", 0, 2 to variables before
                    # calling _daemon_watch (testing.rules.md:## Assign Variables
                    # and Then Call Functions)
                    hdaemon._daemon_watch(
                        test_file,
                        "my_cmd",
                        wait_in_sec=0,
                        debounce_sec=2,
                    )
        # Check outputs.
        log_text = "\n".join(cm.output)
        # TODO(ai_gp): Use assert_equal() to compare whole log output instead
        # of multiple assertIn calls; convert output to string and compare with
        # expected value (testing.rules.md:## Compare Whole Output with
        # assert_equal)
        self.assertIn("Output NOT applied", log_text)
        self.assertIn(hash_mid_run, log_text)
        # Initial run, the regenerate that hit the conflict, and a second
        # regenerate that finally settles.
        self.assertEqual(call_count["n"], 3)
        # The conflict marker is consumed (removed) once handled.
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

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del abort_on_error
            system_cmds.append(cmd)

        fake_clock = {"t": 0.0}

        def fake_time() -> float:
            return fake_clock["t"]

        poll_count = {"n": 0}

        def fake_sleep(_: float) -> None:
            poll_count["n"] += 1
            fake_clock["t"] += 1.0
            if poll_count["n"] == 1:
                hio.to_file(test_file, "v1")
            if poll_count["n"] >= 6:
                raise _StopDaemonLoop
        # Run test.
        with self.assertRaises(_StopDaemonLoop):
            with (
                umock.patch.object(
                    hdaemon.hsystem, "system", side_effect=fake_system
                ),
                umock.patch.object(
                    hdaemon.time, "sleep", side_effect=fake_sleep
                ),
                umock.patch.object(hdaemon.time, "time", side_effect=fake_time),
            ):
                # TODO(ai_gp): Assign "my_cmd", 0, 2,
                # " --skip_action=open_pdf" to variables before calling
                # _daemon_watch (testing.rules.md:## Assign Variables and Then
                # Call Functions)
                hdaemon._daemon_watch(
                    test_file,
                    "my_cmd",
                    wait_in_sec=0,
                    debounce_sec=2,
                    watch_cmd_suffix=" --skip_action=open_pdf",
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
        # TODO(ai_gp): Move hash_during_run computation to "Prepare outputs"
        # section; it is an expected value used in assertions
        # (testing.rules.md:## Use Three Sections in Testing Methods)
        hash_during_run = hashlib.md5(b"v2-during-run").hexdigest()[:8]

        def fake_system(cmd: str, abort_on_error: bool = True) -> None:
            del cmd, abort_on_error
            call_count["n"] += 1
            if call_count["n"] == 2:
                # The first watch-run regenerate: simulate the user's edit
                # landing mid-run. Unlike test2, the command never touches
                # `file_path` and so never raises the conflict marker.
                hio.to_file(test_file, "v2-during-run")

        fake_clock = {"t": 0.0}

        def fake_time() -> float:
            return fake_clock["t"]

        poll_count = {"n": 0}

        def fake_sleep(_: float) -> None:
            poll_count["n"] += 1
            fake_clock["t"] += 1.0
            if poll_count["n"] == 1:
                hio.to_file(test_file, "v1")
            if poll_count["n"] >= 10:
                raise _StopDaemonLoop
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with (
                    umock.patch.object(
                        hdaemon.hsystem, "system", side_effect=fake_system
                    ),
                    umock.patch.object(
                        hdaemon.time, "sleep", side_effect=fake_sleep
                    ),
                    umock.patch.object(
                        hdaemon.time, "time", side_effect=fake_time
                    ),
                ):
                    # TODO(ai_gp): Assign "my_cmd", 0, 2 to variables before
                    # calling _daemon_watch (testing.rules.md:## Assign Variables
                    # and Then Call Functions)
                    hdaemon._daemon_watch(
                        test_file,
                        "my_cmd",
                        wait_in_sec=0,
                        debounce_sec=2,
                    )
        # Check outputs.
        log_text = "\n".join(cm.output)
        # TODO(ai_gp): Use assert_equal() to compare whole log output instead
        # of multiple assertIn/assertNotIn calls; convert output to string and
        # compare with expected value (testing.rules.md:## Compare Whole Output
        # with assert_equal)
        self.assertIn("does not rewrite it in place", log_text)
        self.assertIn(hash_during_run, log_text)
        # Initial run, the regenerate that missed the mid-run edit, and a
        # second regenerate that finally picks it up.
        self.assertEqual(call_count["n"], 3)
        # No conflict marker was ever involved in this path.
        self.assertNotIn("Output NOT applied", log_text)

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

        fake_clock = {"t": 0.0}

        def fake_time() -> float:
            return fake_clock["t"]

        poll_count = {"n": 0}

        def fake_sleep(_: float) -> None:
            poll_count["n"] += 1
            fake_clock["t"] += 1.0
            if poll_count["n"] == 1:
                hio.to_file(test_file, "v1")
            if poll_count["n"] >= 10:
                raise _StopDaemonLoop
        # Run test.
        with self.assertLogs("helpers.hdaemon", level="DEBUG") as cm:
            with self.assertRaises(_StopDaemonLoop):
                with (
                    umock.patch.object(
                        hdaemon.hsystem, "system", side_effect=fake_system
                    ),
                    umock.patch.object(
                        hdaemon.time, "sleep", side_effect=fake_sleep
                    ),
                    umock.patch.object(
                        hdaemon.time, "time", side_effect=fake_time
                    ),
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
        # TODO(ai_gp): Use assert_equal() to compare whole log output instead
        # of multiple assertNotIn calls; convert output to string and compare
        # with expected value (testing.rules.md:## Compare Whole Output with
        # assert_equal)
        self.assertNotIn("does not rewrite it in place", log_text)
        self.assertNotIn("Output NOT applied", log_text)
        # Only the initial run and the one regenerate: the self-rewrite was
        # trusted and never re-triggered a second regenerate.
        self.assertEqual(call_count["n"], 2)
