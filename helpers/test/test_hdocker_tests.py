"""
Unit tests for hdocker_tests.py
"""

import os

import helpers.hdocker_tests as hdtests
import helpers.hio as hio
import helpers.hunit_test as hunitest


# #############################################################################
# Test_get_docker_test_files
# #############################################################################


class Test_get_docker_test_files(hunitest.TestCase):
  """
  Test the get_docker_test_files function.
  """

  def test1(self) -> None:
    """
    Test finding docker test files in a directory.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    # Create test files.
    hio.to_file(os.path.join(scratch_dir, "docker_test_1.py"), "")
    hio.to_file(os.path.join(scratch_dir, "docker_test_2.py"), "")
    hio.to_file(os.path.join(scratch_dir, "other_file.py"), "")
    # Run test.
    actual = hdtests.get_docker_test_files(scratch_dir)
    # Check outputs.
    self.assertEqual(len(actual), 2)
    self.assertTrue(any("docker_test_1.py" in f for f in actual))
    self.assertTrue(any("docker_test_2.py" in f for f in actual))

  def test2(self) -> None:
    """
    Test with no matching files.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    # Create non-matching files.
    hio.to_file(os.path.join(scratch_dir, "test_file.py"), "")
    hio.to_file(os.path.join(scratch_dir, "other_file.py"), "")
    # Run test.
    actual = hdtests.get_docker_test_files(scratch_dir)
    # Check outputs.
    self.assertEqual(len(actual), 0)

  def test3(self) -> None:
    """
    Test with single docker test file.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    hio.to_file(os.path.join(scratch_dir, "docker_test_single.py"), "")
    # Run test.
    actual = hdtests.get_docker_test_files(scratch_dir)
    # Check outputs.
    self.assertEqual(len(actual), 1)
    self.assertTrue("docker_test_single.py" in actual[0])

  def test4(self) -> None:
    """
    Test that files are returned in sorted order.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    hio.to_file(os.path.join(scratch_dir, "docker_test_z.py"), "")
    hio.to_file(os.path.join(scratch_dir, "docker_test_a.py"), "")
    hio.to_file(os.path.join(scratch_dir, "docker_test_m.py"), "")
    # Run test.
    actual = hdtests.get_docker_test_files(scratch_dir)
    # Check outputs.
    self.assertEqual(len(actual), 3)
    # Verify sorted order.
    basenames = [os.path.basename(f) for f in actual]
    self.assertEqual(basenames, ["docker_test_a.py", "docker_test_m.py", "docker_test_z.py"])


# #############################################################################
# Test_run_docker_cmd
# #############################################################################


class Test_run_docker_cmd(hunitest.TestCase):
  """
  Test the run_docker_cmd function.
  """

  def test1(self) -> None:
    """
    Test that error is raised when test file does not exist.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    nonexistent_file = os.path.join(scratch_dir, "nonexistent.py")
    docker_cmd = os.path.join(scratch_dir, "docker_cmd.sh")
    # Create docker_cmd script.
    hio.to_file(docker_cmd, "#!/bin/bash\necho $1")
    # Run test and check output.
    with self.assertRaises(AssertionError):
      hdtests.run_docker_cmd(nonexistent_file, docker_cmd_script=docker_cmd)

  def test2(self) -> None:
    """
    Test that error is raised when docker_cmd.sh does not exist.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    test_file = os.path.join(scratch_dir, "docker_test.py")
    nonexistent_docker_cmd = os.path.join(scratch_dir, "nonexistent_docker_cmd.sh")
    # Create test file.
    hio.to_file(test_file, "")
    # Run test and check output.
    with self.assertRaises(AssertionError):
      hdtests.run_docker_cmd(test_file, docker_cmd_script=nonexistent_docker_cmd)


# #############################################################################
# Test_run_all_tests
# #############################################################################


class Test_run_all_tests(hunitest.TestCase):
  """
  Test the run_all_tests function.
  """

  def test1(self) -> None:
    """
    Test with no docker test files.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    # Create non-matching files.
    hio.to_file(os.path.join(scratch_dir, "test_file.py"), "")
    # Run test.
    actual = hdtests.run_all_tests(scratch_dir)
    # Check outputs.
    self.assertEqual(actual, 0)

  def test2(self) -> None:
    """
    Test with docker test files when docker_cmd.sh doesn't exist.
    """
    # Prepare inputs.
    scratch_dir = self.get_scratch_space()
    hio.to_file(os.path.join(scratch_dir, "docker_test_1.py"), "")
    nonexistent_docker_cmd = os.path.join(scratch_dir, "nonexistent_docker_cmd.sh")
    # Run test and check output.
    with self.assertRaises(AssertionError):
      hdtests.run_all_tests(scratch_dir, docker_cmd_script=nonexistent_docker_cmd)
