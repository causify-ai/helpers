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
        Check with just plantUML code.
        """
        in_lines = [
            "```plantuml",
            "Alice --> Bob",
            "```",
        ]
        self._update_text_and_check(in_lines)

    def test_render_diagrams2(self) -> None:
        """
        Check with plantUML code within other text.
        """
        in_lines = [
            "A",
            "```plantuml",
            "Alice --> Bob",
            "```",
            "B",
        ]
        self._update_text_and_check(in_lines)

    def test_render_diagrams3(self) -> None:
        """
        Check without diagram code.
        """
        in_lines = [
            "A",
            "```bash",
            "Alice --> Bob",
            "```",
            "B",
        ]
        self._update_text_and_check(in_lines)

    def test_render_diagrams4(self) -> None:
        """
        Check with plantUML code that is already correctly formatted.
        """
        in_lines = [
            "```plantuml",
            "@startuml",
            "Alice --> Bob",
            "@enduml",
            "```",
        ]
        self._update_text_and_check(in_lines)

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

    def _update_text_and_check(self, in_lines: List[str]) -> None:
        """
        Check that the text is updated correctly.
        """
        out_file = os.path.join(self.get_scratch_space(), "out.md")
        dst_ext = "png"
        out_lines = dshdredi._render_diagrams(
            in_lines, out_file, dst_ext, dry_run=True
        )
        self.check_string("\n".join(out_lines))
