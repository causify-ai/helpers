import logging
import os

import pytest

import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.dockerize.dockerized_utils as dshddout
import dev_scripts_helpers.dockerize.lib_svg as dshdlisv

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_build_svg_container
# #############################################################################


class Test_build_svg_container1(hunitest.TestCase):
    """
    Test building the `svg` container.
    """

    @pytest.mark.slow
    def test1(self) -> None:
        """
        Test that the SVG Docker container is built correctly.
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        input_dir = self.get_input_dir()
        output_dir = self.get_output_dir()
        hio.create_dir(output_dir, incremental=True)
        input_file = os.path.join(input_dir, "test.svg")
        output_file = os.path.join(output_dir, "test_output.png")
        svg_code = """
        <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="40" fill="blue" />
        </svg>
        """
        hio.to_file(input_file, svg_code)
        # Run test.
        dshdlisv.run_dockerized_svg_with_rsvg_convert(
            input_file,
            output_file,
            output_format="png",
            force_rebuild=True,
            use_sudo=use_sudo,
        )
        # Check outputs.
        dshddout.assert_output_file_exists(self, output_file)


# #############################################################################
# Test_run_dockerized_svg_with_rsvg_convert1
# #############################################################################


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

    @pytest.mark.slow
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

    @pytest.mark.slow
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

    @pytest.mark.slow
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

    @pytest.mark.slow
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
