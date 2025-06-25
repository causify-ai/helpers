import io
import os
import pprint
import re
from contextlib import redirect_stdout

import pytest

import helpers.hio as hio
import helpers.hpytest as hpytest
import helpers.hunit_test as hunitest

# TODO(heanh): Install `junitparser` in `//helpers`.
pytest.importorskip("junitparser")


def _strip_color_codes(text: str) -> str:
    """
    Remove ANSI color escape codes from text.
    """
    # Remove ANSI escape codes: \033[<code>m and \033[0m.
    return re.sub(r"\033\[[0-9;]*m", "", text)


# #############################################################################
# Test_JUnitReporter
# #############################################################################


class Test_JUnitReporter(hunitest.TestCase):
    """
    Test scenario where there are passed, skipped tests with leads to `PASSED`
    result.
    """

    def helper(self) -> None:
        xml_str = """
        <testsuites>
            <testsuite name="dummy-test-suite-1" errors="0" failures="0" skipped="1" tests="2" time="2" timestamp="2025-01-01T12:00:00.000000+00:00" hostname="dummy-host">
                <testcase classname="dummy.test.test_module.DummyTestCase" name="test_dummy_function" time="1" />
                <testcase classname="dummy.test.test_module.DummyTestCase" name="test_another_function" time="1">
                    <skipped type="pytest.skip" message="Dummy skip message for testing purposes.">/app/dummy/test/test_module.py:25: Dummy skip message for testing purposes.</skipped>
                </testcase>
            </testsuite>
            <testsuite name="dummy-test-suite-2" errors="0" failures="0" skipped="0" tests="0" time="1" timestamp="2025-01-01T12:01:00.000000+00:00" hostname="dummy-host" />
        </testsuites>
        """
        input_dir = self.get_scratch_space()
        input_file_path = os.path.join(input_dir, "test.xml")
        hio.to_file(input_file_path, xml_str)
        reporter = hpytest.JUnitReporter(input_file_path)
        return reporter

    def test_parse(self) -> None:
        """
        Test parsing the JUnit XML file.
        """
        reporter = self.helper()
        reporter.parse()
        act = pprint.pformat(reporter.overall_stats)
        exp = r"""
        {'error': 0,
        'failed': 0,
        'passed': 1,
        'skipped': 1,
        'total_tests': 2,
        'total_time': 3.0}
        """
        self.assert_equal(act, exp, dedent=True, fuzzy_match=True)

    def test_print_summary(self) -> None:
        """
        Test printing the summary of the results from JUnit XML file.
        """
        reporter = self.helper()
        reporter.parse()
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            reporter.print_summary()
        act = captured_output.getvalue()
        act = _strip_color_codes(act)
        exp = r"""
        ======================================================================
        collected 2 items

        ======================================================================
        Test: dummy-test-suite-1
        Timestamp: 2025-01-01T12:00:00.000000+00:00
        ----------------------------------------------------------------------
        dummy.test.test_module.DummyTestCase::test_dummy_function PASSED (1.000s)
        dummy.test.test_module.DummyTestCase::test_another_function SKIPPED (1.000s)
        Summary: 1 passed, 1 skipped in 2.000s

        ======================================================================
        Test: dummy-test-suite-2
        Timestamp: 2025-01-01T12:01:00.000000+00:00
        ----------------------------------------------------------------------
        Summary: no tests in 1.000s

        ======================================================================
        Summary: 1 passed, 1 skipped in 3.00s
        Result: PASSED
        """
        self.assert_equal(
            act,
            exp,
            dedent=True,
            fuzzy_match=True,
        )


# #############################################################################
# Test_JUnitReporter2
# #############################################################################


class Test_JUnitReporter2(hunitest.TestCase):
    """
    Test scenario where there are passed, error, failed, and skipped tests with
    leads to `FAILED` result.
    """

    def helper(self) -> None:
        xml_str = """
        <testsuites>
            <testsuite name="dummy-test-suite-1" errors="0" failures="0" skipped="1" tests="2" time="2" timestamp="2025-01-01T12:00:00.000000+00:00" hostname="dummy-host">
                <testcase classname="dummy.test.test_module.DummyTestCase" name="test_dummy_function" time="1" />
                <testcase classname="dummy.test.test_module.DummyTestCase" name="test_another_function" time="1">
                    <skipped type="pytest.skip" message="Dummy skip message for testing purposes.">/app/dummy/test/test_module.py:25: Dummy skip message for testing purposes.</skipped>
                </testcase>
            </testsuite>
            <testsuite name="dummy-test-suite-2" errors="1" failures="1" skipped="0" tests="3" time="3" timestamp="2025-01-01T12:01:00.000000+00:00" hostname="dummy-host">
                <testcase classname="dummy.test.test_module.DummyTestCase" name="test_passed_function" time="1" />
                <testcase classname="dummy.test.test_module.DummyTestCase" name="test_failed_function" time="1">
                    <failure type="AssertionError" message="Dummy failure message for testing purposes.">/app/dummy/test/test_module.py:30: Dummy failure message for testing purposes.</failure>
                </testcase>
                <testcase classname="dummy.test.test_module.DummyTestCase" name="test_error_function" time="1">
                    <error type="RuntimeError" message="Dummy error message for testing purposes.">/app/dummy/test/test_module.py:35: Dummy error message for testing purposes.</error>
                </testcase>
            </testsuite>
            <testsuite name="dummy-test-suite-3" errors="0" failures="0" skipped="0" tests="0" time="1" timestamp="2025-01-01T12:02:00.000000+00:00" hostname="dummy-host" />
        </testsuites>
        """
        input_dir = self.get_scratch_space()
        input_file_path = os.path.join(input_dir, "test.xml")
        hio.to_file(input_file_path, xml_str)
        reporter = hpytest.JUnitReporter(input_file_path)
        return reporter

    def test_parse(self) -> None:
        """
        Test parsing the JUnit XML file.
        """
        reporter = self.helper()
        reporter.parse()
        act = pprint.pformat(reporter.overall_stats)
        exp = r"""
        {'error': 1,
        'failed': 1,
        'passed': 2,
        'skipped': 1,
        'total_tests': 5,
        'total_time': 6.0}
        """
        self.assert_equal(act, exp, dedent=True, fuzzy_match=True)

    def test_print_summary(self) -> None:
        """
        Test printing the summary of the results from JUnit XML file.
        """
        reporter = self.helper()
        reporter.parse()
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            reporter.print_summary()
        act = captured_output.getvalue()
        act = _strip_color_codes(act)
        exp = r"""
        ======================================================================
        collected 5 items

        ======================================================================
        Test: dummy-test-suite-1
        Timestamp: 2025-01-01T12:00:00.000000+00:00
        ----------------------------------------------------------------------
        dummy.test.test_module.DummyTestCase::test_dummy_function PASSED (1.000s)
        dummy.test.test_module.DummyTestCase::test_another_function SKIPPED (1.000s)
        Summary: 1 passed, 1 skipped in 2.000s

        ======================================================================
        Test: dummy-test-suite-2
        Timestamp: 2025-01-01T12:01:00.000000+00:00
        ----------------------------------------------------------------------
        dummy.test.test_module.DummyTestCase::test_passed_function PASSED (1.000s)
        dummy.test.test_module.DummyTestCase::test_failed_function FAILED (1.000s)
        dummy.test.test_module.DummyTestCase::test_error_function ERROR (1.000s)
        Summary: 1 passed, 1 failed, 1 error in 3.000s

        ======================================================================
        Test: dummy-test-suite-3
        Timestamp: 2025-01-01T12:02:00.000000+00:00
        ----------------------------------------------------------------------
        Summary: no tests in 1.000s

        ======================================================================
        Summary: 2 passed, 1 failed, 1 error, 1 skipped in 6.00s
        Result: FAILED
        """
        self.assert_equal(
            act,
            exp,
            dedent=True,
            fuzzy_match=True,
        )
