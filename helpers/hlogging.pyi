"""
Type stub for hlogging module with custom Logger that includes trace method.
"""

import logging
from typing import Any

class Logger(logging.Logger):
    """
    Custom Logger class that includes trace method.
    """
    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

def getLogger(name: str) -> Logger: ...
