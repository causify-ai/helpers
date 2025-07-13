"""
Import as:

import helpers.test.test_unit_test as ttutes
"""

import logging
import tempfile
from typing import Optional, Tuple

import pandas as pd
import pytest

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.hunit_test_purification as huntepur

_LOG = logging.getLogger(__name__)


def _git_add(file_name: str) -> None:
    # pylint: disable=unreachable
    cmd = f"git add -u {file_name}"
    _LOG.debug("> %s", cmd)
    rc = hsystem.system(cmd, abort_on_error=False)
    if rc:
        _LOG.warning(
            "Can't run '%s': you need to add the file manually",
            cmd,
        )


def _to_skip_on_update_outcomes() -> bool:
    """
    Determine whether to skip on `--update_outcomes`.

    Some tests can't pass with `--update_outcomes`, since they exercise
    the logic in `--update_outcomes` itself.

    We can't always use `@pytest.mark.skipif(hunitest.get_update_tests)`
    since pytest decides which tests need to be run before the variable
    is actually set.
    """
    to_skip = False
    if hunitest.get_update_tests():
        _LOG.warning(
            "Skip this test since it exercises the logic for --update_outcomes"
        )
        to_skip = True
    return to_skip


# #############################################################################
# TestTestCase1
# #############################################################################


class TestTestCase1(hunitest.TestCase):
    """
    Test free-standing functions in unit_test.py.
    """

    def test_get_input_dir1(self) -> None:
        """
        Test hunitest.get_input_dir().
        """
        act = self.get_input_dir()
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        exp = "$GIT_ROOT/helpers/test/outcomes/TestTestCase1.test_get_input_dir1/input"
        self.assertEqual(act, exp)

    def test_get_input_dir2(self) -> None:
        use_only_test_class = False
        test_class_name = "test_class"
        test_method_name = "test_method"
        act = self.get_input_dir(
            use_only_test_class=use_only_test_class,
            test_class_name=test_class_name,
            test_method_name=test_method_name,
        )
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        #
        exp = "$GIT_ROOT/helpers/test/outcomes/test_class.test_method/input"
        self.assertEqual(act, exp)

    def test_get_input_dir3(self) -> None:
        use_only_test_class = False
        test_class_name = None
        test_method_name = None
        act = self.get_input_dir(
            use_only_test_class=use_only_test_class,
            test_class_name=test_class_name,
            test_method_name=test_method_name,
        )
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        #
        exp = "$GIT_ROOT/helpers/test/outcomes/TestTestCase1.test_get_input_dir3/input"
        self.assertEqual(act, exp)

    def test_get_input_dir4(self) -> None:
        use_only_test_class = True
        test_class_name = None
        test_method_name = None
        act = self.get_input_dir(
            use_only_test_class=use_only_test_class,
            test_class_name=test_class_name,
            test_method_name=test_method_name,
        )
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        #
        exp = "$GIT_ROOT/helpers/test/outcomes/TestTestCase1/input"
        self.assertEqual(act, exp)

    def test_get_output_dir1(self) -> None:
        """
        Test hunitest.get_output_dir().
        """
        act = self.get_output_dir()
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        exp = "$GIT_ROOT/helpers/test/outcomes/TestTestCase1.test_get_output_dir1/output"
        self.assertEqual(act, exp)

    def test_get_scratch_space1(self) -> None:
        """
        Test hunitest.get_scratch_space().
        """
        act = self.get_scratch_space()
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        exp = (
            "$GIT_ROOT/helpers/test/outcomes/TestTestCase1.test_get_scratch_space1"
            "/tmp.scratch"
        )
        self.assertEqual(act, exp)

    def test_get_scratch_space2(self) -> None:
        test_class_name = "test_class"
        test_method_name = "test_method"
        act = self.get_scratch_space(
            test_class_name=test_class_name, test_method_name=test_method_name
        )
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        exp = (
            "$GIT_ROOT/helpers/test/outcomes/test_class.test_method/tmp.scratch"
        )
        self.assertEqual(act, exp)

    def test_get_scratch_space3(self) -> None:
        test_class_name = "test_class"
        test_method_name = "test_method"
        use_absolute_path = False
        act = self.get_scratch_space(
            test_class_name=test_class_name,
            test_method_name=test_method_name,
            use_absolute_path=use_absolute_path,
        )
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        exp = "outcomes/test_class.test_method/tmp.scratch"
        self.assertEqual(act, exp)

    def test_get_s3_scratch_dir1(self) -> None:
        act = self.get_s3_scratch_dir()
        _LOG.debug("act=%s", act)
        # It is difficult to test, so we just execute.

    def test_get_s3_scratch_dir2(self) -> None:
        test_class_name = "test_class"
        test_method_name = "test_method"
        act = self.get_s3_scratch_dir(
            test_class_name=test_class_name, test_method_name=test_method_name
        )
        _LOG.debug("act=%s", act)
        # It is difficult to test, so we just execute.

    def test_assert_equal1(self) -> None:
        actual = "hello world"
        expected = actual
        self.assert_equal(actual, expected)

    def test_assert_not_equal1(self) -> None:
        actual = "hello world"
        expected = "hello world w"
        tmp_dir = tempfile.mkdtemp()
        with self.assertRaises(RuntimeError):
            self.assert_equal(actual, expected, dst_dir=tmp_dir)

    def test_assert_not_equal2(self) -> None:
        actual = "hello world"
        expected = "hello world w"
        # Create a dir like `/var/tmp/tmph_kun9xq`.
        tmp_dir = tempfile.mkdtemp()
        self.assert_equal(
            actual, expected, abort_on_error=False, dst_dir=tmp_dir
        )
        # Compute the signature from the dir.
        act = hunitest.get_dir_signature(
            tmp_dir, include_file_content=True, num_lines=None
        )
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        act = act.replace(tmp_dir, "$TMP_DIR")
        # pylint: disable=line-too-long
        exp = """
        # Dir structure
        $TMP_DIR
        $TMP_DIR/tmp_diff.sh
        # File signatures
        len(file_names)=1
        file_names=$TMP_DIR/tmp_diff.sh
        # $TMP_DIR/tmp_diff.sh
        num_lines=8
        '''
        #!/bin/bash
        if [[ $1 == "wrap" ]]; then
            cmd='vimdiff -c "windo set wrap"'
        else
            cmd='vimdiff'
        fi;
        cmd="$cmd helpers/test/outcomes/TestTestCase1.test_assert_not_equal2/tmp.final.actual.txt helpers/test/outcomes/TestTestCase1.test_assert_not_equal2/tmp.final.expected.txt"
        eval $cmd

        '''
        """
        # pylint: enable=line-too-long
        self.assert_equal(act, exp, fuzzy_match=True)

    def test_assert_equal_fuzzy_match1(self) -> None:
        actual = "hello world"
        expected = "hello world "
        is_equal = self.assert_equal(actual, expected, fuzzy_match=True)
        self.assertTrue(is_equal)

    def test_assert_equal5(self) -> None:
        actual = "hello world"
        expected = "hello world2"
        with self.assertRaises(RuntimeError):
            self.assert_equal(actual, expected, fuzzy_match=True)

    def _remove_lines1(self) -> None:
        txt = r"""
        # #####################################################################
        * Failed assertion *
        'in1' not in '{'in1': 'out1'}'
        ##
        `in1` already receiving input from node n1
        # #####################################################################
        # #####################################################################
        """
        act = hunitest._remove_spaces(txt)
        exp = r"""
        * Failed assertion *
        'in1' not in '{'in1': 'out1'}'
        ##
        `in1` already receiving input from node n1
        # #####################################################################
        """
        self.assert_equal(act, exp, fuzzy_match=False)


# #############################################################################
# Test_AssertEqual1
# #############################################################################


class Test_AssertEqual1(hunitest.TestCase):
    def test_equal1(self) -> None:
        """
        Matching act and exp without fuzzy matching.
        """
        act = r"""
completed       failure Lint    Run_linter
completed       success Lint    Fast_tests
completed       success Lint    Slow_tests
"""
        exp = r"""
completed       failure Lint    Run_linter
completed       success Lint    Fast_tests
completed       success Lint    Slow_tests
"""
        test_name = self._get_test_name()
        test_dir = self.get_scratch_space()
        is_equal = hunitest.assert_equal(act, exp, test_name, test_dir)
        _LOG.debug(hprint.to_str("is_equal"))
        self.assertTrue(is_equal)

    def test_equal2(self) -> None:
        """
        Matching act and exp with fuzzy matching.
        """
        act = r"""
completed failure Lint Run_linter
completed success Lint Fast_tests
completed success Lint Slow_tests
"""
        exp = r"""
completed       failure Lint    Run_linter
completed       success Lint    Fast_tests
completed       success Lint    Slow_tests
"""
        test_name = self._get_test_name()
        test_dir = self.get_scratch_space()
        fuzzy_match = True
        is_equal = hunitest.assert_equal(
            act, exp, test_name, test_dir, fuzzy_match=fuzzy_match
        )
        _LOG.debug(hprint.to_str("is_equal"))
        self.assertTrue(is_equal)

    def test_not_equal1(self) -> None:
        """
        Mismatching act and exp.
        """
        act = r"""
completed failure Lint    Run_linter
completed       success Lint    Fast_tests
completed       success Lint    Slow_tests
"""
        exp = r"""
completed       failure Lint    Run_linter
completed       success Lint    Fast_tests
completed       success Lint    Slow_tests
"""
        test_name = self._get_test_name()
        test_dir = self.get_scratch_space()
        fuzzy_match = False
        with self.assertRaises(RuntimeError) as cm:
            hunitest.assert_equal(
                act, exp, test_name, test_dir, fuzzy_match=fuzzy_match
            )
        # Check that the assertion is what expected.
        act = str(cm.exception)
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        exp = '''
--------------------------------------------------------------------------------
ACTUAL vs EXPECTED: Test_AssertEqual1.test_not_equal1
--------------------------------------------------------------------------------

                                                                          (
completed failure Lint    Run_linter                                      |  completed       failure Lint    Run_linter
completed       success Lint    Fast_tests                                (
completed       success Lint    Slow_tests                                (
Diff with:
> ./tmp_diff.sh
--------------------------------------------------------------------------------
ACTUAL VARIABLE: Test_AssertEqual1.test_not_equal1
--------------------------------------------------------------------------------
exp = r"""
completed failure Lint    Run_linter
completed       success Lint    Fast_tests
completed       success Lint    Slow_tests
"""'''
        if act != exp:
            hio.to_file("act.txt", act)
            hio.to_file("exp.txt", exp)
            self.assert_equal(act, exp, fuzzy_match=False)
        # We don't use self.assert_equal() since this is exactly we are testing,
        # so we use a trusted function.
        self.assertEqual(act, exp)

    # For debugging: don't commit code with this test enabled.
    @pytest.mark.skip(
        reason="This is only used to debug the debugging the infrastructure"
    )
    def test_not_equal_debug(self) -> None:
        """
        Create a mismatch on purpose to see how the suggested updated to
        expected variable looks like.
        """
        act = r"""empty
start

completed failure Lint    Run_linter
completed       success Lint    Fast_tests
completed       success Lint    Slow_tests

end

"""
        exp = "hello"
        self.assert_equal(act, exp, fuzzy_match=False)


# #############################################################################
# TestCheckString1
# #############################################################################


class TestCheckString1(hunitest.TestCase):
    def test_check_string1(self) -> None:
        """
        Compare the actual value to a matching golden outcome.
        """
        if _to_skip_on_update_outcomes():
            return
        act = "hello world"
        golden_outcome = "hello world"
        #
        tag = "test"
        _, file_name = self._get_golden_outcome_file_name(tag)
        # Overwrite the golden file, so that --update_golden doesn't matter.
        hio.to_file(file_name, golden_outcome)
        try:
            # Check.
            outcome_updated, file_exists, is_equal = self.check_string(act)
            # Actual match the golden outcome and it wasn't updated.
        finally:
            # Clean up.
            hio.to_file(file_name, golden_outcome)
            _git_add(file_name)
        self.assertFalse(outcome_updated)
        self.assertTrue(file_exists)
        self.assertTrue(is_equal)

    def test_check_string_not_equal1(self) -> None:
        """
        Compare the actual value to a mismatching golden outcome.
        """
        if _to_skip_on_update_outcomes():
            return
        act = "hello world"
        golden_outcome = "hello world2"
        #
        tag = "test"
        _, file_name = self._get_golden_outcome_file_name(tag)
        # Modify the golden.
        hio.to_file(file_name, golden_outcome)
        try:
            # Check.
            outcome_updated, file_exists, is_equal = self.check_string(
                act, abort_on_error=False
            )
        finally:
            # Clean up.
            hio.to_file(file_name, golden_outcome)
            _git_add(file_name)
        # Actual doesn't match the golden outcome.
        self.assertFalse(outcome_updated)
        self.assertTrue(file_exists)
        self.assertFalse(is_equal)

    def test_check_string_not_equal2(self) -> None:
        """
        Compare the actual value to a mismatching golden outcome and udpate it.
        """
        if _to_skip_on_update_outcomes():
            return
        act = "hello world"
        golden_outcome = "hello world2"
        # Force updating the golden outcomes.
        self.mock_update_tests()
        #
        tag = "test"
        _, file_name = self._get_golden_outcome_file_name(tag)
        # Modify the golden.
        hio.to_file(file_name, golden_outcome)
        try:
            # Check.
            outcome_updated, file_exists, is_equal = self.check_string(
                act, abort_on_error=False
            )
            new_golden = hio.from_file(file_name)
            _git_add(file_name)
        finally:
            # Clean up.
            hio.to_file(file_name, golden_outcome)
            _git_add(file_name)
        # Actual doesn't match the golden outcome and it was updated.
        self.assertTrue(outcome_updated)
        self.assertTrue(file_exists)
        self.assertFalse(is_equal)
        # The golden outcome was updated.
        self.assertEqual(new_golden, "hello world")

    def test_check_string_not_equal3(self) -> None:
        """
        Like test_check_string_not_equal1() but raising the exception.
        """
        if _to_skip_on_update_outcomes():
            return
        act = "hello world"
        golden_outcome = "hello world2"
        #
        tag = "test"
        _, file_name = self._get_golden_outcome_file_name(tag)
        # Modify the golden.
        hio.to_file(file_name, golden_outcome)
        try:
            # Check.
            with self.assertRaises(RuntimeError):
                self.check_string(act)
        finally:
            # Clean up.
            hio.to_file(file_name, golden_outcome)
            _git_add(file_name)

    def test_check_string_missing1(self) -> None:
        """
        When running with --update_outcomes, the golden outcome was missing and
        so it was added.

        This tests the code path when action_on_missing_golden="update".
        """
        if _to_skip_on_update_outcomes():
            return
        act = "hello world"
        # Force updating the golden outcomes.
        self.mock_update_tests()
        tag = "test"
        _, file_name = self._get_golden_outcome_file_name(tag)
        try:
            # Remove the golden.
            hio.delete_file(file_name)
            # Check.
            outcome_updated, file_exists, is_equal = self.check_string(
                act, abort_on_error=False
            )
            hdbg.dassert_file_exists(file_name)
            new_golden = hio.from_file(file_name)
        finally:
            # Clean up.
            hio.delete_file(file_name)
            _git_add(file_name)
        # Actual doesn't match the golden outcome and it was updated.
        self.assertTrue(outcome_updated)
        self.assertFalse(file_exists)
        self.assertFalse(is_equal)
        #
        self.assertEqual(new_golden, "hello world")

    def test_check_string_missing2(self) -> None:
        """
        Without running with --update_outcomes, the golden outcome was missing,
        action_on_missing_golden="assert", and the unit test framework
        asserted.
        """
        if _to_skip_on_update_outcomes():
            return
        act = "hello world"
        tag = "test"
        _, file_name = self._get_golden_outcome_file_name(tag)
        try:
            # Remove the golden.
            hio.delete_file(file_name)
            # Check.
            outcome_updated, file_exists, is_equal = self.check_string(
                act, abort_on_error=False, action_on_missing_golden="assert"
            )
            hdbg.dassert_file_exists(file_name + ".tmp")
            new_golden = hio.from_file(file_name + ".tmp")
        finally:
            # Clean up.
            hio.delete_file(file_name)
        # Actual doesn't match the golden outcome and it was updated.
        self.assertFalse(outcome_updated)
        self.assertFalse(file_exists)
        self.assertFalse(is_equal)
        #
        self.assertEqual(new_golden, "hello world")

    def test_check_string_missing3(self) -> None:
        """
        Without running with --update_outcomes, the golden outcome was missing,
        action_on_missing_golden="update", and the unit test framework updates
        the golden.
        """
        if _to_skip_on_update_outcomes():
            return
        act = "hello world"
        tag = "test"
        _, file_name = self._get_golden_outcome_file_name(tag)
        try:
            # Remove the golden.
            hio.delete_file(file_name)
            # Check.
            outcome_updated, file_exists, is_equal = self.check_string(
                act, abort_on_error=False, action_on_missing_golden="update"
            )
            hdbg.dassert_file_exists(file_name)
            new_golden = hio.from_file(file_name)
        finally:
            # Clean up.
            hio.delete_file(file_name)
        # Actual doesn't match the golden outcome and it was updated.
        self.assertTrue(outcome_updated)
        self.assertFalse(file_exists)
        self.assertFalse(is_equal)
        #
        self.assertEqual(new_golden, "hello world")


# #############################################################################
# TestCheckDataFrame1
# #############################################################################


class TestCheckDataFrame1(hunitest.TestCase):
    """
    Some of these tests can't pass with `--update_outcomes`, since they
    exercise the logic in `--update_outcomes` itself.
    """

    def test_check_df_equal1(self) -> None:
        """
        Compare the actual value of a df to a matching golden outcome.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1, 2], [3, 4, 5]], columns="a b c".split())
        abort_on_error = True
        err_threshold = 0.0001
        outcome_updated, file_exists, is_equal = self._check_df_helper(
            act, abort_on_error, err_threshold
        )
        # Actual outcome matches the golden outcome and it wasn't updated.
        self.assertFalse(outcome_updated)
        self.assertTrue(file_exists)
        self.assertTrue(is_equal)

    def test_check_df_equal2(self) -> None:
        """
        Compare the actual value of a df to a matching golden outcome.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1.01, 2], [3, 4, 5]], columns="a b c".split())
        abort_on_error = True
        err_threshold = 0.05
        outcome_updated, file_exists, is_equal = self._check_df_helper(
            act, abort_on_error, err_threshold
        )
        # Actual outcome matches the golden outcome and it wasn't updated.
        self.assertFalse(outcome_updated)
        self.assertTrue(file_exists)
        self.assertTrue(is_equal)

    def test_check_df_equal3(self) -> None:
        """
        Compare the actual value of a df to a matching golden outcome.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1.05, 2], [3, 4, 5]], columns="a b c".split())
        abort_on_error = True
        err_threshold = 0.05
        outcome_updated, file_exists, is_equal = self._check_df_helper(
            act, abort_on_error, err_threshold
        )
        # Actual outcome matches the golden outcome and it wasn't updated.
        self.assertFalse(outcome_updated)
        self.assertTrue(file_exists)
        self.assertTrue(is_equal)

    def test_check_df_not_equal1(self) -> None:
        """
        Compare the actual value of a df to a non-matching golden outcome.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1.06, 2], [3, 4, 5]], columns="a b c".split())
        abort_on_error = False
        err_threshold = 0.05
        outcome_updated, file_exists, is_equal = self._check_df_helper(
            act, abort_on_error, err_threshold
        )
        # Actual outcome doesn't match the golden outcome and it wasn't updated.
        self.assertFalse(outcome_updated)
        self.assertTrue(file_exists)
        self.assertFalse(is_equal)
        exp_error_msg = """
            actual=
            a b c
            0 0 1.06 2
            1 3 4.00 5
            expected=
            a b c
            0 0 1 2
            1 3 4 5
            actual_masked=
            [[ nan 1.06 nan]
            [ nan nan nan]]
            expected_masked=
            [[nan 1. nan]
            [nan nan nan]]
            err=
            [[ nan 0.06 nan]
            [ nan nan nan]]
            max_err=0.060
        """
        self.assert_equal(self._error_msg, exp_error_msg, fuzzy_match=True)

    def test_check_df_not_equal2(self) -> None:
        """
        Compare the actual value of a df to a not matching golden outcome.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1, 2], [3, 4, 5]], columns="a d c".split())
        abort_on_error = False
        err_threshold = 0.05
        outcome_updated, file_exists, is_equal = self._check_df_helper(
            act, abort_on_error, err_threshold
        )
        # Actual outcome doesn't match the golden outcome and it wasn't updated.
        self.assertFalse(outcome_updated)
        self.assertTrue(file_exists)
        self.assertFalse(is_equal)

    def test_check_df_not_equal3(self) -> None:
        """
        Compare the actual value to a mismatching golden outcome and update it.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1, 2], [3, 4, 5]], columns="a b c".split())
        golden_outcome = pd.DataFrame(
            [[0, 2, 2], [3, 4, 5]], columns="a b c".split()
        )
        # Force updating the golden outcomes.
        self.mock_update_tests()
        tag = "test_df"
        _, file_name = self._get_golden_outcome_file_name(tag)
        # Modify the golden.
        hio.create_enclosing_dir(file_name, incremental=True)
        golden_outcome.to_csv(file_name)
        try:
            # Check.
            outcome_updated, file_exists, is_equal = self.check_dataframe(
                act, abort_on_error=False
            )
            #
            new_golden = pd.read_csv(file_name, index_col=0)
        finally:
            # Clean up.
            hio.to_file(file_name, str(golden_outcome))
            _git_add(file_name)
        # Actual doesn't match the golden outcome and it was updated.
        self.assertTrue(outcome_updated)
        self.assertTrue(file_exists)
        self.assertFalse(is_equal)
        # Check golden.
        self.assert_equal(str(new_golden), str(act))

    def test_check_df_not_equal4(self) -> None:
        """
        Like `test_check_df_not_equal1()` but raising the exception.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1.06, 2], [3, 4, 5]], columns="a b c".split())
        abort_on_error = True
        err_threshold = 0.05
        with self.assertRaises(RuntimeError):
            self._check_df_helper(act, abort_on_error, err_threshold)

    def test_check_df_missing1(self) -> None:
        """
        When running with --update_outcomes, the golden outcome was missing and
        so it was added.

        This tests the code path when action_on_missing_golden="update".
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1, 2], [3, 4, 5]], columns="a b c".split())
        # Force updating the golden outcomes.
        self.mock_update_tests()
        tag = "test_df"
        _, file_name = self._get_golden_outcome_file_name(tag)
        _LOG.debug(hprint.to_str("file_name"))
        try:
            # Remove the golden.
            hio.delete_file(file_name)
            # Check.
            outcome_updated, file_exists, is_equal = self.check_dataframe(
                act, abort_on_error=False
            )
            hdbg.dassert_file_exists(file_name)
            new_golden = pd.read_csv(file_name, index_col=0)
        finally:
            # Clean up.
            hio.delete_file(file_name)
            _git_add(file_name)
        # Expected outcome doesn't exists and it was updated.
        self.assertTrue(outcome_updated)
        self.assertFalse(file_exists)
        self.assertFalse(is_equal)
        # Check golden.
        self.assert_equal(str(new_golden), str(act))

    def test_check_df_missing2(self) -> None:
        """
        Without running with --update_outcomes, the golden outcome was missing,
        action_on_missing_golden="assert", and the unit test framework
        asserted.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1, 2], [3, 4, 5]], columns="a b c".split())
        tag = "test_df"
        _, file_name = self._get_golden_outcome_file_name(tag)
        try:
            # Remove the golden.
            hio.delete_file(file_name)
            # Check.
            outcome_updated, file_exists, is_equal = self.check_dataframe(
                act, abort_on_error=False, action_on_missing_golden="assert"
            )
            hdbg.dassert_file_exists(file_name + ".tmp")
            new_golden = pd.read_csv(file_name + ".tmp", index_col=0)
            hdbg.dassert_path_not_exists(file_name)
        finally:
            # Clean up.
            hio.delete_file(file_name)
        # Expected outcome doesn't exists and it was not updated.
        self.assertFalse(outcome_updated)
        self.assertFalse(file_exists)
        self.assertIs(is_equal, None)
        # Check golden.
        self.assert_equal(str(new_golden), str(act))

    def test_check_df_missing3(self) -> None:
        """
        Without running with --update_outcomes, the golden outcome was missing,
        action_on_missing_golden="update", and the unit test framework updates
        the golden.
        """
        if _to_skip_on_update_outcomes():
            return
        act = pd.DataFrame([[0, 1, 2], [3, 4, 5]], columns="a b c".split())
        tag = "test_df"
        _, file_name = self._get_golden_outcome_file_name(tag)
        try:
            # Remove the golden.
            hio.delete_file(file_name)
            # Check.
            outcome_updated, file_exists, is_equal = self.check_dataframe(
                act, abort_on_error=False, action_on_missing_golden="update"
            )
            hdbg.dassert_file_exists(file_name)
            new_golden = pd.read_csv(file_name, index_col=0)
        finally:
            # Clean up.
            hio.delete_file(file_name)
        # Expected outcome doesn't exists and it was not updated.
        self.assertTrue(outcome_updated)
        self.assertFalse(file_exists)
        self.assertIs(is_equal, None)
        # Check golden.
        self.assert_equal(str(new_golden), str(act))

    def _check_df_helper(
        self, act: pd.DataFrame, abort_on_error: bool, err_threshold: float
    ) -> Tuple[bool, bool, Optional[bool]]:
        golden_outcomes = pd.DataFrame(
            [[0, 1, 2], [3, 4, 5]], columns="a b c".split()
        )
        #
        tag = "test_df"
        _, file_name = self._get_golden_outcome_file_name(tag)
        # Overwrite the golden file, so that --update_golden doesn't matter.
        hio.create_enclosing_dir(file_name, incremental=True)
        golden_outcomes.to_csv(file_name)
        try:
            outcome_updated, file_exists, is_equal = self.check_dataframe(
                act, abort_on_error=abort_on_error, err_threshold=err_threshold
            )
        finally:
            # Clean up.
            golden_outcomes.to_csv(file_name)
            _git_add(file_name)
        return outcome_updated, file_exists, is_equal


# #############################################################################
# Test_check_string_debug1
# #############################################################################


class Test_check_string_debug1(hunitest.TestCase):
    def test1(self) -> None:
        act = "hello"
        # action_on_missing_golden = "assert"
        action_on_missing_golden = "update"
        self.check_string(act, action_on_missing_golden=action_on_missing_golden)

    def test2(self) -> None:
        act = pd.DataFrame([[0, 1, 2], [3, 4, 5]], columns="a b c".split())
        # action_on_missing_golden = "assert"
        action_on_missing_golden = "update"
        self.check_dataframe(
            act, action_on_missing_golden=action_on_missing_golden
        )


# #############################################################################
# Test_get_dir_signature1
# #############################################################################


class Test_get_dir_signature1(hunitest.TestCase):
    def helper(self, include_file_content: bool) -> str:
        in_dir = self.get_input_dir()
        act = hunitest.get_dir_signature(
            in_dir, include_file_content, num_lines=None
        )
        text_purifier = huntepur.TextPurifier()
        act = text_purifier.purify_txt_from_client(act)
        return act  # type: ignore[no-any-return]

    def test1(self) -> None:
        """
        Test dir signature excluding the file content.
        """
        include_file_content = False
        act = self.helper(include_file_content)
        # pylint: disable=line-too-long
        exp = r"""
        # Dir structure
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_0
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_0/config.pkl
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_0/config.txt
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_0/run_notebook.0.log
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_1
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_1/config.pkl
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_1/config.txt
        $GIT_ROOT/helpers/test/outcomes/Test_get_dir_signature1.test1/input/result_1/run_notebook.1.log
        """
        # pylint: enable=line-too-long
        self.assert_equal(act, exp, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test dir signature including the file content.
        """
        include_file_content = True
        act = self.helper(include_file_content)
        # The golden outcome is long and uninteresting so we use check_string.
        self.check_string(act, fuzzy_match=True)
