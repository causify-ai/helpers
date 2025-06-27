import logging
import os

import pytest

import dev_scripts_helpers.documentation.render_images as dshdreim
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
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
        # Run function.
        paths = dshdreim._get_rendered_file_paths(
            out_file, image_code_idx, dst_ext
        )
        # Check output.
        act = "\n".join(paths)
        exp = """
        tmp.render_images/e.8.txt
        /a/b/c/d/figs
        figs/e.8.png
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_render_image_code1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_render_image_code1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Check rendering of an image code in a Markdown file.
        """
        # Prepare inputs.
        image_code = "digraph { A -> B }"
        image_code_idx = 1
        image_code_type = "graphviz"
        template_out_file = os.path.join(self.get_scratch_space(), "test.md")
        dst_ext = "png"
        use_cache = True
        # Run function.
        rel_img_path = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
            use_cache=use_cache,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test.1.png")

    def test2(self) -> None:
        """
        Check rendering of an image code in a Markdown file with a different
        image code type.
        """
        # Prepare inputs.
        image_code = "digraph { B -> A }"
        image_code_idx = 1
        image_code_type = "mermaid"
        template_out_file = os.path.join(self.get_scratch_space(), "test.md")
        dst_ext = "png"
        use_cache = True
        # Run function.
        rel_img_path = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
            use_cache=use_cache,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test.1.png")

    def test3(self) -> None:
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
        use_cache = False
        # Run function.
        rel_img_path = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
            use_cache=use_cache,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test2.1.svg")


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

    def helper(self, txt: str, file_ext: str, exp: str) -> None:
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
        act = "\n".join(out_lines)
        hdbg.dassert_ne(act, "")
        exp = hprint.dedent(exp)
        self.assert_equal(act, exp, remove_lead_trail_empty_lines=True)

    # ///////////////////////////////////////////////////////////////////////////

    def test1(self) -> None:
        """
        Check text without image code in a LaTeX file.
        """
        in_lines = r"""
        A
        B
        """
        file_ext = "tex"
        exp = in_lines
        self.helper(in_lines, file_ext, exp)

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
        exp = in_lines
        self.helper(in_lines, file_ext, exp)

    # ///////////////////////////////////////////////////////////////////////////

    def test_plantuml1(self) -> None:
        """
        Check bare plantUML code in a Markdown file.
        """
        in_lines = r"""
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "md"
        exp = r"""
        [//]: # ( ```plantuml)
        [//]: # ( Alice --> Bob)
        [//]: # ( ```)
        ![](figs/out.1.png)
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml2(self) -> None:
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
        exp = r"""
        A
        [//]: # ( ```plantuml)
        [//]: # ( Alice --> Bob)
        [//]: # ( ```)
        ![](figs/out.1.png)
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml3(self) -> None:
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
        exp = r"""
        [//]: # ( ```plantuml)
        [//]: # ( @startuml)
        [//]: # ( Alice --> Bob)
        [//]: # ( @enduml)
        [//]: # ( ```)
        ![](figs/out.1.png)
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml4(self) -> None:
        """
        Check bare plantUML code in a LaTeX file.
        """
        in_lines = r"""
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "tex"
        exp = r"""
        % ```plantuml
        % Alice --> Bob
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml5(self) -> None:
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
        exp = r"""
        A
        % ```plantuml
        % Alice --> Bob
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml6(self) -> None:
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
        exp = r"""
        % ```plantuml
        % @startuml
        % Alice --> Bob
        % @enduml
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    # ///////////////////////////////////////////////////////////////////////////

    def test_mermaid1(self) -> None:
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
        exp = r"""
        [//]: # ( ```mermaid)
        [//]: # ( flowchart TD;)
        [//]: # (   A[Start] --> B[End];)
        [//]: # ( ```)
        ![](figs/out.1.png)
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid2(self) -> None:
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
        exp = r"""
        A
        [//]: # ( ```mermaid)
        [//]: # ( flowchart TD;)
        [//]: # (   A[Start] --> B[End];)
        [//]: # ( ```)
        ![](figs/out.1.png)
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid3(self) -> None:
        """
        Check bare mermaid code in a LaTeX file.
        """
        in_lines = r"""
        """
        file_ext = "tex"
        exp = r"""

        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid4(self) -> None:
        """
        Check mermaid code within other text in a LaTeX file.
        """
        in_lines = r"""
        A
        B
        """
        file_ext = "tex"
        exp = r"""
        A
        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid5(self) -> None:
        """
        Check mermaid code within other text in a md file.
        """
        in_lines = r"""
        A



        B
        """
        file_ext = "txt"
        exp = r"""
        A

        // ```mermaid
        // flowchart TD;
        //   A[Start] --> B[End];
        // ```
        ![](figs/out.1.png)


        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid6(self) -> None:
        """
        Check mermaid code within other text in a md file.
        """
        in_lines = r"""
        A

        B
        """
        file_ext = "txt"
        exp = r"""
        A
        // ```mermaid(hello_world.png)
        // flowchart TD;
        //   A[Start] --> B[End];
        // ```
        ![](hello_world.png)

        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid7(self) -> None:
        """
        Check commented mermaid code with an updated output file.
        """
        in_lines = r"""
        A
        // ```mermaid(hello_world2.png)
        // flowchart TD;
        // ```
        ![](hello_world.png)
        B
        """
        file_ext = "txt"
        exp = r"""
        A
        // ```mermaid(hello_world2.png)
        // flowchart TD;
        // ```
        ![](hello_world2.png)
        B
        """
        self.helper(in_lines, file_ext, exp)


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
        # Define input variables.
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        dry_run = True
        # Call function to test.
        out_lines = dshdreim._render_images(
            in_lines,
            out_file,
            dst_ext,
            dry_run=dry_run,
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

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
