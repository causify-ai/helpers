import logging
import sys

import helpers.hopenai as hopenai
import helpers.transform_text as transform_text

_LOG = logging.getLogger(__name__)


# #############################################################################
# Prompts.
# #############################################################################

def format_markdown(user: str) -> str:
    return user


def code_comment(user: str) -> str:
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
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret


def code_docstring(user: str) -> str:
    system = """
You are a proficient Python coder.
I will pass you a chunk of Python code.
Add a docstring to the function passed.
The first comment should be in imperative mode and fit in a single line of less than 80 characters.
To describe the parameters use the REST style, which requires each parameter to be prepended with :param
    """
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret


def code_type_hints(user: str) -> str:
    system = """
You are a proficient Python coder.
Add type hints to the function passed.
    """
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
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

def code_unit_test(user: str) -> str:
    system = _get_code_unit_test_prompt(5)
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret


def code_1_unit_test(user: str) -> str:
    system = _get_code_unit_test_prompt(1)
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret

# #############################################################################


def rewrite_as_tech_writer(user: str) -> str:
    system = """
You are a proficient technical writer.
Rewrite the text passed as if you were writing a technical document to increase
clarity and readability.
Maintain the structure of the text as much as possible, in terms of bullet
points and their indentation
    """
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret


def improve_markdown_slide(user: str) -> str:
    system = r"""
You are a proficient technical writer and expert of machine learning.
I will give you markdown text in the next prompt
You will convert the following markdown text into bullet points to make sure that the text is clean and readable
    """
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    ret = transform_text.remove_end_of_line_periods(ret)
    ret = transform_text.remove_empty_lines(ret)
    return ret


def colorize_markdown_slide(user: str) -> str:
    system = r"""
You are a proficient technical writer and expert of machine learning.
I will give you markdown text in the next prompt
You will use multiple colors using pandoc \textcolor{COLOR}{text} to highlight important phrases
    """
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret



# #############################################################################


def apply_prompt(prompt_tag: str, txt: str) -> str:
    _ = prompt_tag, txt
    python_cmd = f"txt = {prompt_tag}(txt)"
    try:
        exec(python_cmd)
    except NameError:
        _LOG.error(f"Invalid prompt_tag={prompt_tag}")
        sys.exit(1)
    # if prompt_tag == "format_markdown":
    #     pass
    # elif prompt_tag == "code_comment":
    #     txt = code_comment(txt)
    # elif prompt_tag == "code_docstring":
    #     txt = code_docstring(txt)
    # elif prompt_tag == "code_unit_test":
    #     txt = code_unit_test(txt)
    # elif prompt_tag == "code_typehints":
    #     txt = code_type_hints(txt)
    # elif prompt_tag == "rewrite_as_tech_writer":
    #     txt = rewrite_as_tech_writer(txt)
    # elif prompt_tag == "slide_improve":
    #     txt = improve_markdown_slide(txt)
    # elif prompt_tag == "slide_colorize":
    #     txt = colorize_markdown_slide(txt)
    # else:
    #     raise ValueError("Invalid prompt_tag=%s" % prompt_tag)
    return txt
