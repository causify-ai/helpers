"""
Import as:

import helpers.hstring as hstring
"""

import os
import re
import tempfile
import unicodedata
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hpython_code as hpythcode
import helpers.hsystem as hsystem


def remove_prefix(string: str, prefix: str, assert_on_error: bool = True) -> str:
    if string.startswith(prefix):
        res = string[len(prefix) :]
    else:
        res = string
        if assert_on_error:
            raise RuntimeError(
                f"string='{string}' doesn't start with prefix ='{prefix}'"
            )
    return res


def remove_suffix(string: str, suffix: str, assert_on_error: bool = True) -> str:
    if string.endswith(suffix):
        res = string[: -len(suffix)]
    else:
        res = string
        if assert_on_error:
            raise RuntimeError(
                f"string='{string}' doesn't end with suffix='{suffix}'"
            )
    return res


def to_ascii(text: str) -> str:
    """
    Convert Unicode text to ASCII by decomposing and stripping accents.

    :param text: input text with potential non-ASCII characters
    :return: ASCII-safe text (e.g., "Schölkopf" -> "Scholkopf")
    """
    if not text:
        return text
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def diff_strings(
    txt1: str,
    txt2: str,
    txt1_descr: Optional[str] = None,
    txt2_descr: Optional[str] = None,
    width: int = 130,
) -> str:
    # Write file.
    def _to_file(txt: str, txt_descr: Optional[str]) -> str:
        file_name = tempfile.NamedTemporaryFile().name
        if txt_descr is not None:
            txt = "# " + txt_descr + "\n" + txt
        hio.to_file(file_name, txt)
        return file_name

    file_name1 = _to_file(txt1, txt1_descr)
    file_name2 = _to_file(txt2, txt2_descr)
    # Get the difference between the files.
    cmd = f"sdiff --width={width} {file_name1} {file_name2}"
    _, txt = hsystem.system_to_string(
        cmd,
        # We don't care if they are different.
        abort_on_error=False,
    )
    return txt


def get_docstring_line_indices(lines: List[str]) -> List[int]:
    """
    Get indices of lines of code that are inside (doc)strings.

    Moved to hpython_code.get_docstring_line_indices.
    This is a forwarding function for backward compatibility.

    :param lines: the code lines to check
    :return: the indices of docstrings
    """
    return hpythcode.get_docstring_line_indices(lines)


def get_docstrings(lines: List[str]) -> List[List[int]]:
    """
    Get line indices grouped together by the docstring they belong to.

    Moved to hpython_code.get_docstrings.
    This is a forwarding function for backward compatibility.

    :param lines: lines from the file to process
    :return: grouped lines within docstrings
    """
    return hpythcode.get_docstrings(lines)


def get_code_block_line_indices(lines: List[str]) -> List[int]:
    """
    Get indices of lines that are inside code blocks.

    Code blocks are lines surrounded by triple backticks, e.g.,
    ```
    This line.
    ```
    Note that the backticks need to be the leftmost element of their line.

    Moved to hpython_code.get_code_block_line_indices.
    This is a forwarding function for backward compatibility.

    :param lines: the lines to check
    :return: the indices of code blocks
    """
    return hpythcode.get_code_block_line_indices(lines)


def extract_version_from_file_name(file_name: str) -> Tuple[int, int]:
    """
    Extract version number from filename_vXX.json file.

    E.g.
    - 'universe_v3.1.json' -> (3, 1)
    - 'universe_v1.json' -> (1, 0)
    - 'dataset_schema_v3.json' -> (3, 0)

    Currently only JSON file extension is supported.

    :param file_name: file to extract version part from
    :return: file version tuple in format (major, minor)
    """
    basename = os.path.basename(file_name).rstrip(".json")
    m = re.search(r"v(\d+(\.\d+)?)$", basename)
    hdbg.dassert(
        m,
        "Can't parse file '%s', correct format is e.g. 'universe_v03.json'.",
        basename,
    )
    # Groups return tuple.
    version = m.groups(1)[0].split(".")  # type: ignore[arg-type, union-attr]
    major, minor = int(version[0]), 0 if len(version) == 1 else int(version[1])
    return major, minor


def text_to_list(txt: str) -> List[str]:
    """
    Convert a string (e.g., from system_to_string) into a list of lines.
    """
    res = [line.rstrip().lstrip() for line in txt.split("\n")]
    res = [line for line in res if line != ""]
    return res
