import logging
import pprint

import dev_scripts_helpers.documentation.transform_txt as dsdoremd
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


class Test_MarkdownItem1(hunitest.TestCase):
    
    def test_str1(self):
        item = dsdoremd.MarkdownItem("Title", [
            dsdoremd.MarkdownItem("Subitem 1", [
                dsdoremd.MarkdownItem("Subsubitem 1.1")])])
        act = str(item)
        exp = r"""
        * Title
          * Subitem 1
            * Subsubitem 1.1
        """
        self.assert_equal(act, exp, dedent=True)

    def test_str2(self):
        item = dsdoremd.MarkdownItem("Title",
              [dsdoremd.MarkdownItem("Item 1",
                     [
                         dsdoremd.MarkdownItem("Subitem 1")
                     ]),
               dsdoremd.MarkdownItem("Item 2")
               ])
        act = str(item)
        exp = r"""
        * Title
          * Item 1
            * Subitem 1
          * Item 2
        """
        self.assert_equal(act, exp, dedent=True)

    def test_MarkdownItems_to_str1(self):
        item1 = dsdoremd.MarkdownItem("Title", [
            dsdoremd.MarkdownItem("Subitem 1", [
                dsdoremd.MarkdownItem("Subsubitem 1.1")])])
        item2 = dsdoremd.MarkdownItem("Title2", [
            dsdoremd.MarkdownItem("Subitem 1")])
        items = [item1, item2]
        #
        act = dsdoremd.MarkdownItems_to_str(items)
        exp = r"""
        * Title
          * Subitem 1
            * Subsubitem 1.1
        * Title2
          * Subitem 1"""
        self.assert_equal(act, exp, dedent=True)


class Test_parse_markdown1(hunitest.TestCase):

    def _check(self, markdown: str, exp: str) -> None:
        """
        Check the markdown to latex transformation.
        """
        markdown = hprint.dedent(markdown)
        markdown = markdown.split("\n")
        act = dsdoremd._parse_markdown(markdown)
        print(act)
        #
        act = dsdoremd.MarkdownItems_to_str(act)
        self.assert_equal(act, exp)

    def test1(self):
        """
        Test a simple nested list with no frame title.
        """
        markdown = """
        * Item 1
          * Subitem 1.1
          * Subitem 1.2
        * Item 2
        """
        exp = """
        """
        # Run the test.
        self._check(markdown, exp)

    def test2(self):
        """
        Test a nested list that includes a frame title.
        """
        markdown = """
        * Title of Frame
          * Item 1
            * Subitem 1.1
          * Item 2
        """
        exp = """
        \\begin{frame}{Title of Frame}
        \\begin{itemize}
          \\item Title of Frame
            \\item Item 1
              \\item Subitem 1.1
            \\item Item 2
        \\end{itemize}
        \\end{frame}
        """
        # Run the test.
        self._check(markdown, exp)

    def test3(self):
        """
        Test a deeply nested list structure.
        """
        markdown = """
        * Level 1
          * Level 2
            * Level 3
              * Level 4
        """
        exp = """
        \\begin{itemize}
          \\item Level 1
            \\item Level 2
              \\item Level 3
                \\item Level 4
        \\end{itemize>
        """
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
          1. Ordered Subitem 2.1
          2. Ordered Subitem 2.2
        """
        exp = (
            "\\begin{itemize}\n"
            "  \\item Level 1\n"
            "    \\item Level 2\n"
            "      \\item Level 3\n"
            "        \\item Level 4\n"
            "\\end{itemize}\n"
        )
        # Run the test.
        self._check(markdown, exp)

# #############################################################################


class Test_markdown_to_latex1(hunitest.TestCase):

    def _check(self, markdown: str, exp: str) -> None:
        """
        Check the markdown to latex transformation.
        """
        markdown = hprint.dedent(markdown)
        act = dsdoremd.markdown_to_latex(markdown)
        exp = hprint.dedent(exp)
        self.assert_equal(act, exp)

    def test_simple_nested_list(self):
        """
        Test a simple nested list with no frame title.
        """
        markdown = """
        * Item 1
          * Subitem 1.1
          * Subitem 1.2
        * Item 2
        """
        exp = """
        \\begin{itemize}
          \\item Item 1
            \\begin{itemize}
              \\item Subitem 1.1
              \\item Subitem 1.2
            \\end{itemize}
          \\item Item 2
        \\end{itemize}
        """
        # Run the test.
        self._check(markdown, exp)

    def test_list_with_frame_title(self):
        """
        Test a nested list that includes a frame title.
        """
        markdown = """
        * Title of Frame
          * Item 1
            * Subitem 1.1
          * Item 2
        """
        exp = """
        \\begin{frame}{Title of Frame}
        \\begin{itemize}
          \\item Title of Frame
            \\item Item 1
              \\item Subitem 1.1
            \\item Item 2
        \\end{itemize}
        \\end{frame}
        """
        # Run the test.
        self._check(markdown, exp)

    def test_deeply_nested_list(self):
        """
        Test a deeply nested list structure.
        """
        markdown = """
        * Level 1
          * Level 2
            * Level 3
              * Level 4
        """
        exp = """
        \\begin{itemize}
          \\item Level 1
            \\item Level 2
              \\item Level 3
                \\item Level 4
        \\end{itemize>
        """
        # Run the test.
        self._check(markdown, exp)

    def test1(self) -> None:
        markdown = """
        * Title of Frame
        - Item 1
          - Subitem 1.1
            - Subitem 1.1.1
          - Subitem 1.2
        - Item 2
          1. Ordered Subitem 2.1
          2. Ordered Subitem 2.2
        """
        exp = (
            "\\begin{itemize}\n"
            "  \\item Level 1\n"
            "    \\item Level 2\n"
            "      \\item Level 3\n"
            "        \\item Level 4\n"
            "\\end{itemize}\n"
        )
        # Run the test.
        self._check(markdown, exp)