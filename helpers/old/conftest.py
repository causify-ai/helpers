import pathlib
from typing import Any, Optional


def pytest_ignore_collect(  # type: ignore
    collection_path: pathlib.Path, config: Any
) -> Optional[bool]:
    """
    Skip all tests in this directory.

    :param collection_path: path to analyze
    :param config: pytest config object
    :return: True if the path should be ignored
    """
    # Ignore this directory and all its subdirectories.
    return True
