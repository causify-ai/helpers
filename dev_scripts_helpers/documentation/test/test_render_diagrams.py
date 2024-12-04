import logging
import os
from typing import List

import pytest

import dev_scripts_helpers.documentation.render_diagrams as dshdredi
import helpers.hio as hio
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_get_rendered_file_paths(hunitest.TestCase):
    def test_get_rendered_file_paths1(self) -> None:
        """
        Check generation of file paths for rendering images.
        """
        out_file = "/a/b/c/d/e.md"
        diagram_idx = 8
        dst_ext = "png"
        paths = dshdredi._get_rendered_file_paths(out_file, diagram_idx, dst_ext)
        self.check_string("\n".join(paths))


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_get_render_command(hunitest.TestCase):
    def test_get_render_command1(self) -> None:
        """
        Check that the plantUML command is constructed correctly.
        """
        code_file_path = "/a/b/c"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "diagram-images/e.8.png"
        diagram_type = "plantuml"
        dst_ext = "png"
        cmd = dshdredi._get_render_command(
            code_file_path, abs_img_dir_path, rel_img_path, diagram_type, dst_ext
        )
        self.check_string(cmd)

    def test_get_render_command2(self) -> None:
        """
        Check that the error is raised if the image extension is unsupported.
        """
        code_file_path = "/a/b/c"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "diagram-images/e.8.png"
        diagram_type = "plantuml"
        dst_ext = "bmp"
        with self.assertRaises(AssertionError) as cm:
            dshdredi._get_render_command(
                code_file_path,
                abs_img_dir_path,
                rel_img_path,
                diagram_type,
                dst_ext,
            )
        # Check error text.
        self.assertIn("bmp", str(cm.exception))

    def test_get_render_command3(self) -> None:
        """
        Check that the mermaid command is constructed correctly.
        """
        code_file_path = "/a/b/c"
        abs_img_dir_path = "/d/e/f"
        rel_img_path = "diagram-images/e.8.png"
        diagram_type = "mermaid"
        dst_ext = "png"
        cmd = dshdredi._get_render_command(
            code_file_path, abs_img_dir_path, rel_img_path, diagram_type, dst_ext
        )
        self.check_string(cmd)


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_render_diagrams(hunitest.TestCase):
    """
    Test _render_diagrams() with dry run enabled (updating file text without
    creating images).
    """

    def test_render_diagrams1(self) -> None:
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

    def test_render_diagrams2(self) -> None:
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

    def test_render_diagrams3(self) -> None:
        """
        Check text without diagram code in a Markdown file.
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

    def test_render_diagrams4(self) -> None:
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

    def test_render_diagrams5(self) -> None:
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

    def test_render_diagrams6(self) -> None:
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

    def test_render_diagrams7(self) -> None:
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

    def test_render_diagrams8(self) -> None:
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

    def test_render_diagrams9(self) -> None:
        """
        Check text without diagram code in a LaTeX file.
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

    def test_render_diagrams10(self) -> None:
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

    def test_render_diagrams11(self) -> None:
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

    def test_render_diagrams12(self) -> None:
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

    def test_render_diagrams_playback1(self) -> None:
        """
        Test running on a real Markdown file with plantUML code.
        """
        # Define input variables.
        file_name = "im_architecture.md"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        dry_run = True
        # Call function to test.
        out_lines = dshdredi._render_diagrams(
            in_lines=in_lines, out_file=out_file, dst_ext=dst_ext, dry_run=dry_run
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

    def test_render_diagrams_playback2(self) -> None:
        """
        Test running on a real Markdown file with mermaid code.
        """
        # Define input variables.
        file_name = "runnable_repo.md"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        dry_run = True
        # Call function to test.
        out_lines = dshdredi._render_diagrams(
            in_lines=in_lines, out_file=out_file, dst_ext=dst_ext, dry_run=dry_run
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

    def test_render_diagrams_playback3(self) -> None:
        """
        Test running on a full LaTeX file with plantUML code.
        """
        # Define input variables.
        file_name = "sample_file_plantuml.tex"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        dry_run = True
        # Call function to test.
        out_lines = dshdredi._render_diagrams(
            in_lines=in_lines, out_file=out_file, dst_ext=dst_ext, dry_run=dry_run
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

    def test_render_diagrams_playback4(self) -> None:
        """
        Test running on a full LaTeX file with mermaid code.
        """
        # Define input variables.
        file_name = "sample_file_mermaid.tex"
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        dry_run = True
        # Call function to test.
        out_lines = dshdredi._render_diagrams(
            in_lines=in_lines, out_file=out_file, dst_ext=dst_ext, dry_run=dry_run
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
        out_lines = dshdredi._render_diagrams(
            in_lines, out_file, dst_ext, dry_run=True
        )
        self.check_string("\n".join(out_lines))
