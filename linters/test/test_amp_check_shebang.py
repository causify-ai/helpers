import pytest

import helpers.hunit_test as hunitest
import linters.amp_check_shebang as lamchshe


@pytest.mark.skip(reason="Need to install mock")
class Test_check_shebang(hunitest.TestCase):
    def test1(self) -> None:
        """
        Executable with wrong shebang: error.
        """
        file_name = "exec.py"
        txt = """#!/bin/bash
hello
world
"""
        is_executable = True
        expected = "exec.py:1: any executable needs to start with a shebang '#!/usr/bin/env python'"
        self._helper_check_shebang(file_name, txt, is_executable, expected)

    def test2(self) -> None:
        """
        Executable with the correct shebang: correct.
        """
        file_name = "exec.py"
        txt = """#!/usr/bin/env python
hello
world
"""
        is_executable = True
        expected = ""
        self._helper_check_shebang(file_name, txt, is_executable, expected)

    def test3(self) -> None:
        """
        Non executable with a shebang: error.
        """
        file_name = "exec.py"
        txt = """#!/usr/bin/env python
hello
world
"""
        is_executable = False
        expected = "exec.py:1: a non-executable can't start with a shebang."
        self._helper_check_shebang(file_name, txt, is_executable, expected)

    def test4(self) -> None:
        """
        Library without a shebang: correct.
        """
        file_name = "lib.py"
        txt = '''"""
Import as:

import _setenv_lib as selib
'''
        is_executable = False
        expected = ""
        self._helper_check_shebang(file_name, txt, is_executable, expected)

    def _helper_check_shebang(
        self,
        file_name: str,
        txt: str,
        is_executable: bool,
        expected: str,
    ) -> None:
        import mock

        txt_array = txt.split("\n")

        with mock.patch("os.access", return_value=is_executable):
            msg = lamchshe._check_shebang(file_name, txt_array)
        self.assert_equal(msg, expected)
