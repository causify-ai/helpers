import logging
import os

import pytest

import dev_scripts_helpers.documentation.render_images as dshdreim
import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_get_rendered_file_paths1
# #############################################################################


class Test_get_rendered_file_paths1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check generation of file paths for rendering images.
        """
        # Prepare inputs.
        out_file = "/a/b/c/d/e.md"
        image_code_idx = 8
        dst_ext = "png"
        dst_dir = "/a/b/c/d/figs"
        # Prepare outputs.
        expected = """
        tmp.render_images/e.8.txt
        /a/b/c/d/figs
        figs/e.8.png
        """
        # Run test.
        paths = dshdreim._get_rendered_file_paths(
            out_file, image_code_idx, dst_ext, dst_dir
        )
        # Check outputs.
        actual = "\n".join(paths)
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Check generation of file paths with custom dst_dir.
        """
        # Prepare inputs.
        out_file = "/a/b/c/d/e.md"
        image_code_idx = 8
        dst_ext = "png"
        dst_dir = "/custom/path/images"
        # Prepare outputs.
        expected = """
        tmp.render_images/e.8.txt
        /custom/path/images
        ../../../../custom/path/images/e.8.png
        """
        # Run test.
        paths = dshdreim._get_rendered_file_paths(
            out_file, image_code_idx, dst_ext, dst_dir
        )
        # Check outputs.
        actual = "\n".join(paths)
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_remove_image_code1
# #############################################################################


class Test_remove_image_code1(hunitest.TestCase):
    """
    Test `_remove_image_code()` function.
    """

    def helper(self, in_text: str, extension: str, expected: str) -> None:
        """
        Helper function to test `_remove_image_code()`.

        :param in_text: input text as a single string
        :param extension: file extension (e.g., ".md", ".tex")
        :param expected: expected output as a single string
        """
        # Prepare inputs.
        in_text = hprint.dedent(in_text, remove_lead_trail_empty_lines_=True)
        in_lines = in_text.split("\n")
        # Run function.
        actual = dshdreim._remove_image_code(in_lines, extension)
        # Check output.
        actual = "\n".join(actual)
        expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=True)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test with text that has no render markers.
        """
        in_text = r"""
        A
        B
        C
        """
        extension = ".md"
        expected = r"""
        A
        B
        C
        """
        self.helper(in_text, extension, expected)

    def test2(self) -> None:
        """
        Test removing a render_images block.
        """
        in_text = r"""
        Before
        % render_images:begin
        ![](figs/test.1.png)
        % render_images:end
        After
        """
        extension = ".md"
        expected = r"""
        Before
        After
        """
        self.helper(in_text, extension, expected)

    def test3(self) -> None:
        """
        Test removing multiple render_images blocks.
        """
        in_text = r"""
        Text1
        % render_images:begin
        ![](figs/test.1.png)
        % render_images:end
        Text2
        % render_images:begin
        ![](figs/test.2.png)
        % render_images:end
        Text3
        """
        extension = ".md"
        expected = r"""
        Text1
        Text2
        Text3
        """
        self.helper(in_text, extension, expected)

    def test4(self) -> None:
        """
        Test with empty input.
        """
        in_text = """
        """
        extension = ".md"
        expected = """
        """
        self.helper(in_text, extension, expected)

    def test5(self) -> None:
        """
        Test with only markers and no content between them.
        """
        in_text = r"""
        % render_images:begin
        % render_images:end
        """
        extension = ".md"
        expected = r"""
        """
        self.helper(in_text, extension, expected)

    def test6(self) -> None:
        """
        Test uncommenting a rendered_images block containing `-->` in content.

        This verifies the fix for the bug where `-->` inside mermaid edges
        (e.g., `BP --> |Track usage| Providers`) was stripped along with the
        HTML comment closing tag ` -->`, corrupting the diagram. The fix only
        strips the outermost `<!-- ... -->` wrapper, not all ` -->` occurrences.
        """
        in_text = r"""
        Before
        <!--  rendered_images:begin -->
        <!--  ```mermaid -->
        <!--  graph LR -->
        <!--      BP --> |Track usage| Providers -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        After
        """
        extension = ".md"
        expected = r"""
        Before
        ```mermaid
        graph LR
            BP --> |Track usage| Providers
        ```
        After
        """
        self.helper(in_text, extension, expected)

    def test7(self) -> None:
        """
        Test uncommenting a rendered_images block.
        """
        in_text = r"""
        Before
        % rendered_images:begin
        % ```plantuml
        % Alice -> Bob
        % ```
        % rendered_images:end
        After
        """
        extension = ".tex"
        expected = r"""
        Before
        ```plantuml
        Alice -> Bob
        ```
        After
        """
        self.helper(in_text, extension, expected)

    def test8(self) -> None:
        """
        Test with both rendered_images and render_images markers (LaTeX
        extension).
        """
        in_text = r"""
        Before
        % rendered_images:begin
        % ```plantuml
        % Alice -> Bob
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[h]
        ![](figs/test.1.png)
        \end{figure}
        % render_images:end
        After
        """
        extension = ".tex"
        expected = """
        Before
        ```plantuml
        Alice -> Bob
        ```
        After
        """
        self.helper(in_text, extension, expected)

    def test9(self) -> None:
        """
        Test with LaTeX file extension.
        """
        in_text = r"""
        Before
        % rendered_images:begin
        % ```graphviz
        % digraph { A -> B }
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[h]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        After
        """
        extension = ".tex"
        expected = r"""
        Before
        ```graphviz
        digraph { A -> B }
        ```
        After
        """
        self.helper(in_text, extension, expected)

    def test10(self) -> None:
        """
        Test with txt file extension.
        """
        in_text = r"""
        Before
        // rendered_images:begin
        // ```mermaid
        // flowchart TD;
        // ```
        // rendered_images:end
        // render_images:begin
        ![](figs/out.1.png)
        // render_images:end
        After
        """
        extension = ".txt"
        expected = r"""
        Before
        ```mermaid
        flowchart TD;
        ```
        After
        """
        self.helper(in_text, extension, expected)

    def test11(self) -> None:
        """
        Test removing render block with complex nested content.
        """
        in_text = r"""
        Before
        % render_images:begin
        \begin{figure}[h]
          \includegraphics[width=\linewidth]{figs/test.png}
          \caption{Test caption}
          \label{fig:test}
        \end{figure}
        % render_images:end
        After
        """
        extension = ".tex"
        expected = r"""
        Before
        After
        """
        self.helper(in_text, extension, expected)


# #############################################################################
# Test_render_image_code1
# #############################################################################


@pytest.mark.superslow
@pytest.mark.skipif(not hserver.is_host_mac(), reason="See CsfyTask8868")
class Test_render_image_code1(hunitest.TestCase):
    """
    Test `_render_image_code()`.
    """

    def helper(
        self,
        image_code: str,
        image_code_type: str,
        out_file_name: str,
        dst_ext: str,
        expected_path: str,
    ) -> None:
        """
        Test helper for `_render_image_code()`.

        :param image_code: Code for the image to render
        :param image_code_type: Type of image code (graphviz, mermaid, etc.)
        :param out_file_name: Output file name
        :param dst_ext: Destination image extension
        :param expected_path: Expected path to the rendered image
        """
        image_code_idx = 1
        template_out_file = os.path.join(self.get_scratch_space(), out_file_name)
        dst_dir = os.path.join(self.get_scratch_space(), "figs")
        # Run test.
        rel_img_paths = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
            dst_dir,
        )
        # Check outputs.
        self.assert_equal(rel_img_paths[0], expected_path)

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Check rendering of an image code in a Markdown file.
        """
        image_code = "digraph { A -> B }"
        image_code_type = "graphviz"
        out_file_name = "test.md"
        dst_ext = "png"
        expected_path = "figs/test.1.png"
        self.helper(
            image_code, image_code_type, out_file_name, dst_ext, expected_path
        )

    def test2(self) -> None:
        """
        Check rendering of an image code in a Markdown file with a different
        image code type.
        """
        image_code = """
        graph TD
            B --> A
        """
        image_code_type = "mermaid"
        out_file_name = "test.md"
        dst_ext = "png"
        expected_path = "figs/test.1.png"
        self.helper(
            image_code, image_code_type, out_file_name, dst_ext, expected_path
        )

    def test3(self) -> None:
        """
        Check rendering of an image code in a Markdown file with a different
        output file and extension.
        """
        image_code = "digraph { A -> B }"
        image_code_type = "graphviz"
        out_file_name = "test2.md"
        dst_ext = "svg"
        expected_path = "figs/test2.1.svg"
        self.helper(
            image_code, image_code_type, out_file_name, dst_ext, expected_path
        )

    @pytest.mark.slow
    def test4(self) -> None:
        """
        Check rendering of SVG code to PNG.
        """
        image_code = r"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="40" fill="blue" />
        </svg>
        """
        image_code_type = "svg"
        out_file_name = "test_svg.md"
        dst_ext = "png"
        expected_path = "figs/test_svg.1.png"
        self.helper(
            image_code, image_code_type, out_file_name, dst_ext, expected_path
        )


# #############################################################################
# Test_insert_image_code1
# #############################################################################


class Test_insert_image_code1(hunitest.TestCase):
    """
    Test _insert_image_code() for markdown files.
    """

    def helper(
        self,
        rel_img_path: str,
        user_img_size: str,
        label: str,
        caption: str,
        expected: str,
    ) -> None:
        actual = dshdreim._insert_image_code(
            ".md", rel_img_path, user_img_size, label=label, caption=caption
        )
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test markdown output without label or caption.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = ""
        expected = """
        <!--  render_images:begin -->
        ![](figs/test.1.png)
        <!--  render_images:end -->
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)

    def test2(self) -> None:
        """
        Test markdown output with label only.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = ""
        expected = """
        <!--  render_images:begin -->
        ![](figs/test.1.png){#fig:test_diagram}
        <!--  render_images:end -->
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)

    def test3(self) -> None:
        """
        Test markdown output with caption only.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = "Test diagram caption"
        expected = """
        <!--  render_images:begin -->
        ![Test diagram caption](figs/test.1.png)
        <!--  render_images:end -->
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)

    def test4(self) -> None:
        """
        Test markdown output with both label and caption.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = "Test diagram caption"
        expected = """
        <!--  render_images:begin -->
        ![Test diagram caption](figs/test.1.png){#fig:test_diagram}
        <!--  render_images:end -->
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)

    def test5(self) -> None:
        """
        Test markdown output with user-specified size.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = "height=100%"
        label = "fig:test_diagram"
        caption = "Test diagram"
        expected = """
        <!--  render_images:begin -->
        ![Test diagram](figs/test.1.png){#fig:test_diagram height=100%}
        <!--  render_images:end -->
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)


# #############################################################################
# Test_insert_image_code2
# #############################################################################


class Test_insert_image_code2(hunitest.TestCase):
    """
    Test _insert_image_code() for LaTeX files.
    """

    def helper(
        self,
        rel_img_path: str,
        user_img_size: str,
        label: str,
        caption: str,
        expected: str,
    ) -> None:
        actual = dshdreim._insert_image_code(
            ".tex", rel_img_path, user_img_size, label=label, caption=caption
        )
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test1(self) -> None:
        """
        Test LaTeX output without label or caption.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = ""
        expected = r"""
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/test.1.png}
        \end{figure}
        % render_images:end
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)

    def test2(self) -> None:
        """
        Test LaTeX output with label only.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = ""
        expected = r"""
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/test.1.png}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)

    def test3(self) -> None:
        """
        Test LaTeX output with caption only.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = "Test diagram caption"
        expected = r"""
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/test.1.png}
          \caption{Test diagram caption}
        \end{figure}
        % render_images:end
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)

    def test4(self) -> None:
        """
        Test LaTeX output with both label and caption.
        """
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = "Test diagram caption"
        expected = r"""
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/test.1.png}
          \caption{Test diagram caption}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.helper(rel_img_path, user_img_size, label, caption, expected)


# #############################################################################
# Test_render_images1
# #############################################################################


class Test_render_images1(hunitest.TestCase):
    """
    Test _render_images() with dry run enabled (updating file text without
    creating images).
    """

    def helper(self, txt: str, file_ext: str, expected: str) -> None:
        """
        Check that the text is updated correctly.

        :param txt: the input text
        :param file_ext: the extension of the input file
        """
        # Prepare inputs.
        txt_lines = hprint.dedent(
            txt, remove_lead_trail_empty_lines_=True
        ).split("\n")
        out_file = os.path.join(self.get_scratch_space(), f"out.{file_ext}")
        dst_ext = "png"
        dst_dir = os.path.join(self.get_scratch_space(), "figs")
        # Render images.
        out_lines = dshdreim._render_images(
            txt_lines,
            out_file,
            dst_ext,
            dst_dir,
            dry_run=True,
        )
        # Check output.
        actual = "\n".join(out_lines)
        hdbg.dassert_ne(actual, "")
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected, remove_lead_trail_empty_lines=True)

    # ///////////////////////////////////////////////////////////////////////////

    def test1(self) -> None:
        """
        Check text without image code in a LaTeX file.
        """
        # Input.
        in_lines = r"""
        A
        B
        """
        file_ext = "tex"
        expected = in_lines
        # Run.
        self.helper(in_lines, file_ext, expected)

    def test2(self) -> None:
        """
        Check text without image code in a Markdown file.
        """
        in_lines = r"""
        A
        ```bash
        Alice --> Bob
        ```
        B
        """
        file_ext = "md"
        expected = in_lines
        self.helper(in_lines, file_ext, expected)

    # ///////////////////////////////////////////////////////////////////////////

    def test3(self) -> None:
        """
        Check bare plantUML code in a Markdown file.
        """
        in_lines = r"""
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```plantuml -->
        <!--  Alice --> Bob -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/out.1.png)
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test4(self) -> None:
        """
        Check plantUML code within other text in a Markdown file.
        """
        in_lines = r"""
        A
        ```plantuml
        Alice --> Bob
        ```
        B
        """
        file_ext = "md"
        expected = r"""
        A
        <!--  rendered_images:begin -->
        <!--  ```plantuml -->
        <!--  Alice --> Bob -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/out.1.png)
        <!--  render_images:end -->
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test5(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a Markdown
        file.
        """
        in_lines = r"""
        ```plantuml
        @startuml
        Alice --> Bob
        @enduml
        ```
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```plantuml -->
        <!--  @startuml -->
        <!--  Alice --> Bob -->
        <!--  @enduml -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/out.1.png)
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test6(self) -> None:
        """
        Check bare plantUML code in a LaTeX file.
        """
        in_lines = r"""
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "tex"
        expected = r"""
        % rendered_images:begin
        % ```plantuml
        % Alice --> Bob
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test7(self) -> None:
        """
        Check plantUML code within other text in a LaTeX file.
        """
        in_lines = r"""
        A
        ```plantuml
        Alice --> Bob
        ```
        B
        """
        file_ext = "tex"
        expected = r"""
        A
        % rendered_images:begin
        % ```plantuml
        % Alice --> Bob
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test8(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a LaTeX
        file.
        """
        in_lines = r"""
        ```plantuml
        @startuml
        Alice --> Bob
        @enduml
        ```
        """
        file_ext = "tex"
        expected = r"""
        % rendered_images:begin
        % ```plantuml
        % @startuml
        % Alice --> Bob
        % @enduml
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    # ///////////////////////////////////////////////////////////////////////////

    def test9(self) -> None:
        """
        Check bare mermaid code in a Markdown file.
        """
        in_lines = r"""
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```mermaid -->
        <!--  flowchart TD; -->
        <!--    A[Start] --> B[End]; -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/out.1.png)
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test10(self) -> None:
        """
        Check mermaid code within other text in a Markdown file.
        """
        in_lines = r"""
        A
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "md"
        expected = r"""
        A
        <!--  rendered_images:begin -->
        <!--  ```mermaid -->
        <!--  flowchart TD; -->
        <!--    A[Start] --> B[End]; -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/out.1.png)
        <!--  render_images:end -->
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test11(self) -> None:
        """
        Check mermaid code with `-->` inside content that also appears as the
        HTML comment closing tag (e.g., `BP --> |Track usage| Providers`).

        This verifies the fix for the bug where `-->` in mermaid edge labels
        was erroneously stripped by the blanket `.replace(" -->", "")` in the
        old `_uncomment_line()`.
        """
        in_lines = r"""
        ```mermaid
        graph LR
            BP --> |Track usage| Providers
        ```
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```mermaid -->
        <!--  graph LR -->
        <!--      BP --> |Track usage| Providers -->
        <!--  ``` -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/out.1.png)
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test12(self) -> None:
        """
        Check bare mermaid code in a LaTeX file.
        """
        in_lines = r"""
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        """
        file_ext = "tex"
        expected = r"""
        % rendered_images:begin
        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test13(self) -> None:
        """
        Check mermaid code within other text in a LaTeX file.
        """
        in_lines = r"""
        A
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "tex"
        expected = r"""
        A
        % rendered_images:begin
        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test14(self) -> None:
        """
        Check mermaid code within other text in a txt file.
        """
        in_lines = r"""
        A
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "txt"
        expected = r"""
        A
        // rendered_images:begin
        // ```mermaid
        // flowchart TD;
        //   A[Start] --> B[End];
        // ```
        // rendered_images:end
        // render_images:begin
        ![](figs/out.1.png)
        // render_images:end
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test15(self) -> None:
        """
        Check mermaid code within other text in a md file.
        """
        in_lines = r"""
        A
        ```mermaid(hello_world.png)
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "txt"
        expected = r"""
        A
        // rendered_images:begin
        // ```mermaid(hello_world.png)
        // flowchart TD;
        //   A[Start] --> B[End];
        // ```
        // rendered_images:end
        // render_images:begin
        ![](hello_world.png)
        // render_images:end
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test16(self) -> None:
        """
        Check commented mermaid code with an updated output file.
        """
        in_lines = r"""
        A
        // rendered_images:begin
        //     ```mermaid(hello_world.png)
        //     flowchart TD;
        //       A[Start] --> B[End];
        //     ```
        // rendered_images:end
        // render_images:begin
        ![](hello_world.png)
        // render_images:end
        B
        """
        file_ext = "txt"
        expected = in_lines
        self.helper(in_lines, file_ext, expected)

    # ///////////////////////////////////////////////////////////////////////////
    # Metadata tests

    def test17(self) -> None:
        """
        Check graphviz code with label metadata in a Markdown file.
        """
        in_lines = r"""
        ```graphviz
        digraph { A -> B }
        ```
        label=fig:test_diagram
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```graphviz -->
        <!--  digraph { A -> B } -->
        <!--  ``` -->
        <!--  label=fig:test_diagram -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![](figs/out.1.png){#fig:test_diagram}
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test18(self) -> None:
        """
        Check graphviz code with caption metadata in a Markdown file.
        """
        in_lines = r"""
        ```graphviz
        digraph { A -> B }
        ```
        caption=Test diagram showing communication
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```graphviz -->
        <!--  digraph { A -> B } -->
        <!--  ``` -->
        <!--  caption=Test diagram showing communication -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![Test diagram showing communication](figs/out.1.png)
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test19(self) -> None:
        """
        Check graphviz code with both label and caption in a Markdown file.
        """
        in_lines = r"""
        ```graphviz
        digraph { A -> B }
        ```
        label=fig:test_diagram
        caption=Test diagram showing communication
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```graphviz -->
        <!--  digraph { A -> B } -->
        <!--  ``` -->
        <!--  label=fig:test_diagram -->
        <!--  caption=Test diagram showing communication -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![Test diagram showing communication](figs/out.1.png){#fig:test_diagram}
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test20(self) -> None:
        """
        Check graphviz code with multi-line caption in a Markdown file.
        """
        in_lines = r"""
        ```graphviz
        digraph { A -> B }
        ```
        label=fig:test_diagram
        caption=This is a caption
          that spans multiple lines
          to test continuation
        """
        file_ext = "md"
        expected = r"""
        <!--  rendered_images:begin -->
        <!--  ```graphviz -->
        <!--  digraph { A -> B } -->
        <!--  ``` -->
        <!--  label=fig:test_diagram -->
        <!--  caption=This is a caption -->
        <!--    that spans multiple lines -->
        <!--    to test continuation -->
        <!--  rendered_images:end -->
        <!--  render_images:begin -->
        ![This is a caption that spans multiple lines to test continuation](figs/out.1.png){#fig:test_diagram}
        <!--  render_images:end -->
        """
        self.helper(in_lines, file_ext, expected)

    def test21(self) -> None:
        """
        Check graphviz code with label metadata in a LaTeX file.
        """
        in_lines = r"""
        ```graphviz
        digraph { A -> B }
        ```
        label=fig:test_diagram
        """
        file_ext = "tex"
        expected = r"""
        % rendered_images:begin
        % ```graphviz
        % digraph { A -> B }
        % ```
        % label=fig:test_diagram
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test22(self) -> None:
        """
        Check graphviz code with caption metadata in a LaTeX file.
        """
        in_lines = r"""
        ```graphviz
        digraph { A -> B }
        ```
        caption=Test diagram showing communication
        """
        file_ext = "tex"
        expected = r"""
        % rendered_images:begin
        % ```graphviz
        % digraph { A -> B }
        % ```
        % caption=Test diagram showing communication
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
          \caption{Test diagram showing communication}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test23(self) -> None:
        """
        Check graphviz code with both label and caption in a LaTeX file.
        """
        in_lines = r"""
        ```graphviz
        digraph { A -> B }
        ```
        label=fig:test_diagram
        caption=Test diagram showing communication
        """
        file_ext = "tex"
        expected = r"""
        % rendered_images:begin
        % ```graphviz
        % digraph { A -> B }
        % ```
        % label=fig:test_diagram
        % caption=Test diagram showing communication
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
          \caption{Test diagram showing communication}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test24(self) -> None:
        """
        Check that already-rendered graphviz code with metadata remains
        unchanged.
        """
        in_lines = r"""
        % rendered_images:begin
        %     ```graphviz
        %     digraph { A -> B }
        %     ```
        %     label=fig:test_diagram
        %     caption=Test diagram showing communication
        % rendered_images:end
        % render_images:begin
        \begin{figure}[H]
          \includegraphics[width=\linewidth]{figs/out.1.png}
          \caption{Test diagram showing communication}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        file_ext = "tex"
        expected = in_lines
        self.helper(in_lines, file_ext, expected)


# #############################################################################
# Test_render_images2
# #############################################################################


class Test_render_images2(hunitest.TestCase):
    def helper(self, file_name: str) -> None:
        """
        Helper function to test rendering images from a file.
        """
        # Prepare inputs.
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        dst_dir = os.path.join(self.get_scratch_space(), "figs")
        dry_run = True
        # Run test.
        out_lines = dshdreim._render_images(
            in_lines,
            out_file,
            dst_ext,
            dst_dir,
            dry_run=dry_run,
        )
        actual = "\n".join(out_lines)
        # Check outputs.
        hdbg.dassert_ne(actual, "")
        expected_file = os.path.join(self.get_output_dir(), "output.txt")
        expected = hio.from_file(expected_file)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test running on a real Markdown file with plantUML code.
        """
        file_name = "im_architecture.md"
        self.helper(file_name)

    def test2(self) -> None:
        """
        Test running on a real Markdown file with mermaid code.
        """
        file_name = "runnable_repo.md"
        self.helper(file_name)

    def test3(self) -> None:
        """
        Test running on a full LaTeX file with plantUML code.
        """
        file_name = "sample_file_plantuml.tex"
        self.helper(file_name)

    def test4(self) -> None:
        """
        Test running on a full LaTeX file with mermaid code.
        """
        file_name = "sample_file_mermaid.tex"
        self.helper(file_name)

    def test5(self) -> None:
        """
        Test running on a Markdown file with SVG code.
        """
        file_name = "sample_file_svg.md"
        self.helper(file_name)


# #############################################################################
# Test_render_images_script1
# #############################################################################


class Test_render_images_script1(hunitest.TestCase):
    """
    Light end-to-end tests for the render_images.py script.

    These tests verify the script can be invoked successfully with
    different arguments and produces expected behavior.
    """

    def _get_exec_path(self) -> str:
        return hgit.find_file_in_git_tree("render_images.py", super_module=True)

    def test1(self) -> None:
        """
        Test that the script can display help without errors.
        """
        # Prepare inputs.
        cmd = f"{self._get_exec_path()} --help"
        # Run test.
        rc = hsystem.system(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)

    def test2(self) -> None:
        """
        Test script with dry run on a simple Markdown file.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        test_file = os.path.join(scratch_space, "test_input.md")
        test_content = """
        # Test Document

        ```plantuml
        Alice -> Bob: Hello
        ```
        """
        test_content = hprint.dedent(test_content)
        hio.to_file(test_file, test_content)
        cmd = f"{self._get_exec_path()} -i {test_file} --action render --dry_run"
        # Run test.
        rc = hsystem.system(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)

    def test3(self) -> None:
        """
        Test script with default output format (png).
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        test_file = os.path.join(scratch_space, "test_input.md")
        test_content = """
        # Test Document

        ```mermaid
        graph TD
            A --> B
        ```
        """
        test_content = hprint.dedent(test_content)
        hio.to_file(test_file, test_content)
        cmd = f"{self._get_exec_path()} -i {test_file} --action render --dry_run"
        # Run test.
        rc = hsystem.system(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)

    def test4(self) -> None:
        """
        Test script with explicit --output_format png.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        test_file = os.path.join(scratch_space, "test_input.md")
        test_content = """
        # Test Document

        ```graphviz
        digraph G { A -> B; }
        ```
        """
        test_content = hprint.dedent(test_content)
        hio.to_file(test_file, test_content)
        cmd = (
            f"{self._get_exec_path()} -i {test_file} --action render "
            f"--output_format png --dry_run"
        )
        # Run test.
        rc = hsystem.system(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)

    def test5(self) -> None:
        """
        Test script with explicit --output_format svg.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        test_file = os.path.join(scratch_space, "test_input.md")
        test_content = """
        # Test Document

        ```plantuml
        Alice -> Bob: Hello
        ```
        """
        test_content = hprint.dedent(test_content)
        hio.to_file(test_file, test_content)
        cmd = (
            f"{self._get_exec_path()} -i {test_file} --action render "
            f"--output_format svg --dry_run"
        )
        # Run test.
        rc = hsystem.system(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)

    def test6(self) -> None:
        """
        Test that tikz supports png output format.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        test_file = os.path.join(scratch_space, "test_input.md")
        test_content = r"""
        # Test Document

        ```tikz
        \draw (0,0) -- (1,1);
        ```
        """
        test_content = hprint.dedent(test_content)
        hio.to_file(test_file, test_content)
        cmd = (
            f"{self._get_exec_path()} -i {test_file} --action render "
            f"--output_format png --dry_run"
        )
        # Run test.
        rc = hsystem.system(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
