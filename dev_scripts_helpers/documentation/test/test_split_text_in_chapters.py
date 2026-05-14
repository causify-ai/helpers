import logging
import os
from typing import List, Tuple

import dev_scripts_helpers.documentation.extract_chapters_from_text as dshdecfte
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_extract_chapters
# #############################################################################


class Test_extract_chapters(hunitest.TestCase):
    """
    Test `_extract_chapters()` from `extract_chapters_from_text.py`.
    """

    def test1(self) -> None:
        """
        Test extracting a single chapter with content.
        """
        # Prepare inputs.
        content = """
        # Chapter One
        Some content here.
        More text.
        """
        content = hprint.dedent(content)
        # Prepare outputs.
        expected: List[Tuple[str, str]] = [
            (
                "Chapter One",
                "# Chapter One\nSome content here.\nMore text.",
            ),
        ]
        # Run test.
        actual = dshdecfte._extract_chapters(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test extracting multiple chapters separated by level-1 headers.
        """
        # Prepare inputs.
        content = """
        # Chapter One
        Content of chapter one.
        # Chapter Two
        Content of chapter two.
        # Chapter Three
        Content of chapter three.
        """
        content = hprint.dedent(content)
        # Prepare outputs.
        expected: List[Tuple[str, str]] = [
            ("Chapter One", "# Chapter One\nContent of chapter one."),
            ("Chapter Two", "# Chapter Two\nContent of chapter two."),
            (
                "Chapter Three",
                "# Chapter Three\nContent of chapter three.",
            ),
        ]
        # Run test.
        actual = dshdecfte._extract_chapters(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test that empty content produces no chapters.
        """
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected: List[Tuple[str, str]] = []
        # Run test.
        actual = dshdecfte._extract_chapters(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test that content with no level-1 headers produces no chapters.
        """
        # Prepare inputs.
        content = """
        Some text without a header.
        ## Level 2 header
        ### Level 3 header
        """
        content = hprint.dedent(content)
        # Prepare outputs.
        expected: List[Tuple[str, str]] = []
        # Run test.
        actual = dshdecfte._extract_chapters(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test5(self) -> None:
        """
        Test that level-2 headers do not start new chapters.
        """
        # Prepare inputs.
        content = """
        # Chapter One
        ## Subsection
        Subsection content.
        # Chapter Two
        ## Another Subsection
        """
        content = hprint.dedent(content)
        # Prepare outputs.
        expected: List[Tuple[str, str]] = [
            (
                "Chapter One",
                "# Chapter One\n## Subsection\nSubsection content.",
            ),
            ("Chapter Two", "# Chapter Two\n## Another Subsection"),
        ]
        # Run test.
        actual = dshdecfte._extract_chapters(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test6(self) -> None:
        """
        Test that text before the first level-1 header is ignored.
        """
        # Prepare inputs.
        content = """
        Preamble text not in any chapter.
        # Chapter One
        Chapter content.
        """
        content = hprint.dedent(content)
        # Prepare outputs.
        expected: List[Tuple[str, str]] = [
            ("Chapter One", "# Chapter One\nChapter content."),
        ]
        # Run test.
        actual = dshdecfte._extract_chapters(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_sanitize_chapter_title
# #############################################################################


class Test_sanitize_chapter_title(hunitest.TestCase):
    """
    Test `_sanitize_chapter_title()` from `extract_chapters_from_text.py`.
    """

    def test1(self) -> None:
        """
        Test that spaces in title become underscores.
        """
        # Prepare inputs.
        title = "Chapter One"
        # Prepare outputs.
        expected = "Chapter_One"
        # Run test.
        actual = dshdecfte._sanitize_chapter_title(title)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a title with no special characters is unchanged.
        """
        # Prepare inputs.
        title = "Introduction"
        # Prepare outputs.
        expected = "Introduction"
        # Run test.
        actual = dshdecfte._sanitize_chapter_title(title)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that single quotes are replaced with underscores.
        """
        # Prepare inputs.
        title = "It's a test"
        # Prepare outputs.
        expected = "It_s_a_test"
        # Run test.
        actual = dshdecfte._sanitize_chapter_title(title)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test that backticks are replaced with underscores.
        """
        # Prepare inputs.
        title = "Quote `code`"
        # Prepare outputs.
        expected = "Quote__code_"
        # Run test.
        actual = dshdecfte._sanitize_chapter_title(title)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test that a whitespace-only title raises an `AssertionError`.
        """
        # Prepare inputs.
        title = "   "
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdecfte._sanitize_chapter_title(title)


# #############################################################################
# Test_validate_chapters
# #############################################################################


class Test_validate_chapters(hunitest.TestCase):
    """
    Test `_validate_chapters()` from `extract_chapters_from_text.py`.
    """

    def test1(self) -> None:
        """
        Test that a list of chapters with unique sanitized names passes.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("Chapter One", "# Chapter One\nContent."),
            ("Chapter Two", "# Chapter Two\nContent."),
        ]
        # Run test (no exception expected).
        dshdecfte._validate_chapters(chapters)

    def test2(self) -> None:
        """
        Test that an empty list of chapters is accepted.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = []
        # Run test (no exception expected).
        dshdecfte._validate_chapters(chapters)

    def test3(self) -> None:
        """
        Test that an empty chapter title raises an `AssertionError`.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("", "Content."),
        ]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdecfte._validate_chapters(chapters)

    def test4(self) -> None:
        """
        Test that duplicate sanitized names raise `ValueError`.
        """
        # Prepare inputs.
        # Both titles sanitize to the same filename `Chapter_One`.
        chapters: List[Tuple[str, str]] = [
            ("Chapter One", "# Chapter One\nContent."),
            ("Chapter_One", "# Chapter_One\nContent."),
        ]
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            dshdecfte._validate_chapters(chapters)
        self.assertIn("Duplicate chapter filename", str(cm.exception))


# #############################################################################
# Test_check_output_files_exist
# #############################################################################


class Test_check_output_files_exist(hunitest.TestCase):
    """
    Test `_check_output_files_exist()` from `extract_chapters_from_text.py`.
    """

    def test1(self) -> None:
        """
        Test that an empty output directory returns False.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("Chapter One", "Content."),
            ("Chapter Two", "Content."),
        ]
        output_dir = self.get_scratch_space()
        # Run test.
        actual = dshdecfte._check_output_files_exist(
            chapters, output_dir, add_numbers=False
        )
        # Check outputs.
        expected = False
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that an existing chapter file returns True.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("Chapter One", "Content."),
        ]
        output_dir = self.get_scratch_space()
        # Create a pre-existing file matching the sanitized chapter name.
        hio.to_file(os.path.join(output_dir, "Chapter_One.md"), "exists")
        # Run test.
        actual = dshdecfte._check_output_files_exist(
            chapters, output_dir, add_numbers=False
        )
        # Check outputs.
        expected = True
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that file existence is checked with numbered prefix.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("Chapter One", "Content."),
        ]
        output_dir = self.get_scratch_space()
        # Create a pre-existing file with the numbered prefix.
        hio.to_file(os.path.join(output_dir, "1_Chapter_One.md"), "exists")
        # Run test.
        actual = dshdecfte._check_output_files_exist(
            chapters, output_dir, add_numbers=True
        )
        # Check outputs.
        expected = True
        self.assertEqual(actual, expected)


# #############################################################################
# Test_write_chapters
# #############################################################################


class Test_write_chapters(hunitest.TestCase):
    """
    Test `_write_chapters()` from `extract_chapters_from_text.py`.
    """

    def test1(self) -> None:
        """
        Test writing chapters without number prefixes.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("Chapter One", "# Chapter One\nContent one."),
            ("Chapter Two", "# Chapter Two\nContent two."),
        ]
        output_dir = os.path.join(self.get_scratch_space(), "output")
        # Run test.
        dshdecfte._write_chapters(chapters, output_dir, add_numbers=False)
        # Check outputs.
        actual_files = sorted(os.listdir(output_dir))
        expected_files = ["Chapter_One.md", "Chapter_Two.md"]
        self.assert_equal(str(actual_files), str(expected_files))
        # Verify the content of the first chapter file matches input.
        actual_content = hio.from_file(
            os.path.join(output_dir, "Chapter_One.md")
        )
        expected_content = "# Chapter One\nContent one."
        self.assert_equal(actual_content, expected_content)

    def test2(self) -> None:
        """
        Test writing chapters with number prefixes.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("Chapter One", "# Chapter One\nContent one."),
            ("Chapter Two", "# Chapter Two\nContent two."),
        ]
        output_dir = os.path.join(self.get_scratch_space(), "output")
        # Run test.
        dshdecfte._write_chapters(chapters, output_dir, add_numbers=True)
        # Check outputs.
        actual_files = sorted(os.listdir(output_dir))
        expected_files = ["1_Chapter_One.md", "2_Chapter_Two.md"]
        self.assert_equal(str(actual_files), str(expected_files))

    def test3(self) -> None:
        """
        Test writing a single chapter creates the output directory.
        """
        # Prepare inputs.
        chapters: List[Tuple[str, str]] = [
            ("Solo Chapter", "# Solo Chapter\nOnly content."),
        ]
        # The nested output directory does not exist yet.
        output_dir = os.path.join(self.get_scratch_space(), "nested", "output")
        # Run test.
        dshdecfte._write_chapters(chapters, output_dir, add_numbers=False)
        # Check outputs.
        actual_files = sorted(os.listdir(output_dir))
        expected_files = ["Solo_Chapter.md"]
        self.assert_equal(str(actual_files), str(expected_files))


# #############################################################################
# Test_extract_chapters_from_text_script
# #############################################################################


class Test_extract_chapters_from_text_script(hunitest.TestCase):
    """
    Test the script end-to-end via the command line.
    """

    def _run_script(
        self,
        input_content: str,
        *,
        add_numbers: bool = False,
        overwrite: bool = False,
    ) -> str:
        """
        Run the script with the given content and return the output directory.

        :param input_content: markdown content to use as input
        :param add_numbers: whether to add chapter number prefix to filenames
        :param overwrite: whether to allow overwriting existing chapter files
        :return: path to the output directory created by the script
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, input_content)
        output_dir = os.path.join(scratch_dir, "chapters")
        # Build command to call the script.
        script_path = hgit.find_file_in_git_tree("extract_chapters_from_text.py")
        cmd_parts = [
            script_path,
            f"--input={input_file}",
            f"--output={output_dir}",
        ]
        if add_numbers:
            cmd_parts.append("--add_numbers")
        if overwrite:
            cmd_parts.append("--overwrite")
        cmd = " ".join(cmd_parts)
        # Run the script.
        hsystem.system(cmd)
        return output_dir

    def test1(self) -> None:
        """
        Test end-to-end script execution without number prefixes.
        """
        # Prepare inputs.
        content = """
        # Introduction
        Welcome to the book.
        # Chapter One
        First chapter content.
        # Chapter Two
        Second chapter content.
        """
        content = hprint.dedent(content)
        # Run test.
        output_dir = self._run_script(content)
        # Check outputs.
        actual_files = sorted(os.listdir(output_dir))
        expected_files = [
            "Chapter_One.md",
            "Chapter_Two.md",
            "Introduction.md",
        ]
        self.assert_equal(str(actual_files), str(expected_files))

    def test2(self) -> None:
        """
        Test end-to-end script execution with `--add_numbers`.
        """
        # Prepare inputs.
        content = """
        # Introduction
        Welcome.
        # Chapter One
        Content.
        """
        content = hprint.dedent(content)
        # Run test.
        output_dir = self._run_script(content, add_numbers=True)
        # Check outputs.
        actual_files = sorted(os.listdir(output_dir))
        expected_files = ["1_Introduction.md", "2_Chapter_One.md"]
        self.assert_equal(str(actual_files), str(expected_files))

    def test3(self) -> None:
        """
        Test that `--overwrite` replaces existing chapter files.
        """
        # Prepare inputs.
        content = """
        # Chapter One
        First version.
        """
        content = hprint.dedent(content)
        # Run the script once to populate the output directory.
        output_dir = self._run_script(content)
        # Re-run with new content and `--overwrite=True` to replace files.
        new_content = """
        # Chapter One
        Updated version.
        """
        new_content = hprint.dedent(new_content)
        self._run_script(new_content, overwrite=True)
        # Check outputs.
        actual_content = hio.from_file(
            os.path.join(output_dir, "Chapter_One.md")
        )
        expected_content = "# Chapter One\nUpdated version."
        self.assert_equal(actual_content, expected_content)
