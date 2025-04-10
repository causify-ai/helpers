import os
import logging

import helpers.hio as hio
import helpers.hunit_test as hunitest
from dev_scripts_helpers.documentation import generate_readme_index as gri

class TestGenerateReadmeIndex(hunitest.TestCase):
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
        file_path = os.path.abspath(os.path.join(dir_name, file_name))
        # Create the file.
        hio.to_file(file_path, txt)
        return file_path

    def test1(self) -> None:
        # Sample markdown content
        content = """
        # Sample Markdown Document

        This markdown file is for testing the generate_readme_index.py script.

        ## Introduction

        It should be detected in the index and updated with a summary if needed.
        """
        file_name = "sample.md"
        file_path = md_file_path = self.write_input_file(content, file_name)
        # Set cwd to the scratch space to simulate repo root
        repo_path = self.get_scratch_space()
        old_cwd = os.getcwd()
        os.chdir(repo_path)
        try:
            # Simulate command line call
            sys.argv = ["generate_readme_index.py"]

            # Run main function
            script._main()

            # Check if README is created
            readme_path = os.path.join(repo_path, "README.md")
            self.assertTrue(os.path.exists(readme_path), "README.md not created.")

            # Check content
            readme_content = hio.from_file(readme_path)
            self.assertIn("## Markdown Index", readme_content)
            self.assertIn("sample.md", readme_content)
            self.assertNotIn("README.md", readme_content)
        finally:
            os.chdir(old_cwd)