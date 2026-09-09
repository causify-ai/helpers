"""
Import as:

import helpers.htraceback as htraceb
"""

import logging
import posixpath
import re
from typing import List, Match, Optional, Tuple, cast

import helpers.hdbg as hdbg
import helpers.hgit as hgit

_LOG = logging.getLogger(__name__)


# TODO(gp): Move some code to `hcfile.py`.

# Store elements parsed from a line of a traceback:
#   (file_name, line_num, text)
# E.g.,
#   ("test/test_lib_tasks.py",
#    27,
#    "test_get_gh_issue_title2:actual = ltasks._get_gh_issue_title(issue_id, repo)"
#    )
CfileRow = Tuple[str, int, str]

_TRACEBACK_HEADER = "Traceback (most recent call last):"

_FRAME_RE = re.compile(r'^\s*File "(.+)", line (\d+), in (\S+)\s*$')

_GH_ACTIONS_TIMESTAMP_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]+Z "
)

_TRACEBACK_STOP_MARKERS = (
    "________ Test",
    "====== slowest 3 durations",
)


def cfile_row_to_str(cfile_row: CfileRow) -> str:
    # helpers/git.py:295:def get_repo_long_name_from_client(super_module
    hdbg.dassert_isinstance(cfile_row, tuple)
    return ":".join(list(map(str, cfile_row)))


def cfile_to_str(cfile: List[CfileRow]) -> str:
    hdbg.dassert_isinstance(cfile, list)
    return "\n".join(map(cfile_row_to_str, cfile))


def _remove_github_actions_timestamps(lines: List[str]) -> List[str]:
    """
    Remove GitHub Actions timestamp prefixes from traceback lines.

    :param lines: traceback lines
    :return: lines without GitHub Actions timestamp prefixes
    """
    lines = [_GH_ACTIONS_TIMESTAMP_RE.split(line)[-1] for line in lines]
    return lines


def _parse_frame(lines: List[str], frame_idx: int) -> Tuple[CfileRow, int]:
    """
    Parse one traceback frame and its code snippet.

    :param lines: traceback lines
    :param frame_idx: index of the `File ...` line
    :return: parsed cfile row and index of the next line to inspect
    """
    match = _FRAME_RE.match(lines[frame_idx])
    hdbg.dassert(match, "Can't parse '%s'", lines[frame_idx])
    match = cast(Match[str], match)
    file_name = match.group(1)
    line_num = int(match.group(2))
    func_name = match.group(3)
    # Collect indented code lines until the next frame or unindented line.
    code_lines = []
    next_idx = frame_idx + 1
    while next_idx < len(lines):
        line = lines[next_idx]
        if _FRAME_RE.match(line):
            break
        if not line.startswith("  "):
            break
        code_lines.append(line.strip())
        next_idx += 1
    code_as_single_line = "/".join(code_lines)
    # Normalize traceback paths with POSIX semantics, since tracebacks are
    # produced on Linux and Windows `normpath` would turn `/` into `\`.
    file_name = posixpath.normpath(file_name)
    cfile_row = (file_name, line_num, func_name + ":" + code_as_single_line)
    return cfile_row, next_idx


def _parse_frames(
    lines: List[str], start_idx: int
) -> Tuple[List[CfileRow], int]:
    """
    Parse all frames in a traceback.

    :param lines: traceback lines
    :param start_idx: index of the traceback header
    :return: parsed cfile rows and the first index after the frames
    """
    cfile = []
    frame_idx = start_idx + 1
    while frame_idx < len(lines):
        match = _FRAME_RE.match(lines[frame_idx])
        if match is None:
            break
        cfile_row, frame_idx = _parse_frame(lines, frame_idx)
        cfile.append(cfile_row)
    return cfile, frame_idx


def _extend_traceback_end(lines: List[str], end_idx: int) -> int:
    """
    Extend the traceback to include a trailing error and its continuation.

    :param lines: traceback lines
    :param end_idx: index immediately after the parsed frames
    :return: exclusive end index of the traceback
    """
    # Include a trailing error message and its continuation lines. An indented
    # error line has already been consumed as part of the last frame, so this
    # only handles unindented errors such as `NameError:`.
    if end_idx < len(lines) and "Error:" in lines[end_idx]:
        end_idx += 1
        while end_idx < len(lines):
            line = lines[end_idx]
            if line.startswith(_TRACEBACK_HEADER):
                break
            if any(marker in line for marker in _TRACEBACK_STOP_MARKERS):
                break
            end_idx += 1
    return end_idx


def parse_traceback(
    txt: str, *, purify_from_client: bool = True
) -> Tuple[List[CfileRow], Optional[str]]:
    """
    Parse a string containing text including a Python traceback.

    :param txt: the text to parse
    :param purify_from_client: express the files with respect to the Git root
    :return:
    - a list of `CFILE_ROW`, e.g.,
      ```
      ("test/test_lib_tasks.py",
       27,
       "test_get_gh_issue_title2:actual = ltasks._get_gh_issue_title(issue_id, repo)")
    - a string storing the traceback, like:
      ```
      Traceback (most recent call last):
        File "/app/amp/test/test_lib_tasks.py", line 27, in test_get_gh_issue_title2
          actual = ltasks._get_gh_issue_title(issue_id, repo)
        File "/app/amp/lib_tasks.py", line 1265, in _get_gh_issue_title
          task_prefix = hgit.get_task_prefix_from_repo_short_name(repo_short_name)
        File "/app/amp/helpers/git.py", line 397, in get_task_prefix_from_repo_short_name
          if repo_short_name == "amp":
      NameError: name 'repo_short_name' is not defined
      ```
      - A `None` value means that no traceback was found.
    """
    txt += "\n"
    lines = txt.split("\n")
    lines = _remove_github_actions_timestamps(lines)
    start_idx = None
    for idx, line in enumerate(lines):
        if line.startswith(_TRACEBACK_HEADER):
            start_idx = idx
            break
    if start_idx is None:
        cfile: List[CfileRow] = []
        traceback = None
    else:
        cfile, end_idx = _parse_frames(lines, start_idx)
        end_idx = _extend_traceback_end(lines, end_idx)
        hdbg.dassert_lte(start_idx, end_idx)
        hdbg.dassert_lte(end_idx, len(lines))
        traceback = "\n".join(lines[start_idx:end_idx])
        traceback = traceback.removesuffix("\n")
    _LOG.debug("traceback=\n%s", traceback)
    _LOG.debug("cfile=\n%s", cfile_to_str(cfile))
    # Purify filenames from client so that refer to files in this client.
    if cfile and purify_from_client:
        _LOG.debug("# Purifying from client")
        cfile_tmp = []
        for cfile_row in cfile:
            file_name, line_num, text = cfile_row
            # Leave the files relative to the current dir.
            root_dir = hgit.get_client_root(super_module=False)
            mode = "return_all_results"
            file_names = hgit.find_docker_file(
                file_name, root_dir=root_dir, mode=mode
            )
            if len(file_names) == 0:
                _LOG.warning("Can't find file corresponding to '%s'", file_name)
            elif len(file_names) > 1:
                _LOG.warning(
                    "Found multiple potential files corresponding to '%s'",
                    file_name,
                )
            else:
                file_name = file_names[0]
                cfile_tmp.append((file_name, line_num, text))
        cfile = cfile_tmp
        _LOG.debug("# After purifying from client")
        _LOG.debug("cfile=\n%s", cfile_to_str(cfile))
    return cfile, traceback
