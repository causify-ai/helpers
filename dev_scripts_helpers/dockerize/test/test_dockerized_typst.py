import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
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
# Test_run_dockerized_typst
# #############################################################################


class Test_run_dockerized_typst(hunitest.TestCase):
    """
    Test running the `dockerized_typst.py` script.
    """

    def test1(self) -> None:
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

    def test2(self) -> None:
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

    def test3(self) -> None:
        """
        Run `dockerized_typst` through the command line with explicit output.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("dockerized_typst.py")
        in_file_path = _create_typst_file(self)
        out_file_path = os.path.join(self.get_scratch_space(), "custom_output.pdf")
        # Run function.
        cmd = f"{exec_path} --input {in_file_path} --output {out_file_path}"
        hsystem.system(cmd)
        # Check output.
        self.assertTrue(
            os.path.exists(out_file_path),
            msg=f"Output file {out_file_path} not found",
        )
