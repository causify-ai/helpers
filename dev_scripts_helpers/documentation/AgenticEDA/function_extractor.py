"""
Import as:

import dev_scripts_helpers.documentation.AgenticEDA.function_extractor as dshdfuex
"""

import ast
import os
import typing


# #############################################################################
# FunctionExtractor
# #############################################################################


class FunctionExtractor:
    """
    Extracts function information from Python files.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []

    def extract_function_info(
        self, file_path: str, function_name: str, root_dir: str
    ) -> typing.Tuple[typing.Optional[str], typing.Optional[str]]:
        """
        Extract lines and docstring for a specific function or method from a
        Python file.

        Args:
            file_path: Path to the Python file (relative to root_dir)
            function_name: Name of the function
                        or method to extract (e.g., 'my_function' or 'MyClass.my_method')
            root_dir: Root directory to resolve relative paths (default: current working directory)

        Returns
            Tuple of (lines, docstring) or (None, None) if not found
        """
        try:
            if root_dir is None:
                root_dir = os.getcwd()
            # Resolve the absolute path
            if os.path.isabs(file_path):
                absolute_path = file_path
            else:
                absolute_path = os.path.join(root_dir, file_path)
            # Normalize the path to avoid issues with different path formats
            absolute_path = os.path.normpath(absolute_path)
            # Check if the file exists
            if not os.path.exists(absolute_path):
                self.errors.append(
                    f"File not found: {absolute_path} (original: {file_path})"
                )
                return None, None
            with open(absolute_path, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.errors.append(f"Syntax error in {absolute_path}: {e}")
                return None, None
            # Split the function name to handle methods (e.g., 'MyClass.my_method')
            parts = function_name.split(".")
            target_class_name = parts[0] if len(parts) > 1 else None
            target_function_name = parts[-1]
            # Find the function/method
            for node in ast.walk(tree):
                # Case 1: Method inside a class
                if (
                    target_class_name
                    and isinstance(node, ast.ClassDef)
                    and node.name == target_class_name
                ):
                    for sub_node in node.body:
                        if (
                            isinstance(
                                sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)
                            )
                            and sub_node.name == target_function_name
                        ):
                            start_line = sub_node.lineno
                            end_line = getattr(sub_node, "end_lineno", start_line)
                            lines = f"{start_line}-{end_line}"
                            docstring = ast.get_docstring(sub_node)
                            docstring = (
                                " ".join(docstring.strip().split())
                                if docstring
                                else "No docstring"
                            )
                            return lines, docstring

                # Case 2: Top-level function
                elif (
                    not target_class_name
                    and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == target_function_name
                ):
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", start_line)
                    lines = f"{start_line}-{end_line}"
                    docstring = ast.get_docstring(node)
                    docstring = (
                        " ".join(docstring.strip().split())
                        if docstring
                        else "No docstring"
                    )
                    return lines, docstring

            # Handle cases where the function or method is not found
            self.errors.append(
                f"Function/method '{function_name}' not found in {absolute_path}"
            )
            return None, None
        except (OSError, ValueError) as e:
            self.errors.append(f"Error processing {file_path}: {str(e)}")
            return None, None
