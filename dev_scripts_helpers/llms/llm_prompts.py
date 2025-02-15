import logging
from typing import Set

import helpers.hdbg as hdbg
import helpers.hmarkdown as hmarkdo
import helpers.hopenai as hopenai

_LOG = logging.getLogger(__name__)


def _run_all(user: str, system: str, model: str, transforms: Set[str]) -> str:
    def _to_run(action: str) -> bool:
        if action in transforms:
            transforms.remove(action)
            return True
        return False

    response = hopenai.get_completion(user, system=system, model=model)
    ret = hopenai.response_to_txt(response)
    if _to_run("remove_code_delimiters"):
        ret = hmarkdo.remove_code_delimiters(ret)
    if _to_run("remove_end_of_line_periods"):
        ret = hmarkdo.remove_end_of_line_periods(ret)
    if _to_run("remove_empty_lines"):
        ret = hmarkdo.remove_empty_lines(ret)
    hdbg.dassert_eq(
        len(transforms), 0, "Not all transforms were run: %s", transforms
    )
    return ret


# #############################################################################
# Prompts.
# #############################################################################


def code_comment(user: str, model: str) -> str:
    system = """
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
    ret = _run_all(user, system, model, transforms)
    return ret


def code_docstring(user: str, model: str) -> str:
    system = """
You are a proficient Python coder.
I will pass you a chunk of Python code.
Add a docstring to the function passed.
The first comment should be in imperative mode and fit in a single line of less than 80 characters.
To describe the parameters use the REST style, which requires each parameter to be prepended with :param
    """
    transforms = {"remove_code_delimiters"}
    ret = _run_all(user, system, model, transforms)
    return ret


def code_type_hints(user: str, model: str) -> str:
    system = """
You are a proficient Python coder.
Add type hints to the function passed.
    """
    transforms = {"remove_code_delimiters"}
    ret = _run_all(user, system, model, transforms)
    return ret


def _get_code_unit_test_prompt(num_tests: int) -> str:
    system = f"""
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


def code_unit_test(user: str, model: str) -> str:
    system = _get_code_unit_test_prompt(5)
    transforms = {"remove_code_delimiters"}
    ret = _run_all(user, system, model, transforms)
    return ret


def code_1_unit_test(user: str, model: str) -> str:
    system = _get_code_unit_test_prompt(1)
    transforms = {"remove_code_delimiters"}
    ret = _run_all(user, system, model, transforms)
    return ret


# #############################################################################


def md_rewrite(user: str, model: str) -> str:
    system = """
You are a proficient technical writer.
Rewrite the text passed as if you were writing a technical document to increase
clarity and readability.
Maintain the structure of the text as much as possible, in terms of bullet
points and their indentation
    """
    transforms = {"remove_code_delimiters"}
    ret = _run_all(user, system, model, transforms)
    return ret


def md_format(user: str, model: str) -> str:
    _ = model
    return user


def md_summarize_short(user: str, model: str) -> str:
    system = """
You are a proficient technical writer.
Summarize the text in less than 30 words.
    """
    transforms = {"remove_code_delimiters"}
    ret = _run_all(user, system, model, transforms)
    return ret


# #############################################################################


def slide_improve(user: str, model: str) -> str:
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
    ret = _run_all(user, system, model, transforms)
    return ret


def slide_colorize(user: str, model: str) -> str:
    system = r"""
You are a proficient technical writer and expert of machine learning.
I will give you markdown text in the next prompt
You will use multiple colors using pandoc \textcolor{COLOR}{text} to highlight important phrases
    """
    ret = _run_all(user, system, model, {"remove_code_delimiters"})
    return ret


# #############################################################################


def apply_prompt(prompt_tag: str, txt: str, model: str) -> str:
    _ = txt, model
    python_cmd = f"{prompt_tag}(txt, model)"
    ret = str(eval(python_cmd))
    return ret