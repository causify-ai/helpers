import logging
import os
import unittest
from unittest.mock import MagicMock, patch

import helpers.hsystem as hsystem
import helpers.hsystem as hsystem
import helpers.hgit as hgit
import helpers.hunit_test as hunitest

import importlib.util
import sys

# Load pre-commit module dynamically
# Assumes running from repo root
repo_root = os.getcwd()
spec_prco = importlib.util.spec_from_file_location(
    "pre_commit",
    os.path.join(repo_root, "dev_scripts_helpers/git/git_hooks/pre-commit.py"),
)
dsgghprco = importlib.util.module_from_spec(spec_prco)
spec_prco.loader.exec_module(dsgghprco)

# Load commit-msg module dynamically
spec_coms = importlib.util.spec_from_file_location(
    "commit_msg",
    os.path.join(repo_root, "dev_scripts_helpers/git/git_hooks/commit-msg.py"),
)
dsgghcoms = importlib.util.module_from_spec(spec_coms)
spec_coms.loader.exec_module(dsgghcoms)

_LOG = logging.getLogger(__name__)


class Test_git_hooks_integration(hunitest.TestCase):

    def test_pre_commit_success(self) -> None:
        """
        Test pre-commit hook runs successfully when all checks pass.
        """
        # Mock the checks in utils to all pass
        with patch(
            "dev_scripts_helpers.git.git_hooks.utils.check_master"
        ) as mock_master, patch(
            "dev_scripts_helpers.git.git_hooks.utils.check_author"
        ) as mock_author, patch(
            "dev_scripts_helpers.git.git_hooks.utils.check_file_size"
        ) as mock_size, patch(
            "dev_scripts_helpers.git.git_hooks.utils.check_words"
        ) as mock_words, patch(
            "dev_scripts_helpers.git.git_hooks.utils.check_python_compile"
        ) as mock_compile, patch(
            "dev_scripts_helpers.git.git_hooks.utils.check_gitleaks"
        ) as mock_leaks:

            # Run pre-commit main
            dsgghprco._main()

            # Verify all checks were called
            self.assertTrue(mock_master.called)
            self.assertTrue(mock_author.called)
            self.assertTrue(mock_size.called)
            # self.assertTrue(mock_words.called) # Disabled in pre-commit.py
            self.assertTrue(mock_compile.called)
            self.assertTrue(mock_leaks.called)

    def test_commit_msg_success(self) -> None:
        """
        Test commit-msg hook runs successfully.
        """
        # Create a dummy commit message file
        commit_msg_file = "COMMIT_EDITMSG"
        with open(commit_msg_file, "w") as f:
            f.write("Test commit message")

        try:
            # We need to simulate sys.argv
            with patch("sys.argv", ["commit-msg.py", commit_msg_file]), patch(
                "helpers.hsystem.system_to_one_line", return_value=(0, "Test User")
            ), patch("logging.getLogger"):

                # Call _main directly
                try:
                    dsgghcoms._main()
                except SystemExit as e:
                    # _main() implementation of commit-msg.py doesn't return value but might call sys.exit(0)
                    if e.code != 0:
                        raise e

        finally:
            if os.path.exists(commit_msg_file):
                os.remove(commit_msg_file)

    def test_pre_commit_fail_master(self) -> None:
        """
        Test pre-commit hook fails if check_master fails.
        """
        with patch(
            "dev_scripts_helpers.git.git_hooks.utils.check_master"
        ) as mock_master:
            # Simulate failure (usually check_master calls sys.exit(-1))
            mock_master.side_effect = SystemExit(-1)

            with self.assertRaises(SystemExit) as cm:
                dsgghprco._main()
            self.assertEqual(cm.exception.code, -1)
