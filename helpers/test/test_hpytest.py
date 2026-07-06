import helpers.hprint as hprint
import helpers.hpytest as hpytest
import helpers.hunit_test as hunitest


# #############################################################################
# Test__parse_github_ci_log
# #############################################################################


class Test__parse_github_ci_log(hunitest.TestCase):
    def helper(self, txt: str, exp_info: str, exp_log: str) -> None:
        txt = hprint.dedent(txt)
        act_info, act_log = hpytest._parse_github_ci_log(txt)
        act_info_as_str = "\n".join(
            f"{k}={v}" for k, v in sorted(act_info.items())
        )
        self.assert_equal(
            act_info_as_str,
            exp_info,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )
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
        only_file: bool,
        only_class: bool,
        exp_info: str,
    ) -> None:
        txt = hprint.dedent(txt)
        act_info = hpytest.parse_failed_tests(txt, only_file, only_class)
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
        only_file = False
        only_class = False
        exp_info = """
        failed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3::test_run_all1']
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        num_failed=4
        num_passed=43
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_reported_failed=4
        pytest_reported_passed=43
        pytest_reported_skipped=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, only_file, only_class, exp_info)

    def test2(self) -> None:
        # Prepare inputs and outputs.
        txt = self.get_pytest_text1()
        only_file = True
        only_class = False
        exp_info = """
        failed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py']
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        num_failed=4
        num_passed=43
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_reported_failed=4
        pytest_reported_passed=43
        pytest_reported_skipped=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, only_file, only_class, exp_info)

    def test3(self) -> None:
        # Prepare inputs and outputs.
        txt = self.get_pytest_text1()
        only_file = False
        only_class = True
        exp_info = """
        failed_tests=['helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1', 'helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3']
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        num_failed=4
        num_passed=43
        pytest_collection_completed=True
        pytest_duration_in_secs=40.48
        pytest_ended=True
        pytest_reported_failed=4
        pytest_reported_passed=43
        pytest_reported_skipped=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, only_file, only_class, exp_info)

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
        only_file = False
        only_class = False
        # Prepare outputs.
        exp_info = """
        failed_tests=[]
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        num_failed=0
        num_passed=0
        pytest_collection_completed=False
        pytest_duration_in_secs=None
        pytest_ended=False
        pytest_reported_failed=None
        pytest_reported_passed=None
        pytest_reported_skipped=None
        pytest_started=False
        pytest_tag=None
        """
        # Check.
        self.helper(txt, only_file, only_class, exp_info)

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
        only_file = False
        only_class = False
        # Prepare outputs.
        exp_info = """
        failed_tests=[]
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        num_failed=0
        num_passed=0
        pytest_collection_completed=True
        pytest_duration_in_secs=None
        pytest_ended=False
        pytest_reported_failed=None
        pytest_reported_passed=None
        pytest_reported_skipped=None
        pytest_started=True
        pytest_tag=platform darwin -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /venv/bin/python3
        """
        # Check.
        self.helper(txt, only_file, only_class, exp_info)

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
        only_file = False
        only_class = False
        # Prepare outputs.
        exp_info = """
        failed_tests=[]
        github_completed=False
        github_end_timestamp=None
        github_start_timestamp=None
        github_tag=None
        num_failed=34
        num_passed=3157
        pytest_collection_completed=True
        pytest_duration_in_secs=886.58
        pytest_ended=True
        pytest_reported_failed=34
        pytest_reported_passed=3157
        pytest_reported_skipped=235
        pytest_started=True
        pytest_tag=platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- /venv/bin/python
        """
        # Check.
        self.helper(txt, only_file, only_class, exp_info)
