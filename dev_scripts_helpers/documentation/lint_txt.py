#!/usr/bin/env python

"""
See instructions at
docs/tools/documentation_toolchain/all.notes_toolchain.how_to_guide.md.
"""

import argparse
import logging
import os
import re
import tempfile
from typing import Any, List, Optional

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hdockerized_executables as hdocexec
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _preprocess_txt(lines: List[str]) -> List[str]:
    """
    Preprocess the given text before applying `prettier`.

    E.g.,
    - Handle stars `*` from txt files
    - Remove various artifacts (e.g., from Google Docs)
    - Format math equations
    - Format bullet points
    - Format frames

    :param lines: The lines to be processed.
    :return: The preprocessed lines.
    """
    _LOG.debug("lines=%s", lines)
    # 1) Remove some artifacts when copying from Google Docs.
    # TODO(gp): Extract this into remove_google_docs_artifacts() since it is
    # used in other places.
    txt = "\n".join(lines)
    txt = re.sub(r"“", '"', txt)
    txt = re.sub(r"”", '"', txt)
    txt = re.sub(r"…", "...", txt)
    txt_new: List[str] = []
    for line in txt.split("\n"):
        # 2) Skip frames for all the type formats.
        if re.match(r"#+ [#\/\-\=]{6,}$", line):
            continue
        # 3) Transforms * and ** bullets to - STAR and - SSTAR (temporary markers).
        line = re.sub(r"^\s*\*\s+", "- STAR", line)
        line = re.sub(r"^\s*\*\*\s+", "- SSTAR", line)
        # 4) Format math equations.
        #   $$E_{in} = \frac{1}{N} \sum_i e(h(\vx_i), y_i)$$
        # into:
        #   $$E_{in}(\vw) = \frac{1}{N} \sum_i \big(
        #   -y_i \log(\Pr(h(\vx) = 1|\vx)) - (1 - y_i) \log(1 - \Pr(h(\vx)=1|\vx))
        #   \big)$$
        # $$
        if re.search(r"^\s*\$\$\s*$", line):
            txt_new.append(line)
            continue
        # $$ ... $$
        m = re.search(r"^(\s*)(\$\$)(.+)(\$\$)\s*$", line)
        if m:
            for i in range(3):
                txt_new.append(m.group(1) + m.group(2 + i))
            continue
        # ... $$
        m = re.search(r"^(\s*)(\$\$)(.+)$", line)
        if m:
            for i in range(2):
                txt_new.append(m.group(1) + m.group(2 + i))
            continue
        # $$ ...
        m = re.search(r"^(\s*)(.*)(\$\$)$", line)
        if m:
            for i in range(2):
                txt_new.append(m.group(1) + m.group(2 + i))
            continue
        txt_new.append(line)
    # 5) Replace multiple empty lines with one, to avoid `prettier` to start
    #    using `*` instead of `-`.
    txt_new_as_str = "\n".join(txt_new)
    txt_new_as_str = re.sub(r"\n\s*\n", "\n\n", txt_new_as_str)
    #
    _LOG.debug("txt_new_as_str=%s", txt_new_as_str)
    ret = txt_new_as_str.split("\n")
    hdbg.dassert_isinstance(ret, list)
    return ret


def _postprocess_txt(lines: List[str], in_file_name: str) -> List[str]:
    """
    Post-process the given text by applying various transformations.

    :param lines: The lines to be processed.
    :param in_file_name: The name of the input file.
    :return: The post-processed lines.
    """
    _LOG.debug("lines=%s", lines)
    txt = "\n".join(lines)
    # Remove empty lines before ```.
    txt = re.sub(r"^\s*\n(\s*```)$", r"\1", txt, count=0, flags=re.MULTILINE)
    # Remove empty lines before higher level bullets, but not chapters.
    txt = re.sub(r"^\s*\n(\s+-\s+.*)$", r"\1", txt, count=0, flags=re.MULTILINE)
    # True if one is in inside a ``` .... ``` block.
    in_triple_tick_block: bool = False
    lines_new: List[str] = []
    for i, line in enumerate(txt.split("\n")):
        # Undo the transformation `* -> STAR`.
        line = re.sub(r"^\-(\s*)STAR", r"*\1", line, count=0)
        line = re.sub(r"^\-(\s*)SSTAR", r"**\1", line, count=0)
        # Remove empty lines.
        line = re.sub(
            r"^\s*\n(\s*\$\$)", r"\1", line, count=0, flags=re.MULTILINE
        )
        # Handle ``` block.
        m = re.match(r"^\s*```(.*)\s*$", line)
        if m:
            in_triple_tick_block = not in_triple_tick_block
            if in_triple_tick_block:
                tag = m.group(1)
                if not tag:
                    print(f"{in_file_name}:{i + 1}: Missing syntax tag in ```")
        if not in_triple_tick_block:
            # Upper case for `- hello`.
            m = re.match(r"(\s*-\s+)(\S)(.*)", line)
            if m:
                line = m.group(1) + m.group(2).upper() + m.group(3)
            # Upper case for `\d) hello`.
            m = re.match(r"(\s*\d+[\)\.]\s+)(\S)(.*)", line)
            if m:
                line = m.group(1) + m.group(2).upper() + m.group(3)
        #
        lines_new.append(line)
    if in_triple_tick_block:
        print(f"{in_file_name}:{1}: A ``` block was not ending")
    hdbg.dassert_isinstance(lines_new, list)
    return lines_new


# TODO(gp): Should go in `hmarkdown_toc.py`.
def _refresh_toc(
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


# #############################################################################
# Perform all actions.
# #############################################################################


def _to_execute_action(action: str, actions: Optional[List[str]] = None) -> bool:
    to_execute = actions is None or action in actions
    if not to_execute:
        _LOG.debug("Skipping %s", action)
    return to_execute


def _perform_actions(
    lines: List[str],
    in_file_name: str,
    *,
    actions: Optional[List[str]] = None,
    **kwargs: Any,
) -> List[str]:
    """
    Process the given text by applying a series of actions.

    :param lines: The lines to be processed.
    :param in_file_name: The name of the input file.
    :param actions: A list of actions to be performed on the text. If
        None, all default actions are performed.
    :param kwargs: Additional keyword arguments to be passed to the
        actions.
    :return: The processed lines.
    """
    hdbg.dassert_isinstance(lines, list)
    # Get the file type.
    is_md_file = in_file_name.endswith(".md")
    extension = os.path.splitext(in_file_name)[1]
    # Remove the . from the extenstion (e.g., ".txt").
    hdbg.dassert(extension.startswith("."), "Invalid extension='%s'", extension)
    extension = extension[1:]
    # Pre-process text.
    action = "preprocess"
    if _to_execute_action(action, actions):
        lines = _preprocess_txt(lines)
    # Prettify.
    action = "prettier"
    if _to_execute_action(action, actions):
        txt = "\n".join(lines)
        txt = hdocexec.prettier_on_str(txt, file_type=extension, **kwargs)
        lines = txt.split("\n")
    # Post-process text.
    action = "postprocess"
    if _to_execute_action(action, actions):
        lines = _postprocess_txt(lines, in_file_name)
    # Frame chapters.
    action = "frame_chapters"
    if _to_execute_action(action, actions):
        # For markdown files, we don't use the frame since it's not rendered
        # correctly.
        if not is_md_file:
            lines = hmarkdo.frame_chapters(lines)
    # Improve header and slide titles.
    action = "capitalize_header"
    if _to_execute_action(action, actions):
        lines = hmarkdo.capitalize_header(lines)
    # Refresh table of content.
    action = "refresh_toc"
    if _to_execute_action(action, actions):
        if is_md_file:
            lines = _refresh_toc(lines, **kwargs)
    return lines


# #############################################################################

_VALID_ACTIONS = [
    # _preprocess(): preprocess the given text before applying `prettier`.
    "preprocess",
    # _prettier(): prettify the given text with `prettier` for both latex and
    # markdown.
    "prettier",
    # _postprocess(): post-process the given text.
    "postprocess",
    #
    "frame_chapters",
    "capitalize_header",
    # _refresh_toc(): refresh the table of contents.
    "refresh_toc",
]


_DEFAULT_ACTIONS = _VALID_ACTIONS[:]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hparser.add_input_output_args(parser)
    parser.add_argument(
        "--type",
        action="store",
        type=str,
        default="",
        help="The type of the input file, e.g., `md`, `tex`, `txt`",
    )
    parser.add_argument(
        "-w",
        "--print-width",
        action="store",
        type=int,
        default=80,
        help="The maximum line width for the formatted text. If None, 80 is used",
    )
    parser.add_argument(
        "--use_dockerized_prettier",
        action="store_true",
    )
    parser.add_argument(
        "--use_dockerized_markdown_toc",
        action="store_true",
    )
    hparser.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_dockerized_script_arg(parser)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hparser.init_logger_for_input_output_transform(args)
    #
    in_file_name, out_file_name = hparser.parse_input_output_args(
        args, clear_screen=True
    )
    # If the input is stdin, then user needs to specify the type.
    if in_file_name == "-":
        hdbg.dassert_ne(args.type, "")
    # Read input.
    lines = hparser.read_file(in_file_name)
    _LOG.debug("in_file_name=%s", in_file_name)
    # Process.
    out_lines = _perform_actions(
        lines,
        in_file_name,
        actions=args.action,
        print_width=args.print_width,
        use_dockerized_prettier=args.use_dockerized_prettier,
        use_dockerized_markdown_toc=args.use_dockerized_markdown_toc,
    )
    # Write output.
    hparser.write_file(out_lines, out_file_name)


if __name__ == "__main__":
    _main(_parser())
