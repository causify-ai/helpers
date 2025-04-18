import os
import textwrap

import pytest

pytest.importorskip(
    "openai"
)  # noqa: E402 # pylint: disable=wrong-import-position

import dev_scripts_helpers.documentation.generate_readme_index as dshdgrein
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_list_markdown_files
# #############################################################################


class Test_list_markdown_files(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test retrieving all Markdown files in a directory.
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
            self._write_input_file(content, path)
        # Run.
        actual = dshdgrein.list_markdown_files(dir_path)
        # Check.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that non-Markdown files are ignored.
        """
        # Sample nested documents.
        file_structure = {
            "welcome.md": "# welcome page",
            "docs/intro.md": "# Introduction",
            "docs/guide/setup.md": "# Setup Guide",
            "docs/guide/build.py": "Build setup",
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
            self._write_input_file(content, path)
        # Run.
        actual = dshdgrein.list_markdown_files(dir_path)
        # Check.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that the existing README is ignored.
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
            self._write_input_file(content, path)
        # Expected output.
        expected = ["docs/guide/setup.md", "docs/intro.md", "welcome.md"]
        # Run.
        actual = dshdgrein.list_markdown_files(dir_path)
        # Check.
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test for empty directory.
        """
        dir_path = self.get_scratch_space()
        # Expected output.
        expected = []
        # Run.
        actual = dshdgrein.list_markdown_files(dir_path)
        # Check.
        self.assertEqual(actual, expected)

    def _write_input_file(self, txt: str, file_name: str) -> str:
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


# #############################################################################
# Test_generate_readme_index
# #############################################################################


class Test_generate_readme_index(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test generating README from scratch using placeholder summary.
        """
        # Prepare inputs.
        dir_path = self.get_scratch_space()
        markdown_files = [
            "docs/guide/setup.md",
            "docs/guide/usage.md",
            "docs/intro.md",
            "welcome.md",
        ]
        index_mode = "generate"
        model = "placeholder"
        # Run.
        actual = dshdgrein.generate_markdown_index(
            dir_path=dir_path,
            markdown_files=markdown_files,
            index_mode=index_mode,
            model=model,
        )
        # Check.
        self.check_string(actual)

    def test2(self) -> None:
        """
        Test refreshing README by adding a new file.
        """
        # Prepare inputs.
        existing_content = """
        # README for `test/outcomes/Test_generate_readme_index.test2/tmp.scratch`

        Below is a list of all Markdown files found under `test/outcomes/Test_generate_readme_index.test2/tmp.scratch`.

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
        dir_path = self._write_readme(existing_content)
        markdown_files = [
            "docs/guide/new_file.md",
            "docs/guide/setup.md",
            "docs/guide/usage.md",
            "docs/intro.md",
            "welcome.md",
        ]
        index_mode = "refresh"
        model = "placeholder"
        # Run.
        actual = dshdgrein.generate_markdown_index(
            dir_path=dir_path,
            markdown_files=markdown_files,
            index_mode=index_mode,
            model=model,
        )
        # Check.
        self.check_string(actual)

    def test3(self) -> None:
        """
        Test refreshing README by removing an obsolete file.
        """
        # Prepare inputs.
        existing_content = """
        # README for `test/outcomes/Test_generate_readme_index.test3/tmp.scratch`

        Below is a list of all Markdown files found under `test/outcomes/Test_generate_readme_index.test3/tmp.scratch`.

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
        dir_path = self._write_readme(existing_content)
        markdown_files = ["docs/guide/setup.md", "docs/intro.md", "welcome.md"]
        index_mode = "refresh"
        model = "placeholder"
        # Run.
        actual = dshdgrein.generate_markdown_index(
            dir_path=dir_path,
            markdown_files=markdown_files,
            index_mode=index_mode,
            model=model,
        )
        # Check.
        self.check_string(actual)

    def test4(self) -> None:
        """
        Test refreshing README by adding a new file and removing another.
        """
        # Prepare inputs.
        existing_content = """
        # README for `test/outcomes/Test_generate_readme_index.test4/tmp.scratch`

        Below is a list of all Markdown files found under `test/outcomes/Test_generate_readme_index.test4/tmp.scratch`.

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
        dir_path = self._write_readme(existing_content)
        markdown_files = [
            "docs/guide/new_file.md",
            "docs/guide/usage.md",
            "docs/intro.md",
            "welcome.md",
        ]
        index_mode = "refresh"
        model = "placeholder"
        # Run.
        actual = dshdgrein.generate_markdown_index(
            dir_path=dir_path,
            markdown_files=markdown_files,
            index_mode=index_mode,
            model=model,
        )
        # Check.
        self.check_string(actual)

    def _write_readme(self, content: str) -> str:
        """
        Create a README file with content.

        :param content: the content to write into the README file
        :return: the path to the directory containing the README
        """
        content = textwrap.dedent(content)
        dir_path = self.get_scratch_space()
        readme_path = os.path.join(dir_path, "README.md")
        hio.to_file(readme_path, content)
        return dir_path
