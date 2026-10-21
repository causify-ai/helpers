import json
import logging
import os
import re

import pytest

# Skip this test suite if the `uv run` dependencies of the script are missing.
pytest.importorskip("jedi")
pytest.importorskip("networkx")
pytest.importorskip("jinja2")
pytest.importorskip("pygments")

import dev_scripts_helpers.coding_tools.call_graph.extract as dsccgex
import dev_scripts_helpers.coding_tools.call_graph.render as dsccgre
import helpers.hunit_test as hunitest
from helpers import hdbg, hio, hprint

_LOG = logging.getLogger(__name__)


def _create_call_graph(project_root: str) -> dsccgex.CallGraph:
    """
    Build a call graph for a module with one function, without running `jedi`.

    :param project_root: directory where the source file `m.py` is written
    """
    src = '''
    def f(x):
        """
        Say hi.
        """
        return "</script>"
    '''
    hio.to_file(os.path.join(project_root, "m.py"), hprint.dedent(src) + "\n")
    symbols = {
        "m": dsccgex.Symbol(
            id="m",
            kind="module",
            name="m",
            parent="",
            file="m.py",
            line_start=1,
            line_end=5,
        ),
        "m.f": dsccgex.Symbol(
            id="m.f",
            kind="function",
            name="f",
            parent="m",
            file="m.py",
            line_start=1,
            line_end=5,
            signature="(x)",
        ),
    }
    cg = dsccgex.CallGraph(
        root_dir=project_root, project_root=project_root, symbols=symbols
    )
    return cg


def _search(pattern: str, page: str) -> str:
    """
    Get the first group of a regex that must match the page.
    """
    match = re.search(pattern, page)
    match = hdbg.dassert_re_match(match, "Pattern not found in page", pattern)
    return match.group(1)


# #############################################################################
# Test__to_script_json
# #############################################################################


class Test__to_script_json(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the text cannot end the `<script>` element or open a comment,
        and that it is still valid JSON.
        """
        # Prepare inputs.
        obj = {"a": "</script><!-- \u2028"}
        # Run test.
        actual = dsccgre._to_script_json(obj)
        # Check outputs.
        expected = r'{"a":"\u003c/script>\u003c!-- \u2028"}'
        self.assert_equal(actual, expected)
        self.assert_equal(json.loads(actual)["a"], obj["a"])


# #############################################################################
# Test__highlight_files
# #############################################################################


class Test__highlight_files(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the highlighted HTML has one string per source line.
        """
        # Prepare inputs.
        cg = _create_call_graph(self.get_scratch_space())
        # Run test.
        files = dsccgre._highlight_files(cg)
        # Check outputs.
        actual = "\n".join(files["m.py"])
        expected = """
        <span class="k">def</span><span class="w"> </span><span class="nf">f</span><span class="p">(</span><span class="n">x</span><span class="p">):</span>
        <span class="w">    </span><span class="sd">\"\"\"</span>
        <span class="sd">    Say hi.</span>
        <span class="sd">    \"\"\"</span>
            <span class="k">return</span> <span class="s2">"&lt;/script&gt;"</span>
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)


# #############################################################################
# Test_render_html
# #############################################################################


class Test_render_html(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the page embeds the title, the initial view, the graph data,
        and the code.
        """
        # Prepare inputs.
        cg = _create_call_graph(self.get_scratch_space())
        # Run test.
        page = dsccgre.render_html(
            cg, title="A <b> title", focus="m.f", radius=2
        )
        # Check outputs.
        title = _search(r"<title>(.*)</title>", page)
        data = _search(
            r'<script id="cg-data" type="application/json">(.*?)</script>', page
        )
        files = _search(
            r'<script id="cg-files" type="application/json">(.*?)</script>', page
        )
        data = json.loads(data)
        files = json.loads(files)
        actual = "\n".join(
            [
                f"title={title}",
                f"initial={data['initial']}",
                f"symbols={[s['id'] for s in data['symbols']]}",
                f"files={list(files)} lines={len(files['m.py'])}",
                f"has_cytoscape={'cytoscape' in page}",
                f"has_unrendered_template={'{{' in page.split('<script>')[0]}",
            ]
        )
        expected = """
        title=A &lt;b&gt; title
        initial={'node': 'm.f', 'n': 2}
        symbols=['m', 'm.f']
        files=['m.py'] lines=5
        has_cytoscape=True
        has_unrendered_template=False
        """
        self.assert_equal(actual, expected, dedent=True)
