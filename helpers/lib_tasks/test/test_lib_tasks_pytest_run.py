import os
import unittest.mock as umock

import invoke.context as icontext
import pytest

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_pytest_run as hltltpyru


# #############################################################################
# Test_pytest_run_class1
# #############################################################################


class Test_pytest_run_class1(hunitest.TestCase):
    def _create_test_tree(self, duplicate: bool = False) -> str:
        search_root = os.path.join(self.get_scratch_space(), "path with spaces")
        file_dict = {
            "test/test_selected.py": hprint.dedent(
                """
                class TestSelected(object):
                    pass

                class TestSelectedExtra(object):
                    pass
                """
            ),
        }
        if duplicate:
            file_dict["test/test_duplicate.py"] = hprint.dedent(
                """
                class TestSelected(object):
                    pass
                """
            )
        hunitest.create_test_dir(
            search_root, incremental=True, file_dict=file_dict
        )
        return search_root

    def test_exact_class(self) -> None:
        search_root = self._create_test_tree()
        actual = hltltpyru._resolve_pytest_class_target(
            "TestSelected", search_root, run_file=False
        )
        expected = os.path.join(
            search_root, "test/test_selected.py::TestSelected"
        )
        self.assert_equal(actual, expected)

    def test_containing_file(self) -> None:
        search_root = self._create_test_tree()
        actual = hltltpyru._resolve_pytest_class_target(
            "TestSelected", search_root, run_file=True
        )
        expected = os.path.join(search_root, "test/test_selected.py")
        self.assert_equal(actual, expected)

    def test_no_match(self) -> None:
        search_root = self._create_test_tree()
        ctx = icontext.Context()
        with umock.patch.object(ctx, "run") as run:
            with pytest.raises(ValueError, match="Could not find test class"):
                hltltpyru.pytest_run_class(
                    ctx, "TestMissing", search_root=search_root
                )
        run.assert_not_called()

    def test_empty_class_name(self) -> None:
        with pytest.raises(ValueError, match="specify a class name"):
            hltltpyru._resolve_pytest_class_target(
                "", self.get_scratch_space(), run_file=False
            )

    def test_ambiguous_match(self) -> None:
        search_root = self._create_test_tree(duplicate=True)
        ctx = icontext.Context()
        with umock.patch.object(ctx, "run") as run:
            with pytest.raises(ValueError, match="ambiguous; found 2 matches"):
                hltltpyru.pytest_run_class(
                    ctx, "TestSelected", search_root=search_root
                )
        run.assert_not_called()

    def test_safe_path_quoting(self) -> None:
        search_root = self._create_test_tree()
        actual = hltltpyru._build_pytest_run_class_command(
            "TestSelected", search_root=search_root
        )
        target = os.path.join(search_root, "test/test_selected.py::TestSelected")
        expected = f"pytest '{target}'"
        self.assert_equal(actual, expected)

    def test_preview_does_not_execute(self) -> None:
        search_root = self._create_test_tree()
        ctx = icontext.Context()
        with umock.patch.object(ctx, "run") as run:
            actual = hltltpyru.pytest_run_class(
                ctx,
                "TestSelected",
                preview=True,
                search_root=search_root,
            )
        self.assertEqual(actual, 0)
        run.assert_not_called()

    def test_failure_is_propagated(self) -> None:
        search_root = self._create_test_tree()
        ctx = icontext.Context()
        with umock.patch.object(
            ctx, "run", side_effect=RuntimeError("pytest failed")
        ):
            with pytest.raises(RuntimeError, match="pytest failed"):
                hltltpyru.pytest_run_class(
                    ctx, "TestSelected", search_root=search_root
                )
