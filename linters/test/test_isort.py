import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_isort as lampisor


class TestISort(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that isort groups imports properly.

        Modules linters.base and linters.utils must exist in this repo
        in order to be qualified as first-party.
        """
        text = """
import helpers.hio as hio
import pandas as pd

import linters.base as libase
import linters.utils as liutils
import tempfile
"""

        expected = """
import tempfile

import pandas as pd

import helpers.hio as hio
import linters.base as libase
import linters.utils as liutils
"""
        actual = self._isort(text)
        self.assertEqual(expected, actual)

    def test2(self) -> None:
        """
        Test that comments are not moved.
        """
        text = """
import logging
import os  # Inline comment.
import re

# Avoid dependency from other `helpers` modules, such as `helpers.henv`, to prevent
# import cycles.

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio

# End of imports.
"""

        actual = self._isort(text)
        self.assertEqual(text, actual)

    def _isort(self, text: str) -> str:
        """
        Apply isort, then return the modified content.

        :param text: content to be isort-ed
        :return: modified content after isort
        """
        root_dir = hgit.get_client_root(super_module=False)
        test_file = os.path.join(root_dir, "isort.tmp.py")
        hio.to_file(test_file, text)
        _ = lampisor._ISort()._execute(file_name=test_file, pedantic=0)
        content: str = hio.from_file(test_file)
        hio.delete_file(test_file)
        return content
