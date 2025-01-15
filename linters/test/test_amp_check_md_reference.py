import logging
import os
import tempfile
import pytest
import helpers.hunit_test as hunitest
import linters.amp_check_md_reference as licamdref

_LOG = logging.getLogger(__name__)

class Test_check_file_reference(hunitest.TestCase):
    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        """
        Run setup and teardown for each test.
        """
        self.set_up_test()
        yield
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Set up a temporary repository with sample Markdown files.
        """
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.tmp_dir.name
        # Create a README.md file.
        with open(os.path.join(self.repo_path, "README.md"), "w") as readme:
            readme.write(
                "# Repository README\n\n"
                "[Link to file1](file1.md)\n"
                "[Link to file2](file2.md)\n"
            )
        # Create Markdown files.
        with open(os.path.join(self.repo_path, "file1.md"), "w") as file1:
            file1.write("[Link to file2](file2.md)")
        with open(os.path.join(self.repo_path, "file2.md"), "w") as file2:
            file2.write("[Link to file3](file3.md)")
        with open(os.path.join(self.repo_path, "file3.md"), "w") as file3:
            file3.write(
                "[External Link](https://example.com)\n"
                "[Link to file1](file1.md)"
            )
        with open(os.path.join(self.repo_path, "unreferenced.md"), "w") as unreferenced_file:
            unreferenced_file.write("# Unreferenced file")

    def tear_down_test(self) -> None:
        """
        Clean up the temporary directory.
        """
        self.tmp_dir.cleanup()

    def test1(self) -> None:
        """
        Test checking if a Markdown file is referenced in README.md.
        """
        readme_path = os.path.join(self.repo_path, "README.md")
        # Test referenced file.
        warnings1 = licamdref.check_file_reference(readme_path, "file1.md")
        # Test unreferenced file.
        warnings2 = licamdref.check_file_reference(readme_path, "unreferenced.md")
        self.assertEqual(warnings2, [
            "unreferenced.md: 'unreferenced.md' is not referenced in README.md"
        ])
        self.assertEqual(warnings1, [])
        
    def test2(self) -> None:
        """
        Test behavior when README.md is missing.
        """
        os.remove(os.path.join(self.repo_path, "README.md"))
        readme_path = os.path.join(self.repo_path, "README.md")
        warnings = licamdref.check_file_reference(readme_path, "file1.md")
        self.assertEqual(warnings, [
            f"File not found: {readme_path}"
        ])
