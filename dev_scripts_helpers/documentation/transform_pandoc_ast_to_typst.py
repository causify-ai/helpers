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
import tempfile
from typing import Any, Dict, List, Tuple

import dev_scripts_helpers.dockerize.lib_pandoc as dshdlipa
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hselect_action as hselacti

_LOG = logging.getLogger(__name__)

# Default backend for running `pandoc`: see
# `dev_scripts_helpers/dockerize/lib_pandoc.py` for the semantics of
# `auto` / `dockerized` / `host`.
_DEFAULT_PANDOC_BACKEND = "auto"


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
    md_input: str,
    scratch_dir: str,
    *,
    pandoc_backend: str = _DEFAULT_PANDOC_BACKEND,
) -> Tuple[PandocAst, str, str]:
    """
    Convert markdown text to a pandoc AST via pandoc.

    :param md_input: markdown text to convert
    :param scratch_dir: dir to store the input markdown and AST files
    :param pandoc_backend: how to run pandoc (`auto`, `dockerized`, `host`)
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
    dshdlipa.run_pandoc(cmd, pandoc_docker_image, pandoc_backend)
    # Load result.
    ast = _load_ast(ast_file)
    return ast, in_file, ast_file


def convert_pandoc_ast_to_typst(
    ast_input_file: str,
    scratch_dir: str,
    *,
    pandoc_backend: str = _DEFAULT_PANDOC_BACKEND,
) -> Tuple[str, str]:
    """
    Convert a pandoc AST JSON file to typst text via pandoc.

    :param ast_input_file: path to the AST JSON file
    :param scratch_dir: dir to store the output typst file
    :param pandoc_backend: how to run pandoc (`auto`, `dockerized`, `host`)
    :return: tuple of (typst text, typst output file path)
    """
    typst_file = os.path.join(scratch_dir, "output.typ")
    # Run conversion.
    cmd = f"pandoc {ast_input_file} -f json -t typst -o {typst_file}"
    pandoc_docker_image = "pandoc_only"
    dshdlipa.run_pandoc(cmd, pandoc_docker_image, pandoc_backend)
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
    blocks: List[Dict[str, Any]],
    api_version: List[int],
    pandoc_backend: str,
) -> str:
    """
    Render list of AST blocks to typst string via pandoc.

    Builds a mini AST with the given blocks, converts it via `pandoc -f
    json -t typst`, and returns the typst output (stripped of trailing
    whitespace).

    :param blocks: List of AST block elements
    :param api_version: Pandoc API version tuple (e.g., [1, 23, 1])
    :param pandoc_backend: how to run pandoc (`auto`, `dockerized`, `host`)
    :return: Typst code string
    """
    mini_ast = {
        "pandoc-api-version": api_version,
        "meta": {},
        "blocks": blocks,
    }
    ast_json = json.dumps(mini_ast)
    # TODO(gp): Consider using a tmp.render_block_typst dir
    # Use file-based (not stdin/stdout) invocation, and a scratch dir
    # underneath the current dir, so the dockerized backend can bind-mount
    # the files (mounts are rooted at the Git root).
    with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
        in_file = os.path.join(tmp_dir, "in.json")
        out_file = os.path.join(tmp_dir, "out.typ")
        hio.to_file(in_file, ast_json)
        cmd = f"pandoc {in_file} -f json -t typst -o {out_file}"
        dshdlipa.run_pandoc(cmd, "pandoc_only", pandoc_backend)
        typst_code = hio.from_file(out_file).strip()
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
    elem: PandocAst, api_version: List[int], pandoc_backend: str
) -> PandocAst:
    """
    Transform a single element recursively.

    If element is a columns container, replace with RawBlock containing grid code.
    Otherwise, recursively transform children if element contains nested blocks.

    :param elem: AST element (block)
    :param api_version: Pandoc API version
    :param pandoc_backend: how to run pandoc (`auto`, `dockerized`, `host`)
    :return: Transformed element (may be same elem or replacement)
    """
    if _is_columns_container(elem):
        columns = _extract_columns(elem)
        widths = [width for width, _ in columns]
        column_typst_codes = [
            _render_blocks_to_typst(blocks, api_version, pandoc_backend)
            for _, blocks in columns
        ]
        grid_code = _format_grid_code(widths, column_typst_codes)
        raw_block = {"t": "RawBlock", "c": ["typst", grid_code]}
        return raw_block
    if elem.get("t") == "Div" and elem.get("c"):
        children = elem["c"][1]
        transformed_children = [
            _transform_elem(child, api_version, pandoc_backend)
            for child in children
        ]
        elem["c"][1] = transformed_children
    elif elem.get("t") in ("BulletList", "OrderedList") and elem.get("c"):
        list_items = elem["c"]
        for item in list_items:
            for block_idx, block in enumerate(item):
                if isinstance(block, dict):
                    item[block_idx] = _transform_elem(
                        block, api_version, pandoc_backend
                    )
    return elem


def _transform_ast_divved_fence(
    ast: PandocAst, *, pandoc_backend: str = _DEFAULT_PANDOC_BACKEND
) -> PandocAst:
    """
    Transform entire AST: replace all Div[columns] with RawBlock[typst #grid()].

    :param ast: Full pandoc AST dict
    :param pandoc_backend: how to run pandoc (`auto`, `dockerized`, `host`)
    :return: Transformed AST
    """
    api_version = ast.get("pandoc-api-version", [1, 23, 1])
    blocks = ast.get("blocks", [])
    transformed_blocks = [
        _transform_elem(block, api_version, pandoc_backend) for block in blocks
    ]
    ast["blocks"] = transformed_blocks
    return ast


# #############################################################################
# Brace-aware `\textcolor{...}{...}` parsing
# #############################################################################


def _find_matching_brace(latex_string: str, open_index: int) -> int:
    """
    Find the index of the `}` that matches the `{` at `open_index`.

    :param latex_string: string containing the brace group
    :param open_index: index of the opening `{`
    :return: index of the matching closing `}`
    """
    hdbg.dassert_eq(latex_string[open_index], "{")
    depth = 0
    for i in range(open_index, len(latex_string)):
        if latex_string[i] == "{":
            depth += 1
        elif latex_string[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(
        f"Unbalanced braces starting at index {open_index} in: {latex_string}"
    )


def _find_textcolor_calls(
    latex_string: str,
) -> List[Tuple[int, int, str, str]]:
    r"""
    Find all top-level `\textcolor{color}{content}` calls.

    Unlike a naive regex (e.g. `\{([^}]*)\}`), this correctly handles
    `content` containing nested braces, e.g. `\textcolor{red}{x_{n-1}}`.

    :param latex_string: LaTeX math string to scan
    :return: list of `(start, end, color, content)` where `latex_string[start:end]`
        is the full `\textcolor{...}{...}` call
    """
    marker = r"\textcolor{"
    calls = []
    i = 0
    n = len(latex_string)
    while i < n:
        idx = latex_string.find(marker, i)
        if idx == -1:
            break
        color_open = idx + len(marker) - 1
        color_close = _find_matching_brace(latex_string, color_open)
        content_open = color_close + 1
        if content_open >= n or latex_string[content_open] != "{":
            # Malformed `\textcolor` call (missing second argument): skip it
            # and keep scanning past the `\textcolor` we just found.
            i = idx + 1
            continue
        content_close = _find_matching_brace(latex_string, content_open)
        color = latex_string[color_open + 1 : color_close]
        content = latex_string[content_open + 1 : content_close]
        calls.append((idx, content_close + 1, color, content))
        i = content_close + 1
    return calls


# #############################################################################
# ColorTransformer
# #############################################################################


class ColorTransformer:
    """
    Transform LaTeX color commands to Typst syntax.
    """

    # Placeholder wrapped in `\text{...}` so pandoc's LaTeX math parser
    # (texmath) treats it as a single opaque, well-formed atom (just like the
    # `\textcolor{...}{...}` call it stands in for), preserving the
    # surrounding math structure (subscripts, matrix cells, integral bounds,
    # ...) so the "skeleton" formula still parses. texmath renders
    # `\text{X}` to `upright("X")` in Typst, which is what we grep for below.
    _PLACEHOLDER_TEMPLATE = "XCOLORPLACEHOLDER{idx}"

    def __init__(self, pandoc_backend: str = _DEFAULT_PANDOC_BACKEND):
        self.pandoc_backend = pandoc_backend
        self.stats = {
            "textcolor_count": 0,
            "color_count": 0,
            "math_nodes_processed": 0,
            "formulas_transformed": 0,
        }

    def textcolor_to_typst(self, latex_string: str) -> str:
        r"""
        Transform \textcolor{color}{content} to #text(fill: color)[content]

        This is a plain string substitution (no math-awareness): it is used
        for standalone snippets, not for AST `Math` nodes (see
        `process_math_node()` for the AST case, which additionally converts
        `content` from LaTeX math to Typst math).
        """
        calls = _find_textcolor_calls(latex_string)
        if not calls:
            return latex_string
        result = []
        prev_end = 0
        for start, end, color, content in calls:
            result.append(latex_string[prev_end:start])
            self.stats["textcolor_count"] += 1
            _LOG.debug(
                f"  \\textcolor{{{color}}}{{{content}}} → "
                f"#text(fill: {color})[{content}]",
            )
            content_escaped = content.replace("\\", "\\\\")
            content_escaped = content_escaped.replace("]", r"\]")
            content_escaped = content_escaped.replace("[", r"\[")
            result.append(f"#text(fill: {color})[{content_escaped}]")
            prev_end = end
        result.append(latex_string[prev_end:])
        return "".join(result)

    def color_to_typst(self, latex_string: str) -> str:
        r"""
        Transform \color{color} to #set text(fill: color) (placeholder)
        """
        pattern = r"\\color\{([^}]+)\}"

        def replace_color(match: Any) -> str:
            color = match.group(1)
            self.stats["color_count"] += 1
            _LOG.debug(
                "  \\color{%s} → (requires context awareness, skipped)", color
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

    def _latex_math_to_typst(self, latex_str: str) -> str:
        """
        Convert a LaTeX math snippet to a Typst math snippet via pandoc.

        `latex_str` must be a well-formed (balanced) LaTeX math expression
        on its own: it is wrapped as an `InlineMath` node in a throwaway AST
        and converted via `pandoc -f json -t typst`.

        :param latex_str: LaTeX math source (no surrounding `$`)
        :return: equivalent Typst math source (no surrounding `$`)
        """
        mini_ast = {
            "pandoc-api-version": [1, 23, 1],
            "meta": {},
            "blocks": [
                {
                    "t": "Para",
                    "c": [{"t": "Math", "c": [{"t": "InlineMath"}, latex_str]}],
                }
            ],
        }
        ast_json = json.dumps(mini_ast)
        # Use file-based (not stdin/stdout) invocation, and a scratch dir
        # underneath the current dir, so the dockerized backend can
        # bind-mount the files (mounts are rooted at the Git root).
        with tempfile.TemporaryDirectory(dir=".") as tmp_dir:
            in_file = os.path.join(tmp_dir, "in.json")
            out_file = os.path.join(tmp_dir, "out.typ")
            hio.to_file(in_file, ast_json)
            cmd = f"pandoc {in_file} -f json -t typst -o {out_file}"
            dshdlipa.run_pandoc(cmd, "pandoc_only", self.pandoc_backend)
            typst_text = hio.from_file(out_file).strip()
        hdbg.dassert(
            typst_text.startswith("$") and typst_text.endswith("$"),
            "Unexpected pandoc typst output for formula '%s': %s",
            latex_str,
            typst_text,
        )
        return typst_text[1:-1]

    def _formula_to_raw_typst(self, latex_formula: str) -> str:
        r"""
        Convert a LaTeX math formula (possibly with `\textcolor`) to Typst.

        Each top-level `\textcolor{color}{content}` is replaced by a
        placeholder before the surrounding "skeleton" formula is handed to
        pandoc/texmath (which has no notion of `\textcolor`); `content` is
        recursively converted on its own and re-injected afterwards as
        `#text(fill: color)[$...$]`. This way the skeleton stays valid LaTeX
        math (braces/subscripts/environments all balanced) while `content`
        never gets re-parsed as LaTeX after it has been turned into Typst.

        :param latex_formula: LaTeX math source (no surrounding `$`)
        :return: Typst math source (no surrounding `$`), safe to embed
            verbatim in a `RawInline`/`RawBlock`
        """
        calls = _find_textcolor_calls(latex_formula)
        if not calls:
            return self._latex_math_to_typst(latex_formula)
        skeleton_parts = []
        placeholders = []
        prev_end = 0
        for start, end, color, content in calls:
            skeleton_parts.append(latex_formula[prev_end:start])
            idx = len(placeholders)
            placeholder = self._PLACEHOLDER_TEMPLATE.format(idx=idx)
            skeleton_parts.append(rf"\text{{{placeholder}}}")
            placeholders.append((placeholder, color, content))
            prev_end = end
        skeleton_parts.append(latex_formula[prev_end:])
        skeleton = "".join(skeleton_parts)
        typst_skeleton = self._latex_math_to_typst(skeleton)
        for placeholder, color, content in placeholders:
            self.stats["textcolor_count"] += 1
            token = f'upright("{placeholder}")'
            hdbg.dassert_in(
                token,
                typst_skeleton,
                "Placeholder for \\textcolor{%s}{%s} not found in pandoc output",
                color,
                content,
            )
            translated_content = self._formula_to_raw_typst(content)
            replacement = f"#text(fill: {color})[${translated_content}$]"
            typst_skeleton = typst_skeleton.replace(token, replacement, 1)
        return typst_skeleton

    def process_math_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        r"""
        Transform a Math AST node containing `\textcolor`/`\color` into a
        `RawInline` typst node.

        The node is deliberately re-tagged from `Math` to `RawInline` (format
        `typst`): once the formula contains Typst syntax like
        `#text(fill: red)[...]`, it is no longer valid LaTeX, so it must not
        be re-parsed as TeX math again downstream (e.g. by
        `pandoc -f json -t typst`) — that reparse is exactly what raises
        "Could not convert TeX math ... unexpected '#'".
        """
        if node.get("t") != "Math":
            return node
        self.stats["math_nodes_processed"] += 1
        mode_field, latex_formula = node["c"]
        mode = mode_field["t"] if isinstance(mode_field, dict) else mode_field
        if "\\textcolor" not in latex_formula and "\\color" not in latex_formula:
            return node
        self.stats["formulas_transformed"] += 1
        _LOG.debug("Transforming: %s...", latex_formula[:50])
        inner_typst = self._formula_to_raw_typst(latex_formula)
        if mode == "InlineMath":
            raw_typst = f"${inner_typst}$"
        else:
            raw_typst = f"$ {inner_typst} $"
        return {"t": "RawInline", "c": ["typst", raw_typst]}

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


def _transform_ast_color_text(
    ast: PandocAst, pandoc_backend: str = _DEFAULT_PANDOC_BACKEND
) -> PandocAst:
    """
    Transform AST: replace LaTeX color commands with Typst equivalents.

    :param ast: Full pandoc AST dict
    :param pandoc_backend: how to run pandoc (`auto`, `dockerized`, `host`)
    :return: Transformed AST
    """
    transformer = ColorTransformer(pandoc_backend)
    return transformer.walk(ast)


# #############################################################################
# CLI.
# #############################################################################

_VALID_ACTIONS = ["divved_fence", "color_text"]
_DEFAULT_ACTIONS = _VALID_ACTIONS[:]


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
    # TODO(ai_gp): Factor out this as a parser option in the library.
    parser.add_argument(
        "--pandoc_backend",
        type=str,
        choices=dshdlipa.VALID_PANDOC_BACKENDS,
        default=_DEFAULT_PANDOC_BACKEND,
        help="How to run `pandoc`: `auto` uses the host binary "
        "and falls back to Docker otherwise, `dockerized` always runs "
        "pandoc in Docker, `host` always runs the host binary",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main entry point: load AST, transform, save.

    :param parser: ArgumentParser with parsed args
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _LOG.info(
        hselacti.actions_to_string(actions, _VALID_ACTIONS, add_frame=True)
    )
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
                ast = _transform_ast_divved_fence(
                    ast, pandoc_backend=args.pandoc_backend
                )
            elif action == "color_text":
                _LOG.info("Transforming AST: LaTeX colors -> Typst colors")
                ast = _transform_ast_color_text(ast, args.pandoc_backend)
    _LOG.info("Saving transformed AST to '%s'", args.out_file)
    _save_ast(ast, args.out_file)
    _LOG.info("Done")


if __name__ == "__main__":
    _main(_parse())
