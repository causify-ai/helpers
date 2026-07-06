import helpers.hprint as hprint
import helpers.hpytest as hpytest
import helpers.hunit_test as hunitest


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
