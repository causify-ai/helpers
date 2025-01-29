import logging
import os
import re
from typing import List

import dev_scripts_helpers.documentation.render_images as dshdreim
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


# #############################################################################
# Test_get_rendered_file_paths
# #############################################################################


class Test_get_rendered_file_paths(hunitest.TestCase):

    def test_get_rendered_file_paths1(self) -> None:
        """
        Check generation of file paths for rendering images.
        """
        out_file = "/a/b/c/d/e.md"
        image_code_idx = 8
        dst_ext = "png"
        paths = dshdreim._get_rendered_file_paths(
            out_file, image_code_idx, dst_ext
        )
        self.check_string("\n".join(paths))


# #############################################################################
# Test_get_render_command
# #############################################################################


class Test_get_render_command(hunitest.TestCase):

    def test_get_render_command1(self) -> None:
        """
        Check that the plantUML command is constructed correctly.
        """
        code_file_path = "/a/b/c.txt"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "figs/e.8.png"
        dst_ext = "png"
        image_code_type = "plantuml"
        cmd = dshdreim._get_render_command(
            code_file_path,
            abs_img_dir_path,
            rel_img_path,
            dst_ext,
            image_code_type,
        )
        self.check_string(cmd)

    def test_get_render_command2(self) -> None:
        """
        Check that the error is raised if the image extension is unsupported.
        """
        code_file_path = "/a/b/c.txt"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "figs/e.8.png"
        dst_ext = "bmp"
        image_code_type = "plantuml"
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

    def test_get_render_command3(self) -> None:
        """
        Check that the mermaid command is constructed correctly.
        """
        code_file_path = "/a/b/c.txt"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "figs/e.8.png"
        image_code_type = "mermaid"
        dst_ext = "png"
        cmd = dshdreim._get_render_command(
            code_file_path,
            abs_img_dir_path,
            rel_img_path,
            dst_ext,
            image_code_type,
        )
        # Remove the path to the config file to stabilize the test across repos.
        cmd = re.sub(
            r"--puppeteerConfigFile [\w\.\/]+", r"--puppeteerConfigFile <>", cmd
        )
        self.check_string(cmd)


# #############################################################################
# Test_render_images
# #############################################################################


class Test_render_images(hunitest.TestCase):
    """
    Test _render_images() with dry run enabled (updating file text without
    creating images).
    """

    def test_render_images1(self) -> None:
        """
        Check bare plantUML code in a Markdown file.
        """
        in_lines = [
            "```plantuml",
            "Alice --> Bob",
            "```",
        ]
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images2(self) -> None:
        """
        Check plantUML code within other text in a Markdown file.
        """
        in_lines = [
            "A",
            "```plantuml",
            "Alice --> Bob",
            "```",
            "B",
        ]
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images3(self) -> None:
        """
        Check text without image code in a Markdown file.
        """
        in_lines = [
            "A",
            "```bash",
            "Alice --> Bob",
            "```",
            "B",
        ]
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images4(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a Markdown
        file.
        """
        in_lines = [
            "```plantuml",
            "@startuml",
            "Alice --> Bob",
            "@enduml",
            "```",
        ]
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images5(self) -> None:
        """
        Check bare mermaid code in a Markdown file.
        """
        in_lines = [
            "```mermaid",
            "flowchart TD;",
            "  A[Start] --> B[End];",
            "```",
        ]
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images6(self) -> None:
        """
        Check mermaid code within other text in a Markdown file.
        """
        in_lines = [
            "A",
            "```mermaid",
            "flowchart TD;",
            "  A[Start] --> B[End];",
            "```",
            "B",
        ]
        file_ext = "md"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images7(self) -> None:
        """
        Check bare plantUML code in a LaTeX file.
        """
        in_lines = [
            "```plantuml",
            "Alice --> Bob",
            "```",
        ]
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images8(self) -> None:
        """
        Check plantUML code within other text in a LaTeX file.
        """
        in_lines = [
            "A",
            "```plantuml",
            "Alice --> Bob",
            "```",
            "B",
        ]
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images9(self) -> None:
        """
        Check text without image code in a LaTeX file.
        """
        in_lines = [
            "A",
            "```bash",
            "Alice --> Bob",
            "```",
            "B",
        ]
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images10(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a LaTeX
        file.
        """
        in_lines = [
            "```plantuml",
            "@startuml",
            "Alice --> Bob",
            "@enduml",
            "```",
        ]
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images11(self) -> None:
        """
        Check bare mermaid code in a LaTeX file.
        """
        in_lines = [
            "```mermaid",
            "flowchart TD;",
            "  A[Start] --> B[End];",
            "```",
        ]
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images12(self) -> None:
        """
        Check mermaid code within other text in a LaTeX file.
        """
        in_lines = [
            "A",
            "```mermaid",
            "flowchart TD;",
            "  A[Start] --> B[End];",
            "```",
            "B",
        ]
        file_ext = "tex"
        self._update_text_and_check(in_lines, file_ext)

    def test_render_images_playback1(self) -> None:
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

    def test_render_images_playback2(self) -> None:
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

    def test_render_images_playback3(self) -> None:
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

    def test_render_images_playback4(self) -> None:
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

    def _update_text_and_check(self, in_lines: List[str], file_ext: str) -> None:
        """
        Check that the text is updated correctly.

        :param in_lines: the lines of the input file
        :param file_ext: the extension of the input file
        """
        out_file = os.path.join(self.get_scratch_space(), f"out.{file_ext}")
        dst_ext = "png"
        out_lines = dshdreim._render_images(
            in_lines, out_file, dst_ext, run_dockerized=True, dry_run=True
        )
        self.check_string("\n".join(out_lines))
