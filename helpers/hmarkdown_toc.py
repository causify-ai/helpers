"""
Import as:

import helpers.hmarkdown_toc as hmarkdo
"""

import logging
import os
import re
import tempfile
from typing import Any, List, Tuple

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hdockerized_executables as hdocexec
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def extract_yaml_frontmatter(lines: List[str]) -> Tuple[List[str], List[str]]:
    """
    Extract YAML front matter from the beginning of the file.

    YAML front matter is delimited by `---` at the beginning and end.
    Example:
    ```
    ---
    title: My Document
    date: 2024-01-01
    ---
    ```

    :param lines: The lines to be processed.
    :return: A tuple of (frontmatter_lines, remaining_lines).
    """
    _LOG.debug("lines=%s", lines)
    # Check if file starts with YAML front matter.
    if len(lines) < 3:
        # Not enough lines for front matter.
        return [], lines
    if not re.match(r"^---\s*$", lines[0]):
        # No front matter marker at the beginning.
        return [], lines
    # Find the closing --- marker.
    for i in range(1, len(lines)):
        if re.match(r"^---\s*$", lines[i]):
            # Found closing marker.
            frontmatter = lines[: i + 1]
            remaining = lines[i + 1 :]
            _LOG.debug("Found YAML front matter: %d lines", len(frontmatter))
            return frontmatter, remaining
    # No closing marker found, treat as no front matter.
    _LOG.debug("No closing YAML front matter marker found")
    return [], lines


# #############################################################################


def refresh_toc(
    lines: List[str],
    *,
    use_dockerized_markdown_toc: bool = True,
    # TODO(gp): Remove this.
    **kwargs: Any,
) -> List[str]:
    """
    Refresh the table of contents (TOC) in the given text.

    :param lines: The lines to be processed.
    :param use_dockerized_markdown_toc: if True, run markdown-toc in a
        Docker container
    :return: The lines with the updated TOC.
    """
    _LOG.debug("lines=%s", lines)
    # Check whether there is a TOC otherwise add it.
    # Add `<!-- toc -->` comment in the doc to generate the TOC after that
    # line. By default, it will generate at the top of the file.
    # This workaround is useful to generate the TOC after the heading of the doc
    # at the top and not include it in the TOC.
    if "<!-- toc -->" not in lines:
        _LOG.warning("No tags for table of content in md file: adding it")
        lines = ["<!-- toc -->"] + lines
    txt = "\n".join(lines)
    # Write file.
    curr_dir = os.getcwd()
    tmp_file_name = tempfile.NamedTemporaryFile(dir=curr_dir).name
    hio.to_file(tmp_file_name, txt)
    # Process TOC.
    cmd_opts: List[str] = []
    if use_dockerized_markdown_toc:
        # Run `markdown-toc` in a Docker container.
        use_sudo = hdocker.get_use_sudo()
        force_rebuild = False
        hdocexec.run_dockerized_markdown_toc(
            tmp_file_name,
            cmd_opts,
            use_sudo=use_sudo,
            force_rebuild=force_rebuild,
        )
    else:
        # Run `markdown-toc` installed on the host directly.
        executable = "markdown-toc"
        cmd = [executable] + cmd_opts
        cmd.append("-i " + tmp_file_name)
        #
        cmd_as_str = " ".join(cmd)
        _, output_tmp = hsystem.system_to_string(cmd_as_str, abort_on_error=True)
        _LOG.debug("output_tmp=%s", output_tmp)
    # Read file.
    txt = hio.from_file(tmp_file_name)
    # Clean up.
    os.remove(tmp_file_name)
    # Remove empty lines introduced by `markdown-toc`.
    txt = hprint.remove_lead_trail_empty_lines(txt)
    ret = txt.split("\n")
    hdbg.dassert_isinstance(ret, list)
    return ret


def remove_table_of_contents(txt: str) -> str:
    """
    Remove the table of contents from the text of a markdown file.

    The table of contents is stored between
    ```
    <!-- toc -->
    ...
    <!-- tocstop -->
    ```

    :param txt: Input markdown text
    :return: Text with table of contents removed
    """
    txt = re.sub(r"<!-- toc -->.*?<!-- tocstop -->", "", txt, flags=re.DOTALL)
    return txt
