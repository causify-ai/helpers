import unittest.mock as mock
from typing import List

import pandas as pd

import helpers.hunit_test as hunitest

MODULE_PATH = "dev_scripts_helpers.github.github_invite_collaborators"


# #############################################################################
# Test_extract_usernames_from_gsheet
# #############################################################################


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
# Test_send_invitations
# #############################################################################


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
