import ast
import functools
import hashlib
import logging
import os
import re
from typing import Dict, List, Optional, Set, Tuple, Union

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)


# #############################################################################
# get_prompt_tags()
# #############################################################################


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


# #############################################################################


# Store the prompts that need a certain post-transforms to be applied outside
# the container.
_POST_CONTAINER_TRANSFORMS: Dict[str, List[str]] = {}


def get_post_container_transforms(
    transform_name: str,
) -> Dict[str, List[str]]:
    global _POST_CONTAINER_TRANSFORMS
    if not _POST_CONTAINER_TRANSFORMS:
        valid_prompts = get_prompt_tags()
        for prompt in valid_prompts:
            _, _, _, post_container_transforms = eval(f"{prompt}()")
            hdbg.dassert_not_in(prompt, _POST_CONTAINER_TRANSFORMS)
            _POST_CONTAINER_TRANSFORMS[prompt] = list(post_container_transforms)
    hdbg.dassert_in(transform_name, _POST_CONTAINER_TRANSFORMS.keys())
    return _POST_CONTAINER_TRANSFORMS[transform_name]


# #############################################################################
# Prompts.
# #############################################################################


_PROMPT_OUT = Tuple[str, Set[str], Set[str], List[str]]


_CODING_CONTEXT = r"""
    You are a proficient Python coder who pays attention to detail.
    I will pass you a chunk of Python code.
    """


def test() -> _PROMPT_OUT:
    """
    Placeholder to test the flow.
    """
    system = ""
    pre_transforms: Set[str] = set()
    post_transforms: Set[str] = set()
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################
# Fix.
# #############################################################################


def code_fix_existing_comments() -> _PROMPT_OUT:
    """
    Fix the already existing comments in the Python code.
    """
    system = _CODING_CONTEXT
    system += r"""
    Make sure that comments in the code are:
    - in imperative form
    - a correct English phrase
    - end with a period `.`
    - clear

    Comments should be before the code that they refer to
    E.g.,
    ```
    dir_name = self.directory.name  # For example, "helpers".
    ```
    should become
    ```
    # E.g., "helpers".
    dir_name = self.directory.name
    ```

    Variables should be enclosed in a back tick, like `bar`.
    Functions should be reported as `foo()`.

    Do not change the code.
    Do not add any empty line.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_improve_comments() -> _PROMPT_OUT:
    """
    Add comments to Python code.
    """
    system = _CODING_CONTEXT
    system += r"""
    - Add comments for the parts of the code that are not properly commented
        - E.g., every chunk of 4 or 5 lines of code add comment explaining the
          code
    - Comments should go before the logical chunk of code they describe
    - Comments should be in imperative form, a full English phrase, and end with a
      period `.`
    - Do not comment every single line of code and especially logging statements
    - Add examples of the values of variables, when you are sure of the types
      and values of variables. If you are not sure, do not add any information.

    Do not change the code.
    Do not remove any already existing comment.
    Do not add any empty line.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_logging_statements() -> _PROMPT_OUT:
    """
    Add logging statements to Python code.
    """
    system = _CODING_CONTEXT
    system += r'''
    When a variable `foobar` is important for debugging the code in case of
    failure, add statements like:
    ```
    _LOG.debug(hprint.to_str("foobar"))
    ```

    At the beginning of an important function, after the docstring, add code
    like
    ```
       def get_text_report(self) -> str:
       """
       Generate a text report listing each module's dependencies.

       :return: Text report of dependencies, one per line.
       """
       _LOG.debug(hprint.func_signature_to_str())
    ```

    Do not change the code.
    Do not remove any already existing comment.
    Do not add any empty line.
    '''
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_docstrings() -> _PROMPT_OUT:
    """
    Add or complete a REST docstring to Python code.

    Each function should have a docstring that describes the function,
    its parameters, and its return value.

    Create examples of the values in input and output of each function,
    only when you are sure of the types and values of variables. If you
    are not sure, do not add any information.
    """
    system = _CODING_CONTEXT
    system += r'''
    Make sure each function as a REST docstring
    - The first comment should be in imperative mode and fit in a single line of
      less than 80 characters
    - To describe the parameters use the REST style, which requires each
      parameter to be prepended with :param

    An example of a correct docstring is:
    ```
    def _format_greeting(name: str, *, greeting: str = "Hello") -> str:
        """
        Format a greeting message with the given name.

        :param name: the name to include in the greeting (e.g., "John")
        :param greeting: the base greeting message to use (e.g., "Ciao")
        :return: formatted greeting (e.g., "Hello John")
        """
    ```
    '''
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_type_hints() -> _PROMPT_OUT:
    system = _CODING_CONTEXT
    system += r"""
    Add type hints to the Python code passed.

    For example, convert:
    ```
    def process_data(data, threshold=0.5):
        results = []
        for item in data:
            if item > threshold:
                results.append(item)
        return results
    ```
    to:
    ```
    def process_data(data: List[float], *, threshold: float = 0.5) -> List[float]:
        results: List[float] = []
        for item in data:
            if item > threshold:
                results.append(item)
        return results
    ```
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_log_string() -> _PROMPT_OUT:
    """
    Fix the log statements to use % formatting.
    """
    system = _CODING_CONTEXT
    system += r"""
    Fix logging statements and dassert statements by using % formatting instead
    of f-strings (formatted string literals).

    Do not print any comment, but just the converted code.

    For instance, convert:
    ```
    _LOG.info(f"env_var='{str(env_var)}' is not in env_vars='{str(os.environ.keys())}'")
    ```
    to
    ```
    _LOG.info("env_var='%s' is not in env_vars='%s'", env_var, str(os.environ.keys()))
    ```

    For instance, convert:
    ```
    hdbg.dassert_in(env_var, os.environ, f"env_var='{str(env_var)}' is not in env_vars='{str(os.environ.keys())}''")
    ```
    to
    ```
    hdbg.dassert_in(env_var, os.environ, "env_var='%s' is not in env_vars='%s'", env_var, str(os.environ.keys()))
    ```
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_by_using_f_strings() -> _PROMPT_OUT:
    """
    Fix code to use f-strings, like `f"Hello, {name}.

    You are {age} years old."`.
    """
    system = _CODING_CONTEXT
    system += r"""
    Fix statements like:
    ```
    raise ValueError(f"Unsupported data_source='{data_source}'")
    ```
    by using f-strings (formatted string literals) instead of % formatting and
    format strings.

    Do not print any comment, but just the converted code.

    For instance, convert:
    ```
    "Hello, %s. You are %d years old." % (name, age)
    ```
    to
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_by_using_perc_strings() -> _PROMPT_OUT:
    """
    Use % formatting, like `"Hello, %s. You are %d years old." % (name, age)`.
    """
    system = _CODING_CONTEXT
    system += r"""
    Use % formatting instead of f-strings (formatted string literals).
    Do not print any comment, just the converted code.

    For instance, convert:
    `f"Hello, {name}. You are {age} years old."`
    to
    `"Hello, %s. You are %d years old." % (name, age)`
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_from_imports() -> _PROMPT_OUT:
    """
    Fix code to use imports instead of "from import" statements.
    """
    system = _CODING_CONTEXT
    system += r"""
    Replace any Python "from import" statement like `from X import Y` with the
    form `import X` and then replace the uses of `Y` with `X.Y`
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_star_before_optional_parameters() -> _PROMPT_OUT:
    """
    Fix code missing the star before optional parameters.
    """
    system = _CODING_CONTEXT
    system += r"""
    When you find a Python function with optional parameters, add a star after
    the mandatory parameters and before the optional parameters, and make sure
    that the function is called with the correct number of arguments.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_unit_test() -> _PROMPT_OUT:
    """ """
    system = _CODING_CONTEXT
    system += r"""
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_fix_csfy_style() -> _PROMPT_OUT:
    """
    Apply all the transformations required to write code according to the
    Causify conventions.
    """
    # > grep "def code_fix" ./dev_scripts_helpers/llms/llm_prompts.py | awk '{print $2 }'
    function_names = [
        "code_fix_existing_comments",
        "code_fix_docstrings",
        "code_fix_type_hints",
        "code_fix_log_string",
        "code_fix_by_using_f_strings",
        "code_fix_by_using_perc_strings",
        "code_fix_from_imports",
        "code_fix_star_before_optional_parameters",
    ]
    system_prompts = []
    for function_name in function_names:
        (
            system,
            pre_transforms_tmp,
            post_transforms_tmp,
            post_container_transforms_tmp,
        ) = eval(function_name)()
        system_prompts.append(system)
        hdbg.dassert_eq(pre_transforms_tmp, set())
        hdbg.dassert_eq(post_transforms_tmp, {"remove_code_delimiters"})
        hdbg.dassert_eq(post_container_transforms_tmp, [])
    #
    system = "\n\n".join(system_prompts)
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################
# Review.
# #############################################################################


def code_review_correctness() -> _PROMPT_OUT:
    """
    Review the code for correctness.
    """
    system = _CODING_CONTEXT
    system += r"""
    You will review the code and make sure it is:
    - correct
    - clean and readable
    - efficient
    - robust
    - maintainable

    Do not print any comment, besides for each point of improvement, you will
    print the line number and the proposed improvement in the following style:
    <line_number>: <short description of the proposed improvement>
    """
    pre_transforms = {"add_line_numbers"}
    post_transforms = {"convert_to_vim_cfile"}
    post_container_transforms = ["convert_file_names"]
    return system, pre_transforms, post_transforms, post_container_transforms


def code_review_refactoring() -> _PROMPT_OUT:
    """
    Review the code for refactoring opportunities.
    """
    system = _CODING_CONTEXT
    system += r"""
    You will review the code and look for opportunities to refactor the code,
    by removing redundancy and copy-paste code.

    Do not print any comment, besides for each point of improvement, you will
    print the line number and the proposed improvement in the following style:
    <line_number>: <short description of the proposed improvement>
    """
    pre_transforms = {"add_line_numbers"}
    post_transforms = {"convert_to_vim_cfile"}
    post_container_transforms = ["convert_file_names"]
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################
# Transform the code.
# #############################################################################


def code_transform_remove_redundancy() -> _PROMPT_OUT:
    system = _CODING_CONTEXT
    system += r"""
    You will review the code and look for opportunities to refactor the code,
    by removing redundancy and copy-paste code, and apply refactoring to remove
    redundancy in the code, minimizing the number of changes to the code that
    are not needed.
    """
    pre_transforms: Set[str] = set()
    post_transforms: Set[str] = set()
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_transform_apply_csfy_style() -> _PROMPT_OUT:
    """
    Apply the style to the code using template code in `template_code.py`.
    """
    system = _CODING_CONTEXT
    file_name = "template_code.py"
    file_name = os.path.join(hgit.find_helpers_root(), file_name)
    file_content = hio.from_file(file_name)
    system += rf"""
    Apply the style described below to the Python code
    
    ```
    {file_content}
    ```
    
    Do not remove any code, just format the existing code using the style.
    Do not change the behavior of the code.
    Do not report any explanation of what you did, but just the converted code.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_transform_apply_linter_instructions() -> _PROMPT_OUT:
    """
    Apply the transforms passed in a cfile to the code.
    """
    system = _CODING_CONTEXT
    system += r"""
    I will pass you Python code and a list of linting errors in the format
    <line_number>:<error_code>:<error_message>

    You will fix the code according to the linting errors passed, print the
    modified code, minimizing the number of changes to the code that are not
    needed.

    Do not print any discussion, but just the converted code.
    """
    pre_transforms = {"add_line_numbers", "add_instructions"}
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################
# Unit tests.
# #############################################################################


# TODO(gp): Probably obsolete since Cursor can do it.
def _get_code_unit_test_prompt(num_tests: int) -> str:
    system = _CODING_CONTEXT
    system += rf"""
    - You will write a unit test suite for the function passed.

    - Write {num_tests} unit tests for the function passed
    - Just output the Python code
    - Use the following style for the unit tests:
    - When calling the function passed assume it's under the module called uut
      and the user has called `import uut as uut`
    """
    return system


def code_write_unit_test() -> _PROMPT_OUT:
    system = _get_code_unit_test_prompt(5)
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


def code_write_1_unit_test() -> _PROMPT_OUT:
    system = _get_code_unit_test_prompt(1)
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms: List[str] = []
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################


_MD_CONTEXT = r"""
    You are a proficient technical writer.
    I will pass you a chunk of markdown code.
    """


def md_rewrite() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    Rewrite the text passed as if you were writing a technical document to
    increase clarity and readability.
    Maintain the structure of the text as much as possible, in terms of bullet
    points and their indentation
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


def md_summarize_short() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    Summarize the text in less than 30 words.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


def md_clean_up_how_to_guide() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    Format the text passed as a how-to guide.

    An how-to-guide should explain how to solve a specific problem or achieve
    a goal.

    Rewrite the markdown passed to make it a how-to guide and contain the
    the following sections:
    - Goal / Use Case
    - Assumptions / Requirements
    - Step-by-Step Instructions
    - Alternatives or Optional Steps
    - Troubleshooting

    Do not lose any information, just rewrite the text to make it a how-to.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################


def slide_improve() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    I will give you markdown text

    You will:
    - Convert the following markdown text into bullet points
    - Make sure that the text is clean and readable

    Print only the markdown without any explanation.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {
        "remove_code_delimiters",
        "remove_end_of_line_periods",
        "remove_empty_lines",
    }
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


def slide_improve2() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    I will give you markdown text

    You will:
    - Maintain the structure of the text and keep the content of the existing
      text
    - Remove all the words that are not needed, minimizing the changes to the
      text
    - Add bullet points to the text that are important or missing
    - Add examples to clarify the text and help intuition

    Print only the markdown without any explanation.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {
        "remove_code_delimiters",
        "remove_end_of_line_periods",
        "remove_empty_lines",
    }
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


def slide_elaborate() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    I will give you markdown text

    You will:
    - Add bullet points to the text that are important or missing
    - Add examples to clarify the text and help intuition

    Print only the markdown without any explanation.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {
        "remove_code_delimiters",
        "remove_end_of_line_periods",
        "remove_empty_lines",
    }
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


def slide_reduce() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    I will give you markdown text

    You will:
    - Maintain the structure of the text
    - Keep all the figures
    - Make sure that the text is clean and readable
    - Remove all the words that are not needed
    - Minimize the changes to the text

    Print only the markdown without any explanation.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {
        "remove_code_delimiters",
        "remove_end_of_line_periods",
        "remove_empty_lines",
    }
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


def slide_bold() -> _PROMPT_OUT:
    system = _MD_CONTEXT
    system += r"""
    I will give you markdown text

    You will:
    - Not change the text or the structure of the text
    - Highlight in bold only the most important phrases in the text—those that
      are key to understanding the main points
    - Keep the highlights minimal and avoid over-marking. Focus on critical
      concepts, key data, or essential takeaways rather than full sentences or
      excessive details.

    Print only the markdown without any explanation.
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################


def scratch_categorize_topics() -> _PROMPT_OUT:
    system = r"""
    For each of the following title of article, find the best topic among the
    following ones:

    LLM Reasoning, Quant Finance, Time Series, Developer Tools, Python
    Ecosystem, Git and GitHub, Software Architecture, AI Infrastructure,
    Knowledge Graphs, Diffusion Models, Causal Inference, Trading Strategies,
    Prompt Engineering, Mathematical Concepts, Dev Productivity, Rust and C++,
    Marketing and Sales, Probabilistic Programming, Code Refactoring, Open
    Source

    Only print
    - the first 3 words of the title
    - a separator |
    - the topic
    and don't print any explanation.

    if you don't know the topic, print "unknown"
    """
    pre_transforms: Set[str] = set()
    post_transforms = {"remove_code_delimiters"}
    post_container_transforms = ["format_markdown"]
    return system, pre_transforms, post_transforms, post_container_transforms


# #############################################################################
# Transforms.
# #############################################################################


def _extract_vim_cfile_lines(txt: str) -> List[Tuple[int, str]]:
    ret_out: List[Tuple[int, str]] = []
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
            line_number = int(match.group(1))
            description = match.group(2)
        else:
            # ```
            # 98-104: Simplify the hash computation logic with a helper ...
            # ```
            regex = re.compile(
                r"""
                ^(\d+)-\d+:         # Line number(s) followed by colon
                \s*                 # Space
                (.*)$               # Rest of line
                """,
                re.VERBOSE,
            )
            match = regex.match(line)
        if match:
            line_number = int(match.group(1))
            description = match.group(2)
        else:
            _LOG.warning("Can't parse line: '%s'", line)
            continue
        ret_out.append((line_number, description))
    return ret_out


def _convert_to_vim_cfile_str(txt: str, in_file_name: str) -> str:
    """
    Convert the text passed to a string representing a vim cfile.

    E.g.,
    become:
    """
    ret_out = _extract_vim_cfile_lines(txt)
    # Append the file name to the description.
    ret_out2 = []
    for line_number, description in ret_out:
        ret_out2.append(f"{in_file_name}:{line_number}: {description}")
    # Save the output.
    txt_out = "\n".join(ret_out2)
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


def to_run(action: str, transforms: Union[Set[str], List[str]]) -> bool:
    """
    Return True if the action should be run.
    """
    if action in transforms:
        transforms.remove(action)
        return True
    return False


def run_prompt(
    prompt_tag: str,
    txt: str,
    model: str,
    *,
    instructions: str = "",
    in_file_name: str = "",
    out_file_name: str = "",
) -> Optional[str]:
    """
    Run the prompt passed and apply the transforms to the response.

    :param prompt_tag: tag of the prompt to run
    :param txt: text to run the prompt on
    :param model: model to use
    :param instructions: instructions to add to the system prompt (e.g.,
        line numbers and transforms to apply to each file)
    :param in_file_name: name of the input file (needed only for cfile)
    :param out_file_name: name of the output file (needed only for
        cfile)
    :return: transformed text
    """
    _LOG.debug(hprint.func_signature_to_str())
    # Get the info corresponding to the prompt tag.
    prompt_tags = get_prompt_tags()
    hdbg.dassert_in(prompt_tag, prompt_tags)
    python_cmd = f"{prompt_tag}()"
    system_prompt, pre_transforms, post_transforms, post_container_transforms = (
        eval(python_cmd)
    )
    # Check return types.
    hdbg.dassert_isinstance(system_prompt, str)
    hdbg.dassert_isinstance(pre_transforms, set)
    hdbg.dassert_isinstance(post_transforms, set)
    hdbg.dassert_isinstance(post_container_transforms, list)
    system_prompt = hprint.dedent(system_prompt)
    # 1) Run pre-transforms.
    if to_run("add_line_numbers", pre_transforms):
        txt = hmarkdo.add_line_numbers(txt)
    if to_run("add_instructions", pre_transforms):
        # Add the specific instructions to the system prompt.
        # E.g.,
        # The instructions are:
        # 52: in private function `_parse`:D401: First line should be in
        # 174: error: Missing return statement  [return] [mypy]
        # 192: [W1201(logging-not-lazy), _convert_file_names] Use lazy %
        system_prompt = hprint.dedent(system_prompt)
        hdbg.dassert_ne(instructions, "")
        system_prompt += "\nThe instructions are:\n" + instructions + "\n\n"
    hdbg.dassert_eq(
        len(pre_transforms),
        0,
        "Not all pre_transforms were run: %s",
        pre_transforms,
    )
    # 2) Run the prompt.
    if prompt_tag == "test":
        # Compute the hash of the text.
        txt = "\n".join(txt)
        txt_out = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    else:
        # We need to import this here since we have this package only when
        # running inside a Dockerized executable. We don't want an import to
        # this file assert since openai is not available in the local dev
        # environment.
        import helpers.hopenai as hopenai

        _LOG.debug(hprint.to_str("system_prompt"))
        response = hopenai.get_completion(
            txt, system_prompt=system_prompt, model=model, print_cost=True
        )
        # _LOG.debug(hprint.to_str("response"))
        txt_out = hopenai.response_to_txt(response)
    hdbg.dassert_isinstance(txt_out, str)
    # 3) Run post-transforms.
    if to_run("remove_code_delimiters", post_transforms):
        txt_out = hmarkdo.remove_code_delimiters(txt_out)
    if to_run("remove_end_of_line_periods", post_transforms):
        txt_out = hmarkdo.remove_end_of_line_periods(txt_out)
    if to_run("remove_empty_lines", post_transforms):
        txt_out = hmarkdo.remove_empty_lines(txt_out)
    if to_run("convert_to_vim_cfile", post_transforms):
        hdbg.dassert_ne(in_file_name, "")
        hdbg.dassert_ne(out_file_name, "")
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
