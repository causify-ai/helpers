"""
Import as:

import helpers.hparser as hparser
"""

import argparse
import logging
import os
import re
import sys
import textwrap
from typing import Any, Dict, List, Optional

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): arg -> args


# #############################################################################
# CustomHelpFormatter
# #############################################################################

# Fixed `--help` wrap width, used instead of the terminal's actual width so
# `--help` output is stable whether run interactively, piped, or captured
# into a doc (e.g., a README built from `--help` output).
_HELP_WIDTH = 90

# Matches the "(default: ...)" annotation `_get_help_string()` appends, so
# `_format_action()` can colorize it after wrapping (see there for why).
_DEFAULT_ANNOTATION_RE = re.compile(r"\(default: [^()]*\)")


# #############################################################################
# CustomHelpFormatter
# #############################################################################


class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Format `--help` like `RawDescriptionHelpFormatter`, plus:

    - Preserve explicit newlines inside individual argument `help=` strings
      (see `_split_lines()`): `RawDescriptionHelpFormatter` only keeps raw
      formatting for the parser-level `description`/`epilog`, so a
      hand-built bullet list (e.g., via `hprint.dedent()`) in a `help=`
      string would otherwise be collapsed by `argparse` into a single
      wrapped paragraph, losing its line breaks and "-" markers.
    - Wrap to a fixed `width` (default `_HELP_WIDTH`) instead of the
      terminal's width.
    - Append "(default: ...)" to every optional argument that has a
      meaningful default, like `argparse.ArgumentDefaultsHelpFormatter`,
      but skip arguments with no default (`None`, `""`, or `required=True`)
      instead of printing a useless "(default: None)".
    - Colorize section headings, option strings, and default annotations
      when stdout is a terminal and `NO_COLOR` is unset. Colored text is
      measured/padded by its visible length so column alignment matches the
      uncolored output exactly
    """

    def __init__(
        self,
        prog: str,
        *,
        indent_increment: int = 2,
        max_help_position: int = 24,
        width: int = _HELP_WIDTH,
    ) -> None:
        super().__init__(prog, indent_increment, max_help_position, width)
        self._use_color = bool(
            sys.stdout.isatty() and not os.environ.get("NO_COLOR")
        )

    def _color(self, text: str, color: str) -> str:
        if not self._use_color:
            return text
        return hprint.color_highlight(text, color)

    @staticmethod
    def _visible_len(text: str) -> int:
        """
        Return `text`'s length ignoring injected ANSI color codes.
        """
        return len(hprint.remove_non_printable_chars(text))

    @staticmethod
    def _reflow_help_paragraphs(
        text: str,
    ) -> List[Optional[Any]]:
        """
        Group `text`'s authored lines into logical paragraphs.

        A line starting with "- " begins a new bullet paragraph; any following
        non-bullet line is folded into it as a continuation (the author may
        have hand-wrapped the bullet across several physical lines at some
        other width). A blank line, or a non-bullet line while no bullet
        paragraph is active, starts its own fresh, unmerged paragraph -- so a
        standalone fact line (e.g., "Default: ...") stays on its own line
        instead of being swallowed into whatever text preceded it.

        :return: list with one `(indent, paragraph_text)` per paragraph,
            or `None` for each blank line, in original order
        """
        paragraphs: List[Optional[Any]] = []
        current_indent = ""
        current_words: Optional[List[str]] = None
        in_bullet = False
        for raw_line in text.split("\n"):
            if raw_line.strip() == "":
                if current_words is not None:
                    paragraphs.append((current_indent, " ".join(current_words)))
                    current_words = None
                paragraphs.append(None)
                in_bullet = False
                continue
            stripped = raw_line.lstrip(" ")
            indent = raw_line[: len(raw_line) - len(stripped)]
            is_bullet = stripped.startswith("- ")
            if is_bullet or not in_bullet or current_words is None:
                if current_words is not None:
                    paragraphs.append((current_indent, " ".join(current_words)))
                current_indent = indent
                current_words = [stripped]
                in_bullet = is_bullet
            else:
                current_words.append(stripped)
        if current_words is not None:
            paragraphs.append((current_indent, " ".join(current_words)))
        return paragraphs

    def _split_lines(self, text: str, width: int) -> List[str]:
        if "\n" not in text:
            # Same as the base implementation, except `break_on_hyphens`
            # is off so identifiers like `claude-haiku-4-5-20251001`
            # aren't split at every dash.
            text = self._whitespace_matcher.sub(" ", text).strip()
            return textwrap.wrap(text, width, break_on_hyphens=False)
        # Preserve explicit newlines (e.g., a hand-built bullet list) as
        # paragraph breaks, but reflow each logical paragraph (a bullet may
        # span several authored physical lines) to `width`, so long lines
        # don't blow past the fixed help width and short ones don't get
        # spuriously re-wrapped mid-bullet.
        lines: List[str] = []
        for item in self._reflow_help_paragraphs(text):
            if item is None:
                lines.append("")
                continue
            indent, paragraph = item
            subsequent_indent = indent + (
                "  " if paragraph.startswith("- ") else ""
            )
            wrapped = textwrap.wrap(
                paragraph,
                max(width - len(indent), 1),
                initial_indent=indent,
                subsequent_indent=subsequent_indent,
                break_on_hyphens=False,
            )
            lines.extend(wrapped if wrapped else [indent + paragraph])
        return lines

    def start_section(self, heading: Optional[str]) -> None:
        if heading:
            heading = self._color(heading, "bold")
        super().start_section(heading)

    def _format_action_invocation(self, action: argparse.Action) -> str:
        text = super()._format_action_invocation(action)
        return self._color(text, "green")

    def _get_help_string(self, action: argparse.Action) -> str:
        help_ = action.help or ""
        # Don't restate it if the help text already spells it out (e.g.,
        # "... Default: 'py,ipynb,md'"). Require both the word "default"
        # and the value itself, so a value that coincidentally shows up in
        # unrelated prose (e.g., `--rule_level`'s "2=H2") doesn't
        # spuriously suppress the annotation.
        already_stated = (
            "default" in help_.lower() and str(action.default) in help_
        )
        if (
            "%(default)" not in help_
            and action.default not in (None, "", argparse.SUPPRESS)
            and not already_stated
        ):
            # Escape `%` since `_expand_help()` runs `%`-substitution on the
            # string we return. Left uncolored here on purpose: this text
            # still goes through `_split_lines()`'s width-based wrapping,
            # and injecting ANSI codes before that would inflate `len()`
            # and wrap earlier than the uncolored output does. It's
            # colorized after wrapping instead, in `_format_action()`.
            default_str = f"(default: {action.default})".replace("%", "%%")
            help_ = f"{help_} {default_str}" if help_ else default_str
        return help_

    def _colorize_default_annotation(self, line: str) -> str:
        if not self._use_color:
            return line
        return _DEFAULT_ANNOTATION_RE.sub(
            lambda m: self._color(m.group(0), "gray"), line
        )

    def _format_action(self, action: argparse.Action) -> str:
        help_position = min(self._action_max_length + 2, self._max_help_position)
        help_width = max(self._width - help_position, 11)
        action_width = help_position - self._current_indent - 2
        action_header = self._format_action_invocation(action)
        header_len = self._visible_len(action_header)
        indent_first = 0
        if not action.help:
            action_header = "%*s%s\n" % (
                self._current_indent,
                "",
                action_header,
            )
        elif header_len <= action_width:
            pad = " " * (action_width - header_len)
            action_header = "%*s%s%s  " % (
                self._current_indent,
                "",
                action_header,
                pad,
            )
        else:
            action_header = "%*s%s\n" % (
                self._current_indent,
                "",
                action_header,
            )
            indent_first = help_position
        parts = [action_header]
        if action.help and action.help.strip():
            help_text = self._expand_help(action)
            if help_text:
                help_lines = self._split_lines(help_text, help_width)
                help_lines = [
                    self._colorize_default_annotation(line)
                    for line in help_lines
                ]
                parts.append("%*s%s\n" % (indent_first, "", help_lines[0]))
                for line in help_lines[1:]:
                    parts.append("%*s%s\n" % (help_position, "", line))
        elif not action_header.endswith("\n"):
            parts.append("\n")
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))
        return self._join_parts(parts)

    # The 2 methods below duplicate small chunks of
    # `argparse.HelpFormatter.add_argument()`/`_format_action()` so that
    # column alignment is computed from each string's *visible* length
    # instead of Python's `len()`, which would otherwise count the
    # invisible ANSI codes injected by `_format_action_invocation()` and
    # misalign the help column.
    def add_argument(self, action: argparse.Action) -> None:
        if action.help is not argparse.SUPPRESS:
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            for subaction in self._iter_indented_subactions(action):
                invocations.append(get_invocation(subaction))
            invocation_length = max(self._visible_len(s) for s in invocations)
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length, action_length)
        self._add_item(self._format_action, [action])


# #############################################################################
# Verbosity
# #############################################################################


def add_bool_arg(
    parser: argparse.ArgumentParser,
    name: str,
    *,
    default_value: bool = False,
    help_: Optional[str] = None,
) -> argparse.ArgumentParser:
    """
    Add options to a parser like `--xyz` and `--no_xyz`, controlled by
    `args.xyz`.

    E.g., `add_bool_arg(parser, "run_diff_script", default_value=True)` adds
    two options:
    ```
      --run_diff_script     Run the diffing script or not
      --no_run_diff_script
    ```
    corresponding to `args.run_diff_script`, where the default behavior is to have
    that value equal to True unless one specifies `--no_run_diff_script`.
    """
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--" + name, dest=name, action="store_true", help=help_)
    group.add_argument("--no_" + name, dest=name, action="store_false")
    parser.set_defaults(**{name: default_value})
    return parser


def add_verbosity_arg(
    parser: argparse.ArgumentParser, *, log_level: str = "INFO"
) -> argparse.ArgumentParser:
    parser.add_argument(
        "-v",
        dest="log_level",
        default=log_level,
        # TRACE=5
        # DEBUG=10
        # INFO=20
        # WARNING=30
        # CRITICAL=50
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--no_report_command_line",
        action="store_true",
        help="Disable printing of executed commands",
    )
    return parser


# TODO(gp): Use this everywhere.
def parse_verbosity_args(
    args: argparse.Namespace, *args_: Any, **kwargs: Any
) -> None:
    if hasattr(args, "no_report_command_line") and args.no_report_command_line:
        report_command_line = False
    else:
        report_command_line = True
    kwargs["report_command_line"] = report_command_line
    # if args.log_level == "VERB_DEBUG":
    #    args.log_level = 5
    hdbg.init_logger(verbosity=args.log_level, *args_, **kwargs)


# #############################################################################
# Command line options for metadata output.
# #############################################################################


def add_json_output_metadata_args(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """
    Add arguments related to storing the output metadata from a script.

    This data can be read / used by other scripts to post-process a
    script results.
    """
    parser.add_argument(
        "--json_output_metadata",
        type=str,
        action="store",
        help="File storing the output metadata of this script in JSON format",
    )
    return parser


# Store the metadata about the output of a script.
OutputMetadata = Dict[str, str]


def process_json_output_metadata_args(
    args: argparse.Namespace,
    output_metadata: OutputMetadata,
) -> Optional[str]:
    """
    Save the output metadata according to the command line options.

    :return: file name with the output metadata
    """
    hdbg.dassert_isinstance(output_metadata, dict)
    if args.json_output_metadata is None:
        return None
    file_name: str = args.json_output_metadata
    _LOG.info("Saving output metadata into file '%s'", file_name)
    if not file_name.endswith(".json"):
        _LOG.warning(
            "The output metadata file '%s' doesn't end in .json: adding it",
            file_name,
        )
        file_name += ".json"
    hio.to_json(file_name, output_metadata)
    _LOG.info("Saved output metadata into file '%s'", file_name)
    return file_name


def read_output_metadata(output_metadata_file: str) -> OutputMetadata:
    """
    Read the output metadata.
    """
    output_metadata: OutputMetadata = hio.from_json(output_metadata_file)
    return output_metadata


def str_to_bool(value: str) -> bool:
    """
    Convert string representing true or false to the corresponding bool.
    """
    if value.lower() == "true":
        ret = True
    elif value.lower() == "false":
        ret = False
    else:
        raise argparse.ArgumentTypeError(
            f"Invalid boolean value {value}. Use 'true' or 'false'."
        )
    return ret
