import logging
import os

import tempfile

import helpers.hunit_test as hunitest
import linters.amp_check_md_references as licamdref

_LOG = logging.getLogger(__name__)

class TestMarkdownReferences(hunitest.TestCase):
    def setUp(self) -> None:
        """
        Set up a temporary repository with sample Markdown files.
        """
        self.tmp_dir = tempfile.TemporaryDirectory()
        repo_path = self.tmp_dir.name
        # Create Markdown files.
        with open(os.path.join(repo_path, "file1.md"), "w") as file1:
            file1.write("[Link to file2](file2.md)")
        with open(os.path.join(repo_path, "file2.md"), "w") as file2:
            file2.write("[Link to file3](file3.md)")
        with open(os.path.join(repo_path, "file3.md"), "w") as file3:
            file3.write(
                "[External Link](https://example.com)\n"
                "[Link to file1](file1.md)"
            )
        with open(os.path.join(repo_path, "unreferenced.md"), "w") as unreferenced_file:
            unreferenced_file.write("# Unreferenced file")
        self.repo_path = repo_path

    def tearDown(self) -> None:
        """
        Clean up the temporary directory.
        """
        self.tmp_dir.cleanup()

    def test1(self) -> None:
        """
        Test listing all Markdown files in the repository.
        """
        markdown_files = licamdref.list_markdown_files(self.repo_path)
        expected_files = {"file1.md", "file2.md", "file3.md", "unreferenced.md"}
        self.assertEqual(markdown_files, expected_files)

    def test2(self) -> None:
        """
        Test extracting all references from Markdown files.
        """
        markdown_files = {"file1.md", "file2.md", "file3.md"}
        references, warnings = licamdref.extract_all_references(self.repo_path, markdown_files)
        expected_references = {"file1.md", "file2.md", "file3.md", "https://example.com"}
        self.assertEqual(references, expected_references)
        self.assertEqual(warnings, [])

    def test3(self) -> None:
        """
        Test identifying unreferenced Markdown files.
        """
        markdown_files = {"file1.md", "file2.md", "file3.md", "unreferenced.md"}
        references = {"file1.md", "file2.md", "file3.md", "https://example.com"}
        unreferenced_files, warnings = licamdref.find_unreferenced_files(markdown_files, references)
        self.assertEqual(warnings, ["Unreferenced Markdown file: unreferenced.md"])

    def test4(self) -> None:
        """
        Integration test for the overall functionality.
        """
        # Run the check_markdown_references function
        unreferenced_files, warnings = licamdref.check_markdown_references(self.repo_path)
        # Verify the warnings and unreferenced files
        self.assertEqual(warnings, ["Unreferenced Markdown file: unreferenced.md"])
    
    def test5(self) -> None:
        """
        Test behavior when the repository contains no Markdown files.
        """
        empty_dir = tempfile.TemporaryDirectory()
        warnings, unreferenced_files = licamdref.check_markdown_references(empty_dir.name)
        self.assertEqual(warnings, ["No Markdown files found in the repository."])
        self.assertEqual(unreferenced_files, [])
        empty_dir.cleanup()
