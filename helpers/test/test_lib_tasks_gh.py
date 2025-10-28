import logging
from unittest import mock

import pytest

import helpers.hgit as hgit
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.lib_tasks_gh as hlitagh

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


# #############################################################################
# TestLibTasks1
# #############################################################################


class TestLibTasks1(hunitest.TestCase):
    """
    Test some auxiliary functions, e.g., `_get_gh_issue_title()`.
    """

    @pytest.mark.skip("CmTask #2362.")
    def test_get_gh_issue_title1(self) -> None:
        issue_id = 1
        repo = "amp"
        actual = hlitagh._get_gh_issue_title(issue_id, repo)
        expected = (
            "AmpTask1_Bridge_Python_and_R",
            "https://github.com/alphamatic/amp/issues/1",
        )
        self.assert_equal(str(actual), str(expected))

    @pytest.mark.skipif(
        not hgit.is_in_helpers_as_supermodule(),
        reason="""Skip unless helpers is the supermodule. Fails when updating submodules;
            passes in fast tests super-repo run. See CmTask10845.""",
    )
    def test_get_gh_issue_title4(self) -> None:
        cmd = "invoke gh_login"
        hsystem.system(cmd)
        #
        issue_id = 1
        repo = "current"
        _ = hlitagh._get_gh_issue_title(issue_id, repo)


# #############################################################################
# TestGhOrgTeamFunctions
# #############################################################################


class TestGhOrgTeamFunctions(hunitest.TestCase):
    """
    Test gh_get_org_team_names and gh_get_team_member_names with mocked data.
    """

    @mock.patch.object(hlitagh, "_gh_run_and_get_json")
    @mock.patch.object(hlitagh, "_get_org_name")
    def test_gh_get_org_team_names1(
        self, mock_get_org_name: mock.Mock, mock_gh_run: mock.Mock
    ) -> None:
        """
        Test gh_get_org_team_names with sorted team names.
        """
        # Setup mocks.
        mock_get_org_name.return_value = "test-org"
        mock_gh_run.return_value = [
            {"slug": "dev_backend", "id": 1},
            {"slug": "dev_frontend", "id": 2},
            {"slug": "qa_team", "id": 3},
        ]
        # Call function.
        result = hlitagh.gh_get_org_team_names("test-org", sort=True)
        # Verify result.
        expected = ["dev_backend", "dev_frontend", "qa_team"]
        self.assertEqual(result, expected)
        # Verify mocks were called correctly.
        mock_get_org_name.assert_called_once_with("test-org")
        mock_gh_run.assert_called_once_with("gh api /orgs/test-org/teams --paginate")

    @mock.patch.object(hlitagh, "_gh_run_and_get_json")
    @mock.patch.object(hlitagh, "_get_org_name")
    def test_gh_get_team_member_names1(
        self, mock_get_org_name: mock.Mock, mock_gh_run: mock.Mock
    ) -> None:
        """
        Test gh_get_team_member_names with member list.
        """
        # Setup mocks.
        mock_get_org_name.return_value = "test-org"
        mock_gh_run.return_value = [
            {"login": "user1", "id": 101},
            {"login": "user2", "id": 102},
            {"login": "user3", "id": 103},
        ]
        # Call function.
        result = hlitagh.gh_get_team_member_names("dev_team", org_name="test-org")
        # Verify result.
        expected = ["user1", "user2", "user3"]
        self.assertEqual(result, expected)
        # Verify mocks were called correctly.
        mock_get_org_name.assert_called_once_with("test-org")
        mock_gh_run.assert_called_once_with(
            "gh api /orgs/test-org/teams/dev_team/members --paginate"
        )
