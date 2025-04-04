"""
Import as:

import helpers.hretry as hretry
"""
import asyncio
import functools
import logging
import time
from typing import Any, Dict, Tuple, Union

_LOG = logging.getLogger(__name__)


def sync_retry(
    num_attempts_attr: Union[str, int],
    exceptions: Dict[Any, Tuple[bool, str]],
    *,
    retry_delay_in_sec: int = 0,
) -> object:
    """
    Decorator retrying the wrapped function/method num_attempts times if the
    `exceptions` listed in exceptions are thrown.

    :param num_attempts_attr: the number of attempts to make before
        giving up or a string attribute name to get the number of
        attempts from the object
    :param exceptions: A dictionary mapping exceptions to a (bool, str)
        tuple. The boolean indicates whether to retry (True) or raise
        (False), and the string specifies a custom log message. E.g.,
        {TimeoutError: (True, "Retrying due to timeout"), ValueError:
        (False, None)}
    :param retry_delay_in_sec: the number of seconds to wait between
        retry attempts
    :return: the result of the wrapped function/method
    """

    def decorator(func) -> object:
        @functools.wraps(func)
        def retry_wrapper(self, *args, **kwargs):
            num_attempts = (
                getattr(self, num_attempts_attr)
                if isinstance(num_attempts_attr, str)
                else num_attempts_attr
            )
            attempts_count = 1
            last_exception = None
            while attempts_count < num_attempts + 1:
                try:
                    return func(self, *args, **kwargs)
                # Catch all exceptions in the exceptions dictionary.
                except tuple(exceptions.keys()) as e:
                    last_exception = e
                    # Get the retry and custom message values from the
                    # exceptions dictionary for the exception type.
                    retry_and_raise, custom_message = exceptions[type(e)]
                    _LOG.warning(
                        "Exception %s thrown when attempting to run %s, attempt "
                        "%d of %d",
                        e,
                        func,
                        attempts_count,
                        num_attempts,
                    )
                    if custom_message is not None:
                        _LOG.warning(custom_message)
                    # We might not want to retry attempting the function after
                    # certain exceptions, hence the `retry_and_raise` flag. If
                    # False, break the loop and do not retry the function else
                    # retry the function.
                    if not retry_and_raise:
                        break
                    attempts_count += 1
                    time.sleep(retry_delay_in_sec)
            _LOG.error("Function %s failed after %d attempts", func, num_attempts)
            # We might not want to raise the exception for certain exceptions,
            # hence the `retry_and_raise` flag. Raise the last exception if
            # if True else do nothing.
            if retry_and_raise:
                raise last_exception

        return retry_wrapper

    return decorator


def async_retry(
    num_attempts_attr: Union[str, int],
    exceptions: Dict[Any, Tuple[bool, str]],
    *,
    retry_delay_in_sec: int = 0,
) -> object:
    """
    Same as `sync_retry` decorator but for `async` functions.
    """

    def decorator(func) -> object:
        @functools.wraps(func)
        async def retry_wrapper(self, *args, **kwargs):
            num_attempts = (
                getattr(self, num_attempts_attr)
                if isinstance(num_attempts_attr, str)
                else num_attempts_attr
            )
            attempts_count = 1
            last_exception = None
            while attempts_count < num_attempts + 1:
                try:
                    return await func(self, *args, **kwargs)
                # Catch all exceptions in the exceptions dictionary.
                except tuple(exceptions.keys()) as e:
                    last_exception = e
                    # Get the retry and custom message values from the
                    # exceptions dictionary for the exception type.
                    retry_and_raise, custom_message = exceptions[type(e)]
                    _LOG.warning(
                        "Exception %s thrown when attempting to run %s, attempt "
                        "%d of %d",
                        e,
                        func,
                        attempts_count,
                        num_attempts,
                    )
                    if custom_message is not None:
                        _LOG.warning(custom_message)
                    # We might not want to retry attempting the function after
                    # certain exceptions, hence the `retry_and_raise` flag. If
                    # False, break the loop and do not retry the function else
                    # retry the function.
                    if not retry_and_raise:
                        break
                    attempts_count += 1
                    await asyncio.sleep(retry_delay_in_sec)
            _LOG.error("Function %s failed after %d attempts", func, num_attempts)
            # We might not want to raise the exception for certain exceptions,
            # hence the `retry_and_raise` flag. Raise the last exception if
            # if True else do nothing.
            if retry_and_raise:
                raise last_exception

        return retry_wrapper

    return decorator
