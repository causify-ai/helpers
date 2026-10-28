import json
import logging
import os
import shutil
from typing import Any

import pytest

import helpers.hunit_test as hunitest
from helpers import hgit, hio, hsystem

_LOG = logging.getLogger(__name__)

# The browser logic is JavaScript: run it with `node`, skip if it is missing.
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="`node` is not installed"
)


def _symbol(
    sym_id: str, kind: str, parent: str, **kwargs: Any
) -> dict[str, Any]:
    """
    Build a symbol in the format produced by `extract.call_graph_to_dict()`.

    :param sym_id: qualified name, e.g., `m.A.a1`
    :param kind: one of `module`, `class`, `function`, `method`
    :param parent: id of the enclosing module or class
    :param kwargs: fields overriding the defaults
    :return: symbol as a dict
    """
    symbol = {
        "id": sym_id,
        "kind": kind,
        "name": sym_id.split(".")[-1],
        "parent": parent,
        "file": "m.py",
        "line_start": 1,
        "line_end": 2,
        "signature": "()",
        "doc": "",
        "decorators": [],
        "bases": [],
        "attrs": [],
        "visibility": "+",
    }
    symbol.update(kwargs)
    return symbol


def _create_graph() -> dict[str, Any]:
    """
    Build the graph used by the tests.

    ```
    m.f --call--> m.A.a1
    m.f --instantiate--> m.B
    m.A.a2 --call--> m.B.b1
    m.B --inherit--> m.A
    ```

    :return: graph as a dict with `symbols` and `edges`
    """
    symbols = [
        _symbol("m", "module", ""),
        _symbol("m.f", "function", "m"),
        _symbol("m.A", "class", "m", attrs=["x: int"]),
        _symbol("m.A.a1", "method", "m.A", signature="(n: int) -> str"),
        _symbol("m.A.a2", "method", "m.A"),
        _symbol("m.B", "class", "m"),
        _symbol("m.B.b1", "method", "m.B"),
    ]
    edges = [
        {"src": "m.f", "dst": "m.A.a1", "kind": "call", "lines": [5]},
        {"src": "m.f", "dst": "m.B", "kind": "instantiate", "lines": [6]},
        {"src": "m.A.a2", "dst": "m.B.b1", "kind": "call", "lines": [9]},
        {"src": "m.B", "dst": "m.A", "kind": "inherit", "lines": [12]},
    ]
    return {"symbols": symbols, "edges": edges}


# #############################################################################
# Test_call_graph_viewer_core_js
# #############################################################################


class Test_call_graph_viewer_core_js(hunitest.TestCase):
    """
    Test the pure logic of the viewer (`call_graph_viewer_core.js`).
    """

    def helper(self, command: list[str], expected: str) -> None:
        """
        Run a command of the Node runner and compare its JSON output.

        :param command: runner command and its arguments
        :param expected: expected JSON text
        """
        # Prepare inputs.
        data_file = os.path.join(self.get_scratch_space(), "graph.json")
        hio.to_file(data_file, json.dumps(_create_graph()))
        core_file = hgit.find_file_in_git_tree("call_graph_viewer_core.js")
        runner = hgit.find_file_in_git_tree("call_graph_viewer_core_runner.js")
        cmd = ["node", runner, core_file, data_file] + command
        # Run test.
        _, actual = hsystem.system_to_string(" ".join(cmd))
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test one connection around a function, following callers and callees.
        """
        # Prepare inputs.
        command = ["hood", "m.f", "1", "both"]
        # Prepare outputs.
        expected = """
        {
          "m.A.a1": 1,
          "m.B": 1,
          "m.f": 0
        }
        """
        # Run test.
        self.helper(command, expected)

    def test2(self) -> None:
        """
        Test two connections following only the callees: the inheritance edge
        of the reached class is followed.
        """
        # Prepare inputs.
        command = ["hood", "m.f", "2", "callees"]
        # Prepare outputs.
        expected = """
        {
          "m.A": 2,
          "m.A.a1": 1,
          "m.B": 1,
          "m.f": 0
        }
        """
        # Run test.
        self.helper(command, expected)

    def test3(self) -> None:
        """
        Test that radius 0 shows every symbol, the unreachable ones too.
        """
        # Prepare inputs.
        command = ["hood", "m.f", "0", "callers"]
        # Prepare outputs.
        expected = """
        {
          "m.A": "inf",
          "m.A.a1": "inf",
          "m.A.a2": "inf",
          "m.B": "inf",
          "m.B.b1": "inf",
          "m.f": 0
        }
        """
        # Run test.
        self.helper(command, expected)

    def test4(self) -> None:
        """
        Test that the seeds of a class include its methods, and that methods
        collapse into their class in the projection.
        """
        # Prepare inputs.
        command = ["project", "m.A", "1", "both"]
        # Prepare outputs.
        expected = """
        {
          "nodes": [
            "m.A (module m)",
            "m.B (module m)",
            "m.f (module m)"
          ],
          "edges": [
            "inherit|m.B|m.A x1",
            "uses|m.A|m.B x1",
            "uses|m.f|m.A x1",
            "uses|m.f|m.B x1"
          ]
        }
        """
        # Run test.
        self.helper(command, expected)

    def test5(self) -> None:
        """
        Test the UML box of a class: attributes, methods, and highlights.
        """
        # Prepare inputs.
        command = ["box", "m.A", "m.A.a1", "m.A.a2"]
        # Prepare outputs.
        expected = """
        {
          "size": "143x83",
          "attrs": [
            "+ x: int"
          ],
          "methods": [
            "+ a1(n: int): str [selected]",
            "+ a2() [hit]"
          ]
        }
        """
        # Run test.
        self.helper(command, expected)

    def test6(self) -> None:
        """
        Test the mapping of a vertical offset in a box to the row under it.
        """
        # Prepare inputs.
        command = ["rowat", "m.A", "70"]
        # Prepare outputs.
        # The header is 24px, the attribute compartment 22px, and the methods
        # start after 4px of border and padding: y=70 is in the second method
        # row.
        expected = """
        {
          "part": "method",
          "index": 1
        }
        """
        # Run test.
        self.helper(command, expected)

    def test7(self) -> None:
        """
        Test that the navigation state survives a round trip through the URL
        hash and that invalid values fall back to the defaults.
        """
        # Prepare inputs.
        command = ["state", "'#node=pkg.mod.func&n=3&dir=callers&n=x'"]
        # Prepare outputs.
        expected = """
        {
          "state": {
            "node": "pkg.mod.func",
            "n": 3,
            "dir": "callers"
          },
          "hash": "node=pkg.mod.func&n=3&dir=callers"
        }
        """
        # Run test.
        self.helper(command, expected)
