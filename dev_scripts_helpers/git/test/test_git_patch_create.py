"""
End-to-end tests for `git_patch_create.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_patch_create as dsggtgipac
"""

import pytest

import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.git.git_patch_create as dsggipac


# #############################################################################
# Test__create_patch
# #############################################################################


@pytest.mark.slow(reason="Around 7s")
@pytest.mark.skipif(
    not hgit.is_in_amp_as_supermodule(),
    reason="Run only in amp as super-module",
)
class Test__create_patch(hunitest.TestCase):
    """
    Test `_create_patch()`.
    """

    @staticmethod
    def helper(
        modified: bool, branch: bool, last_commit: bool, files: str
    ) -> None:
        dsggipac._create_patch(
            mode="tar",
            files=files,
            modified=modified,
            branch=branch,
            last_commit=last_commit,
        )
        dsggipac._create_patch(
            mode="diff",
            files=files,
            modified=modified,
            branch=branch,
            last_commit=last_commit,
        )

    def test1(self) -> None:
        """
        Test modified files mode.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        files = ""
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test2(self) -> None:
        """
        Test branch mode.
        """
        # Prepare inputs.
        modified = False
        branch = True
        last_commit = False
        files = ""
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test3(self) -> None:
        """
        Test last commit mode.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = False
        branch = False
        last_commit = True
        files = ""
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test4(self) -> None:
        """
        Test with specific files.
        """
        hgit.fetch_origin_master_if_needed()
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        files = __file__
        # Run test.
        self.helper(modified, branch, last_commit, files)

    def test5(self) -> None:
        """
        Test with all flags False raises AssertionError.
        """
        hgit.fetch_origin_master_if_needed()
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dsggipac._create_patch(mode="diff", files=__file__)
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '0'
        ==
        '1'
        Specify only one among --modified, --branch, --last-commit
        """
        self.assert_equal(actual, expected, fuzzy_match=True, dedent=True)


# #############################################################################
# Test_git_patch_create_py
# #############################################################################


class Test_git_patch_create_py(hunitest.TestCase):
    """
    End-to-end smoke test for the `git_patch_create.py` executable.
    """

    def test1(self) -> None:
        """
        Test that `--help` runs successfully.
        """
        # Prepare inputs.
        exec_path = hgit.find_file_in_git_tree("git_patch_create.py")
        cmd = f"{exec_path} --help"
        # Run test.
        rc, _ = hsystem.system_to_string(cmd)
        # Check outputs.
        self.assertEqual(rc, 0)
