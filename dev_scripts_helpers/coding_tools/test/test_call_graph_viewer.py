import json
import logging
import os
import re
from typing import Any
from unittest import mock

import pytest

# Skip this test suite if the `uv run` dependencies of the script are missing.
pytest.importorskip("jedi")
pytest.importorskip("networkx")
pytest.importorskip("jinja2")
pytest.importorskip("pygments")

import dev_scripts_helpers.coding_tools.call_graph.test.call_graph_fixture as dsccgtcgf
import dev_scripts_helpers.coding_tools.call_graph_viewer as dsccacavi
import helpers.hunit_test as hunitest
from helpers import hdbg, hio

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_call_graph_viewer_py
# #############################################################################


class Test_call_graph_viewer_py(hunitest.TestCase):
    """
    End-to-end tests for the `call_graph_viewer.py` executable.
    """

    def _run_main(self, argv: list[str]) -> None:
        """
        Run `dsccacavi._main()` with a mocked `sys.argv`.

        :param argv: command line, including the script name
        """
        parser = dsccacavi._parse()
        with mock.patch("sys.argv", argv):
            dsccacavi._main(parser)

    def _get_cmd(self, *extra_args: str) -> list[str]:
        """
        Create the fixture package and build a command line that analyzes it.

        :param extra_args: options added to the command line
        :return: argv, with the output file under the scratch space
        """
        scratch_dir = self.get_scratch_space()
        dsccgtcgf.create_fixture_package(scratch_dir)
        argv = [
            "call_graph_viewer.py",
            "--input",
            os.path.join(scratch_dir, "pkg"),
            "--project_root",
            scratch_dir,
            "--output",
            os.path.join(scratch_dir, "out.html"),
            "--exclude_tests",
        ]
        return argv + list(extra_args)

    def _read_page_data(self) -> dict[str, Any]:
        """
        Read the graph data embedded in the output page.
        """
        page = hio.from_file(os.path.join(self.get_scratch_space(), "out.html"))
        match = re.search(
            r'<script id="cg-data" type="application/json">(.*?)</script>', page
        )
        match = hdbg.dassert_re_match(match, "Graph data not found in the page")
        return json.loads(match.group(1))

    def test1(self) -> None:
        """
        Test that the page embeds the symbols and the initial view.
        """
        # Prepare inputs.
        argv = self._get_cmd("--focus", "zoo.main", "--radius", "2")
        # Run test.
        self._run_main(argv)
        # Check outputs.
        data = self._read_page_data()
        actual = "\n".join(
            [
                f"initial={data['initial']}",
                f"num_symbols={len(data['symbols'])}",
                f"num_edges={len(data['edges'])}",
            ]
        )
        expected = """
        initial={'node': 'pkg.zoo.main', 'n': 2}
        num_symbols=17
        num_edges=12
        """
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test that `--dry_run` does not write the output file.
        """
        # Prepare inputs.
        argv = self._get_cmd("--dry_run")
        # Run test.
        self._run_main(argv)
        # Check outputs.
        output_file = os.path.join(self.get_scratch_space(), "out.html")
        hdbg.dassert_path_not_exists(output_file)

    def test3(self) -> None:
        """
        Test that `--prune` embeds only the neighborhood of the focus.
        """
        # Prepare inputs.
        argv = self._get_cmd("--focus", "Toy.play", "--radius", "1", "--prune")
        # Run test.
        self._run_main(argv)
        # Check outputs.
        data = self._read_page_data()
        actual = "\n".join(s["id"] for s in data["symbols"])
        expected = """
        pkg.zoo
        pkg.zoo.Dog
        pkg.zoo.Dog.fetch
        pkg.zoo.Toy
        pkg.zoo.Toy.play
        pkg.zoo.Toy.bounce
        """
        self.assert_equal(actual, expected, dedent=True)
