#!/usr/bin/env python
"""
Import as:

import linters.amp_class_method_order as laclmeor
"""

import argparse
import logging
from typing import List, Union

import libcst as cst
import libcst.codemod as codemod

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


def _sorting_key(node: Union[cst.ClassDef, cst.FunctionDef]) -> int:
    """
    Sort the nodes.

    - classes
    - __init__
    - magic
    - public static
    - public regular
    - private static
    - private regular
    """
    if isinstance(node, cst.ClassDef):
        # The class definition.
        return 0
    name = node.name.value
    decorator_names = []
    if node.decorators:
        decorator_names = [
            dec.decorator.value
            for dec in node.decorators
            if isinstance(dec.decorator, cst.Name)
        ]
    if name == "__init__":
        # The __init__ method.
        sorting_num = 1
    elif name.startswith("__") and name.endswith("__"):
        # A magic method.
        sorting_num = 2
    elif name.startswith("_") and "staticmethod" in decorator_names:
        # A private static method.
        sorting_num = 5
    elif name.startswith("_"):
        # A private regular method.
        sorting_num = 6
    elif "staticmethod" in decorator_names:
        # A public static method.
        sorting_num = 3
    else:
        # A public regular method.
        sorting_num = 4
    return sorting_num


# #############################################################################
# _OrderMethods
# #############################################################################


class _OrderMethods(
    codemod.ContextAwareTransformer
):  # pylint: disable=too-many-ancestors

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> Union[cst.BaseStatement, cst.RemovalSentinel]:
        # There will be a bunch of nodes for whitespace, docstrings, arguments, etc. The
        # last node will always be the indented block.
        indented_block: cst.IndentedBlock = updated_node.children[-1]
        exempt_elems = [
            (line_no, x)
            for line_no, x in enumerate(indented_block.body)
            if not isinstance(x, (cst.FunctionDef, cst.ClassDef))
        ]
        elems_to_sort = [
            x
            for x in indented_block.body
            if isinstance(x, (cst.FunctionDef, cst.ClassDef))
        ]
        # Order the methods.
        ordered_body = sorted(elems_to_sort, key=_sorting_key)
        for line_no, elem in exempt_elems:
            ordered_body.insert(line_no, elem)
        ordered_body_upd = []
        for node in ordered_body:
            if isinstance(node, cst.FunctionDef) and not node.leading_lines:
                # Insert an empty line before a method if it is missing.
                node_newline = cst.EmptyLine(
                    indent=False,
                    whitespace=cst.SimpleWhitespace(
                        value="",
                    ),
                    comment=None,
                    newline=cst.Newline(
                        value=None,
                    ),
                )
                ordered_body_upd.append(node_newline)
            ordered_body_upd.append(node)
        updated_node = updated_node.with_changes(
            body=indented_block.with_changes(body=ordered_body_upd)
        )
        return updated_node


def order_methods(txt: str) -> str:
    # Apply transformation.
    context = codemod.CodemodContext()
    c = _OrderMethods(context)
    module = cst.parse_module(txt)
    module = c.transform_module(module)
    res_code: str = module.code
    return res_code


# #############################################################################
# _ClassMethodOrder
# #############################################################################


class _ClassMethodOrder(liaction.Action):
    """
    Put the class methods in the correct order.
    """

    def check_if_possible(self) -> bool:
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        _ = pedantic
        if self.skip_if_not_py(file_name):
            # Apply only to Python files.
            return []
        txt = hio.from_file(file_name)
        # Apply transformation.
        txt_new = order_methods(txt)
        # Write result.
        txt_old = txt.splitlines()
        txt_new = txt_new.splitlines()
        liutils.write_file_back(file_name, txt_old, txt_new)
        return []


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "files",
        nargs="+",
        action="store",
        type=str,
        help="Files to process",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    action = _ClassMethodOrder()
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
