import os
import sys

import dev_scripts_helpers.documentation.generate_readme_index as dshdgrein
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_generate_readme_index
# #############################################################################


class Test_generate_readme_index(hunitest.TestCase):

    def write_input_file(self, txt: str, file_name: str) -> str:
        """
        Write test content to a file in the scratch space.

        :param txt: the content of the file
        :param file_name: the name of the file
        :return: the path to the file with the test content
        """
        txt = txt.strip()
        # Get file path to write.
        dir_name = self.get_scratch_space()
        file_path = os.path.join(dir_name, file_name)
        file_path = os.path.abspath(file_path)
        # Create the file.
        hio.to_file(file_path, txt)
        return file_path

    def test1(self) -> None:
        """
        Tests for README file generation with one markdown document.
        """
        # Sample markdown content
        content = """
        # Sample Markdown Document

        This markdown file is for testing the generate_readme_index.py script.

        ## Introduction

        It should be detected in the index and updated with a summary if needed.
        """
        file_name = "sample.md"
        repo_path = self.get_scratch_space()
        self.write_input_file(content, file_name)

        # Simulate CLI call
        sys.argv = [
            "generate_readme_index.py",
            "--repo_path",
            repo_path,
            "--use_placeholder_summary",
        ]
        dshdgrein._main()

        # Read the generated README.md
        readme_path = os.path.join(repo_path, "README.md")
        readme_content = hio.from_file(readme_path)

        # Check
        self.check_string(readme_content, tag="README.md")

    def test2(self) -> None:
        """
        Tests for README file generation with nested document.
        """
        # Sample nested documents
        file_structure = {
            "welcome.md": "# welcome page",
            "docs/intro.md": "# Introduction",
            "docs/guide/setup.md": "# Setup Guide",
            "docs/guide/usage.md": "# Usage Guide",
        }
        repo_path = self.get_scratch_space()
        for path, content in file_structure.items():
            self.write_input_file(content, path)
        # Simulate CLI call
        sys.argv = [
            "generate_readme_index.py",
            "--repo_path",
            repo_path,
            "--use_placeholder_summary",
        ]
        dshdgrein._main()
        # Read
        readme_path = os.path.join(repo_path, "README.md")
        readme_content = hio.from_file(readme_path)
        # Check
        self.check_string(readme_content, tag="README.md")

    def test3(self) -> None:
        """
        Test for REAME file generation on an empty directory.
        """
        repo_path = self.get_scratch_space()
        # Simulate CLI call
        sys.argv = [
            "generate_readme_index.py",
            "--repo_path",
            repo_path,
            "--use_placeholder_summary",
        ]
        dshdgrein._main()
        # Assert README was not created
        readme_path = os.path.join(repo_path, "README.md")
        existence = os.path.exists(readme_path)
        self.assertFalse(existence)
