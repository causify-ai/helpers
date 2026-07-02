#!/usr/bin/env python3
r"""
Convert pandoc AST by transforming `Div[columns]` into `RawBlock[typst #grid()]`.

Pandoc parses Markdown multi-column layouts (via `:::columns` / `:::column` fences)
into nested `Div` AST nodes.

This script transforms the AST in-place: each `Div` with class `columns` is
replaced with a `RawBlock(typst, "#grid(...)")` that renders columns as typst
grids.

The result can be fed to pandoc for final typst output:
> pandoc input.md -t json | convert_pandoc_divved_fence.py -i - -o output.json
> pandoc output.json -f json -t typst -o slides.typ

Import as:
import dev_scripts_helpers.documentation.convert_pandoc_divved_fence as dsdocdpdf
"""

import argparse
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Tuple

import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Load / Save AST
# #############################################################################

# TODO(ai_gp): Use this everywhere is needed.
PandocAst = Dict[str, Any]

# TODO(gp): Factor out once there are more AST processing scripts.
def _load_ast(filepath: str) -> Dict[str, Any]:
    """
    Load pandoc AST JSON from file.

    :param filepath: Path to JSON file
    :return: AST dict with keys: pandoc-api-version, meta, blocks
    """
    content = hio.from_file(filepath)
    ast = json.loads(content)
    return ast


# TODO(ai_gp): Use ast_to_str
def ast_to_str(ast: Dict[str, Any]) -> str:
    hdbg.dassert_isinstance(ast, dict)
    ast_str = json.dumps(ast, indent=2)
    return ast_str



def _save_ast(ast: Dict[str, Any], filepath: str) -> None:
    """
    Save pandoc AST JSON to file.

    :param ast: AST dict to serialize
    :param filepath: Path to write JSON file
    """
    hdbg.dassert_isinstance(ast, dict)
    # TODO(ai_gp): Use ast_to_str
    content = json.dumps(ast, indent=2)
    hio.to_file(filepath, content)


# #############################################################################
# Convert markdown / typst end-to-end
# #############################################################################


# TODO(ai_gp): Use _load_ast and _save_ast.
def convert_markdown_to_pandoc_ast(
    md_input: str, scratch_dir: str
) -> Tuple[Dict[str, Any], str, str]:
    """
    Convert markdown text to a pandoc AST via dockerized pandoc.

    :param md_input: markdown text to convert
    :param scratch_dir: dir to store the input markdown and AST files
    :return: tuple of (AST dict, input markdown file path, AST JSON file
        path)
    """
    # Write input file.
    in_file = os.path.join(scratch_dir, "input.md")
    hio.to_file(in_file, md_input)
    # Output file.
    ast_file = os.path.join(scratch_dir, "ast.json")
    # Run conversion.
    cmd = f"pandoc {in_file} -f markdown -t json -o {ast_file}"
    # TODO(ai_gp): Assign pandoc_only to variable.
    dshdlipa.run_dockerized_pandoc(cmd, "pandoc_only")
    # Load result.
    ast = json.loads(hio.from_file(ast_file))
    return ast, in_file, ast_file


def convert_pandoc_ast_to_typst(
    ast_input_file: str, scratch_dir: str
) -> Tuple[str, str]:
    """
    Convert a pandoc AST JSON file to typst text via dockerized pandoc.

    :param ast_input_file: path to the AST JSON file
    :param scratch_dir: dir to store the output typst file
    :return: tuple of (typst text, typst output file path)
    """
    typst_file = os.path.join(scratch_dir, "output.typ")
    # Run conversion.
    cmd = f"pandoc {ast_input_file} -f json -t typst -o {typst_file}"
    # TODO(ai_gp): Assign pandoc_only to variable.
    dshdlipa.run_dockerized_pandoc(cmd, "pandoc_only")
    # Load result.
    typst_txt = hio.from_file(typst_file)
    return typst_txt, typst_file


# #############################################################################
# Detect and Extract Columns
# #############################################################################


# TODO(ai_gp2): Add more comments.
def _is_columns_container(elem: Dict[str, Any]) -> bool:
    """
    Check if element is a Div with class 'columns'.

    :param elem: AST element (block)
    :return: True if Div with 'columns' class
    """
    if elem.get("t") != "Div":
        return False
    if not elem.get("c"):
        return False
    id_classes_attrs = elem["c"][0]
    classes = id_classes_attrs[1] if len(id_classes_attrs) > 1 else []
    return "columns" in classes


def _extract_columns(
    container: Dict[str, Any],
) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """
    Extract column divs from a columns container.

    For each child Div with class 'column', extract width attribute (default '1fr')
    and content blocks.

    :param container: Div with class 'columns'
    :return: List of (width_str, blocks_list) tuples
    """
    hdbg.dassert(_is_columns_container(container), "Expected columns container")
    children_blocks = container["c"][1]
    columns = []
    for child in children_blocks:
        if child.get("t") != "Div":
            continue
        if not child.get("c"):
            continue
        id_classes_attrs = child["c"][0]
        classes = id_classes_attrs[1] if len(id_classes_attrs) > 1 else []
        if "column" not in classes:
            continue
        attrs = id_classes_attrs[2] if len(id_classes_attrs) > 2 else []
        width = "1fr"
        for attr in attrs:
            if isinstance(attr, list) and len(attr) == 2 and attr[0] == "width":
                width = attr[1]
                break
        content_blocks = child["c"][1] if len(child["c"]) > 1 else []
        columns.append((width, content_blocks))
    return columns


# #############################################################################
# Render Blocks to Typst
# #############################################################################


def _render_blocks_to_typst(
    blocks: List[Dict[str, Any]], api_version: List[int]
) -> str:
    """
    Render list of AST blocks to typst string via pandoc.

    Builds a mini AST with the given blocks, pipes to `pandoc -f json -t typst`,
    and returns the typst output (stripped of trailing whitespace).

    :param blocks: List of AST block elements
    :param api_version: Pandoc API version tuple (e.g., [1, 23, 1])
    :return: Typst code string
    """
    mini_ast = {
        "pandoc-api-version": api_version,
        "meta": {},
        "blocks": blocks,
    }
    ast_json = json.dumps(mini_ast)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=True
    ) as tmp_in:
        tmp_in.write(ast_json)
        tmp_in.flush()
        tmp_in_path = tmp_in.name
        cmd = f"pandoc -f json -t typst < {tmp_in_path}"
        rc, result = hsystem.system_to_string(cmd, suppress_output=False)
    hdbg.dassert_eq(rc, 0, "pandoc command failed")
    typst_code = result.strip()
    return typst_code


def _format_grid_code(widths: List[str], column_contents: List[str]) -> str:
    """
    Format typst #grid() code for columns.

    :param widths: List of width strings (e.g., ['55%', '45%'])
    :param column_contents: List of typst code strings, one per column
    :return: Complete typst #grid(...) block
    """
    hdbg.dassert_eq(
        len(widths),
        len(column_contents),
        "Mismatch between widths and column contents count",
    )
    columns_tuple = ", ".join(widths)
    formatted_columns = []
    for content in column_contents:
        indented_content = "\n".join(f"  {line}" for line in content.split("\n"))
        formatted_columns.append(f"[\n{indented_content}\n  ]")
    columns_wrapped = ",\n  ".join(formatted_columns)
    grid_code = (
        f"#grid(\n"
        f"  columns: ({columns_tuple}),\n"
        f"  gutter: 0.5em,\n"
        f"  {columns_wrapped}\n"
        f")"
    )
    return grid_code


# #############################################################################
# Transform AST
# #############################################################################


def _transform_elem(
    elem: Dict[str, Any], api_version: List[int]
) -> Dict[str, Any]:
    """
    Transform a single element recursively.

    If element is a columns container, replace with RawBlock containing grid code.
    Otherwise, recursively transform children if element contains nested blocks.

    :param elem: AST element (block)
    :param api_version: Pandoc API version
    :return: Transformed element (may be same elem or replacement)
    """
    if _is_columns_container(elem):
        columns = _extract_columns(elem)
        widths = [width for width, _ in columns]
        column_typst_codes = [
            _render_blocks_to_typst(blocks, api_version) for _, blocks in columns
        ]
        grid_code = _format_grid_code(widths, column_typst_codes)
        raw_block = {"t": "RawBlock", "c": ["typst", grid_code]}
        return raw_block
    if elem.get("t") == "Div" and elem.get("c"):
        children = elem["c"][1]
        transformed_children = [
            _transform_elem(child, api_version) for child in children
        ]
        elem["c"][1] = transformed_children
    elif elem.get("t") in ("BulletList", "OrderedList") and elem.get("c"):
        list_items = elem["c"]
        for item in list_items:
            for block_idx, block in enumerate(item):
                if isinstance(block, dict):
                    item[block_idx] = _transform_elem(block, api_version)
    return elem


def _transform_ast(ast: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform entire AST: replace all Div[columns] with RawBlock[typst #grid()].

    :param ast: Full pandoc AST dict
    :return: Transformed AST
    """
    api_version = ast.get("pandoc-api-version", [1, 23, 1])
    blocks = ast.get("blocks", [])
    transformed_blocks = [
        _transform_elem(block, api_version) for block in blocks
    ]
    ast["blocks"] = transformed_blocks
    return ast


# #############################################################################
# CLI.
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.

    :return: ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--in_file",
        type=str,
        default="",
        help="Input AST JSON file (or - for stdin)",
    )
    parser.add_argument(
        "-o",
        "--out_file",
        type=str,
        default="",
        help="Output AST JSON file (or - for stdout)",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point: load AST, transform, save.

    :param parser: ArgumentParser with parsed args
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    #
    _LOG.info("Loading AST from '%s'", args.in_file)
    ast = _load_ast(args.in_file)
    #
    _LOG.info("Transforming AST: Div[columns] -> RawBlock[typst #grid()]")
    ast = _transform_ast(ast)
    #
    _LOG.info("Saving transformed AST to '%s'", args.out_file)
    _save_ast(ast, args.out_file)
    _LOG.info("Done")


if __name__ == "__main__":
    _main(_parse())
