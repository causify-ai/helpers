"""Test pytest evidence ingestion for the source-to-execution sanity checker."""

import copy
import pprint
from typing import Any, Dict

import helpers.hpytest_sanity as hpytsani
import helpers.hpytest_sanity_inventory as hpysainv
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# Test_parse_json_report
# #############################################################################


class Test_parse_json_report(hunitest.TestCase):
    """Test `helpers.hpytest_sanity.parse_json_report()`."""

    def helper(self) -> Dict[str, Any]:
        """Build a report with two collected cases and one completed case."""
        report = {
            "root": "/fixture",
            "exitcode": 0,
            "summary": {"collected": 2},
            "collectors": [
                {
                    "nodeid": "test_a.py",
                    "outcome": "passed",
                    "result": [
                        {
                            "nodeid": "test_a.py::test1[first [case]]",
                            "lineno": 1,
                        },
                        {"nodeid": "test_a.py::test1[second case]", "lineno": 1},
                    ],
                }
            ],
            "tests": [
                {
                    "nodeid": "test_a.py::test1[first [case]]",
                    "lineno": 1,
                    "outcome": "passed",
                    "call": {"outcome": "passed"},
                }
            ],
        }
        return copy.deepcopy(report)

    def test5(self) -> None:
        """A module-level skip is intentional skip evidence, not a collection
        error.
        """
        report = {
            "root": "/fixture",
            "exitcode": 5,
            "summary": {"collected": 0},
            "collectors": [
                {
                    "nodeid": "test_a.py",
                    "outcome": "skipped",
                    "longrepr": "optional dependency unavailable",
                }
            ],
            "tests": [],
        }
        source = hpysainv.SourceTest("test_a.py::test1", "test_a.py", 1, "")
        inventory = hpysainv.SourceInventory({source.nodeid: source}, {})
        evidence = hpytsani.parse_json_report(report)
        actual = hpytsani.analyze_inventory(inventory, evidence)
        self.assertEqual(actual["tests"][0]["status"], "skipped")
        self.assertEqual(
            actual["tests"][0]["reason"], "optional dependency unavailable"
        )
        self.assertEqual(len(actual["collection_errors"]), 0)

    def test1(self) -> None:
        """Preserve parameter IDs and leave unexecuted outcomes unset."""
        # Prepare inputs.
        report = self.helper()
        # Prepare outputs.
        expected = {
            "test_a.py::test1[first [case]]": {
                "outcome": "passed",
                "reason": "",
                "line": 1,
                "call_executed": True,
            },
            "test_a.py::test1[second case]": {
                "outcome": "",
                "reason": "",
                "line": 1,
                "call_executed": False,
            },
        }
        # Run test.
        actual = hpytsani.parse_json_report(report)
        # Check outputs.
        self.assert_equal(pprint.pformat(actual.items), pprint.pformat(expected))
        self.assertTrue(actual.collection_complete)

    def test2(self) -> None:
        """Keep runtime skip reasons separate from deselected items."""
        # Prepare inputs.
        report = self.helper()
        report["collectors"][0]["result"][1]["deselected"] = True
        report["tests"][0].pop("call")
        report["tests"][0]["outcome"] = "skipped"
        report["tests"][0]["setup"] = {
            "outcome": "skipped",
            "longrepr": "maintenance window",
        }
        # Prepare outputs.
        expected = [
            ("skipped", "setup: maintenance window", False),
            ("deselected", "", False),
        ]
        # Run test.
        evidence = hpytsani.parse_json_report(report)
        actual = [
            (item["outcome"], item["reason"], item["call_executed"])
            for item in evidence.items.values()
        ]
        # Check outputs.
        self.assert_equal(pprint.pformat(actual), pprint.pformat(expected))

    def test3(self) -> None:
        """A runtime-only report does not prove collection completeness."""
        # Prepare inputs.
        report = self.helper()
        report.pop("collectors")
        # Run test.
        evidence = hpytsani.parse_json_report(report)
        # Check outputs.
        self.assertFalse(evidence.collection_complete)
        self.assertEqual(len(evidence.items), 1)

    def test4(self) -> None:
        """Collection failures and interrupted runs are incomplete evidence."""
        # Prepare inputs.
        report = self.helper()
        report["exitcode"] = 2
        report["collectors"].append(
            {
                "nodeid": "test_b.py",
                "outcome": "failed",
                "longrepr": "syntax error",
            }
        )
        expected = {"test_b.py": "syntax error"}
        # Run test.
        evidence = hpytsani.parse_json_report(report)
        # Check outputs.
        self.assertFalse(evidence.collection_complete)
        self.assert_equal(
            pprint.pformat(evidence.collection_errors), pprint.pformat(expected)
        )


# #############################################################################
# Test_analyze_inventory
# #############################################################################


class Test_analyze_inventory(hunitest.TestCase):
    """Test source-to-execution reconciliation."""

    def helper(self, complete: bool) -> Dict[str, Any]:
        """Analyze one omitted source test and one executed parameter case."""
        definitions = {
            name: hpysainv.SourceTest(name, name.split("::")[0], 1, "")
            for name in ("test_a.py::test1", "ignored/test_b.py::test2")
        }
        inventory = hpysainv.SourceInventory(definitions, {})
        items = {
            "test_a.py::test1[case [one]]": {
                "outcome": "passed",
                "reason": "",
                "line": 0,
                "call_executed": True,
            }
        }
        evidence = hpytsani.PytestEvidence(
            "/fixture", items, {}, complete, 0, []
        )
        return hpytsani.analyze_inventory(inventory, evidence)

    def test1(self) -> None:
        """A complete inventory distinguishes omitted source tests from cases."""
        # Prepare inputs.
        complete = True
        expected = {"not_collected": 1, "passed": 1}
        # Run test.
        actual = self.helper(complete)
        # Check outputs.
        self.assert_equal(
            pprint.pformat(actual["summary"]), pprint.pformat(expected)
        )

    def test2(self) -> None:
        """Incomplete collection does not prove a missing source test was
        omitted.
        """
        # Prepare inputs.
        complete = False
        expected = {"passed": 1, "unknown": 1}
        # Run test.
        actual = self.helper(complete)
        # Check outputs.
        self.assert_equal(
            pprint.pformat(actual["summary"]), pprint.pformat(expected)
        )


# #############################################################################
# Test_parse_terminal_report
# #############################################################################


class Test_parse_terminal_report(hunitest.TestCase):
    """Test saved pytest flat collection and verbose execution output."""

    def helper(self, text: str) -> hpytsani.PytestEvidence:
        """Parse a saved log relative to a fixed source root."""
        text = hprint.dedent(text)
        root = "/fixture"
        return hpytsani.parse_terminal_report(text, root, invocation_dir=root)

    def test1(self) -> None:
        """Flat collection retains spaces and brackets in parametrized IDs."""
        # Prepare inputs.
        text = """
        test_a.py::test1[first [case]]
        test_a.py::test1[second case]
        2 tests collected in 0.01s
        """
        expected = [
            "test_a.py::test1[first [case]]",
            "test_a.py::test1[second case]",
        ]
        # Run test.
        actual = self.helper(text)
        # Check outputs.
        self.assertTrue(actual.collection_complete)
        self.assert_equal(
            pprint.pformat(sorted(actual.items)), pprint.pformat(expected)
        )

    def test2(self) -> None:
        """Read the repository's duration prefix without altering node
        identity.
        """
        # Prepare inputs.
        text = """
        collected 1 item
        test_a.py::TestOne::test1 (0.02 s) PASSED [100%]
        ==================== 1 passed in 0.02s ====================
        """
        expected = ["test_a.py::TestOne::test1"]
        # Run test.
        actual = self.helper(text)
        # Check outputs.
        self.assertTrue(actual.collection_complete)
        self.assert_equal(
            pprint.pformat(sorted(actual.items)), pprint.pformat(expected)
        )

    def test3(self) -> None:
        """A truncated execution log does not prove all tests were observed."""
        # Prepare inputs.
        text = """
        collected 2 items
        test_a.py::test1 PASSED [50%]
        """
        # Run test.
        actual = self.helper(text)
        # Check outputs.
        self.assertFalse(actual.collection_complete)
        self.assertEqual(len(actual.items), 1)

    def test4(self) -> None:
        """Normalize verbose paths using the original process working
        directory.
        """
        text = "collected 1 item\nfixture/test_a.py::test1 PASSED [100%]\n=== 1 passed in 0.01s ==="
        actual = hpytsani.parse_terminal_report(
            text, "/repo/fixture", invocation_dir="/repo"
        )
        self.assertTrue(actual.collection_complete)
        self.assert_equal(
            pprint.pformat(list(actual.items)), "['test_a.py::test1']"
        )


# #############################################################################
# Test_merge_evidence
# #############################################################################


class Test_merge_evidence(hunitest.TestCase):
    """Test contradictory captures and preservation of unexecuted cases."""

    def test1(self) -> None:
        """A missing execution outcome remains unexecuted after
        reconciliation.
        """
        collection = hpytsani.parse_terminal_report(
            "test_a.py::test1\ntest_a.py::test2\n2 tests collected in 0.01s",
            "/fixture",
        )
        execution = hpytsani.parse_terminal_report(
            "collected 2 items\ntest_a.py::test1 PASSED [50%]",
            "/fixture",
            invocation_dir="/fixture",
        )
        actual = hpytsani.merge_evidence(collection, execution)
        self.assertTrue(actual.collection_complete)
        self.assertEqual(actual.items["test_a.py::test2"]["outcome"], "")
        self.assertEqual(collection.items["test_a.py::test1"]["outcome"], "")

    def test2(self) -> None:
        """Different selected cases must not establish a complete merged
        capture.
        """
        collection = hpytsani.parse_terminal_report(
            "test_a.py::test1\n1 test collected", "/fixture"
        )
        execution = hpytsani.parse_terminal_report(
            "collected 1 item\ntest_a.py::test2 PASSED [100%]\n=== 1 passed in 0.01s ===",
            "/fixture",
            invocation_dir="/fixture",
        )
        actual = hpytsani.merge_evidence(collection, execution)
        self.assertFalse(actual.collection_complete)
        self.assertEqual(len(actual.items), 2)
