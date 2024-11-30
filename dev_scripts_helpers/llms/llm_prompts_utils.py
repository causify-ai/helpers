import ast
import os
from typing import List

import helpers.hio as hio


def get_transforms() -> List[str]:
    """
    Extract all functions in a Python file that match a specific signature.

    :return: A list of function names that match the signature.
    """
    # Find file path of the llm_prompts.py file.
    curr_path = os.path.abspath(__file__)
    file_path = os.path.join(os.path.dirname(curr_path), "llm_prompts.py")
    file_path = os.path.abspath(file_path)
    file_content = hio.from_file(file_path)
    #
    matched_functions = []
    # Parse the file content into an AST.
    tree = ast.parse(file_content)
    # Iterate through all function definitions in the AST.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check function arguments and return type.
            args = [arg.arg for arg in node.args.args]
            if (
                args == ["user", "model"]
                and isinstance(node.returns, ast.Name)
                and node.returns.id == "str"
            ):
                matched_functions.append(node.name)
    matched_functions = sorted(matched_functions)
    return matched_functions
