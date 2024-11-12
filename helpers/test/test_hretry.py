import asyncio
import logging

import helpers.hretry as hretry
import helpers.htimer as htimer
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

EXCEPTIONS = {AttributeError: (True, "ATTRIBUTE ERROR"), ValueError: (True, None)}


class Test_retry(hunitest.TestCase):
    def test_retry1(self) -> None:
        """
        Test normal case.
        """
        self.exception_count = 0
        self.num_attempts = 3

        @hretry.sync_retry("num_attempts", EXCEPTIONS)
        def func(self) -> bool:
            if self.exception_count < self.num_attempts - 1:
                self.exception_count += 1
                raise ValueError("Simulated expected error")
            _LOG.debug("All good")
            return True

        self.assertTrue(func(self))
        self.assertEqual(self.exception_count, self.num_attempts - 1)

    def test_retry2(self) -> None:
        """
        Test when the number of exceptions is greater than the number of
        retries.
        """
        self.exception_count = 0
        self.num_attempts = 3

        @hretry.sync_retry("num_attempts", EXCEPTIONS)
        def func(self) -> bool:
            if self.exception_count < self.num_attempts:
                self.exception_count += 1
                raise ValueError("Simulated expected error")
            _LOG.debug("All good")
            return True

        with self.assertRaises(ValueError):
            func(self)

    def test_retry3(self) -> None:
        """
        Test when the raised exception is not in the list of expected
        exceptions.
        """
        self.exception_count = 0
        self.num_attempts = 3

        @hretry.sync_retry("num_attempts", EXCEPTIONS)
        def func(self) -> None:
            if self.exception_count < self.num_attempts - 1:
                self.exception_count += 1
                raise IndexError("Simulated non expected error")
            _LOG.debug("All good")

        with self.assertRaises(IndexError):
            func(self)


class Test_retry2(hunitest.TestCase):
    def test_async_retry1(self) -> None:
        """
        Test normal case.
        """
        self.exception_count = 0
        self.num_attempts = 3
        retry_delay_in_sec = 1

        @hretry.async_retry(
            "num_attempts", EXCEPTIONS, retry_delay_in_sec=retry_delay_in_sec
        )
        async def func(self) -> bool:
            if self.exception_count < self.num_attempts - 1:
                self.exception_count += 1
                await asyncio.sleep(0.1)
                raise ValueError("Simulated expected error")
            _LOG.debug("All good")
            return True

        with htimer.TimedScope(logging.INFO, "async_retry_loop") as ts:
            result = asyncio.run(func(self))
        self.assertEqual(round(ts.elapsed_time, 1), 2.2)
        self.assertTrue(result)
        self.assertEqual(self.exception_count, self.num_attempts - 1)

    def test_async_retry2(self) -> None:
        """
        Test when the number of exceptions is greater than the number of
        retries.
        """
        self.exception_count = 0
        self.num_attempts = 3
        retry_delay_in_sec = 1

        @hretry.async_retry(
            "num_attempts", EXCEPTIONS, retry_delay_in_sec=retry_delay_in_sec
        )
        async def func(self) -> bool:
            if self.exception_count < self.num_attempts:
                self.exception_count += 1
                await asyncio.sleep(0.1)
                raise ValueError("Simulated expected error")
            _LOG.debug("All good")
            return True

        with self.assertRaises(ValueError) as fail:
            with htimer.TimedScope(logging.INFO, "async_retry_loop") as ts:
                asyncio.run(func(self))
        self.assertEqual(round(ts.elapsed_time, 1), 3.3)
        actual = str(fail.exception)
        expected = "Simulated expected error"
        self.assert_equal(actual, expected)

    def test_async_retry3(self) -> None:
        """
        Test when the raised exception is not in the list of expected
        exceptions.
        """
        self.exception_count = 0
        self.num_attempts = 3
        retry_delay_in_sec = 1

        @hretry.async_retry(
            "num_attempts", EXCEPTIONS, retry_delay_in_sec=retry_delay_in_sec
        )
        async def func(self) -> None:
            if self.exception_count < self.num_attempts - 1:
                self.exception_count += 1
                await asyncio.sleep(0.1)
                raise IndexError("Simulated non expected error")
            _LOG.debug("All good")

        with self.assertRaises(IndexError) as fail:
            asyncio.run(func(self))
        actual = str(fail.exception)
        expected = "Simulated non expected error"
        self.assert_equal(actual, expected)
