"""
Import as:

import helpers.test.test_hparser as httehpar
"""

import argparse
from typing import Any, Dict, List

import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# _ForceColorFormatter
# #############################################################################


class _ForceColorFormatter(hparser.CustomHelpFormatter):
    """
    `CustomHelpFormatter` with colorization forced on.

    Used instead of relying on `sys.stdout.isatty()`, which is `False`
    (and not controllable) under pytest's captured output.
    """

    def __init__(self, prog: str, **kwargs: Any) -> None:
        super().__init__(prog, **kwargs)
        self._use_color = True


# #############################################################################
# _ForceNoColorFormatter
# #############################################################################


class _ForceNoColorFormatter(hparser.CustomHelpFormatter):
    """
    `CustomHelpFormatter` with colorization forced off.
    """

    def __init__(self, prog: str, **kwargs: Any) -> None:
        super().__init__(prog, **kwargs)
        self._use_color = False


# #############################################################################
# Test_CustomHelpFormatter_split_lines
# #############################################################################


class Test_CustomHelpFormatter_split_lines(hunitest.TestCase):
    """
    Test `hparser.CustomHelpFormatter._split_lines()`.
    """

    def helper(self, text: str, width: int, expected: List[str]) -> None:
        """
        Check `_split_lines()`'s output for `text` at `width`.

        :param text: `help=`-style text to wrap
        :param width: wrap width to pass to `_split_lines()`
        :param expected: expected list of output lines
        """
        # Prepare inputs.
        formatter = hparser.CustomHelpFormatter("prog")
        # Run test.
        actual = formatter._split_lines(text, width)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that a bullet hand-wrapped across several physical lines is
        reflowed to `width` instead of double-wrapping into orphaned
        words.
        """
        # Prepare inputs.
        text = (
            "Execution mode:\n"
            "- 'one_shot_with_cc' applies all rules in a single Claude Code\n"
            "  invocation, shelling out to the `cc` wrapper\n"
            "- 'session' applies incrementally"
        )
        # Prepare outputs.
        expected = [
            "Execution mode:",
            "- 'one_shot_with_cc' applies all rules",
            "  in a single Claude Code invocation,",
            "  shelling out to the `cc` wrapper",
            "- 'session' applies incrementally",
        ]
        # Run test.
        # TODO(ai_gp): Assign width=40 and pass width in all tests.
        self.helper(text, 40, expected)

    def test2(self) -> None:
        """
        Test that non-bullet lines that already fit `width` are kept on
        their own line instead of being merged with neighboring lines.
        """
        # Prepare inputs.
        text = (
            "Comma-separated list of file extensions to process (e.g., "
            "'py,ipynb,md,txt')\n"
            "  Available: py (Python)\n"
            "  Default: 'py,ipynb,md'"
        )
        # Prepare outputs.
        expected = [
            "Comma-separated list of file extensions to process (e.g.,",
            "'py,ipynb,md,txt')",
            "  Available: py (Python)",
            "  Default: 'py,ipynb,md'",
        ]
        # Run test.
        self.helper(text, 66, expected)

    def test3(self) -> None:
        """
        Test that a single-line (no embedded newline) help string doesn't
        get split at every hyphen (e.g., inside a model name).
        """
        # Prepare inputs.
        text = (
            "Model name to use using cc conventions (default: "
            "claude-haiku-4-5-20251001)"
        )
        # Prepare outputs.
        expected = [
            "Model name to use using cc conventions",
            "(default: claude-haiku-4-5-20251001)",
        ]
        # Run test.
        self.helper(text, 40, expected)

    def test4(self) -> None:
        """
        Test that a blank line between two paragraphs round-trips as an
        empty output line.
        """
        # Prepare inputs.
        text = "Para one\n\nPara two"
        # Prepare outputs.
        expected = ["Para one", "", "Para two"]
        # Run test.
        self.helper(text, 40, expected)


# #############################################################################
# Test_CustomHelpFormatter_reflow_help_paragraphs
# #############################################################################


class Test_CustomHelpFormatter_reflow_help_paragraphs(hunitest.TestCase):
    """
    Test `hparser.CustomHelpFormatter._reflow_help_paragraphs()`.
    """

    def test1(self) -> None:
        """
        Test that non-bullet lines following a "- " bullet are folded
        into it as continuations of the same logical paragraph.
        """
        # Prepare inputs.
        text = (
            "- 'a' bullet one line one\n"
            "  continuation of bullet one\n"
            "  more continuation\n"
            "- 'b' bullet two"
        )
        # Prepare outputs.
        expected = [
            (
                "",
                "- 'a' bullet one line one continuation of bullet one "
                "more continuation",
            ),
            ("", "- 'b' bullet two"),
        ]
        # Run test.
        actual = hparser.CustomHelpFormatter._reflow_help_paragraphs(text)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that consecutive non-bullet lines each become their own
        paragraph instead of being merged into one another.
        """
        # Prepare inputs.
        text = "Comma-separated list\n  Available: py\n  Default: 'py'"
        # Prepare outputs.
        expected = [
            ("", "Comma-separated list"),
            ("  ", "Available: py"),
            ("  ", "Default: 'py'"),
        ]
        # Run test.
        actual = hparser.CustomHelpFormatter._reflow_help_paragraphs(text)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that a blank line ends the current paragraph (emitted as
        `None`) and that a bullet after it starts a fresh paragraph.
        """
        # Prepare inputs.
        text = "- 'a' bullet\n\n- 'b' bullet"
        # Prepare outputs.
        expected = [
            ("", "- 'a' bullet"),
            None,
            ("", "- 'b' bullet"),
        ]
        # Run test.
        actual = hparser.CustomHelpFormatter._reflow_help_paragraphs(text)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_CustomHelpFormatter_get_help_string
# #############################################################################


class Test_CustomHelpFormatter_get_help_string(hunitest.TestCase):
    """
    Test `hparser.CustomHelpFormatter._get_help_string()`.
    """

    def helper(self, add_argument_kwargs: Dict[str, Any], expected: str) -> None:
        """
        Build one `--x` argparse `Action` and check its formatted help.

        :param add_argument_kwargs: kwargs forwarded to `add_argument()`
        :param expected: expected return value of `_get_help_string()`
        """
        # Prepare inputs.
        formatter = hparser.CustomHelpFormatter("prog")
        parser = argparse.ArgumentParser()
        action = parser.add_argument("--x", **add_argument_kwargs)
        # Run test.
        actual = formatter._get_help_string(action)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that a meaningful default is appended as "(default: ...)".
        """
        # Prepare inputs.
        kwargs = {
            "type": int,
            "default": 1500,
            "help": "Token budget per merged rule chunk",
        }
        # Prepare outputs.
        expected = "Token budget per merged rule chunk (default: 1500)"
        # Run test.
        self.helper(kwargs, expected)

    def test2(self) -> None:
        """
        Test that a `required=True` option (default `None`) doesn't get a
        useless "(default: None)" annotation.
        """
        # Prepare inputs.
        kwargs = {
            "required": True,
            "choices": ["a", "b"],
            "help": "Execution mode",
        }
        # Prepare outputs.
        expected = "Execution mode"
        # Run test.
        self.helper(kwargs, expected)

    def test3(self) -> None:
        """
        Test that the `default=""` "unset" sentinel doesn't get a
        "(default: )" annotation.
        """
        # Prepare inputs.
        kwargs = {"default": "", "help": "Claude Code skill topic"}
        # Prepare outputs.
        expected = "Claude Code skill topic"
        # Run test.
        self.helper(kwargs, expected)

    def test4(self) -> None:
        """
        Test that the annotation is suppressed when the help text already
        states the default value next to the word "default".
        """
        # Prepare inputs.
        kwargs = {
            "default": "py,ipynb,md",
            "help": "Comma-separated list. Default: 'py,ipynb,md'",
        }
        # Prepare outputs.
        expected = "Comma-separated list. Default: 'py,ipynb,md'"
        # Run test.
        self.helper(kwargs, expected)

    def test5(self) -> None:
        """
        Test that a default value coincidentally appearing in unrelated
        prose (without the word "default") does not suppress the
        annotation.
        """
        # Prepare inputs.
        kwargs = {
            "type": int,
            "default": 2,
            "help": "Header level (1=H1, 2=H2, ...)",
        }
        # Prepare outputs.
        expected = "Header level (1=H1, 2=H2, ...) (default: 2)"
        # Run test.
        self.helper(kwargs, expected)

    def test6(self) -> None:
        """
        Test that a `store_true` flag's `False` default is still shown
        explicitly.
        """
        # Prepare inputs.
        kwargs = {"action": "store_true", "help": "Save instead of executing"}
        # Prepare outputs.
        expected = "Save instead of executing (default: False)"
        # Run test.
        self.helper(kwargs, expected)

    def test7(self) -> None:
        """
        Test that a "%" in the default value is escaped, so
        `_expand_help()`'s later "%"-substitution doesn't choke on it.
        """
        # Prepare inputs.
        kwargs = {"default": "50%off", "help": "Some help"}
        # Prepare outputs.
        expected = "Some help (default: 50%%off)"
        # Run test.
        self.helper(kwargs, expected)

    def test8(self) -> None:
        """
        Test that a help string already using the `%(default)s`
        placeholder isn't given a second, redundant annotation.
        """
        # Prepare inputs.
        kwargs = {
            "default": "X",
            "help": "Uses %(default)s placeholder already",
        }
        # Prepare outputs.
        expected = "Uses %(default)s placeholder already"
        # Run test.
        self.helper(kwargs, expected)


# #############################################################################
# Test_CustomHelpFormatter_color
# #############################################################################


class Test_CustomHelpFormatter_color(hunitest.TestCase):
    """
    Test `hparser.CustomHelpFormatter`'s color auto-detection and
    `_color()`/`_colorize_default_annotation()` helpers.
    """

    def test1(self) -> None:
        """
        Test that `_use_color` is `False` when stdout is not a terminal
        (e.g., under pytest's captured output).
        """
        # Run test.
        formatter = hparser.CustomHelpFormatter("prog")
        # Check outputs.
        self.assertFalse(formatter._use_color)

    def test2(self) -> None:
        """
        Test that `_color()` returns the text unchanged when
        colorization is off.
        """
        # Prepare inputs.
        formatter = _ForceNoColorFormatter("prog")
        # Run test.
        actual = formatter._color("--files", "green")
        # Check outputs.
        expected = "--files"
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that `_color()` matches `hprint.color_highlight()` when
        colorization is on.
        """
        # Prepare inputs.
        formatter = _ForceColorFormatter("prog")
        # Run test.
        actual = formatter._color("--files", "green")
        # Check outputs.
        expected = hprint.color_highlight("--files", "green")
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test that only the "(default: ...)" substring of a help line is
        colorized, not the rest of the line.
        """
        # Prepare inputs.
        formatter = _ForceColorFormatter("prog")
        line = "Token budget per merged rule chunk (default: 1500)"
        # Run test.
        actual = formatter._colorize_default_annotation(line)
        # Check outputs.
        expected_prefix = "Token budget per merged rule chunk "
        expected_suffix = hprint.color_highlight("(default: 1500)", "gray")
        self.assertTrue(actual.startswith(expected_prefix))
        self.assertTrue(actual.endswith(expected_suffix))

    def test5(self) -> None:
        """
        Test that a line with no "(default: ...)" annotation is
        unaffected by `_colorize_default_annotation()`.
        """
        # Prepare inputs.
        formatter = _ForceColorFormatter("prog")
        line = "Select specific files"
        # Run test.
        actual = formatter._colorize_default_annotation(line)
        # Check outputs.
        expected = "Select specific files"
        self.assertEqual(actual, expected)


# #############################################################################
# Test_CustomHelpFormatter_visible_len
# #############################################################################


class Test_CustomHelpFormatter_visible_len(hunitest.TestCase):
    """
    Test `hparser.CustomHelpFormatter._visible_len()`.
    """

    def test1(self) -> None:
        """
        Test that ANSI color codes are excluded from the reported length.
        """
        # Prepare inputs.
        plain = "--files FILES"
        colored = hprint.color_highlight(plain, "green")
        # Run test.
        actual = hparser.CustomHelpFormatter._visible_len(colored)
        # Check outputs.
        self.assertGreater(len(colored), len(plain))
        self.assertEqual(actual, len(plain))

    def test2(self) -> None:
        """
        Test that plain text (no ANSI codes) is unaffected.
        """
        # Prepare inputs.
        text = "--files FILES"
        # Run test.
        actual = hparser.CustomHelpFormatter._visible_len(text)
        # Check outputs.
        expected = len(text)
        self.assertEqual(actual, expected)


# #############################################################################
# Test_CustomHelpFormatter_format_help
# #############################################################################


class Test_CustomHelpFormatter_format_help(hunitest.TestCase):
    """
    Test `argparse.ArgumentParser.format_help()` end-to-end with
    `hparser.CustomHelpFormatter`.
    """

    def _build_parser(self, formatter_class: type) -> argparse.ArgumentParser:
        """
        Build a small parser exercising bullets, a required arg, and a
        default value, mirroring `cc_lint.py`'s `--rule`/`--mode`/
        `--max_chunk_tokens` shape.
        """
        parser = argparse.ArgumentParser(
            prog="myprog", formatter_class=formatter_class
        )
        parser.add_argument(
            "--files", type=str, default="", help="Select specific files"
        )
        parser.add_argument(
            "--max_chunk_tokens",
            type=int,
            default=1500,
            help="Token budget per merged rule chunk",
        )
        parser.add_argument(
            "--mode",
            required=True,
            choices=["a", "b", "c"],
            help=(
                "Execution mode:\n"
                "- 'a' does one thing\n"
                "  with more detail here\n"
                "- 'b' does another"
            ),
        )
        return parser

    def test1(self) -> None:
        """
        Test that `CustomHelpFormatter` wraps to 90 columns by default,
        regardless of the actual terminal size.
        """
        # Run test.
        formatter = hparser.CustomHelpFormatter("prog")
        # Check outputs.
        self.assertEqual(formatter._width, 90)

    def test2(self) -> None:
        """
        Test that a required `--mode` doesn't render "(default: None)",
        while an optional with a real default still does.
        """
        # Prepare inputs.
        parser = self._build_parser(_ForceNoColorFormatter)
        # Prepare outputs.
        expected = """
        usage: myprog [-h] [--files FILES] [--max_chunk_tokens MAX_CHUNK_TOKENS] --mode {a,b,c}

        options:
          -h, --help            show this help message and exit
          --files FILES         Select specific files
          --max_chunk_tokens MAX_CHUNK_TOKENS
                                Token budget per merged rule chunk (default: 1500)
          --mode {a,b,c}        Execution mode:
                                - 'a' does one thing with more detail here
                                - 'b' does another
        """
        # Run test.
        actual = parser.format_help()
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test that a hand-wrapped bullet list is reflowed cleanly in the
        rendered help (no mid-word orphan lines).
        """
        # Prepare inputs.
        parser = self._build_parser(_ForceNoColorFormatter)
        # Prepare outputs.
        expected = """
        usage: myprog [-h] [--files FILES] [--max_chunk_tokens MAX_CHUNK_TOKENS] --mode {a,b,c}

        options:
          -h, --help            show this help message and exit
          --files FILES         Select specific files
          --max_chunk_tokens MAX_CHUNK_TOKENS
                                Token budget per merged rule chunk (default: 1500)
          --mode {a,b,c}        Execution mode:
                                - 'a' does one thing with more detail here
                                - 'b' does another
        """
        # Run test.
        actual = parser.format_help()
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test the key correctness property: colorizing must not change
        column alignment or line wrapping vs. the uncolored render.
        """
        # Prepare inputs.
        colored_help = self._build_parser(_ForceColorFormatter).format_help()
        plain_help = self._build_parser(_ForceNoColorFormatter).format_help()
        # Run test.
        stripped_help = hprint.remove_non_printable_chars(colored_help)
        # Check outputs.
        # Sanity check that colorization actually did something, so this
        # test can't pass vacuously.
        self.assertNotEqual(colored_help, plain_help)
        self.assertEqual(stripped_help, plain_help)
