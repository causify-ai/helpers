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
        log_num_passed=0
        log_num_skipped=0
        log_passed_tests=[]
        log_skipped_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_num_failed=4
        pytest_num_passed=43
        pytest_num_skipped=None
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
        log_num_passed=0
        log_num_skipped=0
        log_passed_tests=[]
        log_skipped_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_num_failed=4
        pytest_num_passed=43
        pytest_num_skipped=None
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
        self.assert_equal(
            str(filtered_files),
            str(['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py'])
        )

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
        log_num_passed=0
        log_num_skipped=0
        log_passed_tests=[]
        log_skipped_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_num_failed=4
        pytest_num_passed=43
        pytest_num_skipped=None
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
        self.assert_equal(
            str(filtered_classes),
            str(['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3'])
        )

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
        log_passed_tests=[]
        log_skipped_tests=[]
        pytest_collection_completed=False
        pytest_duration_in_secs=None
        pytest_ended=False
        pytest_num_failed=None
        pytest_num_passed=None
        pytest_num_skipped=None
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
        log_num_passed=0
        log_num_skipped=0
        log_passed_tests=[]
        log_skipped_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=None
        pytest_ended=False
        pytest_num_failed=None
        pytest_num_passed=None
        pytest_num_skipped=None
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
        log_passed_tests=[]
        log_skipped_tests=[]
        pytest_collection_completed=True
        pytest_duration_in_secs=886.58
        pytest_ended=True
        pytest_num_failed=34
        pytest_num_passed=3157
        pytest_num_skipped=235
        pytest_started=True
        pytest_tag=platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python
        """
        # Check.
        self.helper(txt, exp_info)


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
        Failed: 4/47
        Skipped: 0/47
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
        Failed: 34/3426
        Skipped: 235/3426
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
        Failed: 0/0
        Skipped: 0/0
        """
        # Check.
        self.helper(txt, exp)
