import logging

import pytest

import helpers.hlatex as hlatex
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_markdown_to_latex1
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
        # 1) Prepare inputs.
        markdown = hprint.dedent(markdown)
        # 2) Run tests.
        act = hlatex.markdown_list_to_latex(markdown)
        # 3) Check.
        exp = hprint.dedent(exp)
        self.assert_equal(act, exp)
