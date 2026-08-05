"""
Import as:

import helpers.hretry as hretry
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional, Tuple, cast

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# Type of the function being wrapped/returned by the decorators below.
_RetriedFunc = Callable[..., Any]

# Defaults for `num_attempts` and `retry_delay_in_sec`, shared by `sync_retry`
# and `async_retry`.
_MAX_RETRIES = 3
_RETRY_DELAY_SEC = 5


def sync_retry(
    exceptions: Tuple[Any, ...],
    *,
    num_attempts: int = _MAX_RETRIES,
    retry_delay_in_sec: int = _RETRY_DELAY_SEC,
) -> Callable[[_RetriedFunc], _RetriedFunc]:
    """
    Decorator retrying the wrapped function/method num_attempts times if the
    `exceptions` listed in exceptions are thrown.

    :param exceptions: list of exceptions that trigger a retry attempt
    :param num_attempts: the number of times to repeat the wrapped
        function/method
      - The function will be called `num_attempts` times.
    :param retry_delay_in_sec: the number of seconds to wait between retry
        attempts
    :return: the result of the wrapped function/method
    """

    def decorator(func: _RetriedFunc) -> _RetriedFunc:
        @functools.wraps(func)
        def retry_wrapper(*args, **kwargs):
            attempts_count = 1
            last_exception: Optional[BaseException] = None
            while attempts_count < num_attempts + 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    _LOG.warning(
                        "Exception %s thrown when attempting to run %s, attempt "
                        "%d of %d",
                        e,
                        func,
                        attempts_count,
                        num_attempts,
                    )
                    attempts_count += 1
                    time.sleep(retry_delay_in_sec)
            _LOG.error(
                "Function %s failed after %d attempts", func, num_attempts
            )
            hdbg.dassert_is_not(
                last_exception, None, "No exception was captured"
            )
            # `dassert_is_not` guarantees `last_exception` is set, but pyright
            # can't infer that from a custom assertion function.
            raise cast(BaseException, last_exception)
        return retry_wrapper

    return decorator


def async_retry(
    exceptions: Tuple[Any, ...],
    *,
    num_attempts: int = _MAX_RETRIES,
    retry_delay_in_sec: int = _RETRY_DELAY_SEC,
) -> Callable[[_RetriedFunc], _RetriedFunc]:
    """
    Same as `sync_retry` decorator but for `async` functions.
    """

    def decorator(func: _RetriedFunc) -> _RetriedFunc:
        @functools.wraps(func)
        async def retry_wrapper(*args, **kwargs):
            attempts_count = 1
            last_exception: Optional[BaseException] = None
            while attempts_count < num_attempts + 1:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    _LOG.warning(
                        "Exception %s thrown when attempting to run %s, attempt "
                        "%d of %d",
                        e,
                        func,
                        attempts_count,
                        num_attempts,
                    )
                    attempts_count += 1
                    await asyncio.sleep(retry_delay_in_sec)
            _LOG.error(
                "Function %s failed after %d attempts", func, num_attempts
            )
            hdbg.dassert_is_not(
                last_exception, None, "No exception was captured"
            )
            # `dassert_is_not` guarantees `last_exception` is set, but pyright
            # can't infer that from a custom assertion function.
            raise cast(BaseException, last_exception)
        return retry_wrapper

    return decorator
