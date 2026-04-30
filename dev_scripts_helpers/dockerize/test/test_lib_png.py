import os

import pytest

import helpers.hdocker as hdocker
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_png as dshdlipn


# #############################################################################
# Test_build_png_container1
# #############################################################################


#@pytest.mark.slow
class Test_build_png_container1(hunitest.TestCase):
    """
    Test building the `png` container for tikz to bitmap conversion.
    """

    def test1(self) -> None:
        """
        Test that the PNG Docker container is built correctly.
        """
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        dshdlipn.build_imagemagick_container_image(
            force_rebuild=force_rebuild, use_sudo=use_sudo
        )

    def test2(self) -> None:
        """
        Test that the image conversion tools (imagemagick) version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        image_name = dshdlipn.get_imagemagick_container_image_name()
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'magick convert --version | head -1'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Check version output.
        expected = (
            'WARNING: The convert command is deprecated in IMv7, use "magick"'
            ' instead of "convert" or "magick convert"\n\n'
            "Version: ImageMagick 7.1.2-19 Q16-HDRI aarch64 23897"
            " https://imagemagick.org\n"
        )
        self.assert_equal(output, expected)


# #############################################################################
# Test_run_dockerized_tikz_to_bitmap1
# #############################################################################


#@pytest.mark.slow
class Test_run_dockerized_tikz_to_bitmap1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Run `tikz_to_bitmap` inside a Docker container.
        """
        # Prepare inputs.
        txt = r"""
        \documentclass[tikz, border=10pt]{standalone}
        \usepackage{tikz}

        \begin{document}

        \begin{tikzpicture}[scale=0.8]
            % Define the sets as circles with transparency
            \draw[thick, fill=blue!20, opacity=0.6] (0,0) circle (1.5cm);
            \node at (0,0) {$A$};

            \draw[thick, fill=red!20, opacity=0.6] (4,0) circle (1.5cm);
            \node at (4,0) {$B$};

            \draw[thick, fill=green!20, opacity=0.6] (2,3.5) circle (1.5cm);
            \node at (2,3.5) {$C$};
            % Add a title
            \node[font=\bfseries] at (2,-2.5) {Pairwise Exclusive Sets};
            \node[align=center] at (2,-3.3) {No overlap between any pair of sets};
        \end{tikzpicture}

        \end{document}
        """
        in_file_path = dshddout.create_test_file(self, txt, extension="tex")
        out_file_path = os.path.join(self.get_scratch_space(), "output.png")
        cmd_opts = ["-density 300", "-quality 10"]
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlipn.run_dockerized_tikz_to_bitmap(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, out_file_path)


# #############################################################################
# Test_run_dockerized_imagemagick1
# #############################################################################


class Test_run_dockerized_imagemagick1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Run `imagemagick` inside a Docker container.
        """
        # Prepare inputs.
        txt = r"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="40" fill="blue" />
        </svg>
        """
        in_file_path = dshddout.create_test_file(self, txt, extension="svg")
        out_file_path = os.path.join(self.get_scratch_space(), "output.png")
        cmd_opts = ["-density 300", "-quality 90"]
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        dshdlipn.run_dockerized_imagemagick(
            in_file_path,
            cmd_opts,
            out_file_path,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, out_file_path)
