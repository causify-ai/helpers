import os
import textwrap

import pytest

# Equivalent to `import openai`, but skip this module if the module is not present.
# `mockai` must be imported before `openai` to properly mock it.
mockai = pytest.importorskip("openai")

# Pylint wrong-import-position
# It is necessary that generate_readme_index is imported after mockai.
# If not, real OpenAI API will be called.
import dev_scripts_helpers.documentation.generate_readme_index as dshdgrein
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_list_markdown_files
# #############################################################################


class Test_list_markdown_files(hunitest.TestCase):

    def write_input_file(self, txt: str, file_name: str) -> str:
        """
        Write test content to a file in the scratch space.

        :param testcase: instance of the test case (self)
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
        Test for list generation of directory.
        """
        # Sample nested documents.
        file_structure = {
            "welcome.md": "# welcome page",
            "docs/intro.md": "# Introduction",
            "docs/guide/setup.md": "# Setup Guide",
            "docs/guide/usage.md": "# Usage Guide",
        }
        # Expected output.
        expected = [
            "docs/guide/setup.md",
            "docs/guide/usage.md",
            "docs/intro.md",
            "welcome.md",
        ]
        dir_path = self.get_scratch_space()
        for path, content in file_structure.items():
            self.write_input_file(content, path)
        # Run.
        output = dshdgrein.list_markdown_files(dir_path)
        # Check.
        self.assertEqual(output, expected)

    def test2(self) -> None:
        """
        Test for ignore existing README.
        """
        # Sample nested documents.
        file_structure = {
            "welcome.md": "# welcome page",
            "docs/intro.md": "# Introduction",
            "docs/guide/setup.md": "# Setup Guide",
            "README.md": "# Markdown Index",
        }
        dir_path = self.get_scratch_space()
        for path, content in file_structure.items():
            self.write_input_file(content, path)
        # Expected output.
        expected = ["docs/guide/setup.md", "docs/intro.md", "welcome.md"]
        # Run.
        output = dshdgrein.list_markdown_files(dir_path)
        # Check.
        self.assertEqual(output, expected)

    def test3(self) -> None:
        """
        Test for empty directory.
        """
        dir_path = self.get_scratch_space()
        # Expected output.
        expected = []
        # Run.
        output = dshdgrein.list_markdown_files(dir_path)
        # Check.
        self.assertEqual(output, expected)


# #############################################################################
# Test_generate_readme_index
# #############################################################################


class Test_generate_readme_index(hunitest.TestCase):

    def write_readme(self, content: str) -> str:
        """
        Creates a README file with content.

        :param content: the content to be written to file
        :return: path of README file
        """
        content = textwrap.dedent(content)
        dir_path = self.get_scratch_space()
        readme_path = os.path.join(dir_path, "README.md")
        hio.to_file(readme_path, content)
        return readme_path

    def test1(self) -> None:
        """
        Test for generating README from scratch using placeholder summary.
        """
        dir_path = self.get_scratch_space()
        readme_path = os.path.join(dir_path, "README.md")
        # Sample list of markdown files in directory.
        markdown_files = [
            "docs/guide/setup.md",
            "docs/guide/usage.md",
            "docs/intro.md",
            "welcome.md",
        ]
        # Run.
        output = dshdgrein.generate_markdown_index(
            readme_path=readme_path,
            markdown_files=markdown_files,
            index_mode="generate",
            model="placeholder",
        )
        # Check.
        self.check_string(output, tag="README.md")

    def test2(self) -> None:
        """
        Test for refresh README to add new file using placeholder summary.
        """
        # Create existing README.
        existing_content = """
        # Repository README

        This section lists all Markdown files in the repository.

        ## Markdown Index

        - **File Name**: docs/guide/setup.md
        **Relative Path**: [docs/guide/setup.md](docs/guide/setup.md)
        **Summary**: Provides step-by-step instructions to set up the development environment. Essential for onboarding new contributors and initializing project dependencies.

        - **File Name**: docs/guide/usage.md
        **Relative Path**: [docs/guide/usage.md](docs/guide/usage.md)
        **Summary**: Describes how to use the project's key features and available commands. Helps users understand how to interact with the system effectively.

        - **File Name**: docs/intro.md
        **Relative Path**: [docs/intro.md](docs/intro.md)
        **Summary**: Offers an overview of the project's purpose, goals, and core components. Ideal as a starting point for readers new to the repository.

        - **File Name**: welcome.md
        **Relative Path**: [welcome.md](welcome.md)
        **Summary**: Welcomes readers to the repository and outlines the structure of documentation. Encourages contributors to explore and engage with the content.

        """
        readme_path = self.write_readme(existing_content)
        # New markdown files list.
        markdown_files = [
            "docs/guide/new_file.md",
            "docs/guide/setup.md",
            "docs/guide/usage.md",
            "docs/intro.md",
            "welcome.md",
        ]
        # Run.
        output = dshdgrein.generate_markdown_index(
            readme_path=readme_path,
            markdown_files=markdown_files,
            index_mode="refresh",
            model="placeholder",
        )
        # Check.
        self.check_string(output, tag="README.md")

    def test3(self) -> None:
        """
        Test for refresh README to remove summary of deleted file.
        """
        # Create existing README.
        existing_content = """
        # Repository README

        This section lists all Markdown files in the repository.

        ## Markdown Index

        - **File Name**: docs/guide/setup.md
        **Relative Path**: [docs/guide/setup.md](docs/guide/setup.md)
        **Summary**: Provides step-by-step instructions to set up the development environment. Essential for onboarding new contributors and initializing project dependencies.

        - **File Name**: docs/guide/usage.md
        **Relative Path**: [docs/guide/usage.md](docs/guide/usage.md)
        **Summary**: Describes how to use the project's key features and available commands. Helps users understand how to interact with the system effectively.

        - **File Name**: docs/intro.md
        **Relative Path**: [docs/intro.md](docs/intro.md)
        **Summary**: Offers an overview of the project's purpose, goals, and core components. Ideal as a starting point for readers new to the repository.

        - **File Name**: welcome.md
        **Relative Path**: [welcome.md](welcome.md)
        **Summary**: Welcomes readers to the repository and outlines the structure of documentation. Encourages contributors to explore and engage with the content.

        """
        readme_path = self.write_readme(existing_content)
        # New markdown files list.
        markdown_files = ["docs/guide/setup.md", "docs/intro.md", "welcome.md"]
        # Run.
        output = dshdgrein.generate_markdown_index(
            readme_path=readme_path,
            markdown_files=markdown_files,
            index_mode="refresh",
            model="placeholder",
        )
        # Check.
        self.check_string(output, tag="README.md")

    def test4(self) -> None:
        """
        Test for refresh README to add and delete file.
        """
        # Create existing README.
        existing_content = """
        # Repository README

        This section lists all Markdown files in the repository.

        ## Markdown Index

        - **File Name**: docs/guide/setup.md
        **Relative Path**: [docs/guide/setup.md](docs/guide/setup.md)
        **Summary**: Provides step-by-step instructions to set up the development environment. Essential for onboarding new contributors and initializing project dependencies.

        - **File Name**: docs/guide/usage.md
        **Relative Path**: [docs/guide/usage.md](docs/guide/usage.md)
        **Summary**: Describes how to use the project's key features and available commands. Helps users understand how to interact with the system effectively.

        - **File Name**: docs/intro.md
        **Relative Path**: [docs/intro.md](docs/intro.md)
        **Summary**: Offers an overview of the project's purpose, goals, and core components. Ideal as a starting point for readers new to the repository.

        - **File Name**: welcome.md
        **Relative Path**: [welcome.md](welcome.md)
        **Summary**: Welcomes readers to the repository and outlines the structure of documentation. Encourages contributors to explore and engage with the content.

        """
        readme_path = self.write_readme(existing_content)
        # New markdown files list.
        markdown_files = [
            "docs/guide/new_file.md",
            "docs/guide/usage.md",
            "docs/intro.md",
            "welcome.md",
        ]
        # Run.
        output = dshdgrein.generate_markdown_index(
            readme_path=readme_path,
            markdown_files=markdown_files,
            index_mode="refresh",
            model="placeholder",
        )
        # Check.
        self.check_string(output, tag="README.md")
