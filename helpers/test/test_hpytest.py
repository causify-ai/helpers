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
        exp_failed_tests: str,
        exp_num_failed: int,
        exp_num_passed: int,
    ) -> None:
        act_failed_tests, act_num_failed, act_num_passed = (
            hpytest.parse_failed_tests(txt, only_file, only_class)
        )
        act_failed_tests = "\n".join(act_failed_tests)
        self.assert_equal(
            act_failed_tests,
            exp_failed_tests,
            dedent=True,
            remove_lead_trail_empty_lines=True,
        )
        self.assertEqual(act_num_failed, exp_num_failed)
        self.assertEqual(act_num_passed, exp_num_passed)

    def test1(self) -> None:
        # Prepare inputs and outputs.
        txt = self.get_pytest_text1()
        only_file = False
        only_class = False
        exp_failed_tests = """
        helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1::test2
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1::test1
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3::test_run_all1
        """
        exp_num_failed = 4
        exp_num_passed = 43
        # Check.
        self.helper(
            txt,
            only_file,
            only_class,
            exp_failed_tests,
            exp_num_failed,
            exp_num_passed,
        )

    def test2(self) -> None:
        # Prepare inputs and outputs.
        txt = self.get_pytest_text1()
        only_file = True
        only_class = False
        exp_failed_tests = """
        helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py
        """
        exp_num_failed = 4
        exp_num_passed = 43
        # Check.
        self.helper(
            txt,
            only_file,
            only_class,
            exp_failed_tests,
            exp_num_failed,
            exp_num_passed,
        )

    def test3(self) -> None:
        # Prepare inputs and outputs.
        txt = self.get_pytest_text1()
        only_file = False
        only_class = True
        exp_failed_tests = """
        helpers_root/dev_scripts_helpers/documentation/test/test_notes_to_pdf.py::Test_notes_to_pdf1
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes1
        helpers_root/dev_scripts_helpers/documentation/test/test_preprocess_notes.py::Test_preprocess_notes3
        """
        exp_num_failed = 4
        exp_num_passed = 43
        # Check.
        self.helper(
            txt,
            only_file,
            only_class,
            exp_failed_tests,
            exp_num_failed,
            exp_num_passed,
        )
