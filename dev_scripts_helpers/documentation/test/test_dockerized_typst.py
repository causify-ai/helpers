import os

import pytest

import helpers.hdocker as hdocker
import helpers.hdockerized_executables as hdocexec
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest


def _create_typst_file(self_: hunitest.TestCase) -> str:
    """
    Create a minimal Typst source file in the scratch space.

    :return: path to the created `.typ` file
    """
    txt = r"""
    #set page(width: 10cm, height: auto)
    #set heading(numbering: "1.")

    = Hello, Typst!

    This is a simple Typst document created for testing.

    == Section

    Some content here.
    """
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    file_path = os.path.join(self_.get_scratch_space(), "input.typ")
    hio.to_file(file_path, txt)
    return file_path


# #############################################################################
# Test_build_typst_container
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_build_typst_container(hunitest.TestCase):
    """
    Test running the `typst compile` command inside a Docker container.
    """

    # TODO(gp): Add pytest-order to the container.
    #@pytest.mark.order(1)
    def test1(self) -> None:
        """
        Test that the Typst Docker container is built correctly and `typst
        --version` runs inside it.

        Set `DOCKER_FORCE_REBUILD=1` to rebuild from scratch, e.g.:
        ```bash
        > DOCKER_FORCE_REBUILD=1 pytest test_dockerized_typst.py::Test_run_dockerized_typst::test4
        ```
        """
        # Prepare inputs.
        use_sudo = hdocker.get_use_sudo()
        force_rebuild = hdocker.get_force_rebuild()
        # Build the container using the exported constants (no compile needed).
        image_name = hdocker.build_container_image(
            hdocexec.TYPST_CONTAINER_IMAGE,
            hdocexec.TYPST_DOCKERFILE,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Verify the image exists.
        exists, image_id = hdocker.image_exists(image_name, use_sudo)
        self.assertTrue(
            exists,
            msg=f"Typst Docker image '{image_name}' was not found after build",
        )
        self.assertNotEqual(image_id, "", msg="Expected a non-empty image ID")
        # Run `typst --version` inside the container to verify the binary works.
        docker_executable = hdocker.get_docker_executable(use_sudo)
        cmd = (
            f"{docker_executable} run --rm"
            f' --entrypoint "" {image_name}'
            " bash -c 'typst --version'"
        )
        _, output = hsystem.system_to_string(cmd)
        # Check output.
        self.assertIn(
            "typst",
            output.lower(),
            msg=f"Expected 'typst' in version output, got: {output}",
        )


# #############################################################################
# Test_run_dockerized_typst
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_run_dockerized_typst(hunitest.TestCase):
    """
    Test running the `typst compile` command inside a Docker container.
    """

    def test1(self) -> None:
        """
        Test that Dockerized Typst compiles a `.typ` file to an explicit PDF.
        """
        # Prepare inputs.
        in_file_path = _create_typst_file(self)
        out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
        cmd_opts = []
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        # Run test.
        hdocexec.run_dockerized_typst(
            in_file_path,
            out_file_path,
            cmd_opts,
            force_rebuild=force_rebuild,
            use_sudo=use_sudo,
        )
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )

    def test2(self) -> None:
        """
        Test that the `dockerized_typst.py` script compiles via command line
        with an explicit `--output` path.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("dockerized_typst.py")
        in_file_path = _create_typst_file(self)
        out_file_path = os.path.join(self.get_scratch_space(), "output.pdf")
        # Run test.
        cmd = f"{exec_path} --input {in_file_path} --output {out_file_path}"
        hsystem.system(cmd)
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )

    def test3(self) -> None:
        """
        Test that the `dockerized_typst.py` script uses the default PDF output
        path (same name as input, `.pdf` extension) when `--output` is omitted.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("dockerized_typst.py")
        in_file_path = _create_typst_file(self)
        # Expected output is the same name as input but with .pdf extension.
        expected_out_file_path = hio.change_file_extension(in_file_path, ".pdf")
        # Run test.
        cmd = f"{exec_path} --input {in_file_path}"
        hsystem.system(cmd)
        # Check output.
        self.assertTrue(
            os.path.exists(expected_out_file_path),
            msg=f"Default output file {expected_out_file_path} not found",
        )
