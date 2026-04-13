import logging

import helpers.hpandas as hpandas
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# Test_CheckSummary
# #############################################################################


class Test_CheckSummary(hunitest.TestCase):
    def test1(self) -> None:
        """
        All the tests have passed.
        """
        # Prepare inputs.
        obj = hpandas.CheckSummary()
        obj.add(
            "hello",
            "Number of not submitted OMS child orders=0 / 73 = 0.00%",
            True,
        )
        obj.add("hello2", "ok", True)
        # Check.
        is_ok = obj.is_ok()
        self.assertTrue(is_ok)
        #
        actual = obj.report_outcome(notebook_output=False, assert_on_error=False)
        self.check_string(actual)
        # No assertion expected.
        obj.report_outcome()

    def test2(self) -> None:
        """
        Not all the tests have passed.
        """
        # Prepare inputs.
        obj = hpandas.CheckSummary()
        obj.add(
            "hello",
            "Number of not submitted OMS child orders=0 / 73 = 0.00%",
            True,
        )
        obj.add("hello2", "not_ok", False)
        # Check.
        is_ok = obj.is_ok()
        self.assertFalse(is_ok)
        #
        actual = obj.report_outcome(notebook_output=False, assert_on_error=False)
        self.check_string(actual)
        #
        with self.assertRaises(ValueError) as e:
            actual = obj.report_outcome()
        actual_exception = str(e.exception)
        expected_exception = r"""
        The checks have failed:
          description                                            comment  is_ok
        0       hello  Number of not submitted OMS child orders=0 / 7...   True
        1      hello2                                             not_ok  False
        is_ok=False
        """
        self.assert_equal(actual_exception, expected_exception, fuzzy_match=True)
