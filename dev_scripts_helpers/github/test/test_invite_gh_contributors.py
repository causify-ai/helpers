import pathlib
import unittest.mock as mock
from typing import List

import pandas as pd
import pytest

import helpers.hio as hio
import helpers.hunit_test as hunitest

MODULE_PATH = "dev_scripts_helpers.github.dockerized_invite_gh_contributors"

dshgdigco = pytest.importorskip(
    MODULE_PATH,
    reason="Google client libraries not available; skipping Docker inviter tests.",
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
                f"{MODULE_PATH}.hgodrapi.read_google_file",
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

    def test_basic(self) -> None:
        # Prepare inputs.
        base_dir: pathlib.Path = pathlib.Path(self.get_scratch_space())
        csv_path: pathlib.Path = self._create_file(
            base_dir,
            "users.csv",
            "GitHub user\nalice\nbob\n\n",
        )
        # Run.
        actual: List[str] = dshgdigco.extract_usernames_from_csv(str(csv_path))
        expected: List[str] = ["alice", "bob"]
        # Check.
        self.assertEqual(actual, expected)

    def _create_file(
        self, dir_path: pathlib.Path, file_name: str, content: str
    ) -> pathlib.Path:
        """
        Create a file with content in a directory and return its path.

        :param dir_path: path to directory
        :param file_name: file name
        :param content: content in file
        :return: path to the file
        """
        dir_path.mkdir(parents=True, exist_ok=True)
        file_path: pathlib.Path = dir_path / file_name
        hio.to_file(file_name=str(file_path), txt=content)
        return file_path


# #############################################################################
# Test_send_invitations
# #############################################################################


@pytest.mark.slow(reason="Greater than 5s")
class Test_send_invitations(hunitest.TestCase):
    """
    Test that an invitation is sent once per user.
    """

    def test2(self) -> None:
        usernames = ["alice", "bob"]
        # Mock Github SDK, its repo, and our internal _invite helper.
        with mock.patch(f"{MODULE_PATH}.github.Github") as m_github:
            with mock.patch(f"{MODULE_PATH}._invite") as m_invite:
                dummy_repo = mock.Mock()
                dummy_repo.has_in_collaborators.return_value = False
                m_github.return_value.get_repo.return_value = dummy_repo
                # Import after patches so they take effect.
                mod = __import__(MODULE_PATH, fromlist=["send_invitations"])
                send_invitations = mod.send_invitations
                send_invitations(usernames, "fake_token", "myrepo", "myorg")
        # Assert one invite call per username.
        calls = [mock.call(dummy_repo, u) for u in usernames]
        m_invite.assert_has_calls(calls, any_order=False)
        self.assertEqual(m_invite.call_count, len(usernames))
