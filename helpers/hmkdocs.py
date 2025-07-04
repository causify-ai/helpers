"""
Import as:

import helpers.hmkdocs as hmkdocs
"""

import re


def remove_table_of_contents(txt: str) -> str:
    """
    Remove the table of contents from the text of a markdown file.

    The table of contents is stored between
    ```
    <!-- toc -->
    ...
    <!-- tocstop -->
    ```

    :param txt: Input markdown text
    :return: Text with table of contents removed
    """
    txt = re.sub(r"<!-- toc -->.*?<!-- tocstop -->", "", txt, flags=re.DOTALL)
    return txt


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


# TODO(ai): Make the function general passing the number of input / output spaces.
def replace_indentation_with_four_spaces(txt: str) -> str:
    """
    Replace 2 spaces indentation with 4 spaces since this is what mkdocs needs.

    :param txt: Input markdown text
    :return: Text with 2-space indentation replaced with 4-space
        indentation
    """
    lines = txt.split("\n")
    result = []
    for line in lines:
        # Count leading spaces.
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0 and leading_spaces % 2 == 0:
            # Replace 2-space indentation with 4-space indentation
            new_indentation = " " * (leading_spaces * 2)
            result.append(new_indentation + line.lstrip())
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
    # Apply all preprocessing steps.
    txt = remove_table_of_contents(txt)
    txt = dedent_python_code_blocks(txt)
    txt = replace_indentation_with_four_spaces(txt)
    return txt
