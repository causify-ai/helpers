#!/usr/bin/env -S uv run

# /// script
# dependencies = ["jedi", "networkx", "jinja2", "pygments", "tqdm"]
# ///

"""
Build the call graph of a directory of Python code and write it as one HTML page
to navigate the code.

The page has a graph and a code view side by side:
- The graph shows how functions and classes call each other
  - Classes are drawn with UML notation (name, attributes, methods)
  - Inheritance is a hollow triangle, composition a filled diamond, and a call
    a dashed arrow
  - Zoom with the mouse wheel, pan by dragging
- Hover over a function or a class to see its interface
- Click a function, a method, or a class to jump to its code
- The number of neighbors limits the graph to the symbols within N connections
  of the selected one (0 shows everything)
- Back / Forward in the browser (or the arrows in the toolbar) go through the
  history of clicks

See `call_graph_viewer.README.md` for the architecture and the plan for a local
server.

# Usage Example

- Write the call graph of a directory to the default HTML file and open it:
> call_graph_viewer.py --input helpers --open

- Skip the tests and write to a given file:
> call_graph_viewer.py --input helpers --exclude_tests --output call_graph.html

- Start from a function, showing the symbols within 2 connections:
> call_graph_viewer.py --input helpers --focus hdbg.dassert_eq --radius 2

- Embed only the neighborhood of a symbol, to get a small page for a big repo:
> call_graph_viewer.py --input helpers --focus hdbg.dassert_eq --radius 2 --prune

Import as:

import dev_scripts_helpers.coding_tools.call_graph_viewer as dsccacavi
"""

import argparse
import logging
import os

import dev_scripts_helpers.coding_tools.call_graph.extract as dsccgex
import dev_scripts_helpers.coding_tools.call_graph.render as dsccgre
from helpers import hdbg, hio, hopen, hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        required=True,
        help="Directory of Python code to analyze",
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store",
        default="tmp.call_graph_viewer.html",
        help="HTML file to write",
    )
    parser.add_argument(
        "--project_root",
        action="store",
        default="",
        help="Directory used to name modules and to resolve absolute imports "
        "(default: closest ancestor of the input containing `.git`)",
    )
    parser.add_argument(
        "--focus",
        action="store",
        default="",
        help="Symbol selected when the page opens, as a full name or a unique "
        "suffix (e.g., `hdbg.dassert_eq`)",
    )
    parser.add_argument(
        "--radius",
        action="store",
        type=int,
        default=1,
        help="Initial number of connections shown around the focus (0 shows "
        "everything)",
    )
    parser.add_argument(
        "--title",
        action="store",
        default="",
        help="Title of the page",
    )
    hparser.add_bool_arg(
        parser,
        "exclude_tests",
        default_value=False,
        help_="Skip `test/` dirs and `test_*.py` files",
    )
    hparser.add_bool_arg(
        parser,
        "prune",
        default_value=False,
        help_="Embed only the symbols within `--radius` of `--focus`",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Analyze the code without writing the HTML file",
    )
    hopen.add_open_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    hdbg.dassert_dir_exists(args.input)
    hdbg.dassert_lte(0, args.radius, "The radius must be non-negative")
    hdbg.dassert_imply(
        args.prune,
        args.focus != "",
        "Pruning needs a `--focus` symbol to center on",
    )
    # Extract the symbols and the call graph.
    cg = dsccgex.extract_call_graph(
        args.input,
        project_root=args.project_root,
        exclude_tests=args.exclude_tests,
    )
    # Resolve the focus now, so a typo fails before the page is written.
    focus = ""
    if args.focus:
        focus = dsccgex.find_symbol_id(cg, args.focus)
        _LOG.info("Focus: '%s'", focus)
    if args.prune:
        cg = dsccgex.prune_call_graph(cg, focus, args.radius)
        _LOG.info("Pruned to %d symbols", len(cg.symbols))
    # Render the page.
    title = args.title or (
        f"Call graph: {os.path.basename(os.path.realpath(args.input))}"
    )
    page = dsccgre.render_html(cg, title, focus=focus, radius=args.radius)
    if args.dry_run:
        _LOG.warning(
            "[DRY_RUN] Would write %d bytes to '%s'", len(page), args.output
        )
    else:
        hio.to_file(args.output, page)
        _LOG.info("Wrote '%s' (%d KB)", args.output, len(page) // 1024)
        if args.open:
            hopen.open_file(args.output, app=args.open_app)


if __name__ == "__main__":
    _main(_parse())
