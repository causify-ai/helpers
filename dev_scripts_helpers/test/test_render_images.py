import logging

import dev_scripts_helpers.documentation.render_images as dshdreim
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# #############################################################################
# Test_get_comment_prefix_postfix
# #############################################################################

class Test_get_comment_prefix_postfix(hunitest.TestCase):
    """
    Test _get_comment_prefix_postfix() function.
    """

    def helper(self, extension: str, expected: tuple) -> None:
        """
        Test helper for _get_comment_prefix_postfix().

        :param extension: file extension (e.g., ".md", ".tex")
        :param expected: expected tuple (comment_prefix, comment_postfix)
        """
        # Run test.
        actual = dshdreim._get_comment_prefix_postfix(extension)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test comment prefix/postfix for Markdown files.
        """
        # Prepare inputs.
        extension = ".md"
        # Prepare outputs.
        expected = ("<!-- ", " -->")
        # Run test.
        self.helper(extension, expected)

    def test2(self) -> None:
        """
        Test comment prefix/postfix for LaTeX files.
        """
        # Prepare inputs.
        extension = ".tex"
        # Prepare outputs.
        expected = ("%", "")
        # Run test.
        self.helper(extension, expected)

    def test3(self) -> None:
        """
        Test comment prefix/postfix for text files.
        """
        # Prepare inputs.
        extension = ".txt"
        # Prepare outputs.
        expected = ("//", "")
        # Run test.
        self.helper(extension, expected)

    def test4(self) -> None:
        """
        Test that invalid file extension raises ValueError.
        """
        # Prepare inputs.
        extension = ".invalid"
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            dshdreim._get_comment_prefix_postfix(extension)
        actual = str(cm.exception)
        expected = "Unsupported file type: .invalid"
        self.assert_equal(actual, expected)

# #############################################################################
# Test_comment_line
# #############################################################################

class Test_comment_line(hunitest.TestCase):
    """
    Test _comment_line() function.
    """

    def helper(self, line: str, extension: str, expected: str) -> None:
        """
        Test helper for _comment_line().

        :param line: line to comment
        :param extension: file extension
        :param expected: expected commented line
        """
        # Run test.
        actual = dshdreim._comment_line(line, extension)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test commenting a line in Markdown format.
        """
        # Prepare inputs.
        line = "This is a line"
        extension = ".md"
        # Prepare outputs.
        expected = "<!--  This is a line -->"
        # Run test.
        self.helper(line, extension, expected)

    def test2(self) -> None:
        """
        Test commenting a line in LaTeX format.
        """
        # Prepare inputs.
        line = "\\begin{document}"
        extension = ".tex"
        # Prepare outputs.
        expected = "% \\begin{document}"
        # Run test.
        self.helper(line, extension, expected)

    def test3(self) -> None:
        """
        Test commenting a line in text format.
        """
        # Prepare inputs.
        line = "Some text"
        extension = ".txt"
        # Prepare outputs.
        expected = "// Some text"
        # Run test.
        self.helper(line, extension, expected)

    def test4(self) -> None:
        """
        Test commenting an empty line in Markdown.
        """
        # Prepare inputs.
        line = ""
        extension = ".md"
        # Prepare outputs.
        expected = "<!--   -->"
        # Run test.
        self.helper(line, extension, expected)

# #############################################################################
# Test_uncomment_line
# #############################################################################

class Test_uncomment_line(hunitest.TestCase):
    """
    Test _uncomment_line() function.
    """

    def helper(self, line: str, extension: str, expected: str) -> None:
        """
        Test helper for _uncomment_line().

        :param line: commented line
        :param extension: file extension
        :param expected: expected uncommented line
        """
        # Run test.
        actual = dshdreim._uncomment_line(line, extension)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test uncommenting a line in Markdown format.
        """
        # Prepare inputs.
        line = "<!-- This is a line -->"
        extension = ".md"
        # Prepare outputs.
        expected = "This is a line"
        # Run test.
        self.helper(line, extension, expected)

    def test2(self) -> None:
        """
        Test uncommenting a line in LaTeX format.
        """
        # Prepare inputs.
        line = "% \\begin{document}"
        extension = ".tex"
        # Prepare outputs.
        expected = "\\begin{document}"
        # Run test.
        self.helper(line, extension, expected)

    def test3(self) -> None:
        """
        Test uncommenting a line in text format.
        """
        # Prepare inputs.
        line = "// Some text"
        extension = ".txt"
        # Prepare outputs.
        expected = "Some text"
        # Run test.
        self.helper(line, extension, expected)

    def test4(self) -> None:
        """
        Test uncommenting a line without comment prefix.
        """
        # Prepare inputs.
        line = "This is a normal line"
        extension = ".md"
        # Prepare outputs.
        expected = "This is a normal line"
        # Run test.
        self.helper(line, extension, expected)

# #############################################################################
# Test_insert_image_code
# #############################################################################

# TODO(ai_gp): Factor out common code in a helper
class Test_insert_image_code(hunitest.TestCase):
    """
    Test _insert_image_code() function.
    """

    def test1(self) -> None:
        """
        Test inserting image code in Markdown format without label or caption.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/image.png"
        user_img_size = ""
        # Run test.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size
        )
        # Check outputs.
        expected = """
        <!--  render_images:begin -->
        ![](figs/image.png)
        <!--  render_images:end -->
        """
        self.assert_equal(actual, hprint.dedent(expected))

    def test2(self) -> None:
        """
        Test inserting image code in Markdown with label and caption.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/diagram.png"
        user_img_size = "width=50%"
        label = "fig:my_diagram"
        caption = "This is a diagram"
        # Run test.
        actual = dshdreim._insert_image_code(
            extension,
            rel_img_path,
            user_img_size,
            label=label,
            caption=caption,
        )
        # Check outputs.
        expected = """
        <!--  render_images:begin -->
        ![This is a diagram](figs/diagram.png){#fig:my_diagram width=50%}
        <!--  render_images:end -->
        """
        self.assert_equal(actual, hprint.dedent(expected))

    def test3(self) -> None:
        """
        Test inserting image code in Markdown with size but no label/caption.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/image.png"
        user_img_size = "width=80%"
        # Run test.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size
        )
        # Check outputs.
        expected = """
        <!--  render_images:begin -->
        ![](figs/image.png){width=80%}
        <!--  render_images:end -->
        """
        self.assert_equal(actual, hprint.dedent(expected))

    def test4(self) -> None:
        """
        Test inserting image code in LaTeX format without label or caption.
        """
        # Prepare inputs.
        extension = ".tex"
        rel_img_path = "figs/figure.png"
        user_img_size = ""
        # Run test.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size
        )
        # Check outputs.
        expected = r"""
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/figure.png}
        \end{figure}
        % render_images:end
        """
        self.assert_equal(actual, hprint.dedent(expected))

    def test5(self) -> None:
        """
        Test inserting image code in LaTeX with label and caption.
        """
        # Prepare inputs.
        extension = ".tex"
        rel_img_path = "figs/diagram.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = "Test diagram showing communication"
        # Run test.
        actual = dshdreim._insert_image_code(
            extension,
            rel_img_path,
            user_img_size,
            label=label,
            caption=caption,
        )
        # Check outputs.
        expected = r"""
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/diagram.png}
          \caption{Test diagram showing communication}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.assert_equal(actual, hprint.dedent(expected))

    def test6(self) -> None:
        """
        Test inserting image code in text format.
        """
        # Prepare inputs.
        extension = ".txt"
        rel_img_path = "figs/image.png"
        user_img_size = ""
        # Run test.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size
        )
        # Check outputs.
        expected = """
        // render_images:begin
        ![](figs/image.png)
        // render_images:end
        """
        self.assert_equal(actual, hprint.dedent(expected))

    def test7(self) -> None:
        """
        Test that invalid file extension raises ValueError.
        """
        # Prepare inputs.
        extension = ".invalid"
        rel_img_path = "figs/image.png"
        user_img_size = ""
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            dshdreim._insert_image_code(extension, rel_img_path, user_img_size)
        actual = str(cm.exception)
        expected = "Unsupported file type: .invalid"
        self.assert_equal(actual, expected)

# #############################################################################
# Test_remove_image_code
# #############################################################################

# TODO(ai_gp): Factor out common code in a helper
class Test_remove_image_code(hunitest.TestCase):
    """
    Test _remove_image_code() function.
    """

    def test1(self) -> None:
        """
        Test removing rendered image block and uncommenting original code in Markdown.
        """
        # Prepare inputs.
        lines = """
        Some text before
        <!--  rendered_images:begin -->
        <!--  ```plantuml -->
        <!--  A -> B -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/image.png)
        <!--  render_images:end -->
        Some text after
        """
        lines = hprint.dedent(lines).split("\n")
        extension = ".md"
        # Run test.
        actual = dshdreim._remove_image_code(lines, extension)
        # Check outputs.
        expected = """
        Some text before
        ```plantuml
        A -> B
        ```
        Some text after
        """
        expected_lines = hprint.dedent(expected).split("\n")
        self.assertEqual(actual, expected_lines)

    def test2(self) -> None:
        """
        Test removing rendered image block in LaTeX format.
        """
        # Prepare inputs.
        lines = r"""
        Text before
        % rendered_images:begin
        % ```tikz
        % \draw (0,0) -- (1,1);
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/image.png}
        \end{figure}
        % render_images:end
        Text after
        """
        lines = hprint.dedent(lines).split("\n")
        extension = ".tex"
        # Run test.
        actual = dshdreim._remove_image_code(lines, extension)
        # Check outputs.
        expected = """
        Text before
        ```tikz
        \\draw (0,0) -- (1,1);
        ```
        Text after
        """
        expected_lines = hprint.dedent(expected).split("\n")
        self.assert_equal(str(actual), str(expected_lines))

    def test3(self) -> None:
        """
        Test removing multiple rendered image blocks.
        """
        # Prepare inputs.
        lines = """
        First block:
        <!--  rendered_images:begin -->
        <!--  ```plantuml -->
        <!--  A -> B -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/image1.png)
        <!--  render_images:end -->

        Second block:
        <!--  rendered_images:begin -->
        <!--  ```mermaid -->
        <!--  graph TD -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/image2.png)
        <!--  render_images:end -->
        """
        lines = hprint.dedent(lines).split("\n")
        extension = ".md"
        # Run test.
        actual = dshdreim._remove_image_code(lines, extension)
        # Check outputs.
        expected = """
        First block:
        ```plantuml
        A -> B
        ```

        Second block:
        ```mermaid
        graph TD
        ```
        """
        expected_lines = hprint.dedent(expected).split("\n")
        self.assert_equal("\n".join(actual), "\n".join(expected_lines))

    def test4(self) -> None:
        """
        Test that lines without rendered blocks remain unchanged.
        """
        # Prepare inputs.
        lines = """
        Some normal text
        No rendered images here
        Just plain content
        """
        lines = hprint.dedent(lines).split("\n")
        extension = ".md"
        # Run test.
        actual = dshdreim._remove_image_code(lines, extension)
        # Check outputs.
        expected_lines = hprint.dedent("""
        Some normal text
        No rendered images here
        Just plain content
        """).split("\n")
        self.assertEqual(actual, expected_lines)

    def test5(self) -> None:
        """
        Test handling of empty input.
        """
        # Prepare inputs.
        lines = []
        extension = ".md"
        # Run test.
        actual = dshdreim._remove_image_code(lines, extension)
        # Check outputs.
        self.assertEqual(actual, [])
