"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import pprint
import re
from typing import Dict, List, Tuple

import helpers.hdbg as hdbg
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


def replace_fenced_blocks_with_tags(
    lines: List[str],
) -> Tuple[List[str], Dict[str, str]]:
    """
    Replace fenced blocks with a tag and return the mapping from tags to the
    fenced block text.

    E.g.,
        ````
        hello
        world
        ```python
        foo
        ```
        bye
        ````
    is replaced with:
        ```
        hello
        world
        <fenced_block1>
        bye
        ```

    :param lines: list of lines to process
    :return: tuple containing:
        - list of lines with the fenced blocks replaced by tags
        - mapping from tags to the fenced block text
    """
    hdbg.dassert_isinstance(lines, list)
    result = []
    # True if we are inside a fenced block.
    in_fenced_block = False
    # Count the number of fenced blocks found.
    fenced_block_count = 0
    # Store the mapping between the block number and the fence type.
    fence_map = {}
    # Store the text of the fenced block.
    fence_depth = 0
    fence_text = []
    for i, line in enumerate(lines):
        _LOG.debug("%d:line='%s'", i, line)
        _LOG.debug(
            "  "
            + hprint.to_str("fenced_block_count in_fenced_block fence_depth")
        )
        # Look for the start of a fenced block.
        fence_match = re.match(r"^\s*(`{3,})", line)
        if fence_match:
            _LOG.debug("  -> fence_match")
            curr_fence_depth = len(fence_match.group(0))
            if not in_fenced_block:
                # Start of a fenced block.
                _LOG.debug("  -> start of fenced block")
                in_fenced_block = True
                fence_depth = curr_fence_depth
                fenced_block_count += 1
                fence_text.append(line)
            else:
                # We are already in a fenced block.
                fence_text.append(line)
                if curr_fence_depth == fence_depth:
                    # End of block found.
                    _LOG.debug("  -> end of fenced block")
                    in_fenced_block = False
                    # Replace nested code block markers with tag.
                    result.append(f"<fenced_block{fenced_block_count}>")
                    fence_map[str(fenced_block_count)] = "\n".join(fence_text)
                    _LOG.debug("  -> added to fence_map")
                    # Reset state.
                    fence_depth = 0
                    fence_text = []
        else:
            if in_fenced_block:
                _LOG.debug("  -> in_fenced_block")
                fence_text.append(line)
            else:
                result.append(line)
    return result, fence_map


def replace_tags_with_fenced_blocks(
    lines: List[str], fence_map: Dict[str, str]
) -> List[str]:
    """
    Replace tags with fenced blocks.

    :param lines: list of lines to process
    :param fence_map: mapping from tags to fenced block text
    :return: list of lines with tags replaced by fenced blocks
    """
    hdbg.dassert_isinstance(lines, list)
    hdbg.dassert_isinstance(fence_map, dict)
    result = []
    for line in lines:
        if line.startswith("<fenced_block"):
            # Replace the tag with the fenced block.
            tag = line.split("<fenced_block")[1].split(">")[0]
            hdbg.dassert_in(tag, fence_map, "Found unmatched tag %s", tag)
            result.append(fence_map[tag])
            del fence_map[tag]
        else:
            result.append(line)
    hdbg.dassert_eq(
        len(fence_map),
        0,
        "Found %s unmatched tags:\n%s",
        len(fence_map),
        pprint.pformat(fence_map),
    )
    return result
