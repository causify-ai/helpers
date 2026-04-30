import os

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.lib_svg as dshdlisv


# #############################################################################
# Test_build_svg_container1
# #############################################################################


#@pytest.mark.slow
class Test_build_svg_container1(hunitest.TestCase):
    """
    Test building the `svg` container.
    """

    def test1(self) -> None:
        """
        Test that the SVG Docker container is built correctly.
        """
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        dshdlisv.build_svg_rsvg_convert_container_image(
            force_rebuild=force_rebuild, use_sudo=use_sudo
        )

    def test2(self) -> None:
        """
        Test that the SVG conversion tools (rsvg-convert) version matches expected output.
        """
        use_sudo = hdocker.get_use_sudo()
        docker_executable = hdocker.get_docker_executable(use_sudo)
        # Build the container.
        image_name = dshdlisv.get_svg_rsvg_convert_container_image_name()
        # Run version command inside container.
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'rsvg-convert --version 2>&1 | head -1'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Check version output.
        expected = "rsvg-convert version 2.52.5\n"
        self.assert_equal(output, expected)


# #############################################################################
# Test_run_dockerized_svg_with_rsvg_convert1
# #############################################################################


#@pytest.mark.slow
class Test_run_dockerized_svg_with_rsvg_convert1(hunitest.TestCase):
    """
    Test SVG conversion using rsvg-convert.
    """

    def _run_svg_conversion(
        self, svg_code: str, out_filename: str, output_format: str
    ) -> None:
        in_file = os.path.join(self.get_scratch_space(), "test.svg")
        out_file = os.path.join(self.get_scratch_space(), out_filename)
        hio.to_file(in_file, svg_code)
        # Run conversion.
        use_sudo = hdocker.get_use_sudo()
        dshdlisv.run_dockerized_svg_with_rsvg_convert(
            in_file,
            out_file,
            output_format=output_format,
            force_rebuild=False,
            use_sudo=use_sudo,
        )
        # Check that output file was created.
        self.assertTrue(os.path.exists(out_file))

    def test_svg_to_png(self) -> None:
        """
        Test converting SVG to PNG using rsvg-convert.
        """
        svg_code = r"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="40" fill="blue" />
        </svg>
        """
        out_filename = "test_png.png"
        output_format = "png"
        self._run_svg_conversion(svg_code, out_filename, output_format)

    def test_svg_to_pdf(self) -> None:
        """
        Test converting SVG to PDF using rsvg-convert.
        """
        svg_code = r"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <rect x="10" y="10" width="80" height="80" fill="red" />
        </svg>
        """
        out_filename = "test_pdf.pdf"
        output_format = "pdf"
        self._run_svg_conversion(svg_code, out_filename, output_format)


# #############################################################################
# Test_run_dockerized_svg_with_inkscape1
# #############################################################################


#@pytest.mark.slow
class Test_run_dockerized_svg_with_inkscape1(hunitest.TestCase):
    """
    Test SVG conversion using inkscape.
    """

    def _run_svg_conversion(
        self, svg_code: str, out_filename: str, output_format: str
    ) -> None:
        in_file = os.path.join(self.get_scratch_space(), "test.svg")
        out_file = os.path.join(self.get_scratch_space(), out_filename)
        hio.to_file(in_file, svg_code)
        # Run conversion.
        use_sudo = hdocker.get_use_sudo()
        dshdlisv.run_dockerized_svg_with_inkscape(
            in_file,
            out_file,
            output_format=output_format,
            force_rebuild=False,
            use_sudo=use_sudo,
        )
        # Check that output file was created.
        self.assertTrue(os.path.exists(out_file))

    def test_svg_to_png(self) -> None:
        """
        Test converting SVG to PNG using inkscape.
        """
        svg_code = r"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="40" fill="green" />
        </svg>
        """
        out_filename = "test_inkscape.png"
        output_format = "png"
        self._run_svg_conversion(svg_code, out_filename, output_format)

    def test_svg_to_pdf(self) -> None:
        """
        Test converting SVG to PDF using inkscape.
        """
        svg_code = r"""
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <polygon points="50,10 90,90 10,90" fill="yellow" stroke="black"/>
        </svg>
        """
        out_filename = "test_inkscape.pdf"
        output_format = "pdf"
        self._run_svg_conversion(svg_code, out_filename, output_format)
