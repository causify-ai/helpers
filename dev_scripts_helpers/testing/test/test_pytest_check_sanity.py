"""Test the public pytest sanity checker with real files and pytest processes."""

import json
import os
import shlex
import subprocess
import sys
import unittest.mock as umock
from typing import Any, Dict

import dev_scripts_helpers.testing.pytest_check_sanity as dshtpchsa
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest


# #############################################################################
# Test_pytest_check_sanity_py
# #############################################################################


class Test_pytest_check_sanity_py(hunitest.TestCase):
    """Test `pytest_check_sanity.py` end to end."""

    def helper(self, output_format: str) -> Dict[str, Any]:
        """Run actual pytest collection and execution, then check saved
        reports.
        """
        root = self.get_scratch_space()
        config = os.path.join(root, "pytest.ini")
        config_text = """
        [pytest]
        norecursedirs = omitted
        """
        hio.to_file(config, hprint.dedent(config_text))
        source = """
        def test_pass():
            assert True
        class TestGroup:
            def test_method(self):
                assert True
        """
        hio.to_file(os.path.join(root, "test_a.py"), hprint.dedent(source))
        omitted_dir = os.path.join(root, "omitted")
        os.makedirs(omitted_dir)
        hidden_source = """
        def test_missing():
            assert True
        """
        hio.to_file(
            os.path.join(omitted_dir, "test_hidden.py"),
            hprint.dedent(hidden_source),
        )
        # Isolate the fixture's pytest run from this repository's plugins.
        parts = [
            shlex.quote(sys.executable),
            "-m pytest",
            "-c",
            shlex.quote(config),
            "--confcutdir",
            shlex.quote(root),
            "--rootdir",
            shlex.quote(root),
            "--color=no",
            shlex.quote(root),
        ]
        command = "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 " + " ".join(parts)
        rc, collected = hsystem.system_to_string(command + " --collect-only -q")
        self.assertEqual(rc, 0)
        rc, executed = hsystem.system_to_string(command + " -vv")
        self.assertEqual(rc, 0)
        collection_path = os.path.join(root, "collected.log")
        execution_path = os.path.join(root, "executed.log")
        output_path = os.path.join(root, "sanity." + output_format)
        hio.to_file(collection_path, collected)
        hio.to_file(execution_path, executed)
        argv = [
            "pytest_check_sanity.py",
            "--pytest_input",
            execution_path,
            "--collection_input",
            collection_path,
            "--code_input",
            root,
            "--output",
            output_path,
            "--format",
            output_format,
        ]
        with umock.patch.object(sys, "argv", argv):
            exit_code = dshtpchsa._main(dshtpchsa._parse())
        self.assertEqual(exit_code, 1)
        output = hio.from_file(output_path)
        return (
            json.loads(output) if output_format == "json" else {"output": output}
        )

    def test1(self) -> None:
        """Detect an omitted directory despite an otherwise passing real test
        run.
        """
        # Prepare inputs.
        output_format = "json"
        expected = {"not_collected": 1, "passed": 2}
        # Run test.
        actual = self.helper(output_format)
        # Check outputs.
        self.assertEqual(actual["summary"], expected)
        self.assertTrue(actual["collection_complete"])

    def test2(self) -> None:
        """Escape HTML-like node IDs and reasons in the standalone HTML
        report.
        """
        # Prepare inputs.
        report = {
            "summary": {"skipped": 1},
            "tests": [
                {
                    "status": "skipped",
                    "nodeid": "test.py::test[<script>]",
                    "reason": "a & b",
                }
            ],
            "source_errors": {},
            "collection_errors": {},
            "warnings": [],
        }
        output_format = "html"
        # Run test.
        actual = dshtpchsa._render_report(report, output_format)
        # Check outputs.
        expected = (
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            "<title>Pytest source sanity</title><body><pre>"
            "Pytest source sanity\n\nSummary:\n  skipped: 1\n\nTests:\n"
            "  skipped: test.py::test[&lt;script&gt;]\n    a &amp; b\n"
            "</pre></body></html>\n"
        )
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """An empty, truncated capture cannot pass CI with an empty source
        tree.
        """
        root = self.get_scratch_space()
        input_path = os.path.join(root, "executed.log")
        output_path = os.path.join(root, "sanity.json")
        hio.to_file(input_path, "collecting ...\n")
        argv = [
            "pytest_check_sanity.py",
            "--pytest_input",
            input_path,
            "--code_input",
            root,
            "--output",
            output_path,
        ]
        with umock.patch.object(sys, "argv", argv):
            actual = dshtpchsa._main(dshtpchsa._parse())
        self.assertEqual(actual, 1)
        report = json.loads(hio.from_file(output_path))
        self.assertFalse(report["collection_complete"])

    def test4(self) -> None:
        """Custom naming rules still reveal a source test omitted from
        collection.
        """
        root = self.get_scratch_space()
        hio.to_file(
            os.path.join(root, "pytest.ini"),
            "[pytest]\npython_files = check_*.py\npython_functions = verify\n",
        )
        hio.to_file(
            os.path.join(root, "check_a.py"), "def verify_missing(): pass\n"
        )
        input_path = os.path.join(root, "collected.log")
        output_path = os.path.join(root, "sanity.json")
        hio.to_file(input_path, "0 tests collected in 0.01s\n")
        argv = [
            "pytest_check_sanity.py",
            "--pytest_input",
            input_path,
            "--code_input",
            root,
            "--output",
            output_path,
        ]
        with umock.patch.object(sys, "argv", argv):
            actual = dshtpchsa._main(dshtpchsa._parse())
        self.assertEqual(actual, 1)
        report = json.loads(hio.from_file(output_path))
        self.assertEqual(
            report["tests"][0]["nodeid"], "check_a.py::verify_missing"
        )
        self.assertEqual(report["tests"][0]["status"], "not_collected")

    def test5(self) -> None:
        """Preserve real verbose skip reasons and call execution before teardown
        errors.
        """
        root = self.get_scratch_space()
        hio.to_file(os.path.join(root, "pytest.ini"), "[pytest]\n")
        source = """
        import pytest
        def test_pass():
            assert True
        @pytest.mark.skip(reason="optional feature unavailable")
        def test_skip():
            pass
        @pytest.mark.xfail(reason="known mismatch")
        def test_xfail():
            assert False
        @pytest.fixture
        def teardown_error():
            yield
            raise RuntimeError("fixture cleanup failed")
        def test_teardown(teardown_error):
            assert True
        """
        hio.to_file(
            os.path.join(root, "test_outcomes.py"), hprint.dedent(source)
        )
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-vv",
            "--color=no",
            "--tb=short",
        ]
        result = subprocess.run(
            command,
            cwd=root,
            env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        input_path = os.path.join(root, "executed.log")
        output_path = os.path.join(root, "sanity.json")
        hio.to_file(input_path, result.stdout)
        argv = [
            "pytest_check_sanity.py",
            "--pytest_input",
            input_path,
            "--code_input",
            root,
            "--pytest_cwd",
            root,
            "--output",
            output_path,
        ]
        with umock.patch.object(sys, "argv", argv):
            exit_code = dshtpchsa._main(dshtpchsa._parse())
        self.assertEqual(exit_code, 1)
        report = json.loads(hio.from_file(output_path))
        self.assertEqual(
            report["summary"],
            {"error": 1, "passed": 1, "skipped": 1, "xfailed": 1},
        )
        self.assertTrue(report["collection_complete"])
        cases = {item["nodeid"]: item for item in report["tests"]}
        self.assertEqual(
            cases["test_outcomes.py::test_skip"]["reason"],
            "optional feature unavailable",
        )
        self.assertEqual(
            cases["test_outcomes.py::test_xfail"]["reason"], "known mismatch"
        )
        self.assertTrue(
            cases["test_outcomes.py::test_teardown"]["call_executed"]
        )
