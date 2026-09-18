import logging
import os
from typing import Any, List, Tuple
from unittest import mock

import dev_scripts_helpers.documentation.compress_pdf as dshdcpd
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_compress_pdf_py
# #############################################################################


class Test_compress_pdf_py(hunitest.TestCase):
    """
    End-to-end tests for the `compress_pdf.py` executable.
    """

    def _run_main(self, argv: List[str]) -> None:
        """
        Run `dshdcpd._main()` with a mocked `sys.argv`.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        """
        parser = dshdcpd._parse()
        with mock.patch("sys.argv", argv):
            dshdcpd._main(parser)

    def _check_output(self, output_file: str, expected_content: str) -> None:
        """
        Check that `output_file` contains `expected_content`.

        :param output_file: path to the file to check
        :param expected_content: expected file content
        """
        # Check outputs.
        actual_content = hio.from_file(output_file)
        self.assert_equal(actual_content, expected_content)

    def test1(self) -> None:
        """
        Test compressing a PDF in place through the CLI with the
        `ghostscript_global` backend (the default).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "lecture.pdf")
        hio.to_file(input_file, "original content")
        gs_binary = "/usr/bin/gs"
        # Prepare outputs.
        expected_content = "compressed content"

        def _fake_gs_system(cmd: str) -> int:
            _ = cmd
            # Simulate `gs` writing the compressed file to the temporary
            # output path.
            tmp_output_file = input_file + ".compressed.tmp"
            hio.to_file(tmp_output_file, expected_content)
            return 0

        argv = ["compress_pdf.py", "--input", input_file]
        # Run test.
        with (
            mock.patch.object(
                dshdcpd, "_find_gs_binary", return_value=gs_binary
            ),
            mock.patch.object(
                dshdcpd.hsystem, "system", side_effect=_fake_gs_system
            ),
        ):
            self._run_main(argv)
        # Check outputs.
        self._check_output(input_file, expected_content)

    def test2(self) -> None:
        """
        Test compressing a PDF in place through the CLI with the
        `ghostscript_dockerized` backend.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "lecture.pdf")
        hio.to_file(input_file, "original content")
        # Prepare outputs.
        expected_content = "compressed content"

        def _fake_build_and_run_docker_cmd(*args: Any, **kwargs: Any) -> str:
            _ = args, kwargs
            # Simulate `gs` writing the compressed file to the temporary
            # output path.
            tmp_output_file = input_file + ".compressed.tmp"
            hio.to_file(tmp_output_file, expected_content)
            return ""

        argv = [
            "compress_pdf.py",
            "--input",
            input_file,
            "--backend",
            "ghostscript_dockerized",
        ]
        # Run test.
        with mock.patch.object(
            dshdcpd.hdocker,
            "build_and_run_docker_cmd",
            side_effect=_fake_build_and_run_docker_cmd,
        ):
            self._run_main(argv)
        # Check outputs.
        self._check_output(input_file, expected_content)

    def test3(self) -> None:
        """
        Test compressing a PDF in place through the CLI with a non-default
        `--quality` value.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "lecture.pdf")
        hio.to_file(input_file, "original content")
        gs_binary = "/usr/bin/gs"
        quality = "/screen"
        tmp_output_file = input_file + ".compressed.tmp"
        # Prepare outputs.
        expected_cmd = (
            f"{gs_binary} -sDEVICE=pdfwrite -dPDFSETTINGS={quality} "
            f"-dCompatibilityLevel=1.4 -dColorConversionStrategy=/sRGB "
            f"-dProcessColorModel=/DeviceRGB -dNOPAUSE -dQUIET -dBATCH "
            f"-sOutputFile={tmp_output_file} {input_file}"
        )
        expected_str = hprint.dedent(
            f"""
            [
                {{
                'function': hsystem.system,
                'args': ('{expected_cmd}',),
                'kwargs': {{}},
                }},
            ]
            """
        )
        expected_content = "compressed content"
        argv = [
            "compress_pdf.py",
            "--input",
            input_file,
            "--quality",
            quality,
        ]
        # Run test.
        with (
            mock.patch.object(
                dshdcpd, "_find_gs_binary", return_value=gs_binary
            ),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            # `gs` itself is mocked out, so create the compressed file it
            # would have produced.
            hio.to_file(tmp_output_file, expected_content)
            self._run_main(argv)
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)
        self._check_output(input_file, expected_content)

    def test4(self) -> None:
        """
        Test compressing a PDF to a different output file through the CLI
        (not in-place).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "lecture.pdf")
        hio.to_file(input_file, "original content")
        gs_binary = "/usr/bin/gs"
        output_file = os.path.join(scratch_dir, "lecture.compressed.pdf")
        # Prepare outputs.
        expected_content = "compressed content"

        def _fake_gs_system(cmd: str) -> int:
            _ = cmd
            # Simulate `gs` writing the compressed file to the temporary
            # output path.
            tmp_output_file = output_file + ".compressed.tmp"
            hio.to_file(tmp_output_file, expected_content)
            return 0

        argv = [
            "compress_pdf.py",
            "--input",
            input_file,
            "--output",
            output_file,
        ]
        # Run test.
        with (
            mock.patch.object(
                dshdcpd, "_find_gs_binary", return_value=gs_binary
            ),
            mock.patch.object(
                dshdcpd.hsystem, "system", side_effect=_fake_gs_system
            ),
        ):
            self._run_main(argv)
        # Check outputs.
        self._check_output(output_file, expected_content)
        # The input file must be untouched since compression wrote to a
        # separate `--output` path.
        self.assertTrue(os.path.exists(input_file))


# #############################################################################
# Test__find_gs_binary
# #############################################################################


class Test__find_gs_binary(hunitest.TestCase):
    """
    Test dshdcpd._find_gs_binary().
    """

    def test1(self) -> None:
        """
        Test that an existing candidate path is returned directly.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        gs_binary = os.path.join(scratch_dir, "gs")
        hio.to_file(gs_binary, "fake ghostscript binary")
        os.chmod(gs_binary, 0o755)
        # Prepare outputs.
        expected = gs_binary
        # Run test.
        with mock.patch.object(dshdcpd, "_GS_CANDIDATE_PATHS", [gs_binary]):
            actual = dshdcpd._find_gs_binary()
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that `PATH` lookup is used when no candidate path exists.
        """
        # Prepare inputs.
        gs_binary = "/some/fake/path/gs"
        # Prepare outputs.
        expected = gs_binary
        # Run test.
        with (
            mock.patch.object(dshdcpd, "_GS_CANDIDATE_PATHS", []),
            mock.patch.object(dshdcpd.shutil, "which", return_value=gs_binary),
        ):
            actual = dshdcpd._find_gs_binary()
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test__compress_pdf_ghostscript_global
# #############################################################################


class Test__compress_pdf_ghostscript_global(hunitest.TestCase):
    """
    Test dshdcpd._compress_pdf_ghostscript_global().
    """

    def helper(self, output_file: str, quality: str) -> None:
        """
        Run the function under test with a mocked `gs` binary and check the
        constructed command and the resulting output file.

        :param output_file: path passed as `output_file` (same as, or
            different from, the input file)
        :param quality: Ghostscript `-dPDFSETTINGS` preset to pass to the
            function under test
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "lecture.pdf")
        hio.to_file(input_file, "original content")
        gs_binary = "/usr/bin/gs"
        tmp_output_file = output_file + ".compressed.tmp"
        # Prepare outputs.
        expected_cmd = (
            f"{gs_binary} -sDEVICE=pdfwrite -dPDFSETTINGS={quality} "
            f"-dCompatibilityLevel=1.4 -dColorConversionStrategy=/sRGB "
            f"-dProcessColorModel=/DeviceRGB -dNOPAUSE -dQUIET -dBATCH "
            f"-sOutputFile={tmp_output_file} {input_file}"
        )
        expected_str = hprint.dedent(
            f"""
            [
                {{
                'function': hsystem.system,
                'args': ('{expected_cmd}',),
                'kwargs': {{}},
                }},
            ]
            """
        )
        expected_content = "compressed content"
        # Run test.
        with (
            mock.patch.object(
                dshdcpd, "_find_gs_binary", return_value=gs_binary
            ),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            # `gs` itself is mocked out, so create the compressed file it
            # would have produced.
            hio.to_file(tmp_output_file, expected_content)
            dshdcpd._compress_pdf_ghostscript_global(
                input_file, output_file, quality=quality
            )
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)
        actual_content = hio.from_file(output_file)
        self.assert_equal(actual_content, expected_content)
        self.assertFalse(os.path.exists(tmp_output_file))

    def test1(self) -> None:
        """
        Test compressing a PDF in place (`output_file` equals `input_file`).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "lecture.pdf")
        quality = "/printer"
        # Run test and check outputs.
        self.helper(output_file, quality)

    def test2(self) -> None:
        """
        Test compressing a PDF to a different output file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "lecture.compressed.pdf")
        quality = "/printer"
        # Run test and check outputs.
        self.helper(output_file, quality)

    def test3(self) -> None:
        """
        Test compressing a PDF with a non-default quality preset.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "lecture.pdf")
        quality = "/screen"
        # Run test and check outputs.
        self.helper(output_file, quality)


# #############################################################################
# Test__compress_pdf_ghostscript_dockerized
# #############################################################################


class Test__compress_pdf_ghostscript_dockerized(hunitest.TestCase):
    """
    Test dshdcpd._compress_pdf_ghostscript_dockerized().
    """

    def helper(self, output_file: str, quality: str) -> None:
        """
        Run the function under test with `hdocker.build_and_run_docker_cmd`
        mocked out and check the constructed `gs` command and the resulting
        output file.

        :param output_file: path passed as `output_file` (same as, or
            different from, the input file)
        :param quality: Ghostscript `-dPDFSETTINGS` preset to pass to the
            function under test
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "lecture.pdf")
        hio.to_file(input_file, "original content")
        tmp_output_file = output_file + ".compressed.tmp"
        # Prepare outputs.
        # Compute the in-container paths the same way
        # `_compress_pdf_ghostscript_dockerized()` does (a real, unmocked
        # call: `hdocker` is our own internal wrapper, not the external
        # dependency, so it is not mocked), to build the expected `gs`
        # command and the expected call to `build_and_run_docker_cmd()`.
        (
            is_caller_host,
            use_sibling_container_for_callee,
            caller_mount_path,
            callee_mount_path,
            mount,
        ) = dshdcpd.hdocker.get_docker_mount_context()
        docker_input_file = dshdcpd.hdocker.convert_caller_to_callee_docker_path(
            input_file,
            caller_mount_path,
            callee_mount_path,
            check_if_exists=True,
            is_input=True,
            is_caller_host=is_caller_host,
            use_sibling_container_for_callee=use_sibling_container_for_callee,
        )
        docker_tmp_output_file = dshdcpd.hdocker.convert_caller_to_callee_docker_path(
            tmp_output_file,
            caller_mount_path,
            callee_mount_path,
            check_if_exists=True,
            is_input=False,
            is_caller_host=is_caller_host,
            use_sibling_container_for_callee=use_sibling_container_for_callee,
        )
        expected_cmd = (
            f"gs -sDEVICE=pdfwrite -dPDFSETTINGS={quality} "
            f"-dCompatibilityLevel=1.4 -dColorConversionStrategy=/sRGB "
            f"-dProcessColorModel=/DeviceRGB -dNOPAUSE -dQUIET -dBATCH "
            f"-sOutputFile={docker_tmp_output_file} {docker_input_file}"
        )
        use_sudo = False
        expected_calls = [
            (
                use_sudo,
                callee_mount_path,
                mount,
                dshdcpd._GHOSTSCRIPT_DOCKER_IMAGE,
                "",
                expected_cmd,
                "system",
            )
        ]
        expected_content = "compressed content"
        calls: List[Tuple[Any, ...]] = []

        def _fake_build_and_run_docker_cmd(*args: Any, **kwargs: Any) -> str:
            _ = kwargs
            calls.append(args)
            # The Docker call is mocked out, so create the compressed file
            # it would have produced (at the host path).
            hio.to_file(tmp_output_file, expected_content)
            return ""

        # Run test.
        with mock.patch.object(
            dshdcpd.hdocker,
            "build_and_run_docker_cmd",
            side_effect=_fake_build_and_run_docker_cmd,
        ):
            dshdcpd._compress_pdf_ghostscript_dockerized(
                input_file, output_file, quality=quality
            )
        # Check outputs.
        self.assert_equal(str(calls), str(expected_calls))
        actual_content = hio.from_file(output_file)
        self.assert_equal(actual_content, expected_content)
        self.assertFalse(os.path.exists(tmp_output_file))

    def test1(self) -> None:
        """
        Test compressing a PDF in place (`output_file` equals `input_file`).
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "lecture.pdf")
        quality = "/printer"
        # Run test and check outputs.
        self.helper(output_file, quality)

    def test2(self) -> None:
        """
        Test compressing a PDF to a different output file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "lecture.compressed.pdf")
        quality = "/printer"
        # Run test and check outputs.
        self.helper(output_file, quality)

    def test3(self) -> None:
        """
        Test compressing a PDF with a non-default quality preset.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        output_file = os.path.join(scratch_dir, "lecture.pdf")
        quality = "/screen"
        # Run test and check outputs.
        self.helper(output_file, quality)
