import unittest.mock as umock

import pytest

import helpers.lib_tasks.lib_tasks_pytest_run_class as hltltaprc
import helpers.hunit_test as hunitest

# pylint: disable=protected-access


class Test_resolve_pytest_class_target1(hunitest.TestCase):
    def test_success1(self) -> None:
        file_names = ["helpers/foo/test/test_bar.py"]
        matches = ["helpers/foo/test/test_bar.py::TestBar"]
        with (
            umock.patch.object(
                hltltaprc.hltltafi,
                "_find_test_files",
                return_value=file_names,
            ) as find_files,
            umock.patch.object(
                hltltaprc.hltltafi,
                "_find_test_class",
                return_value=matches,
            ) as find_class,
        ):
            actual = hltltaprc._resolve_pytest_class_target("TestBar", ".")
        self.assert_equal(actual, matches[0])
        find_files.assert_called_once_with(".")
        find_class.assert_called_once_with(
            "TestBar", file_names, exact_match=True
        )

    def test_missing1(self) -> None:
        with (
            umock.patch.object(
                hltltaprc.hltltafi,
                "_find_test_files",
                return_value=["helpers/foo/test/test_bar.py"],
            ),
            umock.patch.object(
                hltltaprc.hltltafi, "_find_test_class", return_value=[]
            ),
            pytest.raises(ValueError, match="Could not find test class"),
        ):
            hltltaprc._resolve_pytest_class_target("TestMissing", ".")

    def test_ambiguous1(self) -> None:
        matches = [
            "helpers/a/test/test_a.py::TestSame",
            "helpers/b/test/test_b.py::TestSame",
        ]
        with (
            umock.patch.object(
                hltltaprc.hltltafi,
                "_find_test_files",
                return_value=["a", "b"],
            ),
            umock.patch.object(
                hltltaprc.hltltafi, "_find_test_class", return_value=matches
            ),
            pytest.raises(ValueError, match="ambiguous"),
        ):
            hltltaprc._resolve_pytest_class_target("TestSame", ".")


class Test_pytest_run_class1(hunitest.TestCase):
    def test_build_command1(self) -> None:
        target = "helpers/foo/test/test_bar.py::TestBar"
        with umock.patch.object(
            hltltaprc,
            "_resolve_pytest_class_target",
            return_value=target,
        ):
            actual = hltltaprc._build_pytest_run_class_command("TestBar")
        self.assert_equal(actual, f"pytest {target}")

    def test_dry_run1(self) -> None:
        ctx = umock.Mock()
        with (
            umock.patch.object(
                hltltaprc,
                "_build_pytest_run_class_command",
                return_value="pytest path/test_x.py::TestX",
            ),
            umock.patch.object(hltltaprc.hltltapy, "_run_test_cmd") as run_cmd,
        ):
            actual = hltltaprc.pytest_run_class.body(
                ctx, "TestX", dry_run=True
            )
        self.assert_equal(actual, 0)
        run_cmd.assert_not_called()

    def test_run1(self) -> None:
        ctx = umock.Mock()
        with (
            umock.patch.object(
                hltltaprc,
                "_build_pytest_run_class_command",
                return_value="pytest path/test_x.py::TestX",
            ),
            umock.patch.object(
                hltltaprc.hltltapy, "_run_test_cmd", return_value=7
            ) as run_cmd,
        ):
            actual = hltltaprc.pytest_run_class.body(
                ctx,
                "TestX",
                stage="dev",
                version="1.2.3",
                skip_pull=True,
            )
        self.assert_equal(actual, 7)
        run_cmd.assert_called_once_with(
            ctx,
            "dev",
            "1.2.3",
            "pytest path/test_x.py::TestX",
            coverage=False,
            collect_only=False,
            skip_pull=True,
            start_coverage_script=False,
        )
