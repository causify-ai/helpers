"""
Import as:

import template_code as tecode
"""

import logging
from typing import Dict, Optional

import pandas as pd

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################


# Default greeting message.
DEFAULT_GREETING = "Hello World"


# #############################################################################
# Helper functions
# #############################################################################


def _format_greeting(name: str, *, greeting: str = DEFAULT_GREETING) -> str:
    """
    Format a greeting message with the given name.

    :param name: the name to include in the greeting
    :param greeting: the base greeting message to use
    :return: formatted greeting
    """
    _LOG.debug("Formatting greeting for name='%s'", name)
    greeting = f"{greeting}, {name}!"
    return greeting


# #############################################################################
# Greeter
# #############################################################################


class Greeter:
    """
    A class that handles greeting operations with caching capabilities.
    """

    def __init__(self, *, default_greeting: str = DEFAULT_GREETING) -> None:
        """
        Initialize the Greeter with a default greeting.

        :param default_greeting: the default greeting to use
        """
        self._greeting_cache: Dict[str, str] = {}
        self._default_greeting = default_greeting
        _LOG.debug(
            "Initialized Greeter with default greeting='%s'", default_greeting
        )

    def greet(self, name: str, *, greeting: Optional[str] = None) -> str:
        """
        Generate a greeting for the given name.

        :param name: the name to greet
        :param greeting: optional custom greeting to use
        :return: the formatted greeting message
        """
        hdbg.dassert_ne(name, "", "Name cannot be empty")
        # Check cache first.
        cache_key = f"{name}_{greeting}"
        if cache_key in self._greeting_cache:
            _LOG.debug("Cache hit for name='%s'", name)
            greeting_with_name = self._greeting_cache[cache_key]
            return greeting_with_name
        # Create a greeting message.
        _LOG.debug("Cache miss for name='%s'", name)
        greeting = greeting or self._default_greeting
        greeting_with_name = _format_greeting(name, greeting=greeting)
        # Update cache.
        self._greeting_cache[cache_key] = greeting_with_name
        return greeting_with_name

    def get_greeting_stats(self) -> pd.DataFrame:
        """
        Get statistics about the greeting cache.

        :return: cache statistics
        """
        stats = {
            "total_greetings": len(self._greeting_cache),
            "unique_names": len(
                set(k.split("_")[0] for k in self._greeting_cache)
            ),
        }
        stats_out = pd.Series(stats).to_frame().T
        return stats_out


# #############################################################################
# Example usage
# #############################################################################


def main() -> None:
    """
    Demonstrate the usage of the Greeter class.
    """
    greeter = Greeter()
    # Use the default greeting.
    print(greeter.greet("Alice"))
    # Use a custom greeting.
    print(greeter.greet("Bob", greeting="Good morning"))
    # Show stats.
    print("\nGreeting Statistics:")
    print(greeter.get_greeting_stats())


if __name__ == "__main__":
    main()
