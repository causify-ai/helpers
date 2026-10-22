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
from helpers import hio, hprint

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


# #############################################################################
# Test__to_script_json
# #############################################################################


class Test__to_script_json(hunitest.TestCase):
    """
    Test `render._to_script_json()` function.
    """

    def test1(self) -> None:
        """
        Test that the text cannot end the `<script>` element or open a comment,
        and that it is still valid JSON.
        """
        # Prepare inputs.
        obj = {"a": "</script><!-- \u2028"}
        # Prepare outputs.
        expected = r'{"a":"\u003c/script>\u003c!-- \u2028"}'
        # Run test.
        actual = dsccgre._to_script_json(obj)
        # Check outputs.
        self.assert_equal(actual, expected)
        # The escaped text decodes back to the input.
        self.assert_equal(str(json.loads(actual)), str(obj))


# #############################################################################
# Test__highlight_files
# #############################################################################


class Test__highlight_files(hunitest.TestCase):
    """
    Test `render._highlight_files()` function.
    """

    def test1(self) -> None:
        """
        Test that the highlighted HTML has one string per source line.
        """
        # Prepare inputs.
        cg = _create_call_graph(self.get_scratch_space())
        # Prepare outputs.
        expected = '''
        <span class="k">def</span><span class="w"> </span><span class="nf">f</span><span class="p">(</span><span class="n">x</span><span class="p">):</span>
        <span class="w">    </span><span class="sd">"""</span>
        <span class="sd">    Say hi.</span>
        <span class="sd">    """</span>
            <span class="k">return</span> <span class="s2">"&lt;/script&gt;"</span>
        '''
        # Run test.
        files = dsccgre._highlight_files(cg)
        actual = "\n".join(files["m.py"])
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)


# #############################################################################
# Test_render_html
# #############################################################################


class Test_render_html(hunitest.TestCase):
    """
    Test `render.render_html()` function.
    """

    def helper(self, pattern: str, page: str) -> str:
        """
        Get the first group of a regex that must match the page.

        :param pattern: regex with one group
        :param page: HTML text to search
        :return: text of the first group
        """
        match = re.search(pattern, page)
        self.assertIsNotNone(match, "Pattern not found in page: " + pattern)
        group = match.group(1) if match else ""
        return group

    def test1(self) -> None:
        """
        Test that the page embeds the title, the initial view, the graph data,
        and the code.
        """
        # Prepare inputs.
        cg = _create_call_graph(self.get_scratch_space())
        title = "A <b> title"
        focus = "m.f"
        radius = 2
        # Prepare outputs.
        expected = """
        title=A &lt;b&gt; title
        initial={'node': 'm.f', 'n': 2}
        symbols=['m', 'm.f']
        files=['m.py'] lines=5
        has_cytoscape=True
        has_unrendered_template=False
        """
        # Run test.
        page = dsccgre.render_html(cg, title, focus=focus, radius=radius)
        # Extract the embedded pieces of the page.
        page_title = self.helper(r"<title>(.*)</title>", page)
        data = self.helper(
            r'<script id="cg-data" type="application/json">(.*?)</script>', page
        )
        files = self.helper(
            r'<script id="cg-files" type="application/json">(.*?)</script>', page
        )
        data = json.loads(data)
        files = json.loads(files)
        actual = "\n".join(
            [
                f"title={page_title}",
                f"initial={data['initial']}",
                f"symbols={[s['id'] for s in data['symbols']]}",
                f"files={list(files)} lines={len(files['m.py'])}",
                f"has_cytoscape={'cytoscape' in page}",
                f"has_unrendered_template={'{{' in page.split('<script>')[0]}",
            ]
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)
