#!/usr/bin/env python
"""
Unit tests for hdaemon.py.

Tests utility functions for file operations and hashing.
"""

import hashlib
import logging
import os

import helpers.hdaemon as hdaem
import helpers.hio as hio
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_file_hash
# #############################################################################


class Test_file_hash(hunitest.TestCase):
    """
    Test `file_hash()` function that computes MD5 hashes of files.
    """

    def helper(self, content: str) -> None:
        """
        Test helper for file_hash.

        :param content: File content to hash
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "test.txt")
        hio.to_file(test_file, content)
        # Prepare outputs.
        expected_hash = hashlib.md5(content.encode()).hexdigest()
        # Run test.
        actual = hdaem.file_hash(test_file)
        # Check outputs.
        self.assert_equal(actual, expected_hash)

    def test1(self) -> None:
        """
        Test hash of empty file.
        """
        # Prepare inputs.
        content = ""
        # Run test.
        self.helper(content)

    def test2(self) -> None:
        """
        Test hash of file with known content.
        """
        # Prepare inputs.
        content = "Hello, World!"
        # Run test.
        self.helper(content)

    def test3(self) -> None:
        """
        Test that different files produce different hashes.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file1 = os.path.join(scratch_dir, "file1.txt")
        file2 = os.path.join(scratch_dir, "file2.txt")
        content1 = "Content A"
        content2 = "Content B"
        hio.to_file(file1, content1)
        hio.to_file(file2, content2)
        # Run test.
        hash1 = hdaem.file_hash(file1)
        hash2 = hdaem.file_hash(file2)
        # Check outputs.
        expected_hash1 = hashlib.md5(content1.encode()).hexdigest()
        expected_hash2 = hashlib.md5(content2.encode()).hexdigest()
        self.assert_equal(hash1, expected_hash1)
        self.assert_equal(hash2, expected_hash2)

    def test4(self) -> None:
        """
        Test hash of large file (>65536 bytes to exercise chunking).
        """
        # Prepare inputs.
        content = "x" * 100000
        # Run test.
        self.helper(content)

    def test5(self) -> None:
        """
        Test that same file produces same hash consistently.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "consistent.txt")
        content = "Consistent content"
        hio.to_file(test_file, content)
        # Run test.
        hash1 = hdaem.file_hash(test_file)
        hash2 = hdaem.file_hash(test_file)
        # Check outputs.
        self.assert_equal(hash1, hash2)
