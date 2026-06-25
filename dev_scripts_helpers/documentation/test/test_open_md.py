import os
import tempfile

import dev_scripts_helpers.documentation.open_md as dshdopmd
import helpers.hunit_test as hunitest


# #############################################################################
# Test_convert_ssh_to_https
# #############################################################################


class Test_convert_ssh_to_https(hunitest.TestCase):
    """
    Test SSH to HTTPS URL conversion.
    """

    def test_ssh_to_https(self) -> None:
        """
        Test converting SSH URL to HTTPS.
        """
        # Prepare inputs.
        ssh_url = "git@github.com:causify-ai/helpers.git"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(ssh_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_ssh_to_https_without_git_suffix(self) -> None:
        """
        Test converting SSH URL without .git suffix.
        """
        # Prepare inputs.
        ssh_url = "git@github.com:causify-ai/helpers"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(ssh_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_https_passthrough(self) -> None:
        """
        Test that HTTPS URLs are passed through.
        """
        # Prepare inputs.
        https_url = "https://github.com/causify-ai/helpers.git"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(https_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_https_without_git_suffix(self) -> None:
        """
        Test HTTPS URL without .git suffix.
        """
        # Prepare inputs.
        https_url = "https://github.com/causify-ai/helpers"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(https_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_unknown_format_passthrough(self) -> None:
        """
        Test unknown URL format is returned as-is.
        """
        # Prepare inputs.
        unknown_url = "file:///home/user/repo"
        expected = "file:///home/user/repo"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(unknown_url)
        # Check output.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_find_git_root_for_file
# #############################################################################


class Test_find_git_root_for_file(hunitest.TestCase):
    """
    Test finding git root for a file, handling subrepos.
    """

    def test_find_git_root_in_main_repo(self) -> None:
        """Test finding git root for file in main repo."""
=======
# #############################################################################
# Test_find_git_root_for_file
# #############################################################################


class Test_find_git_root_for_file(hunitest.TestCase):
    """
    Test finding git root for a file, handling subrepos.
    """

    def test_find_git_root_in_main_repo(self) -> None:
        """
        Test finding git root for file in main repo.
        """
>>>>>>> master
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a git repo.
            git_root = tmpdir
            git_dir = os.path.join(git_root, ".git")
            os.makedirs(git_dir)
            # Create a file in the repo.
            file_path = os.path.join(git_root, "test.md")
            with open(file_path, "w") as f:
                f.write("test")
            # Call function.
            result = dshdopmd._find_git_root_for_file(file_path)
            # Check result.
            self.assertEqual(result, git_root)

    def test_find_git_root_in_subdirectory(self) -> None:
        """
        Test finding git root for file in subdirectory of repo.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a git repo.
            git_root = tmpdir
            git_dir = os.path.join(git_root, ".git")
            os.makedirs(git_dir)
            # Create a subdirectory with a file.
            subdir = os.path.join(git_root, "docs", "guides")
            os.makedirs(subdir)
            file_path = os.path.join(subdir, "test.md")
            with open(file_path, "w") as f:
                f.write("test")
            # Call function.
            result = dshdopmd._find_git_root_for_file(file_path)
            # Check result.
            self.assertEqual(result, git_root)

    def test_find_git_root_in_subrepo(self) -> None:
        """
        Test finding git root for file in subrepo.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create main repo.
            main_root = tmpdir
            main_git_dir = os.path.join(main_root, ".git")
            os.makedirs(main_git_dir)
            # Create subrepo inside main repo.
            subrepo_dir = os.path.join(main_root, "submodule")
            os.makedirs(subrepo_dir)
            subrepo_git_dir = os.path.join(subrepo_dir, ".git")
            os.makedirs(subrepo_git_dir)
            # Create a file in subrepo.
            file_path = os.path.join(subrepo_dir, "test.md")
            with open(file_path, "w") as f:
                f.write("test")
            # Call function.
            result = dshdopmd._find_git_root_for_file(file_path)
            # Should find subrepo git root, not main repo.
            self.assertEqual(result, subrepo_dir)
