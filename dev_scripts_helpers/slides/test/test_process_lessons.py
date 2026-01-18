import logging
import os
from typing import List

import helpers.hunit_test as hunitest

import dev_scripts_helpers.slides.process_lessons as dshsprle

_LOG = logging.getLogger(__name__)

# #############################################################################
# Test_parse_lecture_patterns
# #############################################################################

class Test_parse_lecture_patterns(hunitest.TestCase):
    """
    Test _parse_lecture_patterns function for parsing lecture patterns and ranges.
    """

    def _helper(
        self,
        lectures_arg: str,
        expected_is_range: bool,
        expected_patterns: List[str],
    ) -> None:
        """
        Helper to test _parse_lecture_patterns and assert results.
        """
        # Run test.
        actual_is_range, actual_patterns = dshsprle._parse_lecture_patterns(
            lectures_arg
        )
        # Check outputs.
        self.assertEqual(actual_is_range, expected_is_range)
        self.assertEqual(actual_patterns, expected_patterns)

    def test1(self) -> None:
        """
        Test parsing a single lecture pattern.

        Input: '01.1'
        Expected output: (False, ['01.1'])
        """
        # Prepare inputs.
        lectures_arg = "01.1"
        expected_is_range = False
        expected_patterns = ["01.1"]
        # Run test.
        self._helper(lectures_arg, expected_is_range, expected_patterns)

    def test2(self) -> None:
        """
        Test parsing a wildcard pattern.

        Input: '01*'
        Expected output: (False, ['01*'])
        """
        # Prepare inputs.
        lectures_arg = "01*"
        expected_is_range = False
        expected_patterns = ["01*"]
        # Run test.
        self._helper(lectures_arg, expected_is_range, expected_patterns)

    def test3(self) -> None:
        """
        Test parsing multiple patterns separated by colons (union syntax).

        Input: '01*:02*:03.1'
        Expected output: (False, ['01*', '02*', '03.1'])
        """
        # Prepare inputs.
        lectures_arg = "01*:02*:03.1"
        expected_is_range = False
        expected_patterns = ["01*", "02*", "03.1"]
        # Run test.
        self._helper(lectures_arg, expected_is_range, expected_patterns)

    def test4(self) -> None:
        """
        Test parsing a range pattern with hyphen separator.

        Input: '01.1-03.2'
        Expected output: (True, ['01.1', '03.2'])
        """
        # Prepare inputs.
        lectures_arg = "01.1-03.2"
        expected_is_range = True
        expected_range = ["01.1", "03.2"]
        # Run test.
        self._helper(lectures_arg, expected_is_range, expected_range)

    def test5(self) -> None:
        """
        Test that mixing range and union syntax raises AssertionError.

        Input: '01.1-03.2:04*'
        Expected: AssertionError with message about mixing syntaxes
        """
        # Prepare inputs.
        lectures_arg = "01.1-03.2:04*"
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshsprle._parse_lecture_patterns(lectures_arg)
        expected_error = (
            "Cannot mix range syntax (hyphen) with union syntax (colon)"
        )
        self.assertIn(expected_error, str(cm.exception))

    def test6(self) -> None:
        """
        Test that invalid range format raises AssertionError.

        Input: '01.1-03.2-05.1'
        Expected: AssertionError with message about exactly two parts
        """
        # Prepare inputs.
        lectures_arg = "01.1-03.2-05.1"
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshsprle._parse_lecture_patterns(lectures_arg)
        expected_error = "Range syntax must have exactly two parts (start-end)"
        self.assertIn(expected_error, str(cm.exception))

# #############################################################################
# Test_expand_lecture_range
# #############################################################################

class Test_expand_lecture_range(hunitest.TestCase):
    """
    Test _expand_lecture_range function for finding files in a lesson range.

    Note: These tests require a mock directory structure with lecture files.
    """

    def _create_test_structure(
        self,
        test_files: List[str],
    ) -> str:
        """
        Create test directory structure with lecture files.

        :param test_files: List of lecture filenames to create
        :return: class_dir path
        """
        scratch_dir = self.get_scratch_space()
        class_dir = os.path.join(scratch_dir, "data605")
        lectures_source_dir = os.path.join(class_dir, "lectures_source")
        os.makedirs(lectures_source_dir)
        # Create mock lecture files.
        for filename in test_files:
            filepath = os.path.join(lectures_source_dir, filename)
            with open(filepath, "w") as f:
                f.write(f"Content of {filename}")
        return class_dir

    def test1(self) -> None:
        """
        Test expanding a range that includes multiple lecture files.

        Input:
        - class_dir: 'data605' (with mock files Lesson01.1, Lesson01.2, Lesson02.1)
        - start_lesson: '01.1'
        - end_lesson: '02.1'

        Expected output:
        [
            ('.../Lesson01.1-Intro.txt', 'Lesson01.1-Intro.txt'),
            ('.../Lesson01.2-BigData.txt', 'Lesson01.2-BigData.txt'),
            ('.../Lesson02.1-Git.txt', 'Lesson02.1-Git.txt'),
        ]
        """
        # Prepare inputs.
        test_files = [
            "Lesson01.1-Intro.txt",
            "Lesson01.2-BigData.txt",
            "Lesson02.1-Git.txt",
        ]
        class_dir = self._create_test_structure(test_files)
        start_lesson = "01.1"
        end_lesson = "02.1"
        expected_count = 3
        expected_first_file = "Lesson01.1-Intro.txt"
        expected_last_file = "Lesson02.1-Git.txt"
        # Run test.
        actual_files = dshsprle._expand_lecture_range(
            class_dir, start_lesson, end_lesson
        )
        # Check outputs.
        self.assertEqual(len(actual_files), expected_count)
        self.assertEqual(actual_files[0][1], expected_first_file)
        self.assertEqual(actual_files[-1][1], expected_last_file)

    def test2(self) -> None:
        """
        Test expanding a range that includes only one lecture file.

        Input:
        - class_dir: 'data605' (with mock file Lesson01.1)
        - start_lesson: '01.1'
        - end_lesson: '01.1'

        Expected output:
        [('.../Lesson01.1-Intro.txt', 'Lesson01.1-Intro.txt')]
        """
        # Prepare inputs.
        test_files = ["Lesson01.1-Intro.txt"]
        class_dir = self._create_test_structure(test_files)
        start_lesson = "01.1"
        end_lesson = "01.1"
        expected_count = 1
        expected_file = "Lesson01.1-Intro.txt"
        # Run test.
        actual_files = dshsprle._expand_lecture_range(
            class_dir, start_lesson, end_lesson
        )
        # Check outputs.
        self.assertEqual(len(actual_files), expected_count)
        self.assertEqual(actual_files[0][1], expected_file)

    def test3(self) -> None:
        """
        Test that an empty range raises AssertionError.

        Input:
        - class_dir: 'data605' (with no matching files in range)
        - start_lesson: '99.1'
        - end_lesson: '99.9'

        Expected: AssertionError with message about no files found
        """
        # Prepare inputs.
        test_files = ["Lesson01.1-Intro.txt"]
        class_dir = self._create_test_structure(test_files)
        start_lesson = "99.1"
        end_lesson = "99.9"
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshsprle._expand_lecture_range(class_dir, start_lesson, end_lesson)
        expected_error = "No lecture files found in range"
        self.assertIn(expected_error, str(cm.exception))

# #############################################################################
# Test_find_lecture_files
# #############################################################################

class Test_find_lecture_files(hunitest.TestCase):
    """
    Test _find_lecture_files function for finding lecture files by patterns or range.

    Note: These tests require a mock directory structure with lecture files.
    """

    def _create_test_structure(
        self,
        test_files: List[str],
    ) -> str:
        """
        Create test directory structure with lecture files.

        :param test_files: List of lecture filenames to create
        :return: class_dir path
        """
        scratch_dir = self.get_scratch_space()
        class_dir = os.path.join(scratch_dir, "data605")
        lectures_source_dir = os.path.join(class_dir, "lectures_source")
        os.makedirs(lectures_source_dir)
        # Create mock lecture files.
        for filename in test_files:
            filepath = os.path.join(lectures_source_dir, filename)
            with open(filepath, "w") as f:
                f.write(f"Content of {filename}")
        return class_dir

    def _helper(
        self,
        class_dir: str,
        is_range: bool,
        patterns_or_range: List[str],
        expected_count: int,
    ) -> None:
        """
        Helper to test _find_lecture_files and assert result count.
        """
        # Run test.
        actual_files = dshsprle._find_lecture_files(
            class_dir, is_range, patterns_or_range
        )
        # Check outputs.
        self.assertEqual(len(actual_files), expected_count)

    def test1(self) -> None:
        """
        Test finding files using range mode.

        Input:
        - class_dir: 'data605'
        - is_range: True
        - patterns_or_range: ['01.1', '02.1']

        Expected output: List of tuples for files from Lesson01.1 to Lesson02.1
        """
        # Prepare inputs.
        test_files = [
            "Lesson01.1-Intro.txt",
            "Lesson01.2-BigData.txt",
            "Lesson02.1-Git.txt",
        ]
        class_dir = self._create_test_structure(test_files)
        is_range = True
        patterns_or_range = ["01.1", "02.1"]
        expected_count = 3
        # Run test.
        self._helper(class_dir, is_range, patterns_or_range, expected_count)

    def test2(self) -> None:
        """
        Test finding files using single pattern mode.

        Input:
        - class_dir: 'data605'
        - is_range: False
        - patterns_or_range: ['01*']

        Expected output: List of tuples for all files matching Lesson01*
        """
        # Prepare inputs.
        test_files = [
            "Lesson01.1-Intro.txt",
            "Lesson01.2-BigData.txt",
            "Lesson02.1-Git.txt",
        ]
        class_dir = self._create_test_structure(test_files)
        is_range = False
        patterns_or_range = ["01*"]
        expected_count = 2  # Lesson01.1 and Lesson01.2
        # Run test.
        self._helper(class_dir, is_range, patterns_or_range, expected_count)

    def test3(self) -> None:
        """
        Test finding files using multiple patterns (union syntax).

        Input:
        - class_dir: 'data605'
        - is_range: False
        - patterns_or_range: ['01*', '02*']

        Expected output: List of tuples for all files matching Lesson01* and Lesson02*
        """
        # Prepare inputs.
        test_files = [
            "Lesson01.1-Intro.txt",
            "Lesson01.2-BigData.txt",
            "Lesson02.1-Git.txt",
        ]
        class_dir = self._create_test_structure(test_files)
        is_range = False
        patterns_or_range = ["01*", "02*"]
        expected_count = 3  # All files match
        # Run test.
        self._helper(class_dir, is_range, patterns_or_range, expected_count)

    def test4(self) -> None:
        """
        Test that invalid range length raises AssertionError.

        Input:
        - class_dir: 'data605'
        - is_range: True
        - patterns_or_range: ['01.1', '02.1', '03.1']  # Too many elements

        Expected: AssertionError with message about exactly two elements
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        class_dir = os.path.join(scratch_dir, "data605")
        lectures_source_dir = os.path.join(class_dir, "lectures_source")
        os.makedirs(lectures_source_dir)
        is_range = True
        patterns_or_range = ["01.1", "02.1", "03.1"]
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshsprle._find_lecture_files(class_dir, is_range, patterns_or_range)
        expected_error = "Range must have exactly two elements"
        self.assertIn(expected_error, str(cm.exception))
