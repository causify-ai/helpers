"""
Unit tests for `split_text_in_chapters.py`.
"""

import logging
import os
import shutil
import tempfile
from typing import Generator

import pytest

import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.split_text_in_chapters as dsdstc

_LOG = logging.getLogger(__name__)


class TestExtractChapters(hunitest.TestCase):
    """
    Test chapter extraction from markdown content.
    """

    def test1(self) -> None:
        """
        Extract basic chapters with multiple level-1 headers.
        """
        # Prepare inputs.
        content = """# Chapter 1
This is chapter 1.

# Chapter 2
This is chapter 2.

# Chapter 3
This is chapter 3."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 3)
        self.assertEqual(chapters[0][0], "Chapter 1")
        self.assertIn("This is chapter 1", chapters[0][1])
        self.assertEqual(chapters[1][0], "Chapter 2")
        self.assertIn("This is chapter 2", chapters[1][1])
        self.assertEqual(chapters[2][0], "Chapter 3")
        self.assertIn("This is chapter 3", chapters[2][1])

    def test2(self) -> None:
        """
        Chapter content includes both the header and body.
        """
        # Prepare inputs.
        content = """# Introduction
Some intro text.
More intro text.

# Main Content
Main content here."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 2)
        self.assertIn("# Introduction", chapters[0][1])
        self.assertIn("Some intro text", chapters[0][1])

    def test3(self) -> None:
        """
        Extract with a single chapter.
        """
        # Prepare inputs.
        content = """# Only Chapter
This is the only chapter."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 1)
        self.assertEqual(chapters[0][0], "Only Chapter")

    def test4(self) -> None:
        """
        Level-2 and level-3 headers are treated as content.
        """
        # Prepare inputs.
        content = """# Chapter 1
## Section 1.1
Content here.
### Subsection 1.1.1
More content.

# Chapter 2
Content of chapter 2."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 2)
        self.assertIn("## Section 1.1", chapters[0][1])
        self.assertIn("### Subsection 1.1.1", chapters[0][1])

    def test5(self) -> None:
        """
        Handle chapters with no content between headers.
        """
        # Prepare inputs.
        content = """# Chapter 1
# Chapter 2
Content of chapter 2."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0][0], "Chapter 1")
        self.assertEqual(chapters[1][0], "Chapter 2")

    def test6(self) -> None:
        """
        Content with no level-1 headers.
        """
        # Prepare inputs.
        content = """Just some content.
With no headers.
## Only level 2 headers."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 0)

    def test7(self) -> None:
        """
        Code blocks with `#` lines are treated as chapter headers.

        Note: This is a limitation of the simple regex-based approach.
        The code block contains "# This is not a header" which matches the
        level-1 header pattern and creates a new chapter.
        """
        # Prepare inputs.
        content = """# Chapter 1
```
# This is not a header
It's in a code block.
```

# Chapter 2
More content."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 3)

    def test8(self) -> None:
        """
        Chapter titles containing special characters.
        """
        # Prepare inputs.
        content = """# Chapter 1: Introduction (Part A)
Content.

# Chapter 2 - The Beginning
More content."""
        # Run test.
        chapters = dsdstc._extract_chapters(content)
        # Check outputs.
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0][0], "Chapter 1: Introduction (Part A)")
        self.assertEqual(chapters[1][0], "Chapter 2 - The Beginning")


class TestSanitizeChapterTitle(hunitest.TestCase):
    """
    Test chapter title sanitization for filenames.
    """

    def test1(self) -> None:
        """
        Basic title without special characters.
        """
        # Prepare inputs.
        title = "Introduction"
        # Prepare outputs.
        expected = "Introduction"
        # Run test.
        result = dsdstc._sanitize_chapter_title(title)
        # Check outputs.
        self.assertEqual(result, expected)

    def test2(self) -> None:
        """
        Title with spaces converted to underscores.
        """
        # Prepare inputs.
        title = "Machine Intelligence"
        # Prepare outputs.
        expected = "Machine_Intelligence"
        # Run test.
        result = dsdstc._sanitize_chapter_title(title)
        # Check outputs.
        self.assertEqual(result, expected)

    def test3(self) -> None:
        """
        Title starting with a number.
        """
        # Prepare inputs.
        title = "1 Introduction"
        # Prepare outputs.
        expected = "1_Introduction"
        # Run test.
        result = dsdstc._sanitize_chapter_title(title)
        # Check outputs.
        self.assertEqual(result, expected)

    def test4(self) -> None:
        """
        Title with punctuation marks (colons, parentheses).

        The `purify_file_name()` function preserves colons and parentheses,
        only removing spaces and certain quote characters.
        """
        # Prepare inputs.
        title = "Chapter 1: Introduction (Part A)"
        # Run test.
        result = dsdstc._sanitize_chapter_title(title)
        # Check outputs.
        self.assertIn("_", result)
        self.assertIn(":", result)
        self.assertIn("(", result)
        self.assertIn(")", result)

    def test5(self) -> None:
        """
        Title with dashes.
        """
        # Prepare inputs.
        title = "Cheap Changes Everything"
        # Prepare outputs.
        expected = "Cheap_Changes_Everything"
        # Run test.
        result = dsdstc._sanitize_chapter_title(title)
        # Check outputs.
        self.assertEqual(result, expected)

    def test6(self) -> None:
        """
        Empty or whitespace-only titles raise an assertion error.
        """
        # Prepare inputs.
        empty_title = ""
        whitespace_title = "   "
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dsdstc._sanitize_chapter_title(empty_title)
        with self.assertRaises(AssertionError):
            dsdstc._sanitize_chapter_title(whitespace_title)

    def test7(self) -> None:
        """
        Title with single and double quotes.
        """
        # Prepare inputs.
        title = 'Machine "Magic" Prediction'
        # Run test.
        result = dsdstc._sanitize_chapter_title(title)
        # Check outputs.
        self.assertNotIn('"', result)
        self.assertNotIn("'", result)


class TestValidateChapters(hunitest.TestCase):
    """
    Test chapter validation.
    """

    def test1(self) -> None:
        """
        Validation of valid chapters.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter 1", "Content 1"),
            ("Chapter 2", "Content 2"),
        ]
        # Run test and check output.
        dsdstc._validate_chapters(chapters)

    def test2(self) -> None:
        """
        Empty chapter title raises error.
        """
        # Prepare inputs.
        chapters = [("", "Content")]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dsdstc._validate_chapters(chapters)

    def test3(self) -> None:
        """
        Whitespace-only chapter title raises error.
        """
        # Prepare inputs.
        chapters = [("   ", "Content")]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dsdstc._validate_chapters(chapters)

    def test4(self) -> None:
        """
        Duplicate sanitized filenames raise error.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter 1", "Content 1"),
            ("Chapter 1", "Different content"),
        ]
        # Run test and check output.
        with self.assertRaises(ValueError):
            dsdstc._validate_chapters(chapters)

    def test5(self) -> None:
        """
        Different titles sanitizing to same filename raise error.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter One", "Content 1"),
            ("Chapter_One", "Content 2"),
        ]
        # Run test and check output.
        with self.assertRaises(ValueError):
            dsdstc._validate_chapters(chapters)

    def test6(self) -> None:
        """
        Empty chapter list validation.
        """
        # Prepare inputs.
        chapters: list = []
        # Run test and check output.
        dsdstc._validate_chapters(chapters)


class TestCheckOutputFilesExist(hunitest.TestCase):
    """
    Test checking for existing output files.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator[None, None, None]:
        """
        Setup and teardown for each test.
        """
        self.set_up_test()
        yield
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Setup code that runs before each test.
        """
        self.temp_dir = tempfile.mkdtemp()

    def tear_down_test(self) -> None:
        """
        Cleanup code that runs after each test.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test1(self) -> None:
        """
        No output files exist.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter 1", "Content 1"),
            ("Chapter 2", "Content 2"),
        ]
        add_numbers = False
        # Run test.
        exists = dsdstc._check_output_files_exist(chapters, self.temp_dir, add_numbers)
        # Check outputs.
        self.assertFalse(exists)

    def test2(self) -> None:
        """
        Detection of existing files without chapter numbers.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter 1", "Content 1"),
            ("Chapter 2", "Content 2"),
        ]
        output_file = os.path.join(self.temp_dir, "Chapter_1.md")
        add_numbers = False
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(output_file, "w") as f:
            f.write("existing content")
        # Run test.
        exists = dsdstc._check_output_files_exist(chapters, self.temp_dir, add_numbers)
        # Check outputs.
        self.assertTrue(exists)

    def test3(self) -> None:
        """
        Detection of existing files with chapter numbers.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter 1", "Content 1"),
            ("Chapter 2", "Content 2"),
        ]
        output_file = os.path.join(self.temp_dir, "1_Chapter_1.md")
        add_numbers = True
        os.makedirs(self.temp_dir, exist_ok=True)
        with open(output_file, "w") as f:
            f.write("existing content")
        # Run test.
        exists = dsdstc._check_output_files_exist(chapters, self.temp_dir, add_numbers)
        # Check outputs.
        self.assertTrue(exists)

    def test4(self) -> None:
        """
        Output directory doesn't exist yet.
        """
        # Prepare inputs.
        chapters = [("Chapter 1", "Content 1")]
        non_existent_dir = os.path.join(self.temp_dir, "does_not_exist")
        add_numbers = False
        # Run test.
        exists = dsdstc._check_output_files_exist(chapters, non_existent_dir, add_numbers)
        # Check outputs.
        self.assertFalse(exists)


class TestWriteChapters(hunitest.TestCase):
    """
    Test chapter writing functionality.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator[None, None, None]:
        """
        Setup and teardown for each test.
        """
        self.set_up_test()
        yield
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Setup code that runs before each test.
        """
        self.temp_dir = tempfile.mkdtemp()

    def tear_down_test(self) -> None:
        """
        Cleanup code that runs after each test.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test1(self) -> None:
        """
        Basic chapter file writing.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter 1", "# Chapter 1\nContent 1"),
            ("Chapter 2", "# Chapter 2\nContent 2"),
        ]
        add_numbers = False
        # Run test.
        dsdstc._write_chapters(chapters, self.temp_dir, add_numbers=add_numbers)
        # Check outputs.
        files = os.listdir(self.temp_dir)
        self.assertEqual(len(files), 2)
        self.assertIn("Chapter_1.md", files)
        self.assertIn("Chapter_2.md", files)
        with open(os.path.join(self.temp_dir, "Chapter_1.md"), "r") as f:
            content = f.read()
        self.assertEqual(content, "# Chapter 1\nContent 1")

    def test2(self) -> None:
        """
        Chapter file writing with chapter numbers.
        """
        # Prepare inputs.
        chapters = [
            ("Introduction", "# Introduction\nIntro content"),
            ("Main Content", "# Main Content\nMain content"),
        ]
        add_numbers = True
        # Run test.
        dsdstc._write_chapters(chapters, self.temp_dir, add_numbers=add_numbers)
        # Check outputs.
        files = sorted(os.listdir(self.temp_dir))
        self.assertEqual(len(files), 2)
        self.assertIn("1_Introduction.md", files)
        self.assertIn("2_Main_Content.md", files)

    def test3(self) -> None:
        """
        Output directory is created if it doesn't exist.
        """
        # Prepare inputs.
        output_dir = os.path.join(self.temp_dir, "nonexistent", "subdir")
        chapters = [("Chapter 1", "# Chapter 1\nContent")]
        add_numbers = False
        # Run test.
        dsdstc._write_chapters(chapters, output_dir, add_numbers=add_numbers)
        # Check outputs.
        self.assertTrue(os.path.isdir(output_dir))
        files = os.listdir(output_dir)
        self.assertEqual(len(files), 1)

    def test4(self) -> None:
        """
        Chapter writing with special character titles.
        """
        # Prepare inputs.
        chapters = [
            ("Chapter 1: Introduction", "# Chapter 1: Introduction\nContent"),
        ]
        add_numbers = False
        # Run test.
        dsdstc._write_chapters(chapters, self.temp_dir, add_numbers=add_numbers)
        # Check outputs.
        files = os.listdir(self.temp_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(any(f.startswith("Chapter_1") for f in files))


class TestIntegration(hunitest.TestCase):
    """
    Integration tests for the full chapter splitting workflow.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator[None, None, None]:
        """
        Setup and teardown for each test.
        """
        self.set_up_test()
        yield
        self.tear_down_test()

    def set_up_test(self) -> None:
        """
        Setup code that runs before each test.
        """
        self.temp_dir = tempfile.mkdtemp()

    def tear_down_test(self) -> None:
        """
        Cleanup code that runs after each test.
        """
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test1(self) -> None:
        """
        Complete workflow: extract, validate, and write chapters.
        """
        # Prepare inputs.
        input_file = os.path.join(self.temp_dir, "book.md")
        content = """# Introduction
This is the introduction chapter.

# The Main Content
This is the main content.
With multiple lines.

# Conclusion
Final thoughts."""
        with open(input_file, "w") as f:
            f.write(content)
        # Run test.
        with open(input_file, "r") as f:
            content = f.read()
        chapters = dsdstc._extract_chapters(content)
        dsdstc._validate_chapters(chapters)
        output_dir = os.path.join(self.temp_dir, "output")
        dsdstc._write_chapters(chapters, output_dir, add_numbers=True)
        # Check outputs.
        files = sorted(os.listdir(output_dir))
        self.assertEqual(len(files), 3)
        self.assertIn("1_Introduction.md", files)
        self.assertIn("2_The_Main_Content.md", files)
        self.assertIn("3_Conclusion.md", files)

    def test2(self) -> None:
        """
        All output filenames are unique.
        """
        # Prepare inputs.
        input_content = """# Cheap Changes Everything
Content.

# Prediction Machine Magic
Content.

# Introduction Machine Intelligence
Content.

# The Beginning
Content."""
        # Run test.
        chapters = dsdstc._extract_chapters(input_content)
        self.assertEqual(len(chapters), 4)
        dsdstc._validate_chapters(chapters)
        output_dir = os.path.join(self.temp_dir, "output")
        dsdstc._write_chapters(chapters, output_dir, add_numbers=False)
        # Check outputs.
        files = os.listdir(output_dir)
        self.assertEqual(len(files), len(set(files)))
