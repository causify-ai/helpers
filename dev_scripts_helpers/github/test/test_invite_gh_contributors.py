import os
import unittest.mock as mock
from typing import List, Tuple

import pandas as pd
import pytest

import helpers.hio as hio
import helpers.hunit_test as hunitest

MODULE_PATH = "dev_scripts_helpers.github.invite_gh_contributors"

dshgigco = pytest.importorskip(
    MODULE_PATH,
    reason="GitHub or Google client libraries not available; skipping inviter tests.",
)


# #############################################################################
# Test_extract_usernames_from_gsheet
# #############################################################################


@pytest.mark.slow(reason="Greater than 5s")
class Test_extract_usernames_from_gsheet(hunitest.TestCase):
    """
    Test that github usernames are correctly pulled.
    """

    def test1(self) -> None:
        # Mock and import.
        with (
            mock.patch(
                f"{MODULE_PATH}.hgodrapi.get_credentials", return_value="creds"
            ),
            mock.patch(
                f"{MODULE_PATH}.hgodrapi.from_gsheet",
                return_value=pd.DataFrame(
                    {"GitHub user": ["alice", "bob", None, ""]}
                ),
            ),
        ):
            mod = __import__(
                MODULE_PATH, fromlist=["extract_usernames_from_gsheet"]
            )
            extract = mod.extract_usernames_from_gsheet
            actual = extract("dummy_url")
        expected: List[str] = ["alice", "bob"]
        self.assertEqual(actual, expected)


# #############################################################################
# Test_extract_usernames_from_csv
# #############################################################################


@pytest.mark.slow(reason="Greater than 5s")
class Test_extract_usernames_from_csv(hunitest.TestCase):
    """
    Verify that GitHub usernames are correctly extracted from a CSV file.
    """

    def _create_file(
        self, dir_path: str, file_name: str, content: str
    ) -> str:
        """
        Create a file with content in a directory and return its path.

        :param dir_path: path to directory
        :param file_name: file name
        :param content: content in file
        :return: path to the file
        """
        os.makedirs(dir_path, exist_ok=True)
        file_path: str = os.path.join(dir_path, file_name)
        hio.to_file(file_name=file_path, txt=content)
        return file_path

    def test_basic(self) -> None:
        # Prepare inputs.
        base_dir: str = self.get_scratch_space()
        csv_path: str = self._create_file(
            base_dir,
            "users.csv",
            "GitHub user\nalice\nbob\n\n",
        )
        # Run.
        actual: List[str] = dshgigco.extract_usernames_from_csv(str(csv_path))
        expected: List[str] = ["alice", "bob"]
        # Check.
        self.assertEqual(actual, expected)


# #############################################################################
# Test__get_github_token
# #############################################################################


class Test__get_github_token(hunitest.TestCase):
    """
    Test that the token comes from the env var first, then from `gh`.
    """

    def test_env_var(self) -> None:
        with (
            mock.patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}),
            mock.patch(f"{MODULE_PATH}.hsystem.system_to_string") as m_system,
        ):
            actual = dshgigco._get_github_token()
        # Check.
        self.assertEqual(actual, "env_token")
        m_system.assert_not_called()

    def test_gh_cli(self) -> None:
        with (
            mock.patch.dict(os.environ, clear=True),
            mock.patch(
                f"{MODULE_PATH}.hsystem.system_to_string",
                return_value=(0, "gh_token\n"),
            ) as m_system,
        ):
            actual = dshgigco._get_github_token()
        # Check.
        self.assertEqual(actual, "gh_token")
        self.assertEqual(m_system.call_args.args[0], "gh auth token")

    def test_no_token(self) -> None:
        with (
            mock.patch.dict(os.environ, clear=True),
            mock.patch(
                f"{MODULE_PATH}.hsystem.system_to_string", return_value=(1, "")
            ),
        ):
            with self.assertRaises(AssertionError):
                dshgigco._get_github_token()


# #############################################################################
# Test__split_usernames
# #############################################################################


class Test__split_usernames(hunitest.TestCase):
    """
    Test the difference between the passed users and the already invited ones.
    """

    def test_all_new(self) -> None:
        # Run.
        actual = dshgigco._split_usernames(["alice", "bob"], set(), set())
        # Check.
        expected = ([], [], ["alice", "bob"])
        self.assertEqual(actual, expected)

    def test_mixed(self) -> None:
        # Run.
        actual = dshgigco._split_usernames(
            ["alice", "bob", "carol", "dave"], {"bob"}, {"carol"}
        )
        # Check.
        expected = (["bob"], ["carol"], ["alice", "dave"])
        self.assertEqual(actual, expected)

    def test_case_insensitive_and_duplicates(self) -> None:
        # Run.
        actual = dshgigco._split_usernames(
            ["Alice", "alice", "BOB", "Bob"], {"bob"}, set()
        )
        # Check.
        expected = (["BOB", "Bob"], [], ["Alice", "alice"])
        self.assertEqual(actual, expected)


# #############################################################################
# Test_send_invitations
# #############################################################################


@pytest.mark.slow(reason="Greater than 5s")
class Test_send_invitations(hunitest.TestCase):
    """
    Test that an invitation is sent once per user to invite.
    """

    def _run(
        self,
        usernames: List[str],
        *,
        skip_invited: bool,
        dry_run: bool,
        permission: str = "write",
    ) -> Tuple[mock.Mock, mock.Mock]:
        """
        Run `send_invitations()` with a mocked GitHub repo.

        The repo has `carol` as collaborator and `dave` as pending invitation.

        :return: the mocked `_invite()` and the mocked repo
        """
        with (
            mock.patch(f"{MODULE_PATH}.github.Github") as m_github,
            mock.patch(f"{MODULE_PATH}._invite") as m_invite,
        ):
            repo = mock.Mock()
            repo.get_collaborators.return_value = [mock.Mock(login="Carol")]
            repo.get_pending_invitations.return_value = [
                mock.Mock(invitee=mock.Mock(login="Dave"))
            ]
            m_github.return_value.get_repo.return_value = repo
            dshgigco.send_invitations(
                usernames,
                "fake_token",
                "myrepo",
                "myorg",
                skip_invited=skip_invited,
                dry_run=dry_run,
                permission=permission,
            )
        return m_invite, repo

    def test_invite_all(self) -> None:
        # Run.
        m_invite, repo = self._run(
            ["alice", "bob"], skip_invited=True, dry_run=False
        )
        # Check.
        calls = [
            mock.call(repo, u, permission="write") for u in ["alice", "bob"]
        ]
        m_invite.assert_has_calls(calls, any_order=False)
        self.assertEqual(m_invite.call_count, 2)

    def test_skip_invited(self) -> None:
        # Run.
        m_invite, repo = self._run(
            ["alice", "carol", "dave", "bob"], skip_invited=True, dry_run=False
        )
        # Check.
        calls = [
            mock.call(repo, u, permission="write") for u in ["alice", "bob"]
        ]
        m_invite.assert_has_calls(calls, any_order=False)
        self.assertEqual(m_invite.call_count, 2)

    def test_no_skip_invited(self) -> None:
        # Run.
        m_invite, repo = self._run(
            ["alice", "carol", "dave"], skip_invited=False, dry_run=False
        )
        # Check.
        calls = [
            mock.call(repo, u, permission="write")
            for u in ["alice", "carol", "dave"]
        ]
        m_invite.assert_has_calls(calls, any_order=False)
        self.assertEqual(m_invite.call_count, 3)
        repo.get_collaborators.assert_not_called()
        repo.get_pending_invitations.assert_not_called()

    def test_permission(self) -> None:
        """
        Test that the passed permission is granted to the invited user.
        """
        # Prepare inputs.
        usernames = ["alice"]
        # Run test.
        m_invite, repo = self._run(
            usernames, skip_invited=True, dry_run=False, permission="pull"
        )
        # Check outputs.
        m_invite.assert_called_once_with(repo, "alice", permission="pull")

    def test_dry_run(self) -> None:
        # Run.
        m_invite, repo = self._run(
            ["alice", "bob"], skip_invited=True, dry_run=True
        )
        # Check that no invitation was sent.
        m_invite.assert_not_called()
        repo.add_to_collaborators.assert_not_called()


# #############################################################################
# Test__parse
# #############################################################################


class Test__parse(hunitest.TestCase):
    """
    Test the command line options to select the users to invite.
    """

    def test_add_gh_user(self) -> None:
        """
        Test that `--add_gh_user` can be repeated to pass many users.
        """
        # Prepare inputs.
        argv = [
            "--add_gh_user",
            "alice",
            "--add_gh_user",
            "bob",
            "--repo_name",
            "myrepo",
            "--org_name",
            "myorg",
        ]
        # Prepare outputs.
        expected = ["alice", "bob"]
        # Run test.
        args = dshgigco._parse().parse_args(argv)
        # Check outputs.
        self.assert_equal(str(args.add_gh_user), str(expected))
        self.assertIsNone(args.csv_file)
        self.assertIsNone(args.drive_url)
        self.assert_equal(args.permission, "write")

    def test_input_is_mutually_exclusive(self) -> None:
        """
        Test that `--add_gh_user` and `--csv_file` cannot be passed together.
        """
        # Prepare inputs.
        argv = [
            "--add_gh_user",
            "alice",
            "--csv_file",
            "users.csv",
            "--repo_name",
            "myrepo",
            "--org_name",
            "myorg",
        ]
        # Run test and check outputs.
        with self.assertRaises(SystemExit):
            dshgigco._parse().parse_args(argv)

    def test_input_is_required(self) -> None:
        """
        Test that one of `--add_gh_user`, `--csv_file`, `--drive_url` is needed.
        """
        # Prepare inputs.
        argv = ["--repo_name", "myrepo", "--org_name", "myorg"]
        # Run test and check outputs.
        with self.assertRaises(SystemExit):
            dshgigco._parse().parse_args(argv)


# #############################################################################
# Test__main
# #############################################################################


class Test__main(hunitest.TestCase):
    """
    Test that the users passed with `--add_gh_user` are invited.
    """

    def _run_main(self, argv: List[str]) -> mock.Mock:
        """
        Run `_main()` with a mocked `sys.argv` and a mocked GitHub client.

        :param argv: command-line arguments to inject via
            `mock.patch("sys.argv", ...)`
        :return: the mocked `send_invitations()`
        """
        parser = dshgigco._parse()
        with (
            mock.patch("sys.argv", argv),
            mock.patch(f"{MODULE_PATH}.hdbg.init_logger"),
            mock.patch(
                f"{MODULE_PATH}._get_github_token", return_value="fake_token"
            ),
            mock.patch(f"{MODULE_PATH}.send_invitations") as m_send,
        ):
            dshgigco._main(parser)
        return m_send

    def test_add_gh_user(self) -> None:
        """
        Test that the users are stripped and invited with the passed permission.
        """
        # Prepare inputs.
        argv = [
            "invite_gh_contributors.py",
            "--add_gh_user",
            " alice ",
            "--add_gh_user",
            "bob",
            "--repo_name",
            "myrepo",
            "--org_name",
            "myorg",
            "--permission",
            "pull",
        ]
        # Run test.
        m_send = self._run_main(argv)
        # Check outputs.
        m_send.assert_called_once_with(
            ["alice", "bob"],
            "fake_token",
            "myrepo",
            "myorg",
            skip_invited=True,
            dry_run=False,
            permission="pull",
        )

    def test_blank_user(self) -> None:
        """
        Test that a blank `--add_gh_user` is rejected.
        """
        # Prepare inputs.
        argv = [
            "invite_gh_contributors.py",
            "--add_gh_user",
            "  ",
            "--repo_name",
            "myrepo",
            "--org_name",
            "myorg",
        ]
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            self._run_main(argv)
