import logging
from typing import Any, Dict, List, Optional, Union

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hprint as hprint

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

    :param name: The name to include in the greeting
    :param greeting: The base greeting message to use
    :return: Formatted greeting string
    """
    _LOG.debug("Formatting greeting for name='%s'", name)
    return f"{greeting}, {name}!"


# #############################################################################
# Main functionality
# #############################################################################


class Greeter:
    """
    A class that handles greeting operations with caching capabilities.
    """

    def __init__(self, *, default_greeting: str = DEFAULT_GREETING) -> None:
        """
        Initialize the Greeter with a default greeting.

        :param default_greeting: The default greeting to use
        """
        self._greeting_cache: Dict[str, str] = {}
        self._default_greeting = default_greeting
        _LOG.debug("Initialized Greeter with default greeting='%s'", default_greeting)

    def greet(self, name: str, *, greeting: Optional[str] = None) -> str:
        """
        Generate a greeting for the given name.

        :param name: The name to greet
        :param greeting: Optional custom greeting to use
        :return: The formatted greeting message
        :raises ValueError: If name is empty
        """
        hdbg.dassert_ne(name, "", "Name cannot be empty")
        # Check cache first.
        cache_key = f"{name}_{greeting}"
        if cache_key in self._greeting_cache:
            _LOG.debug("Cache hit for name='%s'", name)
            return self._greeting_cache[cache_key]
        _LOG.debug("Cache miss for name='%s'", name)
        greeting = greeting or self._default_greeting
        result = _format_greeting(name, greeting)
        # Update cache.
        self._greeting_cache[cache_key] = result
        return result

    def get_greeting_stats(self) -> pd.DataFrame:
        """
        Get statistics about the greeting cache.

        :return: DataFrame containing cache statistics
        """
        stats = {
            "total_greetings": len(self._greeting_cache),
            "unique_names": len(set(k.split("_")[0] for k in self._greeting_cache.keys())),
        }
        return pd.Series(stats).to_frame().T


# #############################################################################
# Example usage
# #############################################################################

def main() -> None:
    """
    Demonstrate the usage of the Greeter class.
    """
    greeter = Greeter()
    # Basic usage.
    print(greeter.greet("Alice"))  # Hello World, Alice!
    # Custom greeting.
    print(greeter.greet("Bob", "Good morning"))  # Good morning, Bob!
    # Show stats.
    print("\nGreeting Statistics:")
    print(greeter.get_greeting_stats())


if __name__ == "__main__":
    main()

