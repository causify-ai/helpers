import logging
import os
from unittest import mock

import pytest

import dev_scripts_helpers.documentation.transform_text as dshdotrte
import helpers.hio as hio
import helpers.hlatex as hlatex
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_transform_text_py
# #############################################################################


class Test_transform_text_py(hunitest.TestCase):
    """
    End-to-end tests for the `transform_text.py` executable.
    """

    def _run_main(self, text: str, action: str) -> str:
        """
        Run `dshdotrte._main()` on `text` with the given `action`.

        :param text: content written to the input file
        :param action: value passed to the `-a` command-line option
        :return: content of the output file
        """
        scratch_dir = self.get_scratch_space()
        in_file = os.path.join(scratch_dir, "input.txt")
        out_file = os.path.join(scratch_dir, "output.txt")
        hio.to_file(in_file, text)
        argv = [
            "transform_text.py",
            "-i",
            in_file,
            "-o",
            out_file,
            "-a",
            action,
        ]
        parser = dshdotrte._parse()
        with mock.patch("sys.argv", argv):
            dshdotrte._main(parser)
        return hio.from_file(out_file)

    def test1(self) -> None:
        """
        Test the `md_remove_bullets` action removes leading dashes.
        """
        # Prepare inputs.
        text = hprint.dedent(
            """\
            - item one
            - item two"""
        )
        # Prepare outputs.
        expected = hprint.dedent(
            """\
            item one
            item two"""
        )
        # Run test.
        actual = self._run_main(text, "md_remove_bullets")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test the `md_remove_bullets` action with a single item (edge case).
        """
        # Prepare inputs.
        text = "- single item"
        # Prepare outputs.
        expected = "single item"
        # Run test.
        actual = self._run_main(text, "md_remove_bullets")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test the `md_remove_bullets` action with empty input (edge case).
        """
        # Prepare inputs.
        text = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        actual = self._run_main(text, "md_remove_bullets")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test the `md_add_checkbox` action prefixes non-empty lines.
        """
        # Prepare inputs.
        text = hprint.dedent(
            """\
            item one
            item two"""
        )
        # Prepare outputs.
        expected = hprint.dedent(
            """\
            - [ ] item one
            - [ ] item two"""
        )
        # Run test.
        actual = self._run_main(text, "md_add_checkbox")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test the `md_add_checkbox` action with a single item (edge case).
        """
        # Prepare inputs.
        text = "single item"
        # Prepare outputs.
        expected = "- [ ] single item"
        # Run test.
        actual = self._run_main(text, "md_add_checkbox")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test the `md_add_checkbox` action with empty input (edge case).
        """
        # Prepare inputs.
        text = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        actual = self._run_main(text, "md_add_checkbox")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test7(self) -> None:
        """
        Test the `slide_format_figures` action splits text and figure into a
        two-column layout.
        """
        # Prepare inputs.
        text = hprint.dedent(
            """\
            Some text
            ![alt](image.png)
            More text"""
        )
        # Prepare outputs.
        expected = hprint.dedent(
            """
            ::: columns
            :::: {.column width=65%}
            Some text
            ::::
            :::: {.column width=40%}

            ![alt](image.png)
            More text
            ::::
            :::
            """
        )
        # Run test.
        actual = self._run_main(text, "slide_format_figures")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test8(self) -> None:
        """
        Test the `slide_add_figure` action wraps content in a column block.
        """
        # Prepare inputs.
        text = "![alt](image.png)"
        # Prepare outputs.
        expected = hprint.dedent(
            """
            ::: columns
            :::: {.column width=50%}
            ![alt](image.png)
            ::::
            :::: {.column width=45%}
            ::::
            :::
            """
        )
        # Run test.
        actual = self._run_main(text, "slide_add_figure")
        # Check outputs.
        self.assert_equal(actual, expected)

    def test9(self) -> None:
        """
        Test the `list` action prints every available transform.
        """
        # Prepare inputs.
        # (No explicit input needed; testing available transforms list)
        # Prepare outputs.
        expected = str([
            "test",
            "format_headers",
            "increase_headers_level",
            "toc",
            "md_list_to_latex",
            "md_to_latex",
            "md_remove_formatting",
            "md_remove_bullets",
            "md_clean_up",
            "md_only_format",
            "md_bold_bullets",
            "md_add_checkbox",
            "md_colorize_bold_text",
            "md_format",
            "slide_format_figures",
            "slide_add_figure",
        ])
        # Run test.
        transforms = dshdotrte._get_available_transforms()
        # Check outputs.
        names = [name for name, _ in transforms]
        self.assert_equal(str(names), expected)


# #############################################################################
# Test_markdown_list_to_latex
# #############################################################################


@pytest.mark.superslow
@pytest.mark.skipif(not hserver.is_host_mac(), reason="See CsfyTask8868")
class Test_markdown_list_to_latex(hunitest.TestCase):
    """
    Test `hlatex.markdown_list_to_latex()` function.
    """

    def _check(self, markdown: str, expected: str) -> None:
        """
        Check the markdown to latex transformation.
        """
        # 1) Prepare inputs.
        markdown = hprint.dedent(markdown)
        # 2) Run tests.
        tmp_dir = self.get_scratch_space()
        actual = hlatex.markdown_list_to_latex(markdown, tmp_dir=tmp_dir)
        # 3) Check.
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a simple nested list with no frame title.
        """
        markdown = """
        - Item 1
          - Subitem 1.1
          - Subitem 1.2
        - Item 2
        """
        expected = r"""
        \begin{itemize}
        \item
          Item 1
          \begin{itemize}
          \item
            Subitem 1.1
          \item
            Subitem 1.2
          \end{itemize}
        \item
          Item 2
        \end{itemize}"""
        # Run the test.
        self._check(markdown, expected)

    def test2(self) -> None:
        """
        Test a nested list that includes a frame title.
        """
        markdown = """
        * Title of Frame
          - Item 1
            - Subitem 1.1
          - Item 2
        """
        expected = r"""
        \begin{frame}{Title of Frame}
        \begin{itemize}
        \item
          Item 1
          \begin{itemize}
          \item
            Subitem 1.1
          \end{itemize}
        \item
          Item 2
        \end{itemize}
        \end{frame}"""
        # Run the test.
        self._check(markdown, expected)

    def test3(self) -> None:
        """
        Test a deeply nested list structure.
        """
        markdown = """
        - Level 1
          - Level 2
            - Level 3
              - Level 4
        """
        expected = r"""
        \begin{itemize}
        \item
          Level 1
          \begin{itemize}
          \item
            Level 2
            \begin{itemize}
            \item
              Level 3
              \begin{itemize}
              \item
                Level 4
              \end{itemize}
            \end{itemize}
          \end{itemize}
        \end{itemize}"""
        # Run the test.
        self._check(markdown, expected)

    def test4(self) -> None:
        """
        Test a complex nested list with frame title and multiple levels.
        """
        markdown = """
        * Title of Frame
        - Item 1
          - Subitem 1.1
            - Subitem 1.1.1
          - Subitem 1.2
        - Item 2
          - Ordered Subitem 2.1
          - Ordered Subitem 2.2
        """
        expected = r"""
        \begin{frame}{Title of Frame}
        \begin{itemize}
        \item
          Item 1
          \begin{itemize}
          \item
            Subitem 1.1
            \begin{itemize}
            \item
              Subitem 1.1.1
            \end{itemize}
          \item
            Subitem 1.2
          \end{itemize}
        \item
          Item 2
          \begin{itemize}
          \item
            Ordered Subitem 2.1
          \item
            Ordered Subitem 2.2
          \end{itemize}
        \end{itemize}
        \end{frame}"""
        # Run the test.
        self._check(markdown, expected)

    def test5(self) -> None:
        """
        Test a single item list (edge case).
        """
        markdown = """
        - Single Item
        """
        expected = r"""
        \begin{itemize}
        \item
          Single Item
        \end{itemize}"""
        # Run the test.
        self._check(markdown, expected)

    def test6(self) -> None:
        """
        Test a single item list with frame title (edge case).
        """
        markdown = """
        * Frame Title
        - Single Item
        """
        expected = r"""
        \begin{frame}{Frame Title}
        \begin{itemize}
        \item
          Single Item
        \end{itemize}
        \end{frame}"""
        # Run the test.
        self._check(markdown, expected)
