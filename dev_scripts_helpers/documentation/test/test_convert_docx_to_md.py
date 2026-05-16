"""
Import as:

import dev_scripts_helpers.documentation.test.test_convert_docx_to_md as dshddtcdm
"""

import logging
import os

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


@pytest.mark.superslow
@pytest.mark.skipif(
    not hserver.is_host_mac(),
    reason="Requires Docker sibling container (not available on Linux CI)",
)
class Test_convert_docx_to_md(hunitest.TestCase):
    """
    End-to-end test for `convert_docx_to_md.py`.
    """

    def test1(self) -> None:
        """
        Test converting a DOCX file to Markdown.
        """
        # Prepare inputs.
        input_dir = self.get_input_dir()
        docx_file = os.path.join(input_dir, "sample.docx")
        script_path = hgit.find_file_in_git_tree("convert_docx_to_md.py")
        out_dir = self.get_scratch_space()
        # Run test.
        cmd = (
            f"{script_path}"
            f" --input {docx_file}"
            f" --output {out_dir}"
            f" --skip_figures"
            f" --overwrite"
        )
        hsystem.system(cmd)
        # Check outputs.
        md_file = os.path.join(out_dir, "sample.md")
        actual = hio.from_file(md_file)
        self.check_string(actual)
