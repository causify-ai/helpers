import logging
import os
import re
from typing import List

import dev_scripts_helpers.documentation.render_images as dshdreim
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_get_rendered_file_paths
# #############################################################################


class Test_get_rendered_file_paths(hunitest.TestCase):

    def test_get_rendered_file_paths1(self) -> None:
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
        figs/e.8.png"""
        self.assert_equal(act, exp)


# #############################################################################
# Test_get_render_command
# #############################################################################


class Test_get_render_command(hunitest.TestCase):

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
        exp = ""
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
        exp = ""
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
        in_lines = """
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test2(self) -> None:
        """
        Check plantUML code within other text in a Markdown file.
        """
        in_lines = """
        A
        ```plantuml
        Alice --> Bob
        ```
        B
        """
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test3(self) -> None:
        """
        Check text without image code in a Markdown file.
        """
        in_lines = """
        A
        ```bash
        Alice --> Bob
        ```
        B
        """
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test4(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a Markdown
        file.
        """
        in_lines = """
        ```plantuml
        @startuml
        Alice --> Bob
        @enduml
        ```
        """
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test5(self) -> None:
        """
        Check bare mermaid code in a Markdown file.
        """
        in_lines = """
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        """
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test6(self) -> None:
        """
        Check mermaid code within other text in a Markdown file.
        """
        in_lines = """
        A
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test7(self) -> None:
        """
        Check bare plantUML code in a LaTeX file.
        """
        in_lines = """
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test8(self) -> None:
        """
        Check plantUML code within other text in a LaTeX file.
        """
        in_lines = """
        A
        ```plantuml
        Alice --> Bob
        ```
        B
        """
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test9(self) -> None:
        """
        Check text without image code in a LaTeX file.
        """
        in_lines = """
        A
        ```bash
        Alice --> Bob
        ```
        B
        """
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test10(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a LaTeX
        file.
        """
        in_lines = """
        ```plantuml
        @startuml
        Alice --> Bob
        @enduml
        ```
        """
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test11(self) -> None:
        """
        Check bare mermaid code in a LaTeX file.
        """
        in_lines = """
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        """
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test12(self) -> None:
        """
        Check mermaid code within other text in a LaTeX file.
        """
        in_lines = """
        A
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    # ///////////////////////////////////////////////////////////////////////////

    def _update_text_and_check(self, txt: str, file_ext: str) -> None:
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
        self.check_string(act)


# #############################################################################
# Test_render_images2
# #############################################################################


class Test_render_images2(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test running on a real Markdown file with plantUML code.
        """
        # Define input variables.
        file_name = "im_architecture.md"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        run_dockerized = True
        dry_run = True
        # Call function to test.
        out_lines = dshdreim._render_images(
            in_lines=in_lines,
            out_file=out_file,
            dst_ext=dst_ext,
            run_dockerized=run_dockerized,
            dry_run=dry_run,
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

    def test2(self) -> None:
        """
        Test running on a real Markdown file with mermaid code.
        """
        # Define input variables.
        file_name = "runnable_repo.md"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        run_dockerized = True
        dry_run = True
        # Call function to test.
        out_lines = dshdreim._render_images(
            in_lines=in_lines,
            out_file=out_file,
            dst_ext=dst_ext,
            run_dockerized=run_dockerized,
            dry_run=dry_run,
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

    def test3(self) -> None:
        """
        Test running on a full LaTeX file with plantUML code.
        """
        # Define input variables.
        file_name = "sample_file_plantuml.tex"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        run_dockerized = True
        dry_run = True
        # Call function to test.
        out_lines = dshdreim._render_images(
            in_lines=in_lines,
            out_file=out_file,
            dst_ext=dst_ext,
            run_dockerized=run_dockerized,
            dry_run=dry_run,
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

    def test4(self) -> None:
        """
        Test running on a full LaTeX file with mermaid code.
        """
        # Define input variables.
        file_name = "sample_file_mermaid.tex"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        run_dockerized = True
        dry_run = True
        # Call function to test.
        out_lines = dshdreim._render_images(
            in_lines=in_lines,
            out_file=out_file,
            dst_ext=dst_ext,
            run_dockerized=run_dockerized,
            dry_run=dry_run,
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)