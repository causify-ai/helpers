import logging
import os
from typing import Dict, List, Tuple

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_check_private_functions as lamchprfu

_LOG = logging.getLogger(__name__)


class Test_find_private_function_candidates(hunitest.TestCase):
    """
    Test finding the functions that should be private.
    """

    def helper(
        self,
        files: Dict[str, str],
        file_name: str,
        expected: List[Tuple[str, int]],
    ) -> None:
        """
        Create the input files, run the check and compare the outcome.

        :param files: contents by file name
        :param file_name: the file to check
        :param expected: expected (function name, line number) pairs
        """
        in_dir = self.get_input_dir()
        hio.create_dir(in_dir, incremental=True)
        for cur_file_name, content in files.items():
            hio.to_file(os.path.join(in_dir, cur_file_name), content)
        file_path = os.path.join(in_dir, file_name)
        usages = lamchprfu._collect_usages(in_dir)
        actual = lamchprfu._find_private_function_candidates(file_path, usages)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test a function that is used only within its file and a function
        that is not used anywhere.
        """
        files = {
            "a.py": "\n".join(
                [
                    "def foo() -> int:",
                    "    return 1",
                    "",
                    "",
                    "def bar() -> int:",
                    "    return foo() + 1",
                ]
            ),
        }
        # `bar` is not used anywhere, so it is a candidate as well.
        expected = [("foo", 1), ("bar", 5)]
        self.helper(files, "a.py", expected)

    def test2(self) -> None:
        """
        Test a function that is also used in another file.
        """
        files = {
            "a.py": "\n".join(["def foo():", "    return 1"]),
            "b.py": "\n".join(["import a", "", "x = a.foo()"]),
        }
        expected = []
        self.helper(files, "a.py", expected)

    def test3(self) -> None:
        """
        Test that private, `main` and dunder functions are skipped.
        """
        files = {
            "a.py": "\n".join(
                [
                    "def _private() -> None:",
                    "    pass",
                    "",
                    "",
                    "def main() -> None:",
                    "    pass",
                    "",
                    "",
                    "def __dunder__() -> None:",
                    "    pass",
                ]
            ),
        }
        expected = []
        self.helper(files, "a.py", expected)

    def test4(self) -> None:
        """
        Test a function that is not used anywhere.
        """
        files = {"a.py": "\n".join(["def unused():", "    pass"])}
        expected = [("unused", 1)]
        self.helper(files, "a.py", expected)

    def test5(self) -> None:
        """
        Test that an unrelated identifier with the same name in another
        file keeps the function public.
        """
        files = {
            "a.py": "\n".join(["def foo():", "    pass"]),
            "b.py": "\n".join(["foo = 3", "print(foo)"]),
        }
        expected = []
        self.helper(files, "a.py", expected)

    def test6(self) -> None:
        """
        Test that a function invoked dynamically through a decorator is
        skipped.
        """
        files = {
            "a.py": "\n".join(
                [
                    "from invoke import task",
                    "",
                    "",
                    "@task",
                    "def run_something(ctx):",
                    "    pass",
                ]
            ),
        }
        expected = []
        self.helper(files, "a.py", expected)

    def test7(self) -> None:
        """
        Test that a function exported through `__all__` is skipped.
        """
        files = {
            "a.py": "\n".join(
                [
                    '__all__ = ["foo"]',
                    "",
                    "",
                    "def foo():",
                    "    pass",
                ]
            ),
        }
        expected = []
        self.helper(files, "a.py", expected)

    def test8(self) -> None:
        """
        Test that class methods are not considered.
        """
        files = {
            "a.py": "\n".join(
                [
                    "class Dummy:",
                    "    def method(self):",
                    "        return 1",
                ]
            ),
        }
        expected = []
        self.helper(files, "a.py", expected)


class Test_CheckPrivateFunctions(hunitest.TestCase):
    """
    Test the linter action end-to-end.
    """

    def test1(self) -> None:
        """
        Test running the action on a file.
        """
        in_dir = self.get_input_dir()
        hio.create_dir(in_dir, incremental=True)
        file_name = os.path.join(in_dir, "a.py")
        content = "\n".join(
            [
                "def foo():",
                "    return 1",
                "",
                "",
                "def bar():",
                "    return foo()",
            ]
        )
        hio.to_file(file_name, content)
        action = lamchprfu._CheckPrivateFunctions(search_dirs=[in_dir])
        actual = action.execute(file_name, pedantic=0)
        file_path = os.path.abspath(file_name)
        # `bar` is not used anywhere, so it is a candidate as well.
        expected = [
            f"{file_path}:1: the function 'foo' is only used within this"
            " file and should be renamed to '_foo'",
            f"{file_path}:5: the function 'bar' is only used within this"
            " file and should be renamed to '_bar'",
        ]
        self.assertEqual(actual, expected)


class Test_fix_file(hunitest.TestCase):
    """
    Test the fix mode.
    """

    def test1(self) -> None:
        """
        Test renaming a function and its usages within the defining file.
        """
        in_dir = self.get_input_dir()
        hio.create_dir(in_dir, incremental=True)
        a_py = os.path.join(in_dir, "a.py")
        b_py = os.path.join(in_dir, "b.py")
        hio.to_file(
            a_py,
            "\n".join(
                [
                    "def foo():",
                    "    return 1",
                    "",
                    "",
                    "def bar():",
                    "    return foo()",
                ]
            ),
        )
        hio.to_file(b_py, "x = 3\n")
        msgs = lamchprfu._fix_file(a_py, [in_dir])
        # The functions and their usages in `a.py` are renamed.
        expected_content = "\n".join(
            [
                "def _foo():",
                "    return 1",
                "",
                "",
                "def _bar():",
                "    return _foo()",
            ]
        )
        self.assertEqual(hio.from_file(a_py), expected_content)
        # The other file is not touched.
        self.assertEqual(hio.from_file(b_py), "x = 3\n")
        file_path = os.path.abspath(a_py)
        expected_msgs = [
            f"{file_path}:1: renamed 'foo' to '_foo'",
            f"{file_path}:5: renamed 'bar' to '_bar'",
        ]
        self.assertEqual(msgs, expected_msgs)


class Test_get_rename_edits(hunitest.TestCase):
    """
    Test getting the position-exact rename edits.
    """

    def test1(self) -> None:
        """
        Test the edits for a def, a plain name and an attribute.
        """
        in_dir = self.get_input_dir()
        hio.create_dir(in_dir, incremental=True)
        file_name = os.path.join(in_dir, "a.py")
        lines = [
            "def foo():",
            "    return 1",
            "",
            "",
            "holder = None",
            "holder.foo = foo",
        ]
        hio.to_file(file_name, "\n".join(lines))
        actual = lamchprfu._get_rename_edits(file_name, "foo")
        # The def is at line 1; the attribute and the name are at line 6.
        expected = [
            (1, 4, 7, "_foo"),
            (6, 7, 10, "_foo"),
            (6, 13, 16, "_foo"),
        ]
        self.assertEqual(sorted(actual), expected)
