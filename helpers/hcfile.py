import logging
import re
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hio as hio

_LOG = logging.getLogger(__name__)


def parse_cfile(cfile: str) -> List[Tuple[str, str, str]]:
    """
    Read and parse a cfile.

    :param cfile: path to the cfile
    :return: list of tuples, each containing a line number and a transform, e.g.,
        [(file_name, line_number, transform), ...]
    """
    # Read the cfile.
    cfile_lines = hio.from_file(cfile)
    cfile_lines = cfile_lines.split("\n")
    #
    ret = []
    # Parse the cfile.
    for line in cfile_lines:
        _LOG.debug("line=%s", line)
        hdbg.dassert_isinstance(line, str)
        # Parse the lines of the cfile, like
        # ```
        # dev_scripts_helpers/llms/llm_prompts.py:106: in public function `test`:D404: ...
        # dev_scripts_helpers/llms/llm_prompts.py:110: error: Need type annotation for ...
        # dev_scripts_helpers/llms/dockerized_llm_review.py:63:33: F821 undefined name '_extract_bullet_points' [flake8]
        # ```
        # extracting the file name, line number, and transform.
        regex = r"^([^:]+):(\d+):(.*)$"
        match = re.match(regex, line)
        if match is None:
            _LOG.debug("Failed to parse line '%s'", line)
            continue
        # Extract the file name, line number, and transform.
        file_name = match.group(1)
        line_number = match.group(2)
        transform = match.group(3)
        # Add values to the list.
        ret.append((file_name, line_number, transform))
    return ret


# #############################################################################


def inject_todos_from_cfile(
    cfile_txt: str, todo_user: str, comment_prefix: str
) -> None:
    """
    Inject the TODOs from a cfile in the corresponding files.

    Given a cfile with the following content:
    the function will inject the TODO in the corresponding file and line

    :param cfile_txt: The content of the cfile.
    :param todo_user: The user to use in the TODO.
    :param comment_prefix: The prefix to use for the comment (e.g., "#")
    """
    # For each file, store
    #   - the current file content
    #   - the offset (i.e., how many lines we inserted in the file so far, so
    #     we can inject the TODO at the correct line number)
    #   - the index of the last line modified to make sure the TODOs are for
    #     increasing line numbers.
    file_content = {}
    for todo_line in cfile_txt.split("\n"):
        _LOG.debug("\n%s", hprint.frame("todo line='%s'" % todo_line))
        if todo_line.strip() == "":
            continue
        # dev_scripts_helpers/github/dockerized_sync_gh_repo_settings.py:101: The logic for extracting required status checks and pull request reviews is repeated. Consider creating a helper function to handle this extraction to reduce redundancy.
        m = re.match(r"^\s*(\S+):(\d+):\s*(.*)$", todo_line)
        if not m:
            _LOG.warning("Can't parse line='%s': skipping", todo_line)
            continue
        file_name, todo_line_number, todo = m.groups()
        todo_line_number = int(todo_line_number)
        _LOG.debug(hprint.to_str("file_name todo_line_number todo"))
        # Update the state if needed.
        if file_name not in file_content:
            _LOG.debug("Reading %s", file_name)
            hdbg.dassert_path_exists(file_name)
            txt = hio.from_file(file_name).split("\n")
            offset = 0
            last_line_modified = 0
            file_content[file_name] = (txt, offset, last_line_modified)
        # Extract the info for the file to process.
        txt, offset, last_line_modified = file_content[file_name]
        _LOG.debug(hprint.to_str("offset last_line_modified"))
        hdbg.dassert_lt(
            last_line_modified,
            todo_line_number,
            "The TODOs don't look like they are increasing line numbers: "
            "TODO at line %d is before the last line modified %d",
            todo_line_number,
            last_line_modified,
        )
        # We subtract 1 from the line number since TODOs count from 1, while
        # Python arrays count from 0.
        act_line_number = todo_line_number - 1 + offset
        hdbg.dassert_lte(0, act_line_number)
        hdbg.dassert_lt(act_line_number, len(txt))
        insert_line = txt[act_line_number]
        _LOG.debug(hprint.to_str("act_line_number insert_line"))
        # Extract how many spaces there are at place where the line to insert
        # the TODO.
        m = re.match(r"^(\s*)\S", insert_line)
        hdbg.dassert(m, "Can't parse insert_line='%s'", insert_line)
        spaces = len(m.group(1)) * " "  # type: ignore[union-attr]
        # Build the new line to insert.
        new_line = spaces + f"{comment_prefix} TODO({todo_user}): {todo}"
        _LOG.debug(hprint.to_str("new_line"))
        # Insert the new line in txt at the correct position.
        txt = txt[:act_line_number] + [new_line] + txt[act_line_number:]
        # Update the state.
        offset += 1
        file_content[file_name] = (txt, offset, todo_line_number)
    # Write updated files back.
    for file_name, (txt, offset, last_line_modified) in file_content.items():
        _ = last_line_modified
        _LOG.info("Writing %d lines in %s", offset, file_name)
        txt = "\n".join(txt)
        hio.to_file(file_name, txt)
