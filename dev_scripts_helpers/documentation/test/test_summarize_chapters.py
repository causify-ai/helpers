"""
Import as:

import dev_scripts_helpers.documentation.test.test_summarize_chapters
"""

import logging
import os
from typing import List, Tuple

import pytest

import dev_scripts_helpers.documentation.summarize_chapters as dshdssc
import helpers.hunit_test as hunitest
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


class Test__get_output_path(hunitest.TestCase):
    """
    Test the _get_output_path function.
    """

    def helper(self, input_file: str, expected: str) -> None:
        """
        Test helper for _get_output_path.

        :param input_file: Input file path
        :param expected: Expected output path
        """
        # Run test.
        actual = dshdssc._get_output_path(input_file)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test .md extension is replaced.
        """
        # Prepare inputs.
        input_file = "chapter1.md"
        # Prepare outputs.
        expected = "chapter1.summary.md"
        # Run test.
        self.helper(input_file, expected)

    def test2(self) -> None:
        """
        Test .md extension in path with directories.
        """
        # Prepare inputs.
        input_file = "/path/to/chapter1.md"
        # Prepare outputs.
        expected = "/path/to/chapter1.summary.md"
        # Run test.
        self.helper(input_file, expected)

    def test3(self) -> None:
        """
        Test file without .md extension.
        """
        # Prepare inputs.
        input_file = "chapter1.txt"
        # Prepare outputs.
        expected = "chapter1.txt.summary.md"
        # Run test.
        self.helper(input_file, expected)


# TODO(ai_gp): Create a test list for LLM.
@pytest.mark.skip(reason="Requires LLM credentials and external API")
class Test_summarize_file(hunitest.TestCase):
    """
    Test the _summarize_file function.
    """

    def test1(self) -> None:
        """
        Test summarizing a simple chapter.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "chapter1.md")
        output_file = os.path.join(scratch_dir, "chapter1.summary.md")
        input_content = """
        # 1. Introduction

        This is an introduction that explains the basic concepts. It covers:
        - First concept
        - Second concept
        - Third concept

        ## 1.1. Basic Terminology

        In this section we define key terms used throughout the document.

        A is an important term that means something specific.
        B is another term that relates to A.
        C is a third term that can be derived from A and B.
        """
        input_content = hprint.dedent(input_content)
        hio.to_file(input_file, input_content)
        # Run test.
        dshdssc._summarize_file(
            input_file, output_file, model="gpt-4o-mini"
        )
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        result = hio.from_file(output_file)
        self.assertIn("# 1.", result)
        self.assertIn("-", result)


@pytest.mark.skip(reason="Requires LLM credentials and external API")
class Test_summarize_chapters_script(hunitest.TestCase):
    """
    Test the summarize_chapters script end-to-end.
    """

    def helper(
        self,
        input_file_specs: List[Tuple[str, str]],
    ) -> List[str]:
        """
        Test helper for summarize_chapters script.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_paths = []
        for filename, content in input_file_specs:
            path = os.path.join(scratch_dir, filename)
            hio.to_file(path, content)
            input_paths.append(path)
        # Run test.
        script_path = hgit.find_file_in_git_tree("summarize_chapters.py")
        if len(input_paths) == 1:
            output_path = input_paths[0].replace(".md", ".summary.md")
            cmd = f"{script_path} -i {input_paths[0]} -o {output_path}"
        else:
            cmd = f"{script_path} --input_files='{','.join(input_paths)}'"
        hsystem.system(cmd)
        output_paths = [p.replace(".md", ".summary.md") for p in input_paths]
        return output_paths

    def test1(self) -> None:
        """
        Test single file mode.
        """
        # Prepare inputs.
        input_specs = [
            (
                "chapter1.md",
                """
                # 1. Hello

                This is the hello chapter.

                ## 1.1. Hello world

                The world greeting mechanism.
                """,
            ),
        ]
        input_specs[0] = (
            input_specs[0][0],
            hprint.dedent(input_specs[0][1]),
        )
        # Run test.
        output_paths = self.helper(input_specs)
        # Check outputs.
        self.assertTrue(os.path.exists(output_paths[0]))
        result = hio.from_file(output_paths[0])
        self.assertIn("# 1.", result)

    def test2(self) -> None:
        """
        Test multiple files mode.
        """
        # Prepare inputs.
        input_specs = [
            ("ch1.md", "# 1. Chapter 1\nContent for chapter 1."),
            ("ch2.md", "# 2. Chapter 2\nContent for chapter 2."),
        ]
        # Run test.
        output_paths = self.helper(input_specs)
        # Check outputs.
        for output_path in output_paths:
            self.assertTrue(os.path.exists(output_path))
