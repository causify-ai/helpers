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
        use_github_hosting = False
        # Run function.
        paths = dshdreim._get_rendered_file_paths(
            out_file, image_code_idx, dst_ext, use_github_hosting
        )
        # Check output.
        actual = "\n".join(paths)
        expected = """
        tmp.render_images/e.8.txt
        /a/b/c/d/figs
        figs/e.8.png
        """
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Check generation of file paths for GitHub absolute reference.
        """
        # Prepare inputs.
        out_file = "/a/b/c/d/e.md"
        image_code_idx = 8
        dst_ext = "png"
        use_github_hosting = True
        # Run function.
        paths = dshdreim._get_rendered_file_paths(
            out_file, image_code_idx, dst_ext, use_github_hosting
        )
        # Check output.
        actual = "\n".join(paths)
        repo_name = hgit.get_repo_full_name_from_client(super_module=True)
        expected = f"""
        tmp.render_images/e.8.txt
        /a/b/c/d/figs
        https://raw.githubusercontent.com/{repo_name}/master/figs/e.8.png
        """
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

    def test_md1(self) -> None:
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

    def test_md2(self) -> None:
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

    def test_md4(self) -> None:
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

    def test_md5(self) -> None:
        """
        Test with empty input.
        """
        in_text = """
        """
        extension = ".md"
        expected = """
        """
        self.helper(in_text, extension, expected)

    def test_md6(self) -> None:
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

    def test_tex1(self) -> None:
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

    def test_tex2(self) -> None:
        """
        Test with both rendered_images and render_images markers (LaTeX extension).
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

    def test_tex3(self) -> None:
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

    def test_tex4(self) -> None:
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

    def test_tex5(self) -> None:
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

@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_render_image_code1(hunitest.TestCase):
    """
    Test `_render_image_code()`.
    """

    def test_md1(self) -> None:
        """
        Check rendering of an image code in a Markdown file.
        """
        # Prepare inputs.
        image_code = "digraph { A -> B }"
        image_code_idx = 1
        image_code_type = "graphviz"
        template_out_file = os.path.join(self.get_scratch_space(), "test.md")
        dst_ext = "png"
        # Run function.
        rel_img_path = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test.1.png")

    def test_md2(self) -> None:
        """
        Check rendering of an image code in a Markdown file with a different
        image code type.
        """
        # Prepare inputs.
        image_code = """
        graph TD
            B --> A
        """
        image_code_idx = 1
        image_code_type = "mermaid"
        template_out_file = os.path.join(self.get_scratch_space(), "test.md")
        dst_ext = "png"
        # Run function.
        rel_img_path = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test.1.png")

    def test_md3(self) -> None:
        """
        Check rendering of an image code in a Markdown file with a different
        output file and extension.
        """
        # Prepare inputs.
        image_code = "digraph { A -> B }"
        image_code_idx = 1
        image_code_type = "graphviz"
        template_out_file = os.path.join(self.get_scratch_space(), "test2.md")
        dst_ext = "svg"
        # Run function.
        rel_img_path = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test2.1.svg")



# #############################################################################
# Test_insert_image_code1
# #############################################################################

class Test_insert_image_code1(hunitest.TestCase):
    """
    Test _insert_image_code() for markdown files.
    """

    def test_md1(self) -> None:
        """
        Test markdown output without label or caption.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = ""
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = """
        [//]: # ( render_images:begin )
        ![](figs/test.1.png)
        [//]: # ( render_images:end )
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test_md2(self) -> None:
        """
        Test markdown output with label only.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = ""
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = """
        [//]: # ( render_images:begin )
        ![](figs/test.1.png){#fig:test_diagram}
        [//]: # ( render_images:end )
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test_md3(self) -> None:
        """
        Test markdown output with caption only.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = "Test diagram caption"
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = """
        [//]: # ( render_images:begin )
        ![Test diagram caption](figs/test.1.png)
        [//]: # ( render_images:end )
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test_md4(self) -> None:
        """
        Test markdown output with both label and caption.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = "Test diagram caption"
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = """
        [//]: # ( render_images:begin )
        ![Test diagram caption](figs/test.1.png){#fig:test_diagram}
        [//]: # ( render_images:end )
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test_md5(self) -> None:
        """
        Test markdown output with user-specified size.
        """
        # Prepare inputs.
        extension = ".md"
        rel_img_path = "figs/test.1.png"
        user_img_size = "height=100%"
        label = "fig:test_diagram"
        caption = "Test diagram"
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = """
        [//]: # ( render_images:begin )
        ![Test diagram](figs/test.1.png){#fig:test_diagram height=100%}
        [//]: # ( render_images:end )
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)



# #############################################################################
# Test_insert_image_code2
# #############################################################################

class Test_insert_image_code2(hunitest.TestCase):
    """
    Test _insert_image_code() for LaTeX files.
    """

    def test_tex1(self) -> None:
        """
        Test LaTeX output without label or caption.
        """
        # Prepare inputs.
        extension = ".tex"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = ""
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = r"""
        % render_images:begin
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/test.1.png}
        \end{figure}
        % render_images:end
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test_tex2(self) -> None:
        """
        Test LaTeX output with label only.
        """
        # Prepare inputs.
        extension = ".tex"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = ""
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = r"""
        % render_images:begin
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/test.1.png}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test_tex3(self) -> None:
        """
        Test LaTeX output with caption only.
        """
        # Prepare inputs.
        extension = ".tex"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = ""
        caption = "Test diagram caption"
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = r"""
        % render_images:begin
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/test.1.png}
          \caption{Test diagram caption}
        \end{figure}
        % render_images:end
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)

    def test_tex4(self) -> None:
        """
        Test LaTeX output with both label and caption.
        """
        # Prepare inputs.
        extension = ".tex"
        rel_img_path = "figs/test.1.png"
        user_img_size = ""
        label = "fig:test_diagram"
        caption = "Test diagram caption"
        # Run.
        actual = dshdreim._insert_image_code(
            extension, rel_img_path, user_img_size, label=label, caption=caption
        )
        # Check output.
        expected = r"""
        % render_images:begin
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/test.1.png}
          \caption{Test diagram caption}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.assert_equal(actual, expected, dedent=True, fuzzy_match=True)



# #############################################################################
# Test_render_images1
# #############################################################################

@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
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
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True).split("\n")
        out_file = os.path.join(self.get_scratch_space(), f"out.{file_ext}")
        dst_ext = "png"
        # Render images.
        out_lines = dshdreim._render_images(
            txt,
            out_file,
            dst_ext,
            dry_run=True,
        )
        # Check output.
        actual = "\n".join(out_lines)
        hdbg.dassert_ne(actual, "")
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected, remove_lead_trail_empty_lines=True)

    # ///////////////////////////////////////////////////////////////////////////

    def test_tex1(self) -> None:
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

    def test_md1(self) -> None:
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

    def test_md_plantuml1(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```plantuml )
        [//]: # ( Alice --> Bob )
        [//]: # ( ``` )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![](figs/out.1.png)
        [//]: # ( render_images:end )
        """
        self.helper(in_lines, file_ext, expected)

    def test_md_plantuml2(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```plantuml )
        [//]: # ( Alice --> Bob )
        [//]: # ( ``` )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![](figs/out.1.png)
        [//]: # ( render_images:end )
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test_md_plantuml3(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```plantuml )
        [//]: # ( @startuml )
        [//]: # ( Alice --> Bob )
        [//]: # ( @enduml )
        [//]: # ( ``` )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![](figs/out.1.png)
        [//]: # ( render_images:end )
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_plantuml1(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_plantuml2(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_plantuml3(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    # ///////////////////////////////////////////////////////////////////////////

    def test_md_mermaid1(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```mermaid )
        [//]: # ( flowchart TD; )
        [//]: # (   A[Start] --> B[End]; )
        [//]: # ( ``` )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![](figs/out.1.png)
        [//]: # ( render_images:end )
        """
        self.helper(in_lines, file_ext, expected)

    def test_md_mermaid2(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```mermaid )
        [//]: # ( flowchart TD; )
        [//]: # (   A[Start] --> B[End]; )
        [//]: # ( ``` )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![](figs/out.1.png)
        [//]: # ( render_images:end )
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_mermaid1(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_mermaid2(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        % render_images:end
        B
        """
        self.helper(in_lines, file_ext, expected)

    def test_txt_mermaid1(self) -> None:
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

    def test_txt_mermaid2(self) -> None:
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

    def test_txt_mermaid3(self) -> None:
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

    def test_md_graphviz_with_metadata1(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```graphviz )
        [//]: # ( digraph { A -> B } )
        [//]: # ( ``` )
        [//]: # ( label=fig:test_diagram )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![](figs/out.1.png){#fig:test_diagram}
        [//]: # ( render_images:end )
        """
        self.helper(in_lines, file_ext, expected)

    def test_md_graphviz_with_metadata2(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```graphviz )
        [//]: # ( digraph { A -> B } )
        [//]: # ( ``` )
        [//]: # ( caption=Test diagram showing communication )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![Test diagram showing communication](figs/out.1.png)
        [//]: # ( render_images:end )
        """
        self.helper(in_lines, file_ext, expected)

    def test_md_graphviz_with_metadata3(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```graphviz )
        [//]: # ( digraph { A -> B } )
        [//]: # ( ``` )
        [//]: # ( label=fig:test_diagram )
        [//]: # ( caption=Test diagram showing communication )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![Test diagram showing communication](figs/out.1.png){#fig:test_diagram}
        [//]: # ( render_images:end )
        """
        self.helper(in_lines, file_ext, expected)

    def test_md_graphviz_with_metadata4(self) -> None:
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
        [//]: # ( rendered_images:begin )
        [//]: # ( ```graphviz )
        [//]: # ( digraph { A -> B } )
        [//]: # ( ``` )
        [//]: # ( label=fig:test_diagram )
        [//]: # ( caption=This is a caption )
        [//]: # (   that spans multiple lines )
        [//]: # (   to test continuation )
        [//]: # ( rendered_images:end )
        [//]: # ( render_images:begin )
        ![This is a caption that spans multiple lines to test continuation](figs/out.1.png){#fig:test_diagram}
        [//]: # ( render_images:end )
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_graphviz_with_metadata1(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_graphviz_with_metadata2(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
          \caption{Test diagram showing communication}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_graphviz_with_metadata3(self) -> None:
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
        \begin{figure}[!ht]
          \includegraphics[width=\linewidth]{figs/out.1.png}
          \caption{Test diagram showing communication}
          \label{fig:test_diagram}
        \end{figure}
        % render_images:end
        """
        self.helper(in_lines, file_ext, expected)

    def test_tex_graphviz_with_metadata4(self) -> None:
        """
        Check that already-rendered graphviz code with metadata remains unchanged.
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
        \begin{figure}[!ht]
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

@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
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
        dry_run = True
        # Run function.
        out_lines = dshdreim._render_images(
            in_lines,
            out_file,
            dst_ext,
            dry_run=dry_run,
        )
        actual = "\n".join(out_lines)
        # Check output.
        self.check_string(actual)

    def test1(self) -> None:
        """
        Test running on a real Markdown file with plantUML code.
        """
        self.helper("im_architecture.md")

    def test2(self) -> None:
        """
        Test running on a real Markdown file with mermaid code.
        """
        self.helper("runnable_repo.md")

    def test3(self) -> None:
        """
        Test running on a full LaTeX file with plantUML code.
        """
        self.helper("sample_file_plantuml.tex")

    def test4(self) -> None:
        """
        Test running on a full LaTeX file with mermaid code.
        """
        self.helper("sample_file_mermaid.tex")



# #############################################################################
# Test_render_images_script1
# #############################################################################

class Test_render_images_script1(hunitest.TestCase):
    """
    Light end-to-end tests for the render_images.py script.

    These tests verify the script can be invoked successfully with different
    arguments and produces expected behavior.
    """

    def test_script_help(self) -> None:
        """
        Test that the script can display help without errors.
        """
        # Run the script with --help.
        exec_path = hgit.find_file_in_git_tree(
            "render_images.py", super_module=True
        )
        cmd = f"{exec_path} --help"
        rc = hsystem.system(cmd)
        # Check that it succeeded.
        self.assertEqual(rc, 0)

    def test_script_dry_run_md(self) -> None:
        """
        Test script with dry run on a simple Markdown file.
        """
        # Create a test file in scratch space.
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
        # Run the script with dry_run.
        exec_path = hgit.find_file_in_git_tree(
            "render_images.py", super_module=True
        )
        cmd = f"{exec_path} -i {test_file} --action render --dry_run"
        rc = hsystem.system(cmd)
        # Check that it succeeded.
        self.assertEqual(rc, 0)
