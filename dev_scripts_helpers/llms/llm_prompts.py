import ast
import functools
import hashlib
import logging
import os
import re
from typing import List, Optional, Set, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
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


# Store the prompts that need a certain post-transforms to be applied outside
# the container.
OUTSIDE_CONTAINER_POST_TRANSFORMS = {}


# TODO(gp): We should embed this outside_container_post_transforms in the
# prompts.
if not OUTSIDE_CONTAINER_POST_TRANSFORMS:
    OUTSIDE_CONTAINER_POST_TRANSFORMS = {
        # These are all the prompts with post_transforms with
        # `convert_to_vim_cfile`.
        "convert_file_names": [
            "code_review",
            "code_review_and_find_missing_docstrings",
            "code_propose_refactoring",
        ],
        "prettier_on_str": [
            "md_rewrite",
            "md_summarize_short",
            "slide_improve",
            "slide_colorize",
        ],
    }
    valid_prompts = get_prompt_tags()
    for _, prompts in OUTSIDE_CONTAINER_POST_TRANSFORMS.items():
        for prompt in prompts:
            hdbg.dassert_in(prompt, valid_prompts)


def get_outside_container_post_transforms(transform_name: str) -> Set[str]:
    hdbg.dassert_in(transform_name, OUTSIDE_CONTAINER_POST_TRANSFORMS.keys())
    return OUTSIDE_CONTAINER_POST_TRANSFORMS[transform_name]


# #############################################################################
# Prompts.
# #############################################################################


_PROMPT_OUT = Tuple[str, Set[str], Set[str]]


def test() -> _PROMPT_OUT:
    """
    This is just needed as a placeholder to test the flow.
    """
    system = ""
    pre_transforms = set()
    post_transforms = set()
    return system, pre_transforms, post_transforms


_CONTEXT = r"""
You are a proficient Python coder who pays attention to detail.
I will pass you a chunk of Python code.
"""


def code_comment() -> _PROMPT_OUT:
    """
    Add comments to Python code.
    """
    system = _CONTEXT
    system += r"""
    Every a chunk of 4 or 5 lines of code add comment explaining the code.
    Comments should go before the logical chunk of code they describe.
    Comments should be in imperative form, a full English phrase, and end with a
    period.
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
    """
    Add a REST docstring to Python code.
    """
    system = _CONTEXT
    system += r"""
    Add a docstring to the function passed.
    - The first comment should be in imperative mode and fit in a single line of
      less than 80 characters.
    - To describe the parameters use the REST style, which requires each
      parameter to be prepended with :param
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_type_hints() -> _PROMPT_OUT:
    system = _CONTEXT
    system += r"""
    You will add type hints to the function passed.
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def _get_code_unit_test_prompt(num_tests: int) -> str:
    system = _CONTEXT
    system += r"""
    You will write a unit test suite for the function passed.

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
    system = _CONTEXT
    system += r"""
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


# TODO(gp): This is kind of expensive and we should use a linter stage.
def code_review_and_find_missing_docstrings() -> _PROMPT_OUT:
    """
    Find missing docstrings in Python code.
    """
    system = _CONTEXT
    system += r"""
    You will review the code and find missing docstrings.

    Do not print any comment, only print the line number in the following style:
    <line_number>: <short description of the proposed improvement>
    """
    pre_transforms = {"add_line_numbers"}
    post_transforms = {"convert_to_vim_cfile"}
    return system, pre_transforms, post_transforms


# def code_review_and_fix() -> _PROMPT_OUT:
#     system = _CONTEXT
#     system += r"""
#     You will review the code and make sure it is correct and readable.

#     You will print the code with the proposed improvements, minimizing the
#     number of changes to the code that are not strictly needed.
#     """
#     pre_transforms = {"add_line_numbers"}
#     post_transforms = {"convert_to_vim_cfile"}
#     return system, pre_transforms, post_transforms


def code_propose_refactoring() -> _PROMPT_OUT:
    system = _CONTEXT
    system += r"""
    You will review the code and look for opportunities to refactor the code,
    by removing redundancy and copy-paste code.

    Do not print any comment, besides for each point of improvement, you will
    print the line number and the proposed improvement in the following style:
    <line_number>: <short description of the proposed improvement>
    """
    pre_transforms = {"add_line_numbers"}
    post_transforms = {"convert_to_vim_cfile"}
    return system, pre_transforms, post_transforms


def code_refactor_and_fix() -> _PROMPT_OUT:
    system = _CONTEXT
    system += r"""
    You will review the code and look for opportunities to refactor the code,
    by removing redundancy and copy-paste code, and apply refactoring to remove
    redundancy in the code, minimizing the number of changes to the code that
    are not needed.
    """
    pre_transforms = set()
    post_transforms = set()
    return system, pre_transforms, post_transforms


def code_apply_linter_issues() -> _PROMPT_OUT:
    system = _CONTEXT
    system += r"""
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


def code_fix_string() -> _PROMPT_OUT:
    """
    Fix the log statements to use % formatting.
    """
    system = _CONTEXT
    system += r"""
    Use % formatting instead of f-strings (formatted string literals).
    Do not print any comment, just the converted code.

    For instance, convert:
    _LOG.info(f"env_var='{str(env_var)}' is not in env_vars='{str(os.environ.keys())}'")
    to
    _LOG.info("env_var='%s' is not in env_vars='%s'", env_var, str(os.environ.keys()))

    For instance, convert:
    hdbg.dassert_in(env_var, os.environ, f"env_var='{str(env_var)}' is not in env_vars='{str(os.environ.keys())}''")
    to
    hdbg.dassert_in(env_var, os.environ, "env_var='%s' is not in env_vars='%s'", env_var, str(os.environ.keys()))
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_use_f_strings() -> _PROMPT_OUT:
    """
    Use f-strings, like `f"Hello, {name}. You are {age} years old."`.
    """
    system = _CONTEXT
    system += r"""
    Use f-strings (formatted string literals) instead of % formatting and format
    strings. Do not print any comment, just the converted code.

    For instance, convert:
    "Hello, %s. You are %d years old." % (name, age)
    to
    f"Hello, {name}. You are {age} years old."
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_use_perc_strings() -> _PROMPT_OUT:
    """
    Use % formatting, like `"Hello, %s. You are %d years old." % (name, age)`.
    """
    system = _CONTEXT
    system += r"""
    Use % formatting instead of f-strings (formatted string literals).
    Do not print any comment, just the converted code.

    For instance, convert:
    f"Hello, {name}. You are {age} years old."
    to
    "Hello, %s. You are %d years old." % (name, age)
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_apply_csfy_style1() -> _PROMPT_OUT:
    """
    Apply the csfy style to the code.
    """
    system = _CONTEXT
    file_name = "template_code.py"
    file_content = hio.from_file(file_name)
    system += rf"""
    Apply the style described below to the Python code without changing the
    behavior of the code.
    ```
    {file_content}
    ```
    Do not remove any code, just format the existing code using the style.

    Do not report any explanation of what you did, just the converted code.
    """
    pre_transforms = set()
    post_transforms = {"remove_code_delimiters"}
    return system, pre_transforms, post_transforms


def code_apply_csfy_style2() -> _PROMPT_OUT:
    """
    Apply the csfy style to the code.
    """
    system = _CONTEXT
    system += r"""
    Apply the following style to the code:
    - Convert docstrings into REST docstrings
    - Always use imperative in comments
    - Remove empty spaces in functions
    - Add type hints, when missing
    - Use * before mandatory parameters
    - Make local functions private
    - Convert .format() to f-string unless it’s a _LOG
    """


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
        # 57: The docstring should use more detailed type annotations for ...
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
            # 98-104: Simplify the hash computation logic with a helper ...
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

    This is used to convert the results of the LLM into something that vim can
    use to open the files and jump to the correct lines.

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
    if prompt_tag == "test":
        txt = "\n".join(txt)
        txt_out = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    else:
        # We need to import this here since we have this package only when
        # running inside a Dockerized executable. We don't want an import to
        # this file assert since openai is not available in the local dev
        # environment.
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
