#!/usr/bin/env python

"""
Compare source tests with saved pytest collection and execution reports.

> pytest_check_sanity.py --pytest_input report.json --code_input . --output
sanity.json

Use pytest-json-report output or flat collection / verbose execution logs. This
command reads files only; it does not import or execute the test source.
"""

import argparse
import configparser
import html
import json
import logging
import os
import shlex
import sys
import tomllib
from typing import Any, Dict, List

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hpytest_sanity as hpytsani
import helpers.hpytest_sanity_inventory as hpysainv

_LOG = logging.getLogger(__name__)


# #############################################################################
# Configuration and input adapters
# #############################################################################


def _read_patterns(root: str, config_path: str) -> Dict[str, List[str]]:
    """Read pytest naming patterns without importing project configuration
    code.
    """
    patterns = {
        "python_files": ["test_*.py", "*_test.py"],
        "python_classes": ["Test"],
        "python_functions": ["test"],
    }
    candidates = (
        [config_path]
        if config_path
        else [
            os.path.join(root, name)
            for name in (
                "pytest.ini",
                ".pytest.ini",
                "pyproject.toml",
                "tox.ini",
                "setup.cfg",
            )
        ]
    )
    for path in candidates:
        if not os.path.isfile(path):
            continue
        settings: Dict[str, Any] = {}
        if path.endswith(".toml"):
            with open(path, "rb") as stream:
                settings = (
                    tomllib.load(stream)
                    .get("tool", {})
                    .get("pytest", {})
                    .get("ini_options", {})
                )
            if not settings:
                continue
        else:
            config = configparser.ConfigParser(interpolation=None)
            config.read(path, encoding="utf-8")
            section = "tool:pytest" if path.endswith("setup.cfg") else "pytest"
            if config.has_section(section):
                settings = dict(config[section])
            elif not path.endswith("pytest.ini"):
                continue
        for name in patterns:
            if name in settings:
                value = settings[name]
                patterns[name] = (
                    shlex.split(value) if isinstance(value, str) else list(value)
                )
        break
    return patterns


def _read_evidence(
    path: str, root: str, invocation_dir: str
) -> hpytsani.PytestEvidence:
    """Select a structured or terminal adapter for one saved report."""
    with open(path, encoding="utf-8-sig") as stream:
        text = stream.read()
    if text.lstrip().startswith("{"):
        evidence = hpytsani.parse_json_report(json.loads(text))
        hdbg.dassert_eq(
            os.path.abspath(evidence.root),
            root,
            "Use the report's pytest root as --code_input",
        )
    else:
        evidence = hpytsani.parse_terminal_report(
            text, root, invocation_dir=invocation_dir
        )
    return evidence


def _render_report(report: Dict[str, Any], output_format: str) -> str:
    """Render deterministic machine-readable or human-readable output."""
    if output_format == "json":
        return json.dumps(report, indent=2, sort_keys=True) + "\n"
    lines = ["Pytest source sanity", "", "Summary:"]
    lines.extend(
        f"  {name}: {count}" for name, count in report["summary"].items()
    )
    lines.extend(["", "Tests:"])
    for item in report["tests"]:
        lines.append(f"  {item['status']}: {item['nodeid']}")
        if item["reason"]:
            lines.append(f"    {item['reason']}")
    for category in (
        "source_errors",
        "collection_errors",
        "source_uncertainties",
    ):
        for path, reason in report.get(category, {}).items():
            lines.append(f"{category}: {path}: {reason}")
    lines.extend(f"Warning: {warning}" for warning in report["warnings"])
    text = "\n".join(lines) + "\n"
    if output_format == "html":
        # Source identifiers and error text are data, never HTML markup.
        return (
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            "<title>Pytest source sanity</title><body><pre>"
            + html.escape(text)
            + "</pre></body></html>\n"
        )
    return text


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """Build the public command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pytest_input", required=True, help="Execution or collection report"
    )
    parser.add_argument(
        "--collection_input", default="", help="Matching full collection report"
    )
    parser.add_argument(
        "--code_input", required=True, help="Source / node-ID root directory"
    )
    parser.add_argument(
        "--pytest_cwd",
        default=os.getcwd(),
        help="Working directory of the saved pytest run",
    )
    parser.add_argument("--output", required=True, help="Output report path")
    parser.add_argument(
        "--format", choices=("json", "text", "html"), default="json"
    )
    parser.add_argument(
        "--config", default="", help="Explicit pytest naming configuration"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional inventory directory glob",
    )
    parser.add_argument(
        "--fail_on",
        default="not_collected,unexecuted,unknown,failed,error,collection_error,rerun",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> int:
    """Reconcile saved evidence and return a CI-friendly result code."""
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=False)
    root = os.path.abspath(args.code_input)
    patterns = _read_patterns(root, args.config)
    excluded_dirs = [
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "**/.venv",
        "**/__pycache__",
    ] + args.exclude
    inventory = hpysainv.collect_source_tests(
        root,
        patterns["python_files"],
        patterns["python_classes"],
        patterns["python_functions"],
        excluded_dirs,
    )
    evidence = _read_evidence(args.pytest_input, root, args.pytest_cwd)
    if args.collection_input:
        collected = _read_evidence(args.collection_input, root, args.pytest_cwd)
        # A separate complete inventory makes absent execution outcomes visible.
        # Both captures must use the same code and selection configuration.
        evidence = hpytsani.merge_evidence(collected, evidence)
    report = hpytsani.analyze_inventory(inventory, evidence)
    with open(args.output, "w", encoding="utf-8") as stream:
        stream.write(_render_report(report, args.format))
    _LOG.info("Wrote %d test records to '%s'", len(report["tests"]), args.output)
    if inventory.errors or evidence.collection_errors:
        return 2
    failed_statuses = set(args.fail_on.split(","))
    incomplete = (
        not evidence.collection_complete or bool(inventory.uncertainties)
    ) and "unknown" in failed_statuses
    return int(
        incomplete or bool(failed_statuses.intersection(report["summary"]))
    )


if __name__ == "__main__":
    sys.exit(_main(_parse()))
