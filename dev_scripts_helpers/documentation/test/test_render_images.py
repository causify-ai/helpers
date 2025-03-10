import logging
import os
import re

import dev_scripts_helpers.documentation.render_images as dshdreim
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
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
        e.8.txt
        /a/b/c/d/figs
        figs/e.8.png
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_get_render_command1
# #############################################################################


class Test_get_render_command1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Check that the plantUML command is constructed correctly.
        """
        # Prepare inputs.
        code_file_path = "/a/b/c.txt"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "figs/e.8.png"
        dst_ext = "png"
        image_code_type = "plantuml"
        # Run function.
        cmd = dshdreim._get_render_command(
            code_file_path,
            abs_img_dir_path,
            rel_img_path,
            dst_ext,
            image_code_type,
        )
        # Check output.
        exp = r"""plantuml -t png -o /d/e/f /a/b/c.txt"""
        self.assert_equal(cmd, exp)

    def test2(self) -> None:
        """
        Check that the error is raised if the image extension is unsupported.
        """
        # Prepare inputs.
        code_file_path = "/a/b/c.txt"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "figs/e.8.png"
        dst_ext = "bmp"
        image_code_type = "plantuml"
        # Run function.
        with self.assertRaises(AssertionError) as cm:
            dshdreim._get_render_command(
                code_file_path,
                abs_img_dir_path,
                rel_img_path,
                dst_ext,
                image_code_type,
            )
        # Check error text.
        self.assertIn("bmp", str(cm.exception))

    def test3(self) -> None:
        """
        Check that the mermaid command is constructed correctly.
        """
        # Prepare inputs.
        code_file_path = "/a/b/c.txt"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "figs/e.8.png"
        image_code_type = "mermaid"
        dst_ext = "png"
        # Run function.
        cmd = dshdreim._get_render_command(
            code_file_path,
            abs_img_dir_path,
            rel_img_path,
            dst_ext,
            image_code_type,
        )
        # Check output.
        # Remove the path to the config file to stabilize the test across repos.
        cmd = re.sub(
            r"--puppeteerConfigFile [\w\.\/]+", r"--puppeteerConfigFile <>", cmd
        )
        exp = r"""mmdc --puppeteerConfigFile <> -i /a/b/c.txt -o figs/e.8.png"""
        self.assert_equal(cmd, exp)


# #############################################################################
# Test_render_images1
# #############################################################################


class Test_render_images1(hunitest.TestCase):
    """
    Test _render_images() with dry run enabled (updating file text without
    creating images).
    """

    def test1(self) -> None:
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

    def test2(self) -> None:
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

    def test3(self) -> None:
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
        exp = r"""
        A
        ```bash
        Alice --> Bob
        ```
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test4(self) -> None:
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

    def test5(self) -> None:
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

    def test6(self) -> None:
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

    def test7(self) -> None:
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

        \begin{figure}
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    def test8(self) -> None:
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

        \begin{figure}
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test9(self) -> None:
        """
        Check text without image code in a LaTeX file.
        """
        in_lines = r"""
        A
        B
        """
        file_ext = "tex"
        exp = r"""
        A
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test10(self) -> None:
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

        \begin{figure}
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    def test11(self) -> None:
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
        exp = r"""

        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```

        \begin{figure}
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    def test12(self) -> None:
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
        exp = r"""
        A

        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```

        \begin{figure}
          \includegraphics[width=\linewidth]{figs/out.1.png}
        \end{figure}
        B
        """
        self.helper(in_lines, file_ext, exp)

    # ///////////////////////////////////////////////////////////////////////////

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
            txt, out_file, dst_ext, run_dockerized=True, dry_run=True
        )
        # Check output.
        act = "\n".join(out_lines)
        hdbg.dassert_ne(act, "")
        exp = hprint.dedent(exp)
        self.assert_equal(act, exp, remove_lead_trail_empty_lines=True)


# #############################################################################
# Test_render_images2
# #############################################################################


class Test_render_images2(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test running on a real Markdown file with plantUML code.
        """
        self._test_render_images("im_architecture.md")

    def test2(self) -> None:
        """
        Test running on a real Markdown file with mermaid code.
        """
        self._test_render_images("runnable_repo.md")

    def test3(self) -> None:
        """
        Test running on a full LaTeX file with plantUML code.
        """
        self._test_render_images("sample_file_plantuml.tex")

    def test4(self) -> None:
        """
        Test running on a full LaTeX file with mermaid code.
        """
        self._test_render_images("sample_file_mermaid.tex")

    def _test_render_images(self, file_name: str) -> None:
        """
        Helper function to test rendering images from a file.
        """
        # Define input variables.
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        run_dockerized = True
        dry_run = True
        # Call function to test.
        out_lines = dshdreim._render_images(
            in_lines,
            out_file,
            dst_ext,
            run_dockerized,
            dry_run,
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)
