"""
Import as:

import helpers.himport as himport
"""

import importlib
import warnings
from types import ModuleType
from typing import Optional


def try_import(
    module: str,
) -> Optional[ModuleType]:
    try:
        return importlib.import_module(module)
    except ImportError:
        warnings.warn(f"Module '{module}' is not installed.")
        return None
