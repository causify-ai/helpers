"""
Compare source test inventories with pytest collection and execution evidence.

Import as:

import helpers.hpytest_sanity as hpytsani
"""

import dataclasses
import logging
import os
import re
from typing import Any, Dict, List, Optional

import helpers.hdbg as hdbg
import helpers.hpytest_sanity_inventory as hpysainv

_LOG = logging.getLogger(__name__)


# #############################################################################
# PytestEvidence
# #############################################################################


@dataclasses.dataclass
class PytestEvidence:
    """
    Preserve observed items separately from the completeness of the observation.

    `items` includes individual parametrized node IDs. An absent outcome means
    unexecuted, not skipped. `collection_complete` allows the analyzer to
    distinguish a missing test from an incomplete input report.
    """

    root: str
    items: Dict[str, Dict[str, Any]]
    collection_errors: Dict[str, str]
    collection_complete: bool
    exit_code: int
    warnings: List[str]
    collection_skips: Dict[str, str] = dataclasses.field(default_factory=dict)


# #############################################################################
# Structured pytest evidence
# #############################################################################


def _get_stage_reason(test: Dict[str, Any]) -> str:
    """Retain the reported skip or failure explanation from the relevant
    stage.
    """
    _LOG.debug("Reading reason for nodeid='%s'", test.get("nodeid"))
    reasons = []
    for stage_name in ("setup", "call", "teardown"):
        stage = test.get(stage_name, {})
        # A teardown error can accompany a passed call, so retain both stages.
        if stage.get("outcome") in ("failed", "skipped"):
            reason = stage.get("longrepr", "")
            if reason:
                reasons.append(f"{stage_name}: {reason}")
    return "\n".join(reasons)


def parse_json_report(report: Dict[str, Any]) -> PytestEvidence:
    """
    Read a `pytest-json-report` object without importing the tested source.

    :param report: decoded JSON report, including collectors and test stages
    :return: observed item outcomes and collection-completeness evidence
    """
    _LOG.debug("Parsing report with keys=%s", sorted(report))
    hdbg.dassert_isinstance(report.get("root"), str, "Report root is required")
    hdbg.dassert_isinstance(
        report.get("summary"), dict, "Report summary is required"
    )
    summary = report["summary"]
    hdbg.dassert_isinstance(
        report.get("exitcode"), int, "Report exit code is required"
    )
    exit_code = report["exitcode"]
    collectors = report.get("collectors", [])
    tests = report.get("tests", [])
    hdbg.dassert_isinstance(collectors, list, "Collectors must be a list")
    hdbg.dassert_isinstance(tests, list, "Tests must be a list")
    # Collector IDs identify containers, including custom pytest collectors.
    # All remaining result nodes are items; do not hardcode Function types.
    collector_ids = {collector["nodeid"] for collector in collectors}
    items: Dict[str, Dict[str, Any]] = {}
    collection_errors = {}
    collection_skips = {}
    for collector in collectors:
        if collector.get("outcome") == "failed":
            collection_errors[collector["nodeid"]] = str(
                collector.get("longrepr", collector["outcome"])
            )
        elif collector.get("outcome") == "skipped":
            collection_skips[collector["nodeid"]] = str(
                collector.get("longrepr", "skipped")
            )
        for result in collector.get("result", []):
            nodeid = result["nodeid"]
            if nodeid in collector_ids:
                continue
            items[nodeid] = {
                "outcome": "deselected" if result.get("deselected") else "",
                "reason": "",
                "line": result.get("lineno", -1),
                "call_executed": False,
            }
    # Runtime outcomes are useful even when xdist omits successful collectors.
    collected_item_count = len(items)
    for test in tests:
        nodeid = test["nodeid"]
        items[nodeid] = {
            "outcome": test["outcome"],
            "reason": _get_stage_reason(test),
            "line": test.get("lineno", -1),
            "call_executed": "call" in test,
        }
    # A summary is not an inventory. In particular, xdist and summary-only
    # reports cannot establish that an unmentioned source test was not collected.
    expected_count = summary.get("collected")
    collection_complete = (
        "collectors" in report
        and isinstance(expected_count, int)
        and collected_item_count == expected_count
        and not collection_errors
        and exit_code in (0, 1, 5)
    )
    warnings = []
    if not collection_complete:
        warnings.append(
            "Collection inventory is incomplete or collection failed"
        )
    return PytestEvidence(
        root=report["root"],
        items=items,
        collection_errors=collection_errors,
        collection_complete=collection_complete,
        exit_code=exit_code,
        warnings=warnings,
        collection_skips=collection_skips,
    )


# #############################################################################
# Saved terminal evidence
# #############################################################################


def parse_terminal_report(
    text: str, root: str, *, invocation_dir: Optional[str] = None
) -> PytestEvidence:
    """
    Read verbose execution or flat `--collect-only -q` node-ID output.

    :param text: saved pytest stdout with optional ANSI color sequences
    :param root: node-ID root corresponding to the source inventory
    :param invocation_dir: working directory of the original pytest process
    :return: available evidence, with incomplete inventories explicitly marked
    """
    _LOG.debug("Parsing terminal report for root='%s'", root)
    invocation_dir = os.path.abspath(invocation_dir or os.getcwd())
    root = os.path.abspath(root)
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    items: Dict[str, Dict[str, Any]] = {}
    expected_count = -1
    finished = False
    errors = {}
    # The greedy node group preserves spaces and outcome words in parameter IDs.
    # Optional duration and percentage fields follow pytest's displayed node ID.
    outcome_pattern = re.compile(
        r"^(?P<node>.+?\.py::.+)\s+"
        r"(?:\([\d.]+\s+s\)\s+)?"
        r"(?P<outcome>PASSED|FAILED|SKIPPED|XFAIL|XPASS|ERROR|RERUN)"
        r"(?:\s+\[\s*\d+%\])?(?:\s+\((?P<reason>.*)\))?\s*$"
    )
    for line in text.splitlines():
        line = line.strip()
        count = re.search(r"collected (\d+) items?", line)
        flat_count = re.search(r"(\d+) tests? collected", line)
        count_match = count or flat_count
        if count_match is not None:
            expected_count = int(count_match.group(1))
        if flat_count or re.search(
            r"=+ .*\d+ (passed|failed|skipped).* =+", line
        ):
            finished = True
        match = outcome_pattern.match(line)
        if match:
            outcome = match.group("outcome").lower()
            outcome = {"xfail": "xfailed", "xpass": "xpassed"}.get(
                outcome, outcome
            )
            nodeid = match.group("node")
            # This repository prefixes outcomes with elapsed times.
            nodeid = re.sub(r"\s+\([\d.]+\s+s\)$", "", nodeid)
            # Pytest's verbose terminal writer displays paths relative to its
            # invocation directory, whereas flat collection uses rootdir.
            path, separator, callable_name = nodeid.partition("::")
            path = os.path.relpath(os.path.join(invocation_dir, path), root)
            nodeid = path + separator + callable_name
            items[nodeid] = {
                "outcome": outcome,
                "reason": match.group("reason") or "",
                "line": -1,
                "call_executed": outcome in ("passed", "failed", "xpassed"),
            }
        elif re.match(r"^[^<>]+\.py::\S", line) and not re.search(
            r"\s+\[\s*\d+%\]", line
        ):
            # A bare flat collection ID contains no outcome or progress suffix.
            if expected_count == -1 or not re.search(
                r"\s+(PASSED|FAILED|ERROR)\b", line
            ):
                items.setdefault(
                    line,
                    {
                        "outcome": "",
                        "reason": "",
                        "line": -1,
                        "call_executed": False,
                    },
                )
        if "ERROR collecting " in line:
            errors[line.split("ERROR collecting ", 1)[1].strip(" _=")] = line
    complete = finished and expected_count == len(items) and not errors
    warnings = (
        []
        if complete
        else ["Terminal log does not prove a complete collection inventory"]
    )
    return PytestEvidence(root, items, errors, complete, -1, warnings)


# #############################################################################
# Source-to-execution reconciliation
# #############################################################################


def merge_evidence(
    collection: PytestEvidence, execution: PytestEvidence
) -> PytestEvidence:
    """
    Combine matching captures without hiding contradictory collection evidence.

    :param collection: full collection capture for the same revision and options
    :param execution: saved execution capture
    :return: merged evidence, preserving input objects
    """
    hdbg.dassert_eq(
        os.path.abspath(collection.root),
        os.path.abspath(execution.root),
        "Collection and execution must have the same pytest root",
    )
    items = dict(collection.items)
    items.update(execution.items)
    errors = dict(collection.collection_errors)
    errors.update(execution.collection_errors)
    warnings = list(collection.warnings) + list(execution.warnings)
    skips = dict(collection.collection_skips)
    skips.update(execution.collection_skips)
    unexpected = set(execution.items).difference(collection.items)
    complete = collection.collection_complete and not unexpected and not errors
    if unexpected:
        warnings.append(
            "Execution contains cases absent from the collection capture"
        )
    return PytestEvidence(
        collection.root,
        items,
        errors,
        complete,
        execution.exit_code,
        sorted(set(warnings)),
        skips,
    )


def analyze_inventory(
    inventory: hpysainv.SourceInventory, evidence: PytestEvidence
) -> Dict[str, Any]:
    """
    Compare source definitions with observed individual pytest cases.

    :param inventory: independently discovered source test definitions
    :param evidence: observed collection and test outcomes
    :return: deterministic report with cases, gaps, errors and summary counts
    """
    _LOG.debug(
        "Analyzing %d source tests and %d cases",
        len(inventory.tests),
        len(evidence.items),
    )
    matched = set()
    rows = []
    for nodeid, item in sorted(evidence.items.items()):
        # Only the callable portion is parametrized; brackets in a filename
        # must not change how the source definition is resolved.
        path, separator, callable_name = nodeid.partition("::")
        source_id = path + separator + callable_name.split("[", 1)[0]
        source = inventory.tests.get(source_id)
        if source:
            matched.add(source_id)
        rows.append(
            {
                "nodeid": nodeid,
                "status": item["outcome"] or "unexecuted",
                "reason": item["reason"],
                "source": source_id if source else "",
                "line": source.line if source else item["line"] + 1,
                "call_executed": item["call_executed"],
            }
        )
    for nodeid, source in sorted(inventory.tests.items()):
        if nodeid in matched:
            continue
        status = "not_collected" if evidence.collection_complete else "unknown"
        reason = source.uncertain_reason
        if source.uncertain_reason:
            status = "unknown"
        if source.excluded_reason:
            status = "excluded"
            reason = source.excluded_reason
        for collector, skip_reason in evidence.collection_skips.items():
            if nodeid == collector or nodeid.startswith(collector + "::"):
                status, reason = "skipped", skip_reason
                break
        for collector, collector_reason in evidence.collection_errors.items():
            if nodeid == collector or nodeid.startswith(collector + "::"):
                status, reason = "collection_error", collector_reason
                break
        rows.append(
            {
                "nodeid": nodeid,
                "status": status,
                "reason": reason,
                "source": nodeid,
                "line": source.line,
                "call_executed": False,
            }
        )
    rows.sort(key=lambda row: row["nodeid"])
    summary: Dict[str, int] = {}
    for row in rows:
        status = row["status"]
        summary[status] = summary.get(status, 0) + 1
    return {
        "schema_version": 1,
        "collection_complete": evidence.collection_complete,
        "pytest_exit_code": evidence.exit_code,
        "summary": dict(sorted(summary.items())),
        "tests": rows,
        "source_errors": dict(sorted(inventory.errors.items())),
        "source_uncertainties": dict(sorted(inventory.uncertainties.items())),
        "collection_errors": dict(sorted(evidence.collection_errors.items())),
        "collection_skips": dict(sorted(evidence.collection_skips.items())),
        "warnings": evidence.warnings,
    }
