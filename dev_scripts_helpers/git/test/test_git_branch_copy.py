"""
End-to-end tests for `git_branch_copy.py`.

Import as:

import dev_scripts_helpers.git.test.test_git_branch_copy as dshgtgibc
"""

import unittest.mock as mock

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.git.git_branch_copy as dshggbc


# #############################################################################
# Test_get_remote_tracking_branch
# #############################################################################


class Test_get_remote_tracking_branch(hunitest.TestCase):
    """
    Tests for `_get_remote_tracking_branch()` function.
    """

    def test1(self) -> None:
        """
        Test that the local branch name is extracted from `origin/branch`.
        """
        # Run test.
        with mock.patch(
            "helpers.hsystem.system_to_string",
            return_value=(0, "origin/gp_scratch\n"),
        ):
            actual = dshggbc._get_remote_tracking_branch()
        # Check outputs.
        self.assertEqual(actual, "gp_scratch")

    def test2(self) -> None:
        """
        Test that `None` is returned when there is no upstream branch.
        """
        # Run test.
        with mock.patch(
            "helpers.hsystem.system_to_string",
            return_value=(1, ""),
        ):
            actual = dshggbc._get_remote_tracking_branch()
        # Check outputs.
        self.assertIsNone(actual)


# #############################################################################
# Test_get_parent_branch
# #############################################################################


class Test_get_parent_branch(hunitest.TestCase):
    """
    Tests for `get_parent_branch()` function.
    """

    def test1(self) -> None:
        """
        Test that the explicit override takes priority.
        """
        # Run test.
        with mock.patch(
            "dev_scripts_helpers.git.git_branch_copy._get_remote_tracking_branch",
            return_value="gp_scratch",
        ):
            actual = dshggbc.get_parent_branch("some_other_branch")
        # Check outputs.
        self.assertEqual(actual, "some_other_branch")

    def test2(self) -> None:
        """
        Test that the auto-detected remote tracking branch is used.
        """
        # Run test.
        with mock.patch(
            "dev_scripts_helpers.git.git_branch_copy._get_remote_tracking_branch",
            return_value="gp_scratch",
        ):
            actual = dshggbc.get_parent_branch("")
        # Check outputs.
        self.assertEqual(actual, "gp_scratch")

    def test3(self) -> None:
        """
        Test that `master` is used and a warning is issued when
        auto-detection fails.
        """
        # Run test.
        with mock.patch(
            "dev_scripts_helpers.git.git_branch_copy._get_remote_tracking_branch",
            return_value=None,
        ):
            with self.assertLogs(level="WARNING"):
                actual = dshggbc.get_parent_branch("")
        # Check outputs.
        self.assertEqual(actual, "master")


# #############################################################################
# Test_create_or_checkout_branch
# #############################################################################


class Test_create_or_checkout_branch(hunitest.TestCase):
    """
    Tests for `_create_or_checkout_branch()` function.
    """

    def test1(self) -> None:
        """
        Test creating a new branch from a non-master parent branch.
        """
        # Prepare inputs.
        new_branch_name = "gp_scratch_31"
        parent_branch = "gp_scratch"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.does_branch_exist", return_value=False
            ):
                dshggbc._create_or_checkout_branch(
                    new_branch_name, parent_branch, check_branch_name=True
                )
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ("git checkout gp_scratch && invoke git_branch_create --branch-name 'gp_scratch_31'",)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)

    def test2(self) -> None:
        """
        Test checking out an existing branch instead of creating it.
        """
        # Prepare inputs.
        new_branch_name = "gp_scratch_31"
        parent_branch = "gp_scratch"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.does_branch_exist", return_value=True
            ):
                dshggbc._create_or_checkout_branch(
                    new_branch_name, parent_branch, check_branch_name=True
                )
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('git checkout gp_scratch_31',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)

    def test3(self) -> None:
        """
        Test creating a new branch while skipping the naming convention
        check.
        """
        # Prepare inputs.
        new_branch_name = "gp_scratch_31"
        parent_branch = "gp_scratch"
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.does_branch_exist", return_value=False
            ):
                dshggbc._create_or_checkout_branch(
                    new_branch_name, parent_branch, check_branch_name=False
                )
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ("git checkout gp_scratch && invoke git_branch_create --branch-name 'gp_scratch_31' --no-check-branch-name",)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)


# #############################################################################
# Test_merge_parent_branch
# #############################################################################


class Test_merge_parent_branch(hunitest.TestCase):
    """
    Tests for `_merge_parent_branch()` function.
    """

    def test1(self) -> None:
        """
        Test that copying from `master` uses `invoke git_merge_master`.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            dshggbc._merge_parent_branch("master")
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('invoke git_merge_master --abort-if-not-ff --no-auto-merge',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)

    def test2(self) -> None:
        """
        Test that copying from a non-master parent uses a plain `git
        merge`.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            dshggbc._merge_parent_branch("gp_scratch")
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('git merge gp_scratch --ff-only',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)


# #############################################################################
# Test_copy_branch
# #############################################################################


class Test_copy_branch(hunitest.TestCase):
    """
    End-to-end tests for `copy_branch()`.
    """

    def test1(self) -> None:
        """
        Test copying a scratch branch: both source and new branch branch
        from `gp_scratch`.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.get_branch_name", return_value="gp_scratch_29"
            ):
                with mock.patch(
                    "dev_scripts_helpers.git.git_branch_copy._get_remote_tracking_branch",
                    return_value="gp_scratch",
                ):
                    with mock.patch(
                        "helpers.hgit.does_branch_exist", return_value=False
                    ):
                        dshggbc.copy_branch(new_branch_name="gp_scratch_31")
        # Check outputs: parent is detected as `gp_scratch`, not `master`.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('git clean -fd',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('git merge gp_scratch --ff-only',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ("git checkout gp_scratch && invoke git_branch_create --branch-name 'gp_scratch_31' --no-check-branch-name",)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('git merge --squash --ff gp_scratch_29 && git reset HEAD',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)

    def test2(self) -> None:
        """
        Test copying a task branch: parent stays `master`.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="AmpTask100_Foo",
            ):
                with mock.patch(
                    "dev_scripts_helpers.git.git_branch_copy._get_remote_tracking_branch",
                    return_value="master",
                ):
                    with mock.patch(
                        "helpers.hgit.does_branch_exist", return_value=False
                    ):
                        dshggbc.copy_branch(
                            new_branch_name="AmpTask101_Bar"
                        )
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('git clean -fd',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('invoke git_merge_master --abort-if-not-ff --no-auto-merge',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ("git checkout master && invoke git_branch_create --branch-name 'AmpTask101_Bar'",)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('git merge --squash --ff AmpTask100_Foo && git reset HEAD',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)

    def test3(self) -> None:
        """
        Test that an explicit `--parent_branch` override skips
        auto-detection.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.get_branch_name", return_value="gp_scratch_29"
            ):
                with mock.patch(
                    "helpers.hgit.does_branch_exist", return_value=False
                ):
                    dshggbc.copy_branch(
                        new_branch_name="gp_scratch_31",
                        parent_branch="gp_scratch",
                    )
        # Check outputs: no call to detect the remote tracking branch.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('git clean -fd',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('git merge gp_scratch --ff-only',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ("git checkout gp_scratch && invoke git_branch_create --branch-name 'gp_scratch_31' --no-check-branch-name",)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('git merge --squash --ff gp_scratch_29 && git reset HEAD',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)

    def test4(self) -> None:
        """
        Test that `master` is used with a warning when auto-detection
        fails.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.get_branch_name",
                return_value="AmpTask100_Foo",
            ):
                with mock.patch(
                    "dev_scripts_helpers.git.git_branch_copy._get_remote_tracking_branch",
                    return_value=None,
                ):
                    with mock.patch(
                        "helpers.hgit.does_branch_exist", return_value=False
                    ):
                        with self.assertLogs(level="WARNING"):
                            dshggbc.copy_branch(
                                new_branch_name="AmpTask101_Bar"
                            )
        # Check outputs: falls back to `master`.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('git clean -fd',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('invoke git_merge_master --abort-if-not-ff --no-auto-merge',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ("git checkout master && invoke git_branch_create --branch-name 'AmpTask101_Bar'",)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('git merge --squash --ff AmpTask100_Foo && git reset HEAD',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)

    def test5(self) -> None:
        """
        Test that copying `master` itself is rejected.
        """
        # Run test.
        with mock.patch(
            "helpers.hgit.get_branch_name", return_value="master"
        ):
            with self.assertRaises(AssertionError):
                dshggbc.copy_branch(new_branch_name="AmpTask101_Bar")

    def test6(self) -> None:
        """
        Test that `--skip_git_merge_master` skips the merge step.
        """
        # Run test and capture system calls.
        with hunteuti.capture_sys_calls() as invocations:
            with mock.patch(
                "helpers.hgit.get_branch_name", return_value="gp_scratch_29"
            ):
                with mock.patch(
                    "helpers.hgit.does_branch_exist", return_value=False
                ):
                    dshggbc.copy_branch(
                        new_branch_name="gp_scratch_31",
                        parent_branch="gp_scratch",
                        skip_git_merge_master=True,
                    )
        # Check outputs: no merge call.
        expected_str = r"""[
        {
        'function': hsystem.system
        'args': ('git clean -fd',)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ("git checkout gp_scratch && invoke git_branch_create --branch-name 'gp_scratch_31' --no-check-branch-name",)
        'kwargs': {'log_level': 20}
        },
        {
        'function': hsystem.system
        'args': ('git merge --squash --ff gp_scratch_29 && git reset HEAD',)
        'kwargs': {'log_level': 20}
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, invocations, expected_str)


# #############################################################################
# Test_git_branch_copy_py
# #############################################################################


class Test_git_branch_copy_py(hunitest.TestCase):
    """
    End-to-end tests for the `git_branch_copy.py` executable.
    """

    def test1(self) -> None:
        """
        Test that the CLI wires `--parent_branch` through to `copy_branch`.
        """
        # Prepare inputs.
        argv = [
            "git_branch_copy.py",
            "--new_branch_name",
            "gp_scratch_31",
            "--parent_branch",
            "gp_scratch",
        ]
        # Run test.
        parser = dshggbc._parse()
        with mock.patch("sys.argv", argv):
            with mock.patch(
                "dev_scripts_helpers.git.git_branch_copy.copy_branch"
            ) as copy_branch_mock:
                dshggbc._main(parser)
        # Check outputs.
        copy_branch_mock.assert_called_once_with(
            new_branch_name="gp_scratch_31",
            skip_git_merge_master=False,
            use_patch=False,
            check_branch_name=True,
            method="auto",
            parent_branch="gp_scratch",
        )

    def test2(self) -> None:
        """
        Test that `--no_check_branch_name` is wired through to
        `copy_branch`.
        """
        # Prepare inputs.
        argv = [
            "git_branch_copy.py",
            "--no_check_branch_name",
        ]
        # Run test.
        parser = dshggbc._parse()
        with mock.patch("sys.argv", argv):
            with mock.patch(
                "dev_scripts_helpers.git.git_branch_copy.copy_branch"
            ) as copy_branch_mock:
                dshggbc._main(parser)
        # Check outputs.
        copy_branch_mock.assert_called_once_with(
            new_branch_name="",
            skip_git_merge_master=False,
            use_patch=False,
            check_branch_name=False,
            method="auto",
            parent_branch="",
        )
