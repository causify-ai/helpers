import ast
import logging
import os
import re
from typing import List, Optional, Set, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################
# Prompts.
# #############################################################################


_PROMPT_OUT = Tuple[str, Set[str], Set[str]]


def code_comment() -> _PROMPT_OUT:
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
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_docstring() -> _PROMPT_OUT:
    system = r"""
    You are a proficient Python coder.
    I will pass you a chunk of Python code.
    Add a docstring to the function passed.
    The first comment should be in imperative mode and fit in a single line of less than 80 characters.
    To describe the parameters use the REST style, which requires each parameter to be prepended with :param
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_type_hints() -> _PROMPT_OUT:
    system = r"""
    You are a proficient Python coder.
    Add type hints to the function passed.
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


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


def code_unit_test() -> _PROMPT_OUT:
    system = _get_code_unit_test_prompt(5)
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_1_unit_test() -> _PROMPT_OUT:
    system = _get_code_unit_test_prompt(1)
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_review() -> _PROMPT_OUT:
    system = r"""
    You are a proficient Python coder who pays attention to detail.
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
    pre_transforms = {"add_line_numbers"}
    post_transforms = {"convert_to_vim_cfile"}
    return system, pre_transforms, post_transforms


def code_review_and_improve() -> _PROMPT_OUT:
    system = r"""
    You are a proficient Python coder who pays attention to detail.
    I will pass you Python code.
    You will review the code and make sure it is correct and readable.

    You will print the code with the proposed improvements, minimizing the
    number of changes to the code that are not needed.
    """
    pre_transforms = {"add_line_numbers"}
    post_transforms = {"convert_to_vim_cfile"}
    return system, pre_transforms, post_transforms


def code_propose_refactoring() -> _PROMPT_OUT:
    system = r"""
    You are a proficient Python coder who pays attention to detail.
    I will pass you Python code.
    You will review the code and look for opportunities to refactor the code.

    Do not print any comment, besides for each point of improvement, you will
    print the line number and the proposed improvement in the following style:
    <line_number>: <short description of the proposed improvement>
    """
    pre_transforms = {"add_line_numbers"}
    post_transforms = {"convert_to_vim_cfile"}
    return system, pre_transforms, post_transforms


def code_apply_refactoring() -> _PROMPT_OUT:
    system = r"""
    You are a proficient Python coder who pays attention to detail.
    I will pass you Python code.
    You will review the code and apply refactoring to remove redundancy in the
    code, minimizing the number of changes to the code that are not needed.
    """
    pre_transforms = set()
    post_transforms = set()
    return system, pre_transforms, post_transforms


def code_apply_linter_issues() -> _PROMPT_OUT:
    system = r"""
    You are a proficient Python coder who pays attention to detail.
    I will pass you Python code and a list of linting errors in the format
    <file_name>:<line_number>:<error_code>:<error_message>

    You will fix the code according to the linting errors passed, minimizing the
    number of changes to the code that are not needed.

tutorial_github/github_utils.py:105: [W0718(broad-exception-caught), get_github_contributors] Catching too general exception Exception [pylint]
tutorial_github/github_utils.py:106: [W1203(logging-fstring-interpolation), get_github_contributors] Use lazy % formatting in logging functions [pylint]
    """
    pre_transforms = set()
    post_transforms = set()
    return system, pre_transforms, post_transforms


# #############################################################################


def md_rewrite() -> _PROMPT_OUT:
    system = r"""
    You are a proficient technical writer.
    Rewrite the text passed as if you were writing a technical document to increase
    clarity and readability.
    Maintain the structure of the text as much as possible, in terms of bullet
    points and their indentation
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def md_summarize_short() -> _PROMPT_OUT:
    system = r"""
    You are a proficient technical writer.
    Summarize the text in less than 30 words.
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


# #############################################################################


def slide_improve() -> _PROMPT_OUT:
    system = r"""
    You are a proficient technical writer and expert of machine learning.
    I will give you markdown text in the next prompt
    You will convert the following markdown text into bullet points
    Make sure that the text is clean and readable
    """
    pre_transforms = set()
    post_transforms = {
        "remove_code_delimiters",
        "remove_end_of_line_periods",
        "remove_empty_lines",
    }
    return system, pre_transforms, post_transforms


def slide_colorize() -> _PROMPT_OUT:
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
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def slide_colorize_points() -> _PROMPT_OUT:
    system = r"""
    You are a proficient technical writer and expert of machine learning.
    I will give you markdown text in the next prompt
    - Do not change the text or the structure of the text
    - You will highlight with \textcolor{COLOR}{text} the bullet point at the first level, without highlighting the - character
    - You can use the following colors in the given order: red, orange, green, teal, cyan, blue, violet, brown

    Print only the markdown without any explanation
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


# #############################################################################
# Transforms.
# #############################################################################


def _convert_to_vim_cfile_str(txt: str, in_file_name: str) -> str:
    """
    Convert the text passed to a string representing a vim cfile.
    """
    ret_out = []
    for line in txt.split("\n"):
        _LOG.debug(hprint.to_str("line"))
        if line.strip() == "":
            continue
        # ```
        # 57: The docstring should use more detailed type annotations for clarity, e.g., `List[str]`, `int`, etc.
        # ```
        regex = re.compile(
            r"""
            ^(\d+):         # Line number followed by colon
            \s*             # Space
            (.*)$           # Rest of line
            """,
            re.VERBOSE,
        )
        match = regex.match(line)
        if match:
            line_number = match.group(1)
            description = match.group(2)
        else:
            # ```
            # 98-104: Simplify the hash computation logic with a helper function to avoid redundant steps.
            # ```
            regex = re.compile(
                r"""
                ^(\d+)-\d+:    # Line number(s) followed by colon
                \s*                 # Space
                (.*)$               # Rest of line
                """,
                re.VERBOSE,
            )
            match = regex.match(line)
        if match:
            line_number = match.group(1)
            description = match.group(2)
        else:
            _LOG.warning("Can't parse line: '%s'", line)
            continue
        ret_out.append(f"{in_file_name}:{line_number}: {description}")
    # Save the output.
    txt_out = "\n".join(ret_out)
    return txt_out


def _convert_to_vim_cfile(txt: str, in_file_name: str, out_file_name: str) -> str:
    """
    Convert the text passed to a vim cfile.

    in_file_name: path to the file to convert to a vim cfile (e.g.,
        `/app/helpers_root/tmp.llm_transform.in.txt`)
    """
    _LOG.debug(hprint.to_str("txt in_file_name out_file_name"))
    hdbg.dassert_file_exists(in_file_name)
    #
    txt_out = _convert_to_vim_cfile_str(txt, in_file_name)
    #
    if "cfile" not in out_file_name:
        _LOG.warning("Invalid out_file_name '%s', using 'cfile'", out_file_name)
    return txt_out


# #############################################################################
# run_prompt()
# #############################################################################


# Apply transforms to the response.
def _to_run(action: str, transforms: Set[str]) -> bool:
    if action in transforms:
        transforms.remove(action)
        return True
    return False


def run_prompt(
    prompt_tag: str, txt: str, model: str, in_file_name: str, out_file_name: str
) -> Optional[str]:
    """
    Run the prompt passed and apply the transforms to the response.
    """
    _LOG.debug(hprint.to_str("prompt_tag model in_file_name out_file_name"))
    # Get the info corresponding to the prompt tag.
    prompt_tags = get_prompt_tags()
    _LOG.debug(hprint.to_str("prompt_tags"))
    hdbg.dassert_in(prompt_tag, prompt_tags)
    python_cmd = f"{prompt_tag}()"
    system_prompt, pre_transforms, post_transforms = eval(python_cmd)
    hdbg.dassert_isinstance(system_prompt, str)
    hdbg.dassert_isinstance(pre_transforms, set)
    hdbg.dassert_isinstance(post_transforms, set)
    system_prompt = hprint.dedent(system_prompt)
    # Run pre-transforms.
    if _to_run("add_line_numbers", pre_transforms):
        txt = hmarkdo.add_line_numbers(txt)
    hdbg.dassert_eq(
        len(pre_transforms),
        0,
        "Not all pre_transforms were run: %s",
        pre_transforms,
    )
    # We need to import this here since we have this package only when running
    # inside a Dockerized executable. We don't want an import to this file
    # assert since openai is not available in the local dev environment.
    import helpers.hopenai as hopenai

    response = hopenai.get_completion(
        txt, system_prompt=system_prompt, model=model, print_cost=True
    )
    # _LOG.debug(hprint.to_str("response"))
    txt_out = hopenai.response_to_txt(response)
    hdbg.dassert_isinstance(txt_out, str)
    # Run post-transforms.
    if _to_run("remove_code_delimiters", post_transforms):
        txt_out = hmarkdo.remove_code_delimiters(txt_out)
    if _to_run("remove_end_of_line_periods", post_transforms):
        txt_out = hmarkdo.remove_end_of_line_periods(txt_out)
    if _to_run("remove_empty_lines", post_transforms):
        txt_out = hmarkdo.remove_empty_lines(txt_out)
    if _to_run("convert_to_vim_cfile", post_transforms):
        txt_out = _convert_to_vim_cfile(txt_out, in_file_name, out_file_name)
    hdbg.dassert_eq(
        len(post_transforms),
        0,
        "Not all post_transforms were run: %s",
        post_transforms,
    )
    # Return.
    if txt_out is not None:
        hdbg.dassert_isinstance(txt_out, str)
    return txt_out


def get_prompt_tags() -> List[str]:
    """
    Return the list of functions in this file that can be called as a prompt.
    """
    # Read current file.
    curr_path = os.path.abspath(__file__)
    file_content = hio.from_file(curr_path)
    #
    matched_functions = []
    # Parse the file content into an AST.
    tree = ast.parse(file_content)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check function arguments and return type that match the signature:
            # ```
            # def xyz() -> Tuple[str, Set[str]]:
            # ```
            args = [arg.arg for arg in node.args.args]
            has_no_args = len(args) == 0
            if not hasattr(node, "returns") or node.returns is None:
                return_type_str = ""
            else:
                return_type_str = ast.unparse(node.returns)
            _LOG.debug(hprint.to_str("node.name args return_type_str"))
            if has_no_args and return_type_str == "_PROMPT_OUT":
                _LOG.debug("  -> matched")
                matched_functions.append(node.name)
    matched_functions = sorted(matched_functions)
    return matched_functions
