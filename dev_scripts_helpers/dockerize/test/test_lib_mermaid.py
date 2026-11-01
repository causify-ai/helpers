import os
import struct
from typing import Tuple

import pytest

import dev_scripts_helpers.dockerize.dockerized_utils as dshddou
import dev_scripts_helpers.dockerize.lib_mermaid as dshdlime
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

# #############################################################################
# Test_build_mermaid_container1
# #############################################################################


@pytest.mark.superslow
@pytest.mark.skipif(not hserver.is_host_mac(), reason="See CsfyTask8868")
class Test_build_mermaid_container1(hunitest.TestCase):
    """
    Test building the `mermaid` container.
    """

    @pytest.mark.order(1)
    @pytest.mark.timeout(0)
    def test1(self) -> None:
        """
        Test that the Mermaid Docker container is built correctly.
        """
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        dshdlime.build_mermaid_container_image(
            force_rebuild=force_rebuild, use_sudo=use_sudo
        )

    @pytest.mark.order(2)
    def test2(self) -> None:
        """
        Test that the Mermaid version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        image_name = dshdlime.get_mermaid_container_image_name()
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'mmdc --version'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Check version output.
        expected = "11.12.0\n"
        self.assert_equal(output, expected, purify_text=True)


# #############################################################################
# Test_run_dockerized_mermaid1
# #############################################################################


@pytest.mark.superslow
@pytest.mark.skipif(not hserver.is_host_mac(), reason="See CsfyTask8868")
class Test_run_dockerized_mermaid1(hunitest.TestCase):
    """
    Test running mermaid diagrams in a Docker container.
    """

    def helper(self, txt: str) -> None:
        """
        Test running mermaid diagram in a Docker container.

        :param txt: Mermaid diagram code
        """
        # Prepare inputs.
        in_file_path = dshddou.create_test_file(self, txt, extension="mmd")
        out_file_path = os.path.join(self.get_scratch_space(), "output.svg")
        cmd_opts = []
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlime.run_dockerized_mermaid(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )

    def test1(self) -> None:
        """Run `mermaid` flowchart with simple sequence inside a Docker
        container.
        """
        # Prepare inputs.
        txt = """
        graph TD
            A[Start] --> B[Process]
            B --> C[End]
        """
        # Run test.
        self.helper(txt)

    def test2(self) -> None:
        """Run `mermaid` flowchart with decision branches inside a Docker
        container.
        """
        # Prepare inputs.
        txt = """
        graph LR
            A[Input] --> B{Decision}
            B -->|Yes| C[Action 1]
            B -->|No| D[Action 2]
            C --> E[Output]
            D --> E
        """
        # Run test.
        self.helper(txt)


# #############################################################################
# Test_run_dockerized_mermaid2
# #############################################################################


def _get_png_size(file_path: str) -> Tuple[int, int]:
    """
    Read the (width, height) of a PNG from its IHDR header.
    """
    with open(file_path, "rb") as fd:
        header = fd.read(24)
    width, height = struct.unpack(">II", header[16:24])
    return width, height


@pytest.mark.superslow
@pytest.mark.skipif(not hserver.is_host_mac(), reason="See CsfyTask8868")
class Test_run_dockerized_mermaid2(hunitest.TestCase):
    """
    Test that the canvas size options change the size of the rendered image.
    """

    def helper(self, txt: str, out_name: str, **kwargs) -> Tuple[int, int]:
        """
        Render a mermaid diagram to PNG and return its size.

        :param txt: Mermaid diagram code
        :param out_name: name of the output PNG file
        :param kwargs: extra args for `run_dockerized_mermaid()`
        :return: (width, height) of the PNG in pixels
        """
        in_file_path = dshddou.create_test_file(self, txt, extension="mmd")
        out_file_path = os.path.join(self.get_scratch_space(), f"{out_name}.png")
        use_sudo = hdocker.get_use_sudo()
        dshdlime.run_dockerized_mermaid(
            in_file_path,
            [],
            out_file_path,
            force_rebuild=False,
            use_sudo=use_sudo,
            **kwargs,
        )
        self.assertTrue(os.path.exists(out_file_path))
        return _get_png_size(out_file_path)

    def test1(self) -> None:
        """
        Check that `width` resizes a flowchart.
        """
        # Prepare inputs.
        txt = """
        flowchart LR
            A[Start] --> B[One] --> C[Two] --> D[Three] --> E[Four] --> F[End]
        """
        # Run test.
        small = self.helper(txt, "small", width=400)
        large = self.helper(txt, "large", width=2400)
        # Check outputs.
        self.assertLess(small[0], large[0])

    def test2(self) -> None:
        """
        Check that `width` lays out a C4 diagram in fewer rows.
        """
        # Prepare inputs.
        txt = """
        C4Context
          Person(user, "Quant researcher", "Gives a list of papers")
          System(sys, "Estimate Paper Quality pipeline", "Resolves, downloads, converts")
          System_Ext(bib, "Bibliographic APIs", "Semantic Scholar, Crossref, arXiv")
          System_Ext(sites, "Paper hosts", "arXiv, SSRN, publisher sites")
          System_Ext(llm, "LLM provider", "OpenAI or OpenRouter")
          Rel(user, sys, "Runs", "CLI")
          Rel(sys, bib, "Looks up metadata", "HTTPS")
          Rel(sys, sites, "Downloads PDFs", "HTTPS")
          Rel(sys, llm, "Extracts features", "HTTPS")
        """
        # Run test.
        default = self.helper(txt, "default")
        wide = self.helper(txt, "wide", width=2400)
        # Check outputs.
        self.assertGreater(wide[0], default[0])
        self.assertLess(wide[1], default[1])

    def test3(self) -> None:
        """
        Check that a Mermaid config file resizes a C4 diagram.
        """
        # Prepare inputs.
        txt = """
        C4Context
          Person(user, "Quant researcher", "Gives a list of papers")
          System(sys, "Estimate Paper Quality pipeline", "Resolves, downloads, converts")
          System_Ext(bib, "Bibliographic APIs", "Semantic Scholar, Crossref, arXiv")
          System_Ext(sites, "Paper hosts", "arXiv, SSRN, publisher sites")
          System_Ext(llm, "LLM provider", "OpenAI or OpenRouter")
          Rel(user, sys, "Runs", "CLI")
          Rel(sys, bib, "Looks up metadata", "HTTPS")
          Rel(sys, sites, "Downloads PDFs", "HTTPS")
          Rel(sys, llm, "Extracts features", "HTTPS")
        """
        config_file_path = os.path.join(self.get_scratch_space(), "cfg.json")
        hio.to_file(config_file_path, '{"c4": {"width": 400, "height": 120}}')
        # Run test.
        default = self.helper(txt, "default")
        resized = self.helper(txt, "resized", config_file_path=config_file_path)
        # Check outputs.
        self.assertNotEqual(default, resized)
