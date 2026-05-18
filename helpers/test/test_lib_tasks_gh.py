import logging
import os
import unittest.mock as umock
from typing import Any, Dict, List

import pandas as pd
import pytest

import helpers.hgit as hgit
import helpers.hplayback as hplayba
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

    def test_get_org_name1(self) -> None:
        """
        Test _get_org_name when org_name is provided.
        """
        org_name = "test-org"
        result = hlitagh._get_org_name(org_name)
        expected = "test-org"
        self.assertEqual(result, expected)

    @umock.patch.object(hgit, "get_repo_full_name_from_dirname")
    def test_get_org_name2(self, mock_get_repo: umock.Mock) -> None:
        """
        Test _get_org_name when org_name is empty (infers from repo).
        """
        mock_get_repo.return_value = "causify-ai/helpers"
        result = hlitagh._get_org_name("")
        expected = "causify-ai"
        self.assertEqual(result, expected)
        mock_get_repo.assert_called_once_with(".", include_host_name=False)


# #############################################################################
# TestGhOrgTeamFunctions
# #############################################################################


class TestGhOrgTeamFunctions(hunitest.TestCase):
    """
    Test gh_get_org_team_names and gh_get_team_member_names with mocked data.
    """

    @umock.patch.object(hlitagh, "_gh_run_and_get_json")
    @umock.patch.object(hlitagh, "_get_org_name")
    def test_gh_get_org_team_names1(
        self, mock_get_org_name: umock.Mock, mock_gh_run: umock.Mock
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
        mock_gh_run.assert_called_once_with(
            "gh api /orgs/test-org/teams --paginate"
        )

    @umock.patch.object(hlitagh, "_gh_run_and_get_json")
    @umock.patch.object(hlitagh, "_get_org_name")
    def test_gh_get_team_member_names1(
        self, mock_get_org_name: umock.Mock, mock_gh_run: umock.Mock
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
        result = hlitagh.gh_get_team_member_names(
            "dev_team", org_name="test-org"
        )
        # Verify result.
        expected = ["user1", "user2", "user3"]
        self.assertEqual(result, expected)
        # Verify mocks were called correctly.
        mock_get_org_name.assert_called_once_with("test-org")
        mock_gh_run.assert_called_once_with(
            "gh api /orgs/test-org/teams/dev_team/members --paginate"
        )


# #############################################################################
# _MockDictTestHelper
# #############################################################################


class _MockDictTestHelper(hunitest.TestCase):
    """
    Base class that writes a `MockDict` fixture into a scratch directory.

    Each fixture is self-contained: the test writes the records it needs and
    then patches `_gh_run_and_get_json` to replay them. This lets unit tests
    cover the helper functions without requiring real GitHub access or the
    production fixture file produced by `invoke gh_workflow_list --create_mock`.
    """

    def _write_fixture(
        self, records: List[Dict[str, Any]]
    ) -> hplayba.MockDict:
        """
        Save `records` to a fixture file and return a `MockDict` for it.

        :param records: list of `{args, kwargs, result}` dicts
        :return: `MockDict` instance ready to patch
            `_gh_run_and_get_json`
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        fixture_path = os.path.join(scratch_dir, "fixture.json")
        # Run test.
        hplayba._save_records(fixture_path, records)
        return hplayba.MockDict(fixture_path)


# #############################################################################
# Test_gh_get_workflows1
# #############################################################################


class Test_gh_get_workflows1(_MockDictTestHelper):
    """
    Test `gh_get_workflows` via `MockDict`-replayed `_gh_run_and_get_json`.
    """

    def test1(self) -> None:
        """
        Test that workflows are returned sorted by name with string ids.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh workflow list --json id,name --repo {repo_name}"
        records = [
            {
                "args": [cmd],
                "kwargs": {},
                "result": [
                    {"id": 200, "name": "Slow tests"},
                    {"id": 100, "name": "Fast tests"},
                ],
            }
        ]
        mock_dict = self._write_fixture(records)
        # Run test.
        with mock_dict.patch("helpers.lib_tasks_gh._gh_run_and_get_json"):
            actual = hlitagh.gh_get_workflows(repo_name)
        # Prepare outputs.
        expected = [
            {"id": "100", "name": "Fast tests"},
            {"id": "200", "name": "Slow tests"},
        ]
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that `sort=False` preserves the order returned by GitHub.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh workflow list --json id,name --repo {repo_name}"
        records = [
            {
                "args": [cmd],
                "kwargs": {},
                "result": [
                    {"id": 200, "name": "Slow tests"},
                    {"id": 100, "name": "Fast tests"},
                ],
            }
        ]
        mock_dict = self._write_fixture(records)
        # Run test.
        with mock_dict.patch("helpers.lib_tasks_gh._gh_run_and_get_json"):
            actual = hlitagh.gh_get_workflows(repo_name, sort=False)
        # Prepare outputs.
        expected = [
            {"id": "200", "name": "Slow tests"},
            {"id": "100", "name": "Fast tests"},
        ]
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_gh_get_workflow_details1
# #############################################################################


class Test_gh_get_workflow_details1(_MockDictTestHelper):
    """
    Test `gh_get_workflow_details` via `MockDict`.
    """

    def test1(self) -> None:
        """
        Test that the recorded workflow status is returned unchanged.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        workflow_id = "12345"
        fields = ["conclusion", "status", "url", "workflowName"]
        limit = 1
        cmd = f"""
    gh run list \\
        --json {",".join(fields)} \\
        --repo {repo_name} \\
        --branch master \\
        --limit {limit} \\
        --workflow "{workflow_id}"
    """
        recorded = [
            {
                "conclusion": "success",
                "status": "completed",
                "url": "https://github.com/causify-ai/helpers/actions/runs/1",
                "workflowName": "Fast tests",
            }
        ]
        records = [{"args": [cmd], "kwargs": {}, "result": recorded}]
        mock_dict = self._write_fixture(records)
        # Run test.
        with mock_dict.patch("helpers.lib_tasks_gh._gh_run_and_get_json"):
            actual = hlitagh.gh_get_workflow_details(
                repo_name, workflow_id, fields, limit
            )
        # Check outputs.
        self.assertEqual(actual, recorded)


# #############################################################################
# Test_gh_get_open_prs1
# #############################################################################


class Test_gh_get_open_prs1(_MockDictTestHelper):
    """
    Test `gh_get_open_prs` via `MockDict`.
    """

    def test1(self) -> None:
        """
        Test that the recorded list of open PRs is returned unchanged.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh pr list --state 'open' --json id --repo {repo_name}"
        recorded = [{"id": "PR_kwDO_a"}, {"id": "PR_kwDO_b"}]
        records = [{"args": [cmd], "kwargs": {}, "result": recorded}]
        mock_dict = self._write_fixture(records)
        # Run test.
        with mock_dict.patch("helpers.lib_tasks_gh._gh_run_and_get_json"):
            actual = hlitagh.gh_get_open_prs(repo_name)
        # Check outputs.
        self.assertEqual(actual, recorded)


# #############################################################################
# Test_gh_get_workflow_type_names1
# #############################################################################


class Test_gh_get_workflow_type_names1(_MockDictTestHelper):
    """
    Test `gh_get_workflow_type_names` via `MockDict`.
    """

    def test1(self) -> None:
        """
        Test that workflow names are returned sorted.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh workflow list --json name --repo {repo_name}"
        records = [
            {
                "args": [cmd],
                "kwargs": {},
                "result": [
                    {"name": "Slow tests"},
                    {"name": "Fast tests"},
                ],
            }
        ]
        mock_dict = self._write_fixture(records)
        # Run test.
        with mock_dict.patch("helpers.lib_tasks_gh._gh_run_and_get_json"):
            actual = hlitagh.gh_get_workflow_type_names(repo_name)
        # Prepare outputs.
        expected = ["Fast tests", "Slow tests"]
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_gh_get_overall_build_status_for_repo1
# #############################################################################


class Test_gh_get_overall_build_status_for_repo1(hunitest.TestCase):
    """
    Test `gh_get_overall_build_status_for_repo`, which derives its result
    directly from a DataFrame and does not call `_gh_run_and_get_json`.
    """

    def test1(self) -> None:
        """
        Test that an all-success table reports "Success".
        """
        # Prepare inputs.
        repo_df = pd.DataFrame({"conclusion": ["success", "success"]})
        # Run test.
        actual = hlitagh.gh_get_overall_build_status_for_repo(
            repo_df, use_colors=False
        )
        # Prepare outputs.
        expected = "Success"
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that any failure in the table flips the overall status to
        "Failed".
        """
        # Prepare inputs.
        repo_df = pd.DataFrame({"conclusion": ["success", "failure"]})
        # Run test.
        actual = hlitagh.gh_get_overall_build_status_for_repo(
            repo_df, use_colors=False
        )
        # Prepare outputs.
        expected = "Failed"
        # Check outputs.
        self.assertEqual(actual, expected)
