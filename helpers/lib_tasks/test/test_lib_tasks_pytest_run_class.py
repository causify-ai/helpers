import contextlib
import io
import os
import shlex
import unittest.mock as umock
from typing import Tuple

import invoke
import pytest

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_pytest as hltltapy

# pylint: disable=protected-access


# #############################################################################
# Test_pytest_run_class
# #############################################################################


@pytest.mark.slow
class Test_pytest_run_class(hunitest.TestCase):
    """
    Exercise the real finder and pytest, without collecting unrelated modules.
    """

    def _prepare(self, *, fail: bool = False) -> Tuple[str, str, str]:
        """
        Create a test suite under a path requiring shell quoting.
        """
        root = os.path.join(self.get_scratch_space(), "suite space' $value")
        test_dir = os.path.join(root, "test")
        os.makedirs(test_dir)
        marker = os.path.join(root, "executed.txt")
        target = os.path.join(test_dir, "test_selected.py")
        source = f"""
        class TestSelected(object):
            def test_selected(self):
                with open({marker!r}, "a") as stream:
                    stream.write("selected;")
                assert {not fail!r}

        class TestSelectedExtra(object):
            def test_extra(self):
                with open({marker!r}, "a") as stream:
                    stream.write("extra;")
        """
        hio.to_file(target, hprint.dedent(source))
        # Collecting this unrelated module must fail, even before tests run.
        unrelated = os.path.join(test_dir, "test_unrelated.py")
        hio.to_file(unrelated, 'raise RuntimeError("Unrelated collection")')
        hio.to_file(os.path.join(root, "pytest.ini"), "[pytest]")
        return root, marker, target

    def _run(
        self,
        root: str,
        *,
        class_name: str = "TestSelected",
        test_file: bool = False,
        preview: bool = False,
    ) -> str:
        """
        Run with an isolated pytest configuration and capture task stdout.
        """
        config = os.path.join(root, "pytest.ini")
        pytest_opts = (
            f"-q -c {shlex.quote(config)} --confcutdir {shlex.quote(root)}"
        )
        env = {
            "PYTEST_ADDOPTS": pytest_opts,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "SKIP_VERSION_CHECK": "1",
        }
        output = io.StringIO()
        with (
            umock.patch.dict(os.environ, env),
            contextlib.redirect_stdout(output),
        ):
            hltltapy.pytest_run_class.body(
                None,
                class_name,
                dir_name=root,
                test_file=test_file,
                preview=preview,
            )
        return output.getvalue()

    def test1(self) -> None:
        """
        Run only the exact class, with no import of an unrelated test module.
        """
        root, marker, _ = self._prepare()
        self._run(root)
        actual = hio.from_file(marker)
        expected = "selected;"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        File mode runs both classes in the selected file and no other file.
        """
        root, marker, _ = self._prepare()
        self._run(root, test_file=True)
        actual = hio.from_file(marker)
        expected = "selected;extra;"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Preview prints a reusable command and does not run the selected test.
        """
        root, marker, target = self._prepare()
        output = self._run(root, preview=True)
        actual = shlex.split(output.splitlines()[-1])
        expected = ["pytest", f"{target}::TestSelected"]
        self.assertEqual(actual, expected)
        self.assertFalse(os.path.exists(marker))

    def test4(self) -> None:
        """
        Preview of file mode contains exactly the selected file argument.
        """
        root, marker, target = self._prepare()
        output = self._run(root, test_file=True, preview=True)
        actual = shlex.split(output.splitlines()[-1])
        expected = ["pytest", target]
        self.assertEqual(actual, expected)
        self.assertFalse(os.path.exists(marker))

    def test5(self) -> None:
        """
        A partial class name must not run any tests.
        """
        root, marker, _ = self._prepare()
        class_name = "TestSelect"
        with self.assertRaises(AssertionError):
            self._run(root, class_name=class_name)
        self.assertFalse(os.path.exists(marker))

    def test6(self) -> None:
        """
        Ambiguous classes fail before execution, including in file mode.
        """
        root, marker, _ = self._prepare()
        duplicate = os.path.join(root, "test", "test_duplicate.py")
        source = """
        class TestSelected(object):
            pass
        """
        hio.to_file(duplicate, hprint.dedent(source))
        for test_file in (False, True):
            with self.assertRaises(AssertionError):
                self._run(root, test_file=test_file)
        self.assertFalse(os.path.exists(marker))

    def test7(self) -> None:
        """
        Empty and whitespace-only names cannot launch the full suite.
        """
        root, marker, _ = self._prepare()
        for class_name in ("", "   "):
            with self.assertRaises(AssertionError):
                self._run(root, class_name=class_name)
        self.assertFalse(os.path.exists(marker))

    def test8(self) -> None:
        """
        Preserve pytest's failure exit status instead of reporting success.
        """
        root, marker, _ = self._prepare(fail=True)
        with self.assertRaises(invoke.exceptions.Exit) as cm:
            self._run(root)
        self.assertEqual(cm.exception.code, 1)
        actual = hio.from_file(marker)
        expected = "selected;"
        self.assert_equal(actual, expected)

    def test9(self) -> None:
        """
        Preserve pytest's no-tests-collected exit status as well.
        """
        root, marker, target = self._prepare()
        source = """
        class TestSelected(object):
            pass
        """
        hio.to_file(target, hprint.dedent(source))
        with self.assertRaises(invoke.exceptions.Exit) as cm:
            self._run(root)
        self.assertEqual(cm.exception.code, 5)
        self.assertFalse(os.path.exists(marker))
