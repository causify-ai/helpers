#!/usr/bin/env python3
r"""
Transform pandoc AST to typst: handle divved fences and LaTeX colors.

Supports two transformation actions:

1. **divved_fence**: Transform `Div[columns]` into `RawBlock[typst #grid()]`
   - Pandoc parses Markdown multi-column layouts (via `:::columns`/`:::column`)
     into nested `Div` AST nodes
   - This action replaces each `Div` with class `columns` with a `RawBlock`
     containing typst `#grid(...)` code

2. **color_text**: Transform LaTeX color commands in Math nodes
   - Converts `\textcolor{color}{content}` to `#text(fill: color)[content]`
   - Handles nested braces with proper parsing

Usage:
> pandoc input.md -t json | \
    transform_pandoc_ast_to_typst.py \
        -i - -o output.json -a divved_fence -a color_text
> pandoc output.json -f json -t typst -o slides.typ

Import as:
import dev_scripts_helpers.documentation.transform_pandoc_ast_to_typst as dsdocut
"""

import argparse
import json
import logging
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Tuple

import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hselect_action as hselacti
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Load / Save AST
# #############################################################################

PandocAst = Dict[str, Any]


# TODO(gp): Factor out once there are more AST processing scripts.
def _load_ast(filepath: str) -> PandocAst:
    """
    Load pandoc AST JSON from file.

    :param filepath: Path to JSON file
    :return: AST dict with keys: pandoc-api-version, meta, blocks
    """
    content = hio.from_file(filepath)
    ast = json.loads(content)
    return ast


def ast_to_str(ast: PandocAst) -> str:
    hdbg.dassert_isinstance(ast, dict)
    ast_str = json.dumps(ast, indent=2)
    return ast_str


def _save_ast(ast: PandocAst, filepath: str) -> None:
    """
    Save pandoc AST JSON to file.

    :param ast: AST dict to serialize
    :param filepath: Path to write JSON file
    """
    hdbg.dassert_isinstance(ast, dict)
    content = ast_to_str(ast)
    hio.to_file(filepath, content)


# #############################################################################
# Convert markdown / typst end-to-end
# #############################################################################


def convert_markdown_to_pandoc_ast(
    md_input: str, scratch_dir: str
) -> Tuple[PandocAst, str, str]:
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
    pandoc_docker_image = "pandoc_only"
    dshdlipa.run_dockerized_pandoc(cmd, pandoc_docker_image)
    # Load result.
    ast = _load_ast(ast_file)
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
    pandoc_docker_image = "pandoc_only"
    dshdlipa.run_dockerized_pandoc(cmd, pandoc_docker_image)
    # Load result.
    typst_txt = hio.from_file(typst_file)
    return typst_txt, typst_file


# #############################################################################
# Detect and Extract Columns
# #############################################################################


def _is_columns_container(elem: Dict[str, Any]) -> bool:
    """
    Check if element is a Div with class 'columns'.

    In pandoc AST, a Div element is structured as:
    {"t": "Div", "c": [[id, [classes], [attributes]], [blocks]]}

    This function checks:
    1. Element type is Div
    2. Element has content (c key)
    3. Element has 'columns' in its class list

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
        rc, result = hsystem.system_to_string(cmd)
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


def _transform_elem(elem: PandocAst, api_version: List[int]) -> PandocAst:
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


def _transform_ast_divved_fence(ast: PandocAst) -> PandocAst:
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
# Color Transformation (LaTeX to Typst)
# #############################################################################


class ColorTransformer:
    """
    Transform LaTeX color commands to Typst syntax.
    """

    def __init__(self):
        self.stats = {
            "textcolor_count": 0,
            "color_count": 0,
            "math_nodes_processed": 0,
            "formulas_transformed": 0,
        }

    def textcolor_to_typst(self, latex_string: str) -> str:
        r"""
        Transform \textcolor{color}{content} to #text(fill: color)[content]
        """
        pattern = r"\\textcolor\{([^}]+)\}\{([^}]*)\}"

        def replace_color(match: Any) -> str:
            color = match.group(1)
            content = match.group(2)
            self.stats["textcolor_count"] += 1
            _LOG.debug(
                f"  \\textcolor{{{color}}}{{{content}}} → "
                f"#text(fill: {color})[{content}]",
            )
            content_escaped = content.replace("\\", "\\\\")
            content_escaped = content_escaped.replace("]", r"\]")
            content_escaped = content_escaped.replace("[", r"\[")
            return f"#text(fill: {color})[{content_escaped}]"

        result = re.sub(pattern, replace_color, latex_string)
        return result

    def color_to_typst(self, latex_string: str) -> str:
        r"""
        Transform \color{color} to #set text(fill: color) (placeholder)
        """
        pattern = r"\\color\{([^}]+)\}"

        def replace_color(match: Any) -> str:
            color = match.group(1)
            self.stats["color_count"] += 1
            _LOG.debug(
                f"  \\color{{{color}}} → (requires context awareness, skipped)",
                file=sys.stderr,
            )
            return f"\\color{{{color}}}"

        result = re.sub(pattern, replace_color, latex_string)
        return result

    def transform_formula(self, latex_string: str) -> str:
        """
        Apply all transformations to a formula string.
        """
        result = latex_string
        result = self.textcolor_to_typst(result)
        result = self.color_to_typst(result)
        return result

    def process_math_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform a Math AST node.
        """
        if node.get("t") != "Math":
            return node
        self.stats["math_nodes_processed"] += 1
        math_mode = node["c"][0]
        latex_formula = node["c"][1]
        if "\\textcolor" not in latex_formula and "\\color" not in latex_formula:
            return node
        self.stats["formulas_transformed"] += 1
        _LOG.debug(f"Transforming: {latex_formula[:50]}...", file=sys.stderr)
        typst_formula = self.transform_formula(latex_formula)
        return {"t": "Math", "c": [math_mode, typst_formula]}

    def walk(self, obj: Any) -> Any:
        """
        Recursively transform AST.
        """
        if isinstance(obj, dict):
            if obj.get("t") == "Math":
                return self.process_math_node(obj)
            return {key: self.walk(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.walk(item) for item in obj]
        else:
            return obj

    def get_stats(self) -> Dict[str, int]:
        """
        Return transformation statistics.
        """
        return self.stats


def _transform_ast_color_text(ast: PandocAst) -> PandocAst:
    """
    Transform AST: replace LaTeX color commands with Typst equivalents.

    :param ast: Full pandoc AST dict
    :return: Transformed AST
    """
    transformer = ColorTransformer()
    return transformer.walk(ast)


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
    valid_actions = ["divved_fence", "color_text"]
    default_actions = ["divved_fence", "color_text"]
    hselacti.add_action_arg(parser, valid_actions, default_actions)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point: load AST, transform, save.

    :param parser: ArgumentParser with parsed args
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    valid_actions = ["divved_fence", "color_text"]
    default_actions = ["divved_fence", "color_text"]
    actions = hselacti.select_actions(args, valid_actions, default_actions)
    _LOG.info(hselacti.actions_to_string(actions, valid_actions, add_frame=True))
    _LOG.info("Loading AST from '%s'", args.in_file)
    ast = _load_ast(args.in_file)
    while actions:
        action = actions[0]
        to_execute, actions = hselacti.mark_action(action, actions)
        if to_execute:
            if action == "divved_fence":
                _LOG.info(
                    "Transforming AST: Div[columns] -> RawBlock[typst #grid()]"
                )
                ast = _transform_ast_divved_fence(ast)
            elif action == "color_text":
                _LOG.info("Transforming AST: LaTeX colors -> Typst colors")
                ast = _transform_ast_color_text(ast)
    _LOG.info("Saving transformed AST to '%s'", args.out_file)
    _save_ast(ast, args.out_file)
    _LOG.info("Done")


if __name__ == "__main__":
    _main(_parse())
