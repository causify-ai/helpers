import logging
import os

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_check_md_reference as lachmdre

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_check_file_reference
# #############################################################################


class Test_check_file_reference(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test for a referenced Markdown file in README.md.
        """
        repo_path = self._create_tmp_dir_with_file()
        readme_path = os.path.join(repo_path, "README.md")
        # Test referenced file.
        warnings = lachmdre.check_file_reference(readme_path, "file1.md")
        self.assertEqual(warnings, [])

    def test2(self) -> None:
        """
        Test for an unreferenced Markdown file in README.md.
        """
        repo_path = self._create_tmp_dir_with_file()
        readme_path = os.path.join(repo_path, "README.md")
        # Test unreferenced file.
        warnings = lachmdre.check_file_reference(readme_path, "unreferenced.md")
        self.assertEqual(
            warnings,
            ["unreferenced.md: 'unreferenced.md' is not referenced in README.md"],
        )

    def _create_tmp_dir_with_file(self) -> str:
        """
        Create a temporary directory with markdown files.
        """
        repo_path = self.get_scratch_space()
        # Create a README.md file.
        content = """
# README

[Link to referenced file](file1.md)
        """
        hio.to_file(
            os.path.join(repo_path, "README.md"),
            content,
        )
        # Create Markdown files.
        hio.to_file(
            os.path.join(repo_path, "file1.md"),
            "# Referenced file",
        )
        hio.to_file(
            os.path.join(repo_path, "unreferenced.md"),
            "# Unreferenced file",
        )
        return repo_path
