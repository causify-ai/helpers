import logging
import re
from typing import Any, Dict, List, Optional

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


def remove_latex_formatting(latex_string: str) -> str:
    """
    Remove LaTeX formatting such as \textcolor{color}{content} and retains
    only the content.
    """
    cleaned_string = re.sub(r'\\textcolor\{[^}]*\}\{([^}]*)\}', r'\1',
                            latex_string)
    return cleaned_string


def remove_end_of_line_periods(txt: str) -> str:
    """
    Remove periods at the end of each line in the given text.

    :param txt: The input text to process
    :return: The text with end-of-line periods removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line.rstrip(".") for line in txt.split("\n")]
    txt_out = "\n".join(txt_out)
    return txt_out


def remove_empty_lines(txt: str) -> str:
    """
    Remove empty lines from the given text.

    :param txt: The input text to process
    :return: The text with empty lines removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line for line in txt.split("\n") if line != ""]
    txt_out = "\n".join(txt_out)
    return txt_out