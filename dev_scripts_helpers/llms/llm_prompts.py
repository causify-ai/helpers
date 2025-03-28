from typing import List, Optional, Set, Tuple
import ast
import logging
import os
import re

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hopenai as hopenai
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################
# Prompts.
# #############################################################################


def code_comment() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient Python coder.
    I will pass you a chunk of Python code.
    Every 10 lines of code add comment explaining the code.
    Comments should go before the logical chunk of code they describe.
    Comments should be in imperative form, a full English phrase, and end with a period.
    """
    # You are a proficient Python coder and write English very well.
    # Given the Python code passed below, improve or add comments to the code.
    # Comments must be for every logical chunk of 4 or 5 lines of Python code.
    # Do not comment every single line of code and especially logging statements.
    # Each comment should be in imperative form, a full English phrase, and end
    # with a period.
    transforms = {"remove_code_delimiters"}
    return system, transforms


def code_docstring() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient Python coder.
    I will pass you a chunk of Python code.
    Add a docstring to the function passed.
    The first comment should be in imperative mode and fit in a single line of less than 80 characters.
    To describe the parameters use the REST style, which requires each parameter to be prepended with :param
    """
    transforms = {"remove_code_delimiters"}
    return system, transforms


def code_type_hints() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient Python coder.
    Add type hints to the function passed.
    """
    transforms = {"remove_code_delimiters"}
    return system, transforms


def _get_code_unit_test_prompt(num_tests: int) -> str:
    system = rf"""
    You are a world-class Python developer with an eagle eye for unintended bugs and edge cases.

    I will pass you Python code and you will write a unit test suite for the function.

    Write {num_tests} unit tests for the function passed
    Just output the Python code
    Use the following style for the unit tests:
    When calling the function passed assume it's under the module called uut and the user has called `import uut as uut`
    ```
    act = call to the function passed
    exp = expected code
    self.assert_equal(act, exp)
    ```
    """
    return system


def code_unit_test() -> Tuple[str, Set[str]]:
    system = _get_code_unit_test_prompt(5)
    transforms = {"remove_code_delimiters"}
    return system, transforms


def code_1_unit_test() -> Tuple[str, Set[str]]:
    system = _get_code_unit_test_prompt(1)
    transforms = {"remove_code_delimiters"}
    return system, transforms


def code_review() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient Python coder that pays attention to detail.
    I will pass you Python code.
    You will review the code and make sure it is correct.
    You will also make sure that the code is clean and readable.
    You will also make sure that the code is efficient.
    You will also make sure that the code is robust.
    You will also make sure that the code is maintainable.

    Do not print any comment, besides for each point of improvement, you will
    print the line number and the proposed improvement in the following style:
    <line_number>: <short description of the proposed improvement>
    """
    transforms = {"convert_to_vim_cfile"}
    return system, transforms


def code_review_and_improve() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient Python coder that pays attention to detail.
    I will pass you Python code.
    You will review the code and make sure it is correct.
    You will also make sure that the code is clean and readable.
    You will also make sure that the code is efficient.
    You will also make sure that the code is robust.
    You will also make sure that the code is maintainable.

    You will print the code with the proposed improvements, minimizing the number of
    changes to the code that are not needed.
    """
    transforms = {}
    return system, transforms


def code_propose_refactoring() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient Python coder that pays attention to detail.
    I will pass you Python code.
    You will review the code and look for opportunities to refactor the code.

    Do not print any comment, besides for each point of improvement, you will
    print the line number and the proposed improvement in the following style:
    <line_number>: <short description of the proposed improvement>
    """
    transforms = {}
    return system, transforms


# #############################################################################


def md_rewrite() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient technical writer.
    Rewrite the text passed as if you were writing a technical document to increase
    clarity and readability.
    Maintain the structure of the text as much as possible, in terms of bullet
    points and their indentation
    """
    transforms = {"remove_code_delimiters"}
    return system, transforms


def md_summarize_short() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient technical writer.
    Summarize the text in less than 30 words.
    """
    transforms = {"remove_code_delimiters"}
    return system, transforms


# #############################################################################


def slide_improve() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient technical writer and expert of machine learning.
    I will give you markdown text in the next prompt
    You will convert the following markdown text into bullet points
    Make sure that the text is clean and readable
    """
    transforms = {
        "remove_code_delimiters",
        "remove_end_of_line_periods",
        "remove_empty_lines",
    }
    return system, transforms


def slide_colorize() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient technical writer and expert of machine learning.
    I will give you markdown text in the next prompt
    - Do not change the text or the structure of the text
    - You will use multiple colors using pandoc \textcolor{COLOR}{text} to highlight
    only the most important phrases in the text—those that are key to understanding
    the main points. Keep the highlights minimal and avoid over-marking. Focus on
    critical concepts, key data, or essential takeaways rather than full sentences
    or excessive details.
    - You can use the following colors in the given order: red, orange, green, teal, cyan, blue, violet, brown

    - You can highlight only 4 words or phrases in the text

    Print only the markdown without any explanation
    """
    transforms = {"remove_code_delimiters"}
    return system, transforms


def slide_colorize_points() -> Tuple[str, Set[str]]:
    system = r"""
    You are a proficient technical writer and expert of machine learning.
    I will give you markdown text in the next prompt
    - Do not change the text or the structure of the text
    - You will highlight with \textcolor{COLOR}{text} the bullet point at the first level, without highlighting the - character
    - You can use the following colors in the given order: red, orange, green, teal, cyan, blue, violet, brown

    Print only the markdown without any explanation
    """
    transforms = {"remove_code_delimiters"}
    return system, transforms


# #############################################################################
# Transforms.
# #############################################################################


def _convert_to_vim_cfile_str(txt: str, in_file_name: str) -> str:
    """
    Convert the text passed to a string representing a vim cfile.
    """
    ret_out = []
    for line in txt.split("\n"):
        # 57: The docstring should use more detailed type annotations for clarity, e.g., `List[str]`, `int`, etc.
        regex = re.compile(r"""
            ^(\d+):         # Line number followed by colon
            \s*             # Space
            (.*)$           # Rest of line
            """, re.VERBOSE)
        match = regex.match(line)
        if match:
            line_number = match.group(1)
            description = match.group(2)
        else:
            # 98-104: Simplify the hash computation logic with a helper function to avoid redundant steps.
            regex = re.compile(r"""
                ^(\d+):\d+:    # Line number(s) followed by colon
                \s*                 # Space
                (.*)$               # Rest of line
                """, re.VERBOSE)
            match = regex.match(line)
            hdbg.dassert(match, "Can't parse line: '%s'", line)
            line_number = match.group(1)
            description = match.group(2)
        ret_out.append(f"{in_file_name}:{line_number}: {description}")
    # Save the output.
    txt_out = "\n".join(ret_out)
    return txt_out


def _convert_to_vim_cfile(txt: str, in_file_name: str, out_file_name: str) -> None:
    """
    Convert the text passed to a vim cfile.
    """
    txt_out = _convert_to_vim_cfile_str(txt, in_file_name)
    #
    if out_file_name != "cfile":
        _LOG.warning("Invalid out_file_name '%s', using 'cfile'", out_file_name)
    out_file_name = "cfile"
    hio.to_file(out_file_name, txt_out)
    print("Saved file in %s", out_file_name)


# #############################################################################
# run_prompt()
# #############################################################################


def run_prompt(prompt_tag: str, txt: str, model: str, in_file_name: str, out_file_name: str) -> Optional[str]:
    """
    Run the prompt passed and apply the transforms to the response.
    """
    _LOG.debug(hprint.to_str("prompt_tag model in_file_name out_file_name"))
    #
    prompt_tags = get_prompt_tags()
    hdbg.dassert_in(prompt_tag, prompt_tags)
    python_cmd = f"{prompt_tag}()"
    system_prompt, transforms = eval(python_cmd)
    hdbg.dassert_isinstance(system_prompt, str)
    hdbg.dassert_isinstance(transforms, set)
    #
    system_prompt = hprint.dedent(system_prompt)
    response = hopenai.get_completion(txt, system_prompt=system_prompt, model=model, print_cost=True)
    #_LOG.debug(hprint.to_str("response"))
    txt_out = hopenai.response_to_txt(response)
    hdbg.dassert_isinstance(txt_out, str)

    # Apply transforms to the response.
    def _to_run(action: str) -> bool:
        if action in transforms:
            transforms.remove(action)
            return True
        return False
    if _to_run("remove_code_delimiters"):
        txt_out = hmarkdo.remove_code_delimiters(txt_out)
    if _to_run("remove_end_of_line_periods"):
        txt_out = hmarkdo.remove_end_of_line_periods(txt_out)
    if _to_run("remove_empty_lines"):
        txt_out = hmarkdo.remove_empty_lines(txt_out)
    if _to_run("convert_to_vim_cfile"):
        _convert_to_vim_cfile(txt_out, in_file_name, out_file_name)
        txt_out = None
    hdbg.dassert_eq(
        len(transforms), 0, "Not all transforms were run: %s", transforms
    )
    # Return.
    if txt_out is not None:
        hdbg.dassert_isinstance(txt_out, str)
    return txt_out


def get_prompt_tags() -> List[str]:
    """
    Return the list of functions in this file that can be called.
    """
    # Find file path of the llm_prompts.py file.
    curr_path = os.path.abspath(__file__)
    file_content = hio.from_file(curr_path)
    #
    matched_functions = []
    # Parse the file content into an AST.
    tree = ast.parse(file_content)
    # Iterate through all function definitions in the AST.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check function arguments and return type that match:
            # ```
            # def xyz() -> Tuple[str, Set[str]]:
            # ```
            args = [arg.arg for arg in node.args.args]
            if (
                args == ["user", "model"]
                and isinstance(node.returns, ast.Name)
                and node.returns.id == "str"
            ):
                matched_functions.append(node.name)
    matched_functions = sorted(matched_functions)
    return matched_functions
