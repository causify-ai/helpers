"""
Import as:

import helpers.hmkdocs as hmkdocs
"""

import re

import helpers.hdbg as hdbg
import helpers.hmarkdown as hmarkdo


# TODO(ai): Make function private.
# TODO(ai): Convert str to List[str]
# TODO(ai): Add unit tests.


# TODO(gp): -> hmarkdown_?.py
def dedent_python_code_blocks(txt: str) -> str:
    """
    Dedent Python code blocks so they are aligned to column 0.

    This is needed by mkdocs to render a Python code block correctly.

    :param txt: Input markdown text
    :return: Text with Python code blocks dedented
    """
    import textwrap

    lines = txt.split("\n")
    result = []
    # Store whether the parser is inside a code block.
    in_python_block = False
    # Store the current Python code block.
    code_block_lines = []
    for line in lines:
        if line.strip() == "```python":
            in_python_block = True
            result.append(line)
        elif line.strip() == "```" and in_python_block:
            # Process the accumulated code block.
            if code_block_lines:
                # Dedent the code block.
                code_text = "\n".join(code_block_lines)
                dedented_code = textwrap.dedent(code_text)
                result.extend(dedented_code.split("\n"))
                code_block_lines = []
            result.append(line)
            in_python_block = False
        elif in_python_block:
            code_block_lines.append(line)
        else:
            result.append(line)
    return "\n".join(result)


def replace_indentation(txt: str, input_spaces: int, output_spaces: int) -> str:
    """
    Replace indentation from input_spaces to output_spaces.

    :param txt: Input markdown text
    :param input_spaces: Number of spaces to detect as one indentation
        level
    :param output_spaces: Number of spaces to replace each indentation
        level with
    :return: Text with indentation replaced
    """
    hdbg.dassert_lte(1, input_spaces)
    hdbg.dassert_lte(1, output_spaces)
    lines = txt.split("\n")
    result = []
    for line in lines:
        # Count leading spaces.
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0 and leading_spaces % input_spaces == 0:
            # Calculate indentation level and convert to output spaces.
            indentation_level = leading_spaces // input_spaces
            new_indentation = " " * (indentation_level * output_spaces)
            result.append(new_indentation + line.lstrip())
        else:
            result.append(line)
    return "\n".join(result)


def replace_indentation_with_four_spaces(txt: str) -> str:
    """
    Replace 2 spaces indentation with 4 spaces since this is what mkdocs needs.

    :param txt: Input markdown text
    :return: Text with 2-space indentation replaced with 4-space
        indentation
    """
    return replace_indentation(txt, input_spaces=2, output_spaces=4)


def convert_slides_to_markdown(txt: str, level: int) -> str:
    """
    Convert strings storing "slides", i.e., `* ...`  to markdown headers.

    E.g.,
        ```
        * Tools for Vision component
        ```
    to:
        ```
        #### Tools for Vision component
        ```
    """
    lines = txt.split("\n")
    result = []
    for line in lines:
        if line.startswith("* "):
            result.append("#" * level + " " + line[2:])
        else:
            result.append(line)
    return "\n".join(result)


def preprocess_mkdocs_markdown(txt: str) -> str:
    """
    Preprocess markdown text for mkdocs.

    This function applies the following transformations:
    1. Remove table of contents
    2. Dedent Python code blocks
    3. Replace 2 spaces indentation with 4 spaces

    :param txt: Input markdown text
    :return: Preprocessed markdown text
    """
    txt = hmarkdo.remove_table_of_contents(txt)
    txt = dedent_python_code_blocks(txt)
    txt = replace_indentation_with_four_spaces(txt)
    txt = convert_slides_to_markdown(txt, level=4)
    return txt
