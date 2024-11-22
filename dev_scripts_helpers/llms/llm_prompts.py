import logging

import helpers.hopenai as hopenai

_LOG = logging.getLogger(__name__)


# #############################################################################
# Prompts.
# #############################################################################


def add_comments_one_shot_learning1(user: str) -> str:
    system = """
You are a proficient Python coder.
Given the Python code passed below,
every 10 lines of code add comment explaining the code.
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


def add_docstring_one_shot_learning1(user: str) -> str:
    system = """
You are a proficient Python coder.
Add a docstring to the function passed.
The first comment should be in imperative mode and fit in a single line of less than 80 characters.
To describe the parameters use the REST style, which requires each parameter to be prepended with :param
    """
    # - If the first comment is not clear enough and needs more details then you
    #   can add another comment shorter than one 3 lines.
    # - Do not change the code, but print it exactly as it is
    # - Do not specify the types of the parameters.
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret


def add_type_hints(user: str) -> str:
    system = """
You are a proficient Python coder.
Add type hints to the function passed.
    """
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret


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
You are a profecient technical writer and expert of machine learning.
I will give you in the next prompt markdown text
You will leave the markdown structure unchanged and change as little text as possible to make sure it is clear and readable
You will use multiple colors using pandoc \textcolor{COLOR}{text} to highlight important phrases
    """
    response = hopenai.get_completion(user, system=system)
    ret = hopenai.response_to_txt(response)
    ret = hopenai.remove_code_delimiters(ret)
    return ret


# #############################################################################


def apply_prompt(prompt_tag: str, txt: str) -> str:
    if prompt_tag == "format_markdown":
        pass
    elif prompt_tag == "comment":
        txt = add_comments_one_shot_learning1(txt)
    elif prompt_tag == "docstring":
        txt = add_docstring_one_shot_learning1(txt)
    elif prompt_tag == "typehints":
        txt = add_type_hints(txt)
    elif prompt_tag == "rewrite_as_tech_writer":
        txt = rewrite_as_tech_writer(txt)
    elif prompt_tag == "improve_markdown_slide":
        txt = improve_markdown_slide(txt)
    else:
        raise ValueError("Invalid prompt_tag=%s" % prompt_tag)
    return txt
