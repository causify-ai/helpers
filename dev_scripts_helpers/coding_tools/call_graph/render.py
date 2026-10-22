"""
Render a `CallGraph` as one self-contained HTML page.

The page embeds everything it needs (graph data, highlighted source code, the
vendored JavaScript libraries, CSS), so it works offline and can be shared as a
single file. See `call_graph_viewer.README.md`.

Import as:

import dev_scripts_helpers.coding_tools.call_graph.render as dsccgre
"""

import html
import json
import logging
import os
from typing import Any

import jinja2
import pygments
import pygments.formatters
import pygments.lexers

import dev_scripts_helpers.coding_tools.call_graph.extract as dsccgex
from helpers import hdbg, hgit, hio, hprint

_LOG = logging.getLogger(__name__)

# #############################################################################
# Assets
# #############################################################################


def _get_assets_dir() -> str:
    """
    Find the dir storing the template, CSS, JS, and vendored libraries.

    Locate the template with `hgit.find_file_in_git_tree()` instead of deriving
    the path from `__file__`, so the assets can be moved or symlinked.

    :return: path of the dir containing `call_graph_viewer.html.j2`
    """
    template_path = hgit.find_file_in_git_tree("call_graph_viewer.html.j2")
    assets_dir = os.path.dirname(template_path)
    _LOG.debug("return=%s", assets_dir)
    return assets_dir


def _read_vendor_js(assets_dir: str) -> str:
    """
    Concatenate the vendored libraries in dependency order.

    `cytoscape-fcose` needs `cose-base`, which needs `layout-base`, and all of
    them find each other through browser globals.

    :param assets_dir: dir containing the `vendor/` dir (see `_get_assets_dir()`)
    :return: JavaScript text of all the libraries
    """
    _LOG.debug(hprint.to_str("assets_dir"))
    vendor_files = [
        "cytoscape-3.34.4.min.js",
        "layout-base-2.0.1.js",
        "cose-base-2.2.0.js",
        "cytoscape-fcose-2.2.0.js",
        "cytoscape-node-html-label-1.2.2.min.js",
        "split-1.6.5.min.js",
    ]
    parts = []
    for file_name in vendor_files:
        path = os.path.join(assets_dir, "vendor", file_name)
        hdbg.dassert_file_exists(path)
        txt = hio.from_file(path)
        # A literal closing tag would end the inline script early.
        hdbg.dassert_not_in(
            "</script", txt, "Vendor file '%s' breaks inlining", path
        )
        parts.append(txt)
    # A leading `;` protects against files that omit the final semicolon.
    vendor_js = "\n;\n".join(parts)
    return vendor_js


# #############################################################################
# Data embedding
# #############################################################################


def _to_script_json(obj: Any) -> str:
    r"""
    Serialize an object so it is safe inside a `<script>` element.

    - `ensure_ascii` avoids the U+2028 / U+2029 line terminators
    - Escaping every `<` as `\u003c` stops the HTML parser from seeing
      `</script>` or `<!--`, and it is still valid JSON (`\/` is, but
      `\!` is not)

    :param obj: JSON-serializable object
    :return: JSON text
    """
    txt = json.dumps(obj, ensure_ascii=True, separators=(",", ":"))
    txt = txt.replace("<", r"\u003c")
    return txt


def _highlight_files(cg: dsccgex.CallGraph) -> dict[str, list[str]]:
    """
    Highlight the source of every file that defines a symbol.

    :param cg: extracted call graph
    :return: map from the file path (relative to the project root) to one HTML
        string per source line, so the viewer can scroll to and mark line ranges
    """
    _LOG.debug(hprint.to_str("len(cg.symbols)"))
    lexer = pygments.lexers.PythonLexer()
    # `nowrap` yields the bare token spans, without a `<pre>` wrapper.
    formatter = pygments.formatters.HtmlFormatter(nowrap=True)
    rel_paths = sorted({s.file for s in cg.symbols.values()})
    files: dict[str, list[str]] = {}
    for rel_path in rel_paths:
        src = hio.from_file(os.path.join(cg.project_root, rel_path))
        highlighted = pygments.highlight(src, lexer, formatter)
        # Pygments closes and reopens a token span at each newline, so the
        # i-th HTML line is the i-th source line.
        html_lines = highlighted.split("\n")
        num_lines = len(src.split("\n"))
        # A final newline ends the last line, it does not start a new one.
        if src.endswith("\n"):
            num_lines -= 1
        html_lines = html_lines[:num_lines]
        hdbg.dassert_eq(
            len(html_lines), num_lines, "Highlighting changed the line count"
        )
        files[rel_path] = html_lines
    return files


# #############################################################################
# Public API
# #############################################################################


def render_html(
    cg: dsccgex.CallGraph,
    title: str,
    *,
    focus: str = "",
    radius: int = 1,
) -> str:
    """
    Render a call graph as a self-contained HTML page.

    :param cg: extracted call graph
    :param title: title of the page
    :param focus: id of the symbol selected when the page opens
        - Empty: the viewer picks an initial view
    :param radius: initial number of connections shown around `focus`
        - `0` shows everything
    :return: HTML text
    """
    _LOG.debug(hprint.to_str("title focus radius"))
    hdbg.dassert_lte(0, radius, "Radius must be non-negative")
    assets_dir = _get_assets_dir()
    # Graph data plus the initial view.
    data = dsccgex.call_graph_to_dict(cg)
    data["initial"] = {"node": focus, "n": radius}
    # Source code, highlighted once at generation time.
    files = _highlight_files(cg)
    pygments_css = pygments.formatters.HtmlFormatter(
        style="default"
    ).get_style_defs("#code")
    # Fill the template.
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(assets_dir),
        # The injected blocks are code, not text, so they are not escaped.
        autoescape=False,
        keep_trailing_newline=True,
    )
    template = env.get_template("call_graph_viewer.html.j2")
    page = template.render(
        title=html.escape(title),
        css=hio.from_file(os.path.join(assets_dir, "call_graph_viewer.css")),
        pygments_css=pygments_css,
        data_json=_to_script_json(data),
        files_json=_to_script_json(files),
        vendor_js=_read_vendor_js(assets_dir),
        core_js=hio.from_file(
            os.path.join(assets_dir, "call_graph_viewer_core.js")
        ),
        app_js=hio.from_file(
            os.path.join(assets_dir, "call_graph_viewer_app.js")
        ),
    )
    return page
