import os
import shlex
import sys
from typing import Tuple

import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest


# #############################################################################
# Test_pytest_run_class_integration1
# #############################################################################


class Test_pytest_run_class_integration1(hunitest.TestCase):
    def _create_test_tree(self) -> str:
        search_root = os.path.join(
            self.get_scratch_space(), "path with spaces 'quote $dollar"
        )
        file_dict = {
            "test/test_selected.py": hprint.dedent(
                """
                class TestSelected:
                    def test_passes(self):
                        assert True

                class TestSibling(object):
                    def test_fails(self):
                        raise AssertionError("sibling executed")

                class TestPreview(object):
                    def test_must_not_run(self):
                        raise AssertionError("preview executed")

                class TestNoTests(object):
                    pass

                class TestOuter:
                    if True:
                        class TestInner:
                            def test_passes(self):
                                assert True
                """
            ),
            "test/test_unrelated.py": hprint.dedent(
                """
                raise RuntimeError("unrelated module collected")
                """
            ),
        }
        hunitest.create_test_dir(
            search_root, incremental=True, file_dict=file_dict
        )
        return search_root

    def _run_invoke(self, args: str) -> Tuple[int, str]:
        python_dir = os.path.dirname(sys.executable)
        cmd = (
            f"PATH={shlex.quote(python_dir)}:$PATH "
            "CSFY_ECR_BASE_PATH=unused "
            f"{shlex.quote(sys.executable)} -m invoke {args}"
        )
        return hsystem.system_to_string(cmd, abort_on_error=False)

    def test_registered_task_runs_only_selected_class(self) -> None:
        search_root = self._create_test_tree()
        quoted_root = shlex.quote(search_root)
        args = f"pytest_run_class -c TestSelected --search-root {quoted_root}"
        rc, output = self._run_invoke(args)
        self.assertEqual(rc, 0)
        self.assertIn("1 passed", output)
        self.assertNotIn("sibling executed", output)
        self.assertNotIn("unrelated module collected", output)

    def test_registered_task_runs_nested_class(self) -> None:
        search_root = self._create_test_tree()
        quoted_root = shlex.quote(search_root)
        args = f"pytest_run_class -c TestInner --search-root {quoted_root}"
        rc, output = self._run_invoke(args)
        self.assertEqual(rc, 0)
        self.assertIn("1 passed", output)
        self.assertNotIn("unrelated module collected", output)

    def test_registered_task_runs_nested_class_containing_file(self) -> None:
        search_root = self._create_test_tree()
        quoted_root = shlex.quote(search_root)
        args = (
            "--warn-only pytest_run_class -c TestInner --run-file "
            f"--search-root {quoted_root}"
        )
        rc, output = self._run_invoke(args)
        self.assertEqual(rc, 1)
        self.assertIn("sibling executed", output)
        self.assertNotIn("unrelated module collected", output)

    def test_registered_task_previews_without_execution(self) -> None:
        search_root = self._create_test_tree()
        quoted_root = shlex.quote(search_root)
        args = (
            "pytest_run_class -c TestPreview --preview "
            f"--search-root {quoted_root}"
        )
        rc, output = self._run_invoke(args)
        self.assertEqual(rc, 0)
        preview_target = os.path.join(
            search_root, "test/test_selected.py::TestPreview"
        )
        expected = f"pytest {shlex.quote(preview_target)}"
        self.assertIn(expected, output.splitlines())
        self.assertNotIn("preview executed", output)
        self.assertNotIn("1 failed", output)

    def test_registered_task_propagates_containing_file_failure(self) -> None:
        search_root = self._create_test_tree()
        quoted_root = shlex.quote(search_root)
        args = (
            "--warn-only pytest_run_class -c TestSelected --run-file "
            f"--search-root {quoted_root}"
        )
        rc, output = self._run_invoke(args)
        self.assertEqual(rc, 1)
        self.assertIn("sibling executed", output)
        self.assertNotIn("unrelated module collected", output)

    def test_registered_task_propagates_no_tests_exit(self) -> None:
        search_root = self._create_test_tree()
        quoted_root = shlex.quote(search_root)
        args = (
            "--warn-only pytest_run_class -c TestNoTests "
            f"--search-root {quoted_root}"
        )
        rc, output = self._run_invoke(args)
        self.assertEqual(rc, 5)
        self.assertIn("no tests ran", output)
        self.assertNotIn("unrelated module collected", output)

    def test_cli_help(self) -> None:
        rc, output = self._run_invoke("--help pytest_run_class")
        self.assertEqual(rc, 0)
        self.assertIn("-c STRING, --class-name=STRING", output)
        self.assertIn("--preview", output)
        self.assertIn("--run-file", output)
        self.assertIn("--search-root=STRING", output)
