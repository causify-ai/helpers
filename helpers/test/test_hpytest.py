import os
import pprint
from typing import Any, Dict

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hpytest as hpytest
import helpers.hunit_test as hunitest


# #############################################################################
# Test__parse_github_ci_log
# #############################################################################


class Test__parse_github_ci_log(hunitest.TestCase):
    def helper(self, txt: str, exp_info: str, exp_log: str) -> None:
        txt = hprint.dedent(txt)
        lines = txt.split("\n")
        act_info, act_log_lines = hpytest._parse_github_ci_log(lines)
        act_info_as_str = "\n".join(
            f"{k}={v}" for k, v in sorted(act_info.items())
        )
        self.assert_equal(
            act_info_as_str,
            exp_info,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )
        act_log = "\n".join(act_log_lines)
        self.assert_equal(
            act_log,
            exp_log,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )

    def test1(self) -> None:
        # Prepare inputs and outputs.
        txt = (
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:35.1181332Z Current runner version: '2.335.1'\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T18:04:49.3717677Z Post job cleanup.\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T18:04:49.6516170Z Cleaning up orphan processes\n"
        )
        exp_info = """
        github_completed=True
        github_end_timestamp=2026-07-06T18:04:49.6516170Z
        github_start_timestamp=2026-07-06T17:59:35.1181332Z
        github_tag=run_fast_tests
        """
        exp_log = """
        Current runner version: '2.335.1'
        Post job cleanup.
        Cleaning up orphan processes
        """
        # Check.
        self.helper(txt, exp_info, exp_log)

    def test2(self) -> None:
        # Prepare inputs and outputs.
        txt = (
            "run_slow_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:35.1181332Z ##[group]Run tests\n"
            "run_slow_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T18:04:49.3717677Z ##[error]Process completed\n"
        )
        exp_info = """
        github_completed=False
        github_end_timestamp=2026-07-06T18:04:49.3717677Z
        github_start_timestamp=2026-07-06T17:59:35.1181332Z
        github_tag=run_slow_tests
        """
        exp_log = """
        ##[group]Run tests
        ##[error]Process completed
        """
        # Check.
        self.helper(txt, exp_info, exp_log)

    def test3(self) -> None:
        # Prepare inputs and outputs: first line has a leading BOM before the timestamp.
        txt = (
            "run_fast_tests / run_tests\tUNKNOWN STEP\t﻿"
            "2026-07-06T17:59:35.1143554Z Current runner version: '2.335.1'\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:35.1181332Z ##[group]Runner Image\n"
        )
        exp_info = """
        github_completed=False
        github_end_timestamp=2026-07-06T17:59:35.1181332Z
        github_start_timestamp=2026-07-06T17:59:35.1143554Z
        github_tag=run_fast_tests
        """
        exp_log = """
        Current runner version: '2.335.1'
        ##[group]Runner Image
        """
        # Check.
        self.helper(txt, exp_info, exp_log)


# #############################################################################
# Test_parse_failed_tests
# #############################################################################


class Test_parse_failed_tests(hunitest.TestCase):
    def get_pytest_text1(self) -> str:
        txt = """
        20:48:15 - ^[[36mINFO ^[[0m hdbg.py init_logger:1018                               > cmd='/venv/bin/pytest helpers_root/dev_scripts_helpers/documentation/'
        collected 47 items

        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1 (2.07 s) FAILED [  2%]
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1 (0.00 s) PASSED [  4%]
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2 (0.00 s) PASSED [  6%]
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3 (0.00 s) PASSED [  8%]


        =================================== FAILURES ===================================
        _________________________ Test_preprocess_notes1.test1 _________________________

        FAILED helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3::test_run_all1 - AttributeError: 'list' object has no attribute 'split'
        FAILED helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2 - RuntimeError: cmd='(/app/helpers_root/dev_scripts_helpers/documentation/notes_to_pdf.py --input /app/helpers_root/dev_scripts_helpers/documentation/test/outcomes/Test_notes

        ======================== 4 failed, 43 passed in 40.48s =========================
        """
        txt = hprint.dedent(txt)
        return txt

    def helper(
        self,
        txt: str,
        exp_info: str,
    ) -> None:
        txt = hprint.dedent(txt)
        lines = txt.split("\n")
        act_info = hpytest.parse_failed_tests(lines)
        act_info_as_str = "\n".join(
            f"{k}={v}" for k, v in sorted(act_info.items())
        )
        self.assert_equal(
            act_info_as_str,
            exp_info,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )

    def test1(self) -> None:
        # Prepare inputs and outputs.
        txt = self.get_pytest_text1()
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3::test_run_all1']
        log_num_failed=3
        log_num_failed_classes=3
        log_num_failed_files=2
        log_num_passed=3
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3']
        log_skipped_tests=[]
        log_test_durations={'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1': 2.07, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1': 0.0, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2': 0.0, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_num_collected=47
        pytest_num_deselected=None
        pytest_num_failed=4
        pytest_num_passed=43
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, exp_info)

    def test2(self) -> None:
        # Prepare inputs and outputs (now filters are done by callers).
        txt = self.get_pytest_text1()
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3::test_run_all1']
        log_num_failed=3
        log_num_failed_classes=3
        log_num_failed_files=2
        log_num_passed=3
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3']
        log_skipped_tests=[]
        log_test_durations={'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1': 2.07, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1': 0.0, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2': 0.0, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_num_collected=47
        pytest_num_deselected=None
        pytest_num_failed=4
        pytest_num_passed=43
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, exp_info)
        # Test filtering by file.
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        filtered_files = hpytest.filter_failed_tests(
            info["log_failed_tests"], only_file=True, only_class=False
        )
        actual_str = "\n".join(filtered_files)
        expected_str = """
        helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py
        """
        self.assert_equal(actual_str, expected_str, dedent=True)

    def test3(self) -> None:
        # Prepare inputs and outputs (now filters are done by callers).
        txt = self.get_pytest_text1()
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3::test_run_all1']
        log_num_failed=3
        log_num_failed_classes=3
        log_num_failed_files=2
        log_num_passed=3
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3']
        log_skipped_tests=[]
        log_test_durations={'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1': 2.07, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1': 0.0, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2': 0.0, 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_num_collected=47
        pytest_num_deselected=None
        pytest_num_failed=4
        pytest_num_passed=43
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, exp_info)
        # Test filtering by class.
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        filtered_classes = hpytest.filter_failed_tests(
            info["log_failed_tests"], only_file=False, only_class=True
        )
        actual_str = "\n".join(filtered_classes)
        expected_str = """
        helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3
        """
        self.assert_equal(actual_str, expected_str, dedent=True)

    def test4(self) -> None:
        """
        Test the status dict when pytest never started (e.g., a Docker image
        pull failure before pytest runs).
        """
        # Prepare inputs.
        txt = """
        Traceback (most recent call last):
          File "invoke", line 8, in <module>
            sys.exit(program.run())
        RuntimeError: _system() failed
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=0
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=[]
        log_skipped_tests=[]
        log_test_durations={}
        log_updated_tests=[]
        pytest_collection_completed=False
        pytest_duration_in_secs=None
        pytest_ended=False
        pytest_num_collected=None
        pytest_num_deselected=None
        pytest_num_failed=None
        pytest_num_passed=None
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, exp_info)

    def test5(self) -> None:
        """
        Test the status dict when pytest started and collected tests but did
        not print the final summary (e.g., the run was killed mid-way).
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 3421 items / 5 skipped

        test_foo.py::Test_foo1::test1 (0.00 s) PASSED [ 0%]
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=1
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=['test_foo.py::Test_foo1::test1']
        log_skipped_tests=[]
        log_test_durations={'test_foo.py::Test_foo1::test1': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=None
        pytest_ended=False
        pytest_num_collected=3421
        pytest_num_deselected=None
        pytest_num_failed=None
        pytest_num_passed=None
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=5
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test6(self) -> None:
        """
        Test the status dict when pytest started, collected, and printed the
        final summary line, including ANSI color codes and a skipped count.
        """
        # Prepare inputs.
        txt = (
            "\x1b[1m============================= test session starts =====\x1b[0m\n"
            "platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python\n"
            "collected 3361 items / 156 deselected / 7 skipped / 3205 selected\n"
            "\n"
            "\x1b[31m=========== \x1b[1m34 failed\x1b[0m, \x1b[32m3157 passed\x1b[0m, "
            "\x1b[33m235 skipped\x1b[0m\x1b[31m in 886.58s (0:14:46)\x1b[0m\x1b[31m ===========\x1b[0m\n"
        )
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=0
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=[]
        log_skipped_tests=[]
        log_test_durations={}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=886.58
        pytest_ended=True
        pytest_num_collected=3361
        pytest_num_deselected=156
        pytest_num_failed=34
        pytest_num_passed=3157
        pytest_num_selected=3205
        pytest_num_skipped=235
        pytest_num_skipped_at_collection=7
        pytest_started=True
        pytest_tag=platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python
        """
        # Check.
        self.helper(txt, exp_info)

    def test7(self) -> None:
        """
        Test a verbose PASSED line with no duration, e.g., a plain
        module-level function test that pytest doesn't time.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 2 items

        test_foo.py::test1 (0.00 s) PASSED [ 50%]
        test_foo.py::test_function PASSED                [100%]

        ======================== 0 failed, 2 passed in 0.01s =========================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=2
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=['test_foo.py::test1', 'test_foo.py::test_function']
        log_skipped_tests=[]
        log_test_durations={'test_foo.py::test1': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=0.01
        pytest_ended=True
        pytest_num_collected=2
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=2
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test8(self) -> None:
        """
        Test a verbose PASSED line with a golden-file "(WARNING: Test was
        updated)" annotation inserted between the duration and the status.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 1 items

        test_foo.py::Test1::test_check_string_missing3 (0.13 s) (WARNING: Test was updated) PASSED [100%]

        ======================== 0 failed, 1 passed in 0.13s =========================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=1
        log_num_skipped=0
        log_num_updated=1
        log_passed_tests=['test_foo.py::Test1::test_check_string_missing3']
        log_skipped_tests=[]
        log_test_durations={'test_foo.py::Test1::test_check_string_missing3': 0.13}
        log_updated_tests=['test_foo.py::Test1::test_check_string_missing3']
        pytest_collection_completed=True
        pytest_duration_in_secs=0.13
        pytest_ended=True
        pytest_num_collected=1
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=1
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test9(self) -> None:
        """
        Test a PASSED status whose duration/status is glued (no separating
        space) to a golden-file "WARNING: ..." message printed by the test
        itself, so the node id ends up alone on the preceding line.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 1 items

        test_foo.py::Test1::test_check_df_missing3
        WARNING: Update golden outcome file '/some/path/test_df.txt'(0.11 s) (WARNING: Test was updated) PASSED [100%]

        ======================== 0 failed, 1 passed in 0.11s =========================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=1
        log_num_skipped=0
        log_num_updated=1
        log_passed_tests=['test_foo.py::Test1::test_check_df_missing3']
        log_skipped_tests=[]
        log_test_durations={}
        log_updated_tests=['test_foo.py::Test1::test_check_df_missing3']
        pytest_collection_completed=True
        pytest_duration_in_secs=0.11
        pytest_ended=True
        pytest_num_collected=1
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=1
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test10(self) -> None:
        """
        Test that skips are counted from the "short test summary info"
        aggregate `SKIPPED [N] ...` lines, which is the only source that
        accounts for `@pytest.mark.skip`/`skipif` tests (never run, so no
        per-test verbose line), and that a skip reported both inline and
        in the summary (a "live" `pytest.skip()` call) isn't double-counted.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 8 items

        test_foo.py::Test1::test_live_skip (0.00 s) SKIPPED [ 33%]
        test_foo.py::Test1::test2 (0.00 s) PASSED [ 66%]
        test_foo.py::Test1::test3 (0.00 s) PASSED [100%]

        =========================== short test summary info ============================
        SKIPPED [1] test_foo.py:10: decorator skip reason
        SKIPPED [1] test_foo.py:20: live skip reason
        SKIPPED [4] test_foo.py:30: parametrized skip reason

        ======================== 0 failed, 2 passed, 6 skipped in 0.01s =========================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=2
        log_num_skipped=6
        log_num_updated=0
        log_passed_tests=['test_foo.py::Test1::test2', 'test_foo.py::Test1::test3']
        log_skipped_tests=['test_foo.py:10:decorator skip reason#0', 'test_foo.py:20:live skip reason#0', 'test_foo.py:30:parametrized skip reason#0', 'test_foo.py:30:parametrized skip reason#1', 'test_foo.py:30:parametrized skip reason#2', 'test_foo.py:30:parametrized skip reason#3']
        log_test_durations={'test_foo.py::Test1::test_live_skip': 0.0, 'test_foo.py::Test1::test2': 0.0, 'test_foo.py::Test1::test3': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=0.01
        pytest_ended=True
        pytest_num_collected=8
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=2
        pytest_num_selected=None
        pytest_num_skipped=6
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test11(self) -> None:
        """
        Test that a "slowest N durations" summary section (printed with
        `pytest --durations`) is not mistaken for per-test result lines,
        e.g.,
        ```
        146.56s call     helpers/test/test_amp_dev_scripts.py::Test_env1::test_get_system_signature1
        ```
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 3 items

        test_foo.py::Test1::test1 (0.01 s) PASSED [ 33%]
        test_foo.py::Test1::test2 (0.02 s) PASSED [ 66%]
        test_foo.py::Test1::test3 (0.03 s) PASSED [100%]

        ============================= slowest 3 durations ==============================
        146.56s call     helpers/test/test_amp_dev_scripts.py::Test_env1::test_get_system_signature1
        146.36s call     helpers/test/test_henv.py::Test_env1::test_get_system_signature1
        146.22s call     helpers/test/test_hserver.py::Test_hserver_outside_docker_container_on_gp_mac1::test_get_docker_info1

        ======================== 0 failed, 3 passed in 0.06s =========================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=3
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=['test_foo.py::Test1::test1', 'test_foo.py::Test1::test2', 'test_foo.py::Test1::test3']
        log_skipped_tests=[]
        log_test_durations={'test_foo.py::Test1::test1': 0.01, 'test_foo.py::Test1::test2': 0.02, 'test_foo.py::Test1::test3': 0.03}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=0.06
        pytest_ended=True
        pytest_num_collected=3
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=3
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test12(self) -> None:
        """
        Test a live, ANSI-colored run that is killed mid-test (e.g., a CI
        timeout), so the last test id is printed alone with no trailing
        status and never gets resolved, and no final summary line is
        printed.
        """
        # Prepare inputs.
        txt = (
            "\x1b[1m============================= test session starts "
            "==============================\x1b[0m\n"
            "platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 "
            "-- /venv/bin/python3\n"
            "collected 3421 items / 5 skipped\n"
            "\n"
            "test_foo.py::Test1::test1 (0.00 s) \x1b[32mPASSED\x1b[0m"
            "\x1b[32m [ 0%]\x1b[0m\n"
            "test_foo.py::Test2::test_run_fast_tests4 \x1b[33mSKIPPED\x1b[0m"
            "\x1b[31m [ 30%]\x1b[0m\n"
            "test_foo.py::Test3::test_get_system_signature1"
        )
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=1
        log_num_skipped=1
        log_num_updated=0
        log_passed_tests=['test_foo.py::Test1::test1']
        log_skipped_tests=['test_foo.py::Test2::test_run_fast_tests4']
        log_test_durations={'test_foo.py::Test1::test1': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=None
        pytest_ended=False
        pytest_num_collected=3421
        pytest_num_deselected=None
        pytest_num_failed=None
        pytest_num_passed=None
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=5
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check. Note: the truncated `test_get_system_signature1` id is
        # never resolved to a status, so it is dropped rather than counted.
        self.helper(txt, exp_info)

    def test13(self) -> None:
        """
        Test a full GitHub Actions CI log parsed end to end via
        `parse_failed_tests()`, including the "short test summary info"
        skip section and a final summary line with "deselected" and
        "rerun" counts alongside "failed"/"passed"/"skipped".
        """
        # Prepare inputs.
        txt = (
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:35.1181332Z Current runner version: '2.335.1'\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:36.0000000Z ============================= test session starts ==============================\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:37.0000000Z platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:38.0000000Z collected 5 items / 1 deselected / 4 selected\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:39.0000000Z test_foo.py::Test1::test1 (0.01 s) PASSED [ 25%]\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:40.0000000Z test_foo.py::Test1::test2 (0.02 s) PASSED [ 50%]\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:41.0000000Z FAILED test_foo.py::Test2::test3 - RuntimeError:\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:42.0000000Z =========================== short test summary info ============================\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:43.0000000Z SKIPPED [1] test_foo.py:10: could not import 'openai': No module named 'openai'\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:44.0000000Z = 1 failed, 2 passed, 1 skipped, 1 deselected, 1 rerun in 10.00s (0:00:10) =\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:45.0000000Z Post job cleanup.\n"
        )
        # Prepare outputs.
        exp_info = """
        github_completed=True
        github_end_timestamp=2026-07-06T17:59:45.0000000Z
        github_start_timestamp=2026-07-06T17:59:35.1181332Z
        github_tag=run_fast_tests
        log_failed_tests=['test_foo.py::Test2::test3']
        log_num_failed=1
        log_num_failed_classes=1
        log_num_failed_files=1
        log_num_passed=2
        log_num_skipped=1
        log_num_updated=0
        log_passed_tests=['test_foo.py::Test1::test1', 'test_foo.py::Test1::test2']
        log_skipped_tests=["test_foo.py:10:could not import 'openai': No module named 'openai'#0"]
        log_test_durations={'test_foo.py::Test1::test1': 0.01, 'test_foo.py::Test1::test2': 0.02}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=10.0
        pytest_ended=True
        pytest_num_collected=5
        pytest_num_deselected=1
        pytest_num_failed=1
        pytest_num_passed=2
        pytest_num_selected=4
        pytest_num_skipped=1
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python
        """
        # Check.
        self.helper(txt, exp_info)

    def test14(self) -> None:
        """
        Test a full GitHub Actions CI log parsed end to end via
        `parse_failed_tests()`, same as `test13()` but with every
        PASSED/FAILED/SKIPPED tag and the final summary line wrapped in
        ANSI color codes rendered as visible caret notation (e.g.,
        "^[[32mPASSED^[[0m") instead of a real ESC byte, as seen in some
        captured GitHub Actions logs. The result should be identical to
        `test13()`'s, since the caret-notation color codes should be
        stripped just like real ESC-based ones.
        """
        # Prepare inputs.
        txt = (
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:35.1181332Z Current runner version: '2.335.1'\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:36.0000000Z ^[[1m============================= test session starts ==============================^[[0m\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:37.0000000Z platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:38.0000000Z collected 5 items / 1 deselected / 4 selected\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:39.0000000Z test_foo.py::Test1::test1 (0.01 s) ^[[32mPASSED^[[0m^[[32m [ 25%]^[[0m\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:40.0000000Z test_foo.py::Test1::test2 (0.02 s) ^[[32mPASSED^[[0m^[[32m [ 50%]^[[0m\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:41.0000000Z ^[[31mFAILED^[[0m test_foo.py::^[[1mTest2::test3^[[0m - RuntimeError:\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:42.0000000Z =========================== short test summary info ============================\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:43.0000000Z SKIPPED [1] test_foo.py:10: could not import 'openai': No module named 'openai'\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:44.0000000Z ^[[31m= ^[[31m^[[1m1 failed^[[0m, ^[[32m2 passed^[[0m, ^[[33m1 skipped^[[0m, ^[[33m1 deselected^[[0m, ^[[33m1 rerun^[[0m^[[31m in 10.00s (0:00:10)^[[0m^[[31m =^[[0m\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:45.0000000Z Post job cleanup.\n"
        )
        # Prepare outputs.
        exp_info = """
        github_completed=True
        github_end_timestamp=2026-07-06T17:59:45.0000000Z
        github_start_timestamp=2026-07-06T17:59:35.1181332Z
        github_tag=run_fast_tests
        log_failed_tests=['test_foo.py::Test2::test3']
        log_num_failed=1
        log_num_failed_classes=1
        log_num_failed_files=1
        log_num_passed=2
        log_num_skipped=1
        log_num_updated=0
        log_passed_tests=['test_foo.py::Test1::test1', 'test_foo.py::Test1::test2']
        log_skipped_tests=["test_foo.py:10:could not import 'openai': No module named 'openai'#0"]
        log_test_durations={'test_foo.py::Test1::test1': 0.01, 'test_foo.py::Test1::test2': 0.02}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=10.0
        pytest_ended=True
        pytest_num_collected=5
        pytest_num_deselected=1
        pytest_num_failed=1
        pytest_num_passed=2
        pytest_num_selected=4
        pytest_num_skipped=1
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python
        """
        # Check.
        self.helper(txt, exp_info)

    def test15(self) -> None:
        """
        Test the final summary line for an all-passing run, e.g.:
        ```
        ============================== 3 passed in 0.05s ===============================
        ```
        Pytest omits categories with a zero count, so a clean run's summary
        has no "0 failed," prefix at all. `pytest_ended` and
        `pytest_num_failed`/`pytest_num_passed` must still be set (with
        `pytest_num_failed` defaulting to 0), not left as if the summary
        line was never printed.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 3 items

        test_foo.py::Test1::test1 (0.00 s) PASSED [ 33%]
        test_foo.py::Test1::test2 (0.00 s) PASSED [ 66%]
        test_foo.py::Test1::test3 (0.00 s) PASSED [100%]

        ============================== 3 passed in 0.05s ===============================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=3
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=['test_foo.py::Test1::test1', 'test_foo.py::Test1::test2', 'test_foo.py::Test1::test3']
        log_skipped_tests=[]
        log_test_durations={'test_foo.py::Test1::test1': 0.0, 'test_foo.py::Test1::test2': 0.0, 'test_foo.py::Test1::test3': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=0.05
        pytest_ended=True
        pytest_num_collected=3
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=3
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test16(self) -> None:
        """
        Test the final summary line for an all-failing run, e.g.:
        ```
        ============================== 3 failed in 0.05s ===============================
        ```
        Pytest omits the "passed" category entirely when nothing passed, so
        `pytest_num_passed` must default to 0 rather than staying unset.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 3 items

        test_foo.py::Test1::test1 (0.00 s) FAILED [ 33%]
        test_foo.py::Test1::test2 (0.00 s) FAILED [ 66%]
        test_foo.py::Test1::test3 (0.00 s) FAILED [100%]

        ============================== 3 failed in 0.05s ===============================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=['test_foo.py::Test1::test1', 'test_foo.py::Test1::test2', 'test_foo.py::Test1::test3']
        log_num_failed=3
        log_num_failed_classes=1
        log_num_failed_files=1
        log_num_passed=0
        log_num_skipped=0
        log_num_updated=0
        log_passed_tests=[]
        log_skipped_tests=[]
        log_test_durations={'test_foo.py::Test1::test1': 0.0, 'test_foo.py::Test1::test2': 0.0, 'test_foo.py::Test1::test3': 0.0}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=0.05
        pytest_ended=True
        pytest_num_collected=3
        pytest_num_deselected=None
        pytest_num_failed=3
        pytest_num_passed=0
        pytest_num_selected=None
        pytest_num_skipped=None
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test17(self) -> None:
        """
        Test that two distinct "short test summary info" skip groups sharing
        the same file:line but different reasons aren't merged into one.

        This is a regression test for a real-world case (pytest attributing
        two different `skipif` conditions to the same reported line):
        ```
        SKIPPED [2] test_foo.py:15: mdformat package not installed
        SKIPPED [3] test_foo.py:15: flowmark package not installed
        ```
        Before the fix, both lines built the same synthetic keys (the
        reason was dropped whenever a line number was present), so the
        second line's counts collided with and were absorbed by the
        first's after dedup, undercounting 5 skips as 3.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 5 items

        =========================== short test summary info ============================
        SKIPPED [2] test_foo.py:15: mdformat package not installed
        SKIPPED [3] test_foo.py:15: flowmark package not installed

        ======================== 0 failed, 0 passed, 5 skipped in 0.01s =========================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=0
        log_num_skipped=5
        log_num_updated=0
        log_passed_tests=[]
        log_skipped_tests=['test_foo.py:15:flowmark package not installed#0', 'test_foo.py:15:flowmark package not installed#1', 'test_foo.py:15:flowmark package not installed#2', 'test_foo.py:15:mdformat package not installed#0', 'test_foo.py:15:mdformat package not installed#1']
        log_test_durations={}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=0.01
        pytest_ended=True
        pytest_num_collected=5
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=0
        pytest_num_selected=None
        pytest_num_skipped=5
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test18(self) -> None:
        """
        Test a "short test summary info" skip line with no line number at
        all, e.g.:
        ```
        SKIPPED [27] test_foo.py: some shared reason
        ```
        Pytest prints this form (file only, no ":line") when the repeated
        reason isn't tied to one specific source line.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 2 items

        =========================== short test summary info ============================
        SKIPPED [2] test_foo.py: some shared reason

        ======================== 0 failed, 0 passed, 2 skipped in 0.01s =========================
        """
        # Prepare outputs.
        exp_info = """
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        log_failed_tests=[]
        log_num_failed=0
        log_num_failed_classes=0
        log_num_failed_files=0
        log_num_passed=0
        log_num_skipped=2
        log_num_updated=0
        log_passed_tests=[]
        log_skipped_tests=['test_foo.py:some shared reason#0', 'test_foo.py:some shared reason#1']
        log_test_durations={}
        log_updated_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=0.01
        pytest_ended=True
        pytest_num_collected=2
        pytest_num_deselected=None
        pytest_num_failed=0
        pytest_num_passed=0
        pytest_num_selected=None
        pytest_num_skipped=2
        pytest_num_skipped_at_collection=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, exp_info)

    def test19(self) -> None:
        """
        Test that a garbled per-test status line (e.g., the test's own
        stdout byte-interleaved with the "SKIPPED" tag, corrupting it to
        "SKIPPEDt)") is flagged with a `_LOG.warning` and excluded from the
        counts, instead of being silently dropped or miscounted.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 2 items

        test_foo.py::Test1::test1 (0.00 s) PASSED [ 50%]
        test_foo.py::Test1::test_garbled SKIPPEDt) [100%]

        ======================== 0 failed, 1 passed in 0.01s =========================
        """
        lines = hprint.dedent(txt).split("\n")
        # Check that the garbled line is flagged.
        with self.assertLogs("helpers.hpytest", level="WARNING") as cm:
            info = hpytest.parse_failed_tests(lines)
        self.assertIn(
            "Could not parse test status", "\n".join(cm.output)
        )
        self.assertIn("test_garbled", "\n".join(cm.output))
        # Check that the garbled test is excluded from the counts (rather
        # than being counted as passed, failed, or skipped).
        self.assertEqual(info["log_num_passed"], 1)
        self.assertEqual(info["log_num_skipped"], 0)
        self.assertEqual(info["log_num_failed"], 0)

    def test20(self) -> None:
        """
        Test a file-level collection error (e.g., a module that failed to
        import), which pytest reports without a `::` node id, e.g.:
        ```
        ERROR test_bar.py - ModuleNotFoundError: No module named 'bar'
        ```
        This is a regression test for a crash: `prefix_pattern` didn't
        require a `::` in the test path (unlike the other status
        patterns), so this line used to be accepted as a "failed test",
        and then `filter_failed_tests()` would raise trying to split a
        bare file path into `path::class::test`. It should instead be
        flagged as unparseable (via the same warning as `test19()`) and
        excluded from the counts.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 2 items

        test_foo.py::Test1::test1 (0.00 s) PASSED [100%]
        ERROR test_bar.py - ModuleNotFoundError: No module named 'bar'

        ======================== 0 failed, 1 passed in 0.05s =========================
        """
        lines = hprint.dedent(txt).split("\n")
        # Check that parsing doesn't crash and flags the bare-path line.
        with self.assertLogs("helpers.hpytest", level="WARNING") as cm:
            info = hpytest.parse_failed_tests(lines)
        self.assertIn(
            "Could not parse test status", "\n".join(cm.output)
        )
        self.assertIn("test_bar.py", "\n".join(cm.output))
        # Check that the collection error isn't counted as a failed test.
        self.assertEqual(info["log_num_passed"], 1)
        self.assertEqual(info["log_num_failed"], 0)
        self.assertEqual(info["log_failed_tests"], [])


# #############################################################################
# Test_info_to_str
# #############################################################################


class Test_info_to_str(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that per-test durations are not printed in the report, even
        though `log_test_durations` is present in the parsed `info` dict.
        """
        # Prepare inputs.
        txt = Test_parse_failed_tests().get_pytest_text1()
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        # Prepare outputs.
        exp = """
        ################################################################################
        Results
        ################################################################################
        {'github_completed': False,
         'github_end_timestamp': None,
         'github_start_timestamp': None,
         'github_tag': None,
         'log_num_failed': 3,
         'log_num_failed_classes': 3,
         'log_num_failed_files': 2,
         'log_num_passed': 3,
         'log_num_skipped': 0,
         'log_num_updated': 0,
         'pytest_collection_completed': True,
         'pytest_duration_in_secs': 40.48,
         'pytest_ended': True,
         'pytest_num_collected': 47,
         'pytest_num_deselected': None,
         'pytest_num_failed': 4,
         'pytest_num_passed': 43,
         'pytest_num_selected': None,
         'pytest_num_skipped': None,
         'pytest_num_skipped_at_collection': None,
         'pytest_started': False,
         'pytest_tag': None}
        ################################################################################
        Summary
        ################################################################################
        Run: local
        Pytest completed: True
        Duration: 40.48 s
        Passed: 43/47
        Skipped: 0/47
        Failed: 4/47
        Updated: 0/47
        """
        # Run test.
        act = hpytest.info_to_str(info)
        # Check outputs.
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )


# #############################################################################
# Test_info_to_comments
# #############################################################################


class Test_info_to_comments(hunitest.TestCase):
    def helper(self, txt: str, exp: str) -> None:
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        act = hpytest.info_to_comments(info)
        self.assert_equal(
            act, exp, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        """
        Test the commentary for a local run that completed with failures.
        """
        # Prepare inputs and outputs.
        txt = Test_parse_failed_tests().get_pytest_text1()
        exp = """
        Run: local
        Pytest completed: True
        Duration: 40.48 s
        Passed: 43/47
        Skipped: 0/47
        Failed: 4/47
        Updated: 0/47
        """
        # Check. Note: pytest_num_failed=4, pytest_num_passed=43, total=47
        self.helper(txt, exp)

    def test2(self) -> None:
        """
        Test the commentary for a GitHub CI run with a reported skipped count.
        """
        # Prepare inputs and outputs.
        txt = (
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:35.1181332Z ============================= test session starts =====\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:36.0000000Z platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T17:59:37.0000000Z collected 3361 items / 156 deselected / 7 skipped / 3205 selected\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T18:04:49.0000000Z =========== 34 failed, 3157 passed, 235 skipped in 886.58s (0:14:46) ===========\n"
            "run_fast_tests / run_tests\tUNKNOWN STEP\t"
            "2026-07-06T18:04:49.3717677Z Post job cleanup.\n"
        )
        exp = """
        Run: GitHub CI (run_fast_tests)
        Pytest completed: True
        Duration: 886.58 s
        Passed: 3157/3426
        Skipped: 235/3426
        Failed: 34/3426
        Updated: 0/3426
        """
        # Check.
        self.helper(txt, exp)

    def test3(self) -> None:
        """
        Test the commentary when pytest never started.
        """
        # Prepare inputs and outputs.
        txt = "RuntimeError: _system() failed"
        exp = """
        Run: local
        Pytest completed: False
        Duration: 0.00 s
        Passed: 0/0
        Skipped: 0/0
        Failed: 0/0
        Updated: 0/0
        """
        # Check.
        self.helper(txt, exp)


# #############################################################################
# Test_write_passed_tests
# #############################################################################


class Test_write_passed_tests(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that passed tests are written one per line to a file.
        """
        # Prepare inputs.
        txt = Test_parse_failed_tests().get_pytest_text1()
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        file_name = os.path.join(self.get_scratch_space(), "passed.txt")
        # Prepare outputs.
        expected = """
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question1
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question2
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_process_question1::test_process_question3
        """
        # Run test.
        hpytest.write_passed_tests(info, file_name)
        # Check outputs.
        actual = hio.from_file(file_name)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )


# #############################################################################
# Test_write_skipped_tests
# #############################################################################


class Test_write_skipped_tests(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that skipped tests are written one per line to a file.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 8 items

        test_foo.py::Test1::test_live_skip (0.00 s) SKIPPED [ 33%]
        test_foo.py::Test1::test2 (0.00 s) PASSED [ 66%]
        test_foo.py::Test1::test3 (0.00 s) PASSED [100%]

        =========================== short test summary info ============================
        SKIPPED [1] test_foo.py:10: decorator skip reason
        SKIPPED [1] test_foo.py:20: live skip reason
        SKIPPED [4] test_foo.py:30: parametrized skip reason

        ======================== 0 failed, 2 passed, 6 skipped in 0.01s =========================
        """
        txt = hprint.dedent(txt)
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        file_name = os.path.join(self.get_scratch_space(), "skipped.txt")
        # Prepare outputs.
        expected = """
        test_foo.py:10:decorator skip reason#0
        test_foo.py:20:live skip reason#0
        test_foo.py:30:parametrized skip reason#0
        test_foo.py:30:parametrized skip reason#1
        test_foo.py:30:parametrized skip reason#2
        test_foo.py:30:parametrized skip reason#3
        """
        # Run test.
        hpytest.write_skipped_tests(info, file_name)
        # Check outputs.
        actual = hio.from_file(file_name)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )


# #############################################################################
# Test_write_updated_tests
# #############################################################################


class Test_write_updated_tests(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that updated tests are written one per line to a file.
        """
        # Prepare inputs.
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 2 items

        test_foo.py::Test1::test_check_string_missing3 (0.13 s) (WARNING: Test was updated) PASSED [ 50%]
        test_foo.py::Test1::test2 (0.00 s) PASSED [100%]

        ======================== 0 failed, 2 passed in 0.13s =========================
        """
        txt = hprint.dedent(txt)
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        file_name = os.path.join(self.get_scratch_space(), "updated.txt")
        # Prepare outputs.
        expected = """
        test_foo.py::Test1::test_check_string_missing3
        """
        # Run test.
        hpytest.write_updated_tests(info, file_name)
        # Check outputs.
        actual = hio.from_file(file_name)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )


# #############################################################################
# Test_write_tests_by_duration
# #############################################################################


class Test_write_tests_by_duration(hunitest.TestCase):
    def get_multi_class_info(self) -> Dict[str, Any]:
        """
        Build the `info` dict for a run with tests spread across two files
        and three classes, with distinct durations to make the sort order
        unambiguous.
        """
        txt = """
        ============================= test session starts ==============================
        platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        collected 4 items

        file_a.py::ClassA::test1 (1.00 s) PASSED [ 25%]
        file_a.py::ClassA::test2 (2.00 s) PASSED [ 50%]
        file_a.py::ClassB::test1 (0.50 s) PASSED [ 75%]
        file_b.py::ClassC::test1 (4.00 s) PASSED [100%]

        ======================== 0 failed, 4 passed in 7.50s =========================
        """
        txt = hprint.dedent(txt)
        lines = txt.split("\n")
        info = hpytest.parse_failed_tests(lines)
        return info

    def test1(self) -> None:
        """
        Test that all timed tests are written ordered by duration,
        descending, regardless of outcome.
        """
        # Prepare inputs.
        info = self.get_multi_class_info()
        file_name = os.path.join(self.get_scratch_space(), "by_duration.txt")
        # Prepare outputs.
        expected = """
        4.00 s  file_b.py::ClassC::test1
        2.00 s  file_a.py::ClassA::test2
        1.00 s  file_a.py::ClassA::test1
        0.50 s  file_a.py::ClassB::test1
        """
        # Run test.
        hpytest.write_tests_by_duration(info, file_name)
        # Check outputs.
        actual = hio.from_file(file_name)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )


# #############################################################################
# Test_compute_duration_stats_by_file
# #############################################################################


class Test_compute_duration_stats_by_file(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that durations are aggregated by file, sorted by total
        duration descending.
        """
        # Prepare inputs.
        info = Test_write_tests_by_duration().get_multi_class_info()
        # Prepare outputs.
        expected = """
        {'file_b.py': {'count': 1,
                       'total_secs': 4.0,
                       'mean_secs': 4.0,
                       'max_secs': 4.0},
         'file_a.py': {'count': 3,
                       'total_secs': 3.5,
                       'mean_secs': 1.1666666666666667,
                       'max_secs': 2.0}}
        """
        # Run test.
        actual = hpytest.compute_duration_stats_by_file(info)
        # Check outputs.
        self.assert_equal(
            pprint.pformat(actual, sort_dicts=False),
            expected,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )


# #############################################################################
# Test_compute_duration_stats_by_class
# #############################################################################


class Test_compute_duration_stats_by_class(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that durations are aggregated by class, sorted by total
        duration descending.
        """
        # Prepare inputs.
        info = Test_write_tests_by_duration().get_multi_class_info()
        # Prepare outputs.
        expected = """
        {'file_b.py::ClassC': {'count': 1,
                               'total_secs': 4.0,
                               'mean_secs': 4.0,
                               'max_secs': 4.0},
         'file_a.py::ClassA': {'count': 2,
                               'total_secs': 3.0,
                               'mean_secs': 1.5,
                               'max_secs': 2.0},
         'file_a.py::ClassB': {'count': 1,
                               'total_secs': 0.5,
                               'mean_secs': 0.5,
                               'max_secs': 0.5}}
        """
        # Run test.
        actual = hpytest.compute_duration_stats_by_class(info)
        # Check outputs.
        self.assert_equal(
            pprint.pformat(actual, sort_dicts=False),
            expected,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )


# #############################################################################
# Test_write_duration_stats
# #############################################################################


class Test_write_duration_stats(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that duration statistics, aggregated by file and by class,
        are written to a file.
        """
        # Prepare inputs.
        info = Test_write_tests_by_duration().get_multi_class_info()
        file_name = os.path.join(self.get_scratch_space(), "duration_stats.txt")
        # Prepare outputs.
        expected = """
        ################################################################################
        Duration by file
        ################################################################################
        File | Count | Total (secs) | Mean (secs) | Max (secs)
        file_b.py | 1 | 4.00 | 4.00 | 4.00
        file_a.py | 3 | 3.50 | 1.17 | 2.00
        ################################################################################
        Duration by class
        ################################################################################
        Class | Count | Total (secs) | Mean (secs) | Max (secs)
        file_b.py::ClassC | 1 | 4.00 | 4.00 | 4.00
        file_a.py::ClassA | 2 | 3.00 | 1.50 | 2.00
        file_a.py::ClassB | 1 | 0.50 | 0.50 | 0.50
        """
        # Run test.
        hpytest.write_duration_stats(info, file_name)
        # Check outputs.
        actual = hio.from_file(file_name)
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )
