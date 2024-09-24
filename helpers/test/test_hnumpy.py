import logging

import numpy as np
import collections

import helpers.hnumpy as hnumpy
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


class TestRandomSeedContext(hunitest.TestCase):
    def test_example1(self) -> None:
        """
        Getting more random numbers without context manager changes the
        sequence of random numbers.
        """
        n = 3
        # First batch.
        np.random.seed(0)
        vals1a = np.random.randn(n)
        vals2a = np.random.randn(n)
        # Second batch.
        np.random.seed(0)
        vals1b = np.random.randn(n)
        vals = np.random.randn(n)
        _ = vals
        vals2b = np.random.randn(n)
        # Check.
        self.assertEqual(str(vals1a), str(vals1b))
        # Of course this might fail with a vanishingly small probability.
        self.assertNotEqual(str(vals2a), str(vals2b))

    def test_example2(self) -> None:
        """
        Getting more random numbers with context manager doesn't change the
        sequence of random numbers.
        """
        n = 3
        # First batch.
        np.random.seed(0)
        vals1a = np.random.randn(n)
        vals2a = np.random.randn(n)
        # Second batch.
        np.random.seed(0)
        vals1b = np.random.randn(n)
        with hnumpy.random_seed_context(42):
            vals = np.random.randn(n)
            _ = vals
        vals2b = np.random.randn(n)
        # Check.
        self.assertEqual(str(vals1a), str(vals1b))
        self.assertEqual(str(vals2a), str(vals2b))


class TestFloorWithPrecision(hunitest.TestCase):
    def test_floor_with_precision1(self) -> None:
        """
        Test for negative float values as input.
        """
        expected_as_str = "-4.63"
        self._test_floor_with_precision(-4.6385, 2, expected_as_str)

    def test_floor_with_precision2(self) -> None:
        """
        Test for Zero precision.
        """
        expected_as_str = "-4.0"
        self._test_floor_with_precision(-4.6385, 0, expected_as_str)

    def test_floor_with_precision3(self) -> None:
        """
        Test for negative precision.
        """
        value = 4.6385
        amount_precision = -2
        with self.assertRaises(AssertionError) as cm:
            hnumpy.floor_with_precision(value, amount_precision)
        # Check.
        act = str(cm.exception)
        exp = """
        * Failed assertion *
        0 <= -2
        """
        self.assert_equal(act, exp, fuzzy_match=True)

    def test_floor_with_precision4(self) -> None:
        """
        Test for positive float values as input.
        """
        expected_as_str = "4.63"
        self._test_floor_with_precision(4.6385, 2, expected_as_str)

    def test_floor_with_precision5(self) -> None:
        """
        Test for integer values as input.
        """
        expected_as_str = "4.0"
        self._test_floor_with_precision(4, 0, expected_as_str)

    def test_floor_with_precision6(self) -> None:
        """
        Test for very small value as input.
        """
        expected = 0.0000532
        self._test_floor_with_precision(0.0000532999, 7, str(expected))

    def test_floor_with_precision7(self) -> None:
        """
        Test for very large value as input.
        """
        expected_as_str = "4289734.12345"
        self._test_floor_with_precision(4289734.1234599999, 5, expected_as_str)

    def _test_floor_with_precision(
        self,
        value: float,
        precision: int,
        expected: str,
    ) -> None:
        """ """
        actual = hnumpy.floor_with_precision(value, precision)
        self.assert_equal(str(actual), expected)


class Test_OrderedDict_repr_str(hunitest.TestCase):
    """
    The tests are used to gatekeep the expected behavior of
    dunder method __str__ and __repr__ for the OrderedDict class.

    The tests stem from changes in Python 3.12. Observe below:

    Python 3.9.5:
        >>> from collections import OrderedDict
        >>> import numpy
        >>> dct = OrderedDict({ "test": numpy.int64(42)})
        >>> dct["test"]
        42
        >>> print(dct)
        OrderedDict([('test', 42)])
        >>> str(dct)
        "OrderedDict([('test', 42)])"
        >>> repr(dct)
        "OrderedDict([('test', 42)])"
        >>> str(dct["test"])
        '42'
        >>> repr(dct["test"])
        '42'

    Python 3.12.3:
        >>> from collections import OrderedDict
        >>> import numpy
        >>> dct = OrderedDict({"test": numpy.int64(42)})
        >>> dct = OrderedDict({"test": numpy.int64(42)})
        KeyboardInterrupt
        >>> str(dct)
        "OrderedDict({'test': np.int64(42)})"
        >>> repr(dct)
        "OrderedDict({'test': np.int64(42)})"
        >>> str(dct["test"])
        '42'
        >>> repr(dct["test"])
        'np.int64(42)'
    """

    def test_str_single1(self) -> None:
        """
        Test that the __str__ method on a single item in OrderedDict returns the expected string.
        """
        d = collections.OrderedDict({"test": np.int64(42)})
        act = str(d["test"])
        exp = "42"
        self.assert_equal(act, exp)

    def test_repr_single1(self) -> None:
        """
        Test that the __repr__ method on a single item in OrderedDict returns the expected string.
        """
        d = collections.OrderedDict({"test": np.int64(42)})
        act = repr(d["test"])
        exp = "np.int64(42)"
        self.assert_equal(act, exp)
    
    def test_str_full1(self) -> None:
        """
        Test that the __str__ method of OrderedDict returns the expected string.
        """
        d = collections.OrderedDict({"test": np.int64(42)})
        act = str(d)
        exp = "OrderedDict({'test': np.int64(42)})"
        self.assert_equal(act, exp)

    def test_repr_full1(self) -> None:
        """
        Test that the __repr__ method of OrderedDict returns the expected string.
        """
        d = collections.OrderedDict({"test": np.int64(42)})
        act = repr(d)
        exp = "OrderedDict({'test': np.int64(42)})"
        self.assert_equal(act, exp)
