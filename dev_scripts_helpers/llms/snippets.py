import logging
from dataclasses import dataclass
from typing import List, Tuple

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


# #############################################################################
# Manipulate code.
# #############################################################################


import ast
import re
import textwrap

import helpers.hio as hio


def remove_docstring(code: str) -> str:
    # Remove multi-line comments (docstrings)
    code = re.sub(r'"""[\s\S]*?"""', "", code)
    code = re.sub(r"'''[\s\S]*?'''", "", code)
    # Remove empty lines.
    code = "\n".join(line for line in code.splitlines() if line.strip())
    return code


def remove_comments(code: str) -> str:
    # Remove single-line comments.
    code_tmp = []
    for line in code.split("\n"):
        if not re.search(r"^\s*\#.*", line):
            code_tmp.append(line)
    code = "\n".join(code_tmp)
    return code


def split_code_by_function(code: str) -> List[str]:
    # Parse the code into an AST
    tree = ast.parse(code)
    # Initialize a list to store function snippets
    function_snippets = []
    # Iterate through the AST nodes
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            # Get the source code for the function
            function_code = ast.get_source_segment(code, node)
            # Dedent the function code
            function_code = textwrap.dedent(function_code)
            # Add the function code to our list
            function_snippets.append(function_code)
    return function_snippets


def get_functions(function_tag: str) -> List[str]:
    """
    Read a set of functions and returned them as a list of strings.
    """
    # Read code based on the function function_tag.
    if function_tag == "hdbg":
        txt = hio.from_file("helpers/hdbg.py")
    elif function_tag == "code_snippets1":
        # This contains a single function and it's used for testing.
        txt = hio.from_file("code_snippets1.txt")
    elif function_tag == "code_snippets2":
        # This contains a few functions and it's used for evaluating.
        txt = hio.from_file("code_snippets2.txt")
    else:
        raise ValueError(f"Invalid function_tag='{function_tag}'")
    # Split in functions.
    functions = split_code_by_function(txt)
    return functions


# #############################################################################


def get_code_snippet1() -> str:
    """
    Code snippet without docstring.
    """
    code_snippet = """
def _extract(obj: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    hdbg.dassert_isinstance(obj, dict)
    obj_tmp = {}
    for key in keys:
        hdbg.dassert_in(key, obj)
        obj_tmp[key] = getattr(obj, key)
    return obj_tmp
    """
    return code_snippet


def build_few_shot_learning() -> str:
    functions = get_functions1()
    text = """
You are a proficient Python coder.

I will provide you with 5 examples of adding comments to a Python function. For
each example, I will show you the function without comments and then the same
function with comments added.

Then, I want you to perform the same task on a new input.
"""
    examples_idx = [1, 2, 3, 4]
    for idx in examples_idx:
        func = functions[idx]
        text += get_in_out_example(idx, func)
    text += """
Now, perform the task on this new input.
    """
    return text


# #############################################################################
# InOut
# #############################################################################


# TODO(gp): TransformExample? IoaExample?
@dataclass
class InOut:
    """
    Represent an input / output example.
    """

    # Input (e.g., code without comments).
    in_: str
    # Desired output (e.g., code with comments).
    # TODO(gp): exp?
    out: str
    # Actual output (e.g., code with comments from LLM).
    act: str

    def __str__(self) -> str:
        text = ""
        text += "\nInput:\n"
        text += f"'\n{self.in_}\n'"
        text += "\nOutput:\n"
        text += f"'\n{self.out}\n'"
        return text


# TODO(gp): -> in_out_to_gpt_text
def get_in_out_example(idx: int, func: str) -> str:
    text = ""
    remove_comments(func)
    return text


def get_in_out_functions(function_tag: str, transform_tag: str) -> List[InOut]:
    """
    Generate a list of InOut instances by applying a transformation to a set of
    functions.

    This function retrieves a list of functions based on the `function_tag`, applies
    a transformation specified by `transform_tag` to each function, and encapsulates
    the input and output in `InOut` instances. The transformed function
    serves as the input, and the original function serves as the output.

    :param function_tag: A tag specifying which functions to retrieve.
    :param transform_tag: A tag specifying which transformation to apply to the functions.
    :return: A list of InOut instances containing the input (transformed
        function) and output (original function).
    """
    # Get code.
    functions = get_functions(function_tag)
    # Pick transform function.
    if transform_tag == "remove_comments":
        transform = remove_comments
    elif transform_tag == "remove_docstring":
        transform = remove_docstring
    else:
        raise ValueError(f"Invalid transform_tag='{transform_tag}'")
    # Convert in input / output examples.
    in_outs = []
    for func in functions:
        in_ = transform(func)
        out = func
        in_outs.append(InOut(in_, out, ""))
    return in_outs


def _extract_values(
    in_outs: List[InOut],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Extract the input, output, and action from each InOut instance.
    """
    hdbg.dassert_isinstance(in_outs, list)
    ins = []
    outs = []
    acts = []
    for in_out in in_outs:
        ins.append(in_out.in_)
        outs.append(in_out.out)
        acts.append(in_out.act)
    return acts, ins, outs


def in_outs_to_files(in_outs: List[InOut]) -> None:
    """
    Save the input, output, and action of each InOut instance to separate
    files.

    This function iterates over a list of InOut instances, extracting
    the input, output, and action from each. These are then saved to
    'in.txt', 'out.txt', and 'act.txt' files respectively.

    :param in_outs: A list of InOut instances to be processed
    """
    acts, ins, outs = _extract_values(in_outs)
    _LOG.info("Saving results ...")

    def _functions_to_file(funcs: List[str], file_name: str) -> None:
        hdbg.dassert_isinstance(funcs, list)
        txt = "\n\n".join(funcs)
        hio.to_file(file_name, txt)

    _functions_to_file(ins, "in.txt")
    _functions_to_file(outs, "out.txt")
    _functions_to_file(acts, "act.txt")


# def in_outs_to_str(in_outs: List[InOut]) -> str:
def in_outs_to_str(in_outs):
    acts, ins, outs = _extract_values(in_outs)
    ret = ""
    ret += "\n\n### in.txt ###\n"
    ret += "\n\n".join(ins)
    ret += "\n\n### out.txt ###\n"
    ret += "\n\n".join(outs)
    ret += "\n\n### act.txt ###\n"
    ret += "\n\n".join(acts)
    return ret


# #############################################################################
# Eval.
# #############################################################################

import tqdm


def eval_prompt(
    function_tag: str,
    transform_tag: str,
    prompt_tag: str,
    *,
    save_to_file: bool = True,
) -> List[InOut]:
    """
    Evaluate a given prompt by applying a transformation to a set of functions.

    This function retrieves a list of functions based on the `function_tag`, applies
    a transformation specified by `transform_tag` to each function, and then applies
    a prompt specified by `prompt_tag` to the transformed function. The results are
    encapsulated in InOut instances and returned as a list.

    If `save_to_file` is True, the results are also saved to files.

    :param function_tag: A tag specifying which functions to retrieve.
    :param transform_tag: A tag specifying which transformation to apply to the functions.
    :param prompt_tag: A tag specifying which prompt to apply to the transformed functions.
    :param save_to_file: A boolean indicating whether to save the results to files.
    :return: A list of InOut instances containing the input, output, and action for each function.
    """
    # Get the input / output examples.
    in_outs = get_in_out_functions(function_tag, transform_tag)
    # Process examples one by one.
    _LOG.info("Processing %s examples", len(in_outs))
    in_outs_tmp = []
    for in_out in tqdm.tqdm(in_outs):
        txt = apply_prompt(prompt_tag, in_out.in_)
        # Update the example.
        hdbg.dassert_ne(txt, "")
        in_out.act = txt
        in_outs_tmp.append(in_out)
    # Save to files, if needed.
    if save_to_file:
        in_outs_to_files(in_outs_tmp)
    return in_outs_tmp
