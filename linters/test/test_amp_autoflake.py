import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_autoflake as lampauto


class TestAutoflake(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that unused imports are removed.
        """
        text = """
import re
import string
from typing import List, Tuple

import numpy as np
import pandas as pd

import helpers.hio as hio
import linters.action as liaction


def func() -> Tuple[str, str]:
    text = hio.from_file("test.txt")
    text_modified = re.sub("1", "2", txt)
    return text, text_modified

text, text_modified = func()
df = pd.DataFrame({text: [text_modified]})
"""

        expected = """
import re
from typing import Tuple

import pandas as pd

import helpers.hio as hio


def func() -> Tuple[str, str]:
    text = hio.from_file("test.txt")
    text_modified = re.sub("1", "2", txt)
    return text, text_modified

text, text_modified = func()
df = pd.DataFrame({text: [text_modified]})
"""
        actual = self._autoflake(text)
        self.assertEqual(expected, actual)

    def test2(self) -> None:
        """
        Test that unused variables are removed.
        """
        text = """
def func() -> int:
    a = 2
    b = 3
    c = a + b
    d = "unused"
    return c
"""
        expected = """
def func() -> int:
    a = 2
    b = 3
    c = a + b
    return c
"""
        actual = self._autoflake(text)
        self.assertEqual(expected, actual)

    def _autoflake(self, text: str) -> str:
        """
        Run the `autoflake` wrapper.

        :param text: content of the file to be modified
        :return: modified content after autoflake
        """
        root_dir = hgit.get_client_root(super_module=False)
        test_file = os.path.join(root_dir, "autoflake.tmp.py")
        hio.to_file(test_file, text)
        _ = lampauto._Autoflake()._execute(file_name=test_file, pedantic=0)
        content: str = hio.from_file(test_file)
        hio.delete_file(test_file)
        return content
