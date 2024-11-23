import logging

import pytest

import dev_scripts_helpers.documentation.transform_txt as dshdtrtx
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_markdown_to_latex1(hunitest.TestCase):
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
        exp = r"""
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
        self._check(markdown, exp)

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
        exp = r"""
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
        self._check(markdown, exp)

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
        exp = r"""
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
        self._check(markdown, exp)

    def test4(self) -> None:
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
        exp = r"""
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
        self._check(markdown, exp)

    def _check(self, markdown: str, exp: str) -> None:
        """
        Check the markdown to latex transformation.
        """
        markdown = hprint.dedent(markdown)
        act = dshdtrtx.markdown_list_to_latex(markdown)
        exp = hprint.dedent(exp)
        self.assert_equal(act, exp)


# #############################################################################


class Test_remove_latex_formatting(hunitest.TestCase):
    def test1(self) -> None:
        txt = """
        - If there is \textcolor{red}{no pattern}, we can try learning:
          - Measure if \textcolor{blue}{learning works}.
          - In the \textcolor{orange}{worst case}, conclude that it
            \textcolor{green}{does not work}.
        - If we can find the \textcolor{purple}{solution in one step} or
          \textcolor{cyan}{program the solution}:
          - \textcolor{brown}{Machine learning} is not the \textcolor{teal}{recommended
            technique}, but it still works.
        - Without \textcolor{magenta}{data}, we cannot do anything:
          \textcolor{violet}{data is all that matters}.
        """
        exp = """
        """
        act = dshdtrtx.remove_latex_formatting(txt)
        self.assert_equal(act, exp)