#!/usr/bin/env python

"""
See instructions at docs/tools/documentation_toolchain/all.notes_toolchain.how_to_guide.md
"""


import argparse
import logging
import os
import re
import tempfile
from typing import Any, List, Optional

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################


def _preprocess(txt: str) -> str:
    """
    Preprocess the given text before applying `prettier`.

    E.g.,
    - removes specific artifacts
    - formats math equations
    - formats bullet points
    - formats frames

    :param txt: The text to be processed.
    :return: The preprocessed text.
    """
    _LOG.debug("txt=%s", txt)
    # 1) Remove some artifacts when copying from Google Docs.
    # TODO(gp): Extract this into remove_google_docs_artifacts() since it is
    # used in other places.
    txt = re.sub(r"’", "'", txt)
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
    txt_new_as_str = "\n".join(txt_new)
    # 5) Replace multiple empty lines with one, to avoid `prettier` to start
    #    using `*` instead of `-`.
    txt_new_as_str = re.sub(r"\n\s*\n", "\n\n", txt_new_as_str)
    #
    _LOG.debug("txt_new_as_str=%s", txt_new_as_str)
    return txt_new_as_str


# TODO(gp): Rename to `postprocess_after_prettier`.
def _postprocess(txt: str, in_file_name: str) -> str:
    """
    Post-process the given text by applying various transformations.

    :param txt: The text to be processed.
    :param in_file_name: The name of the input file.
    :return: The post-processed text.
    """
    _LOG.debug("txt=%s", txt)
    # Remove empty lines before ```.
    txt = re.sub(r"^\s*\n(\s*```)$", r"\1", txt, count=0, flags=re.MULTILINE)
    # Remove empty lines before higher level bullets, but not chapters.
    txt = re.sub(r"^\s*\n(\s+-\s+.*)$", r"\1", txt, count=0, flags=re.MULTILINE)
    # True if one is in inside a ``` .... ``` block.
    in_triple_tick_block: bool = False
    txt_new: List[str] = []
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
        txt_new.append(line)
    if in_triple_tick_block:
        print(f"{in_file_name}:{1}: A ``` block was not ending")
    txt_new_as_str = "\n".join(txt_new)
    return txt_new_as_str


def _frame_chapters(txt: str, *, max_lev: int = 4) -> str:
    """
    Add the frame around each chapter.
    """
    txt_new: List[str] = []
    # _LOG.debug("txt=%s", txt)
    for i, line in enumerate(txt.split("\n")):
        _LOG.debug("line=%d:%s", i, line)
        m = re.match(r"^(\#+) ", line)
        txt_processed = False
        if m:
            comment = m.group(1)
            lev = len(comment)
            _LOG.debug("  -> lev=%s", lev)
            if lev < max_lev:
                sep = comment + " " + "#" * (80 - 1 - len(comment))
                txt_new.append(sep)
                txt_new.append(line)
                txt_new.append(sep)
                txt_processed = True
            else:
                _LOG.debug(
                    "  -> Skip formatting the chapter frame: lev=%d, max_lev=%d",
                    lev,
                    max_lev,
                )
        if not txt_processed:
            txt_new.append(line)
    txt_new_as_str = "\n".join(txt_new).rstrip("\n")
    return txt_new_as_str


# TODO(gp): Should go in `hmarkdown.py`.
def _refresh_toc(
    txt: str,
    *,
    use_dockerized_markdown_toc: bool = True,
    # TODO(gp): Remove this.
    **kwargs: Any,
) -> str:
    """
    Refresh the table of contents (TOC) in the given text.

    :param txt: The text to be processed.
    :param use_dockerized_markdown_toc: if True, run markdown-toc in a
        Docker container
    :return: The text with the updated TOC.
    """
    _LOG.debug("txt=%s", txt)
    # Check whether there is a TOC otherwise add it.
    txt_as_arr = txt.split("\n")
    # Add `<!-- toc -->` comment in the doc to generate the TOC after that
    # line. By default, it will generate at the top of the file.
    # This workaround is useful to generate the TOC after the heading of the doc
    # at the top and not include it in the TOC.
    if "<!-- toc -->" not in txt_as_arr:
        _LOG.warning("No tags for table of content in md file: adding it")
        txt = "<!-- toc -->\n" + txt
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
        hdocker.run_dockerized_markdown_toc(
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
    return txt  # type: ignore


def _improve_header_and_slide_titles(txt: str) -> str:
    """
    Improve the header and slide titles.

    - Headers start with one or more `#`s.
    - Slide titles start with one `*`
    - The title is transformed to title case as below:
        - ML theory -> ML Theory
        - A map of machine learning -> A Map of Machine Learning
    """
    txt_new: List[str] = []
    for i, line in enumerate(txt.split("\n")):
        # Parse header (starting with `#`) and slide title (starting with `*`).
        m = re.match(r"^(\#+|\*) (.*)$", line)
        if m:
            # Parse the title.
            title = m.group(2)
            # Transform to title case, leaving words that are all capitalized
            # and conjunctions as is.
            non_cap_words = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for',
                'in', 'of', 'on', 'or', 'the', 'to', 'vs', 'with'}
            # Split into words
            words = title.split()
            # Process each word.
            for i, word in enumerate(words):
                if i == 0 and not word.isupper():
                    # Capitalize the first word.
                    words[i] = word.title()
                elif word.isupper():
                    # Skip words that are all caps (e.g. ML, API).
                    continue
                elif word.lower() in non_cap_words:
                    # Don't capitalize conjunctions and other minor words.
                    words[i] = word.lower()
                else:
                    # Capitalize other words.
                    words[i] = word.title()
                    
            title = ' '.join(words)
            # Reconstruct the line.
            line = m.group(1) + " " + title
            txt_new.append(line)
        else:
            txt_new.append(line)
    txt_new_as_str = "\n".join(txt_new)
    return txt_new_as_str


# #############################################################################
# Perform all actions.
# #############################################################################


def _to_execute_action(action: str, actions: Optional[List[str]] = None) -> bool:
    to_execute = actions is None or action in actions
    if not to_execute:
        _LOG.debug("Skipping %s", action)
    return to_execute


# TODO(gp): -> _perform_actions()
def _process(
    txt: str,
    in_file_name: str,
    *,
    actions: Optional[List[str]] = None,
    **kwargs: Any,
) -> str:
    """
    Process the given text by applying a series of actions.

    :param txt: The text to be processed.
    :param in_file_name: The name of the input file.
    :param actions: A list of actions to be performed on the text. If
        None, all default actions are performed.
    :param kwargs: Additional keyword arguments to be passed to the
        actions.
    :return: The processed text.
    """
    # Get the file type.
    is_md_file = in_file_name.endswith(".md")
    extension = os.path.splitext(in_file_name)[1]
    # Remove the . from the extenstion (e.g., ".txt").
    hdbg.dassert(extension.startswith("."), "Invalid extension='%s'", extension)
    extension = extension[1:]
    # Pre-process text.
    action = "preprocess"
    if _to_execute_action(action, actions):
        txt = _preprocess(txt)
    # Prettify.
    action = "prettier"
    if _to_execute_action(action, actions):
        txt = hdocker.prettier_on_str(txt, file_type=extension, **kwargs)
    # Post-process text.
    action = "postprocess"
    if _to_execute_action(action, actions):
        txt = _postprocess(txt, in_file_name)
    # Frame chapters.
    action = "frame_chapters"
    if _to_execute_action(action, actions):
        # For markdown files, we don't use the frame since it's not rendered
        # correctly.
        if not is_md_file:
            txt = _frame_chapters(txt)
    # Improve header and slide titles.
    action = "improve_header_and_slide_titles"
    if _to_execute_action(action, actions):
        txt = _improve_header_and_slide_titles(txt)
    # Refresh table of content.
    action = "refresh_toc"
    if _to_execute_action(action, actions):
        if is_md_file:
            txt = _refresh_toc(txt, **kwargs)
    return txt


# #############################################################################

_VALID_ACTIONS = [
    # _preprocess(): preprocess the given text before applying `prettier`.
    "preprocess",
    # _prettier(): prettify the given text with `prettier` for both latex and
    # markdown.
    "prettier",
    # _postprocess(): post-process the given text.
    "postprocess",
    # _frame_chapters(): frame the chapters.
    "frame_chapters",
    "improve_header_and_slide_titles",
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
        help="The maximum line width for the formatted text. If None, 80 is used"
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
    txt = hparser.read_file(in_file_name)
    txt = "\n".join(txt)
    _LOG.debug("in_file_name=%s", in_file_name)
    # Process.
    out_txt = _process(
        txt,
        in_file_name,
        actions=args.action,
        print_width=args.print_width,
        use_dockerized_prettier=args.use_dockerized_prettier,
        use_dockerized_markdown_toc=args.use_dockerized_markdown_toc,
    )
    # Write output.
    hparser.write_file(out_txt, out_file_name)


if __name__ == "__main__":
    _main(_parser())
