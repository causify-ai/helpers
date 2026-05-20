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
import helpers.lib_tasks.lib_tasks_gh as hlitagh

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
# TestGhHelpersWithMockDict1
# #############################################################################


class TestGhHelpersWithMockDict1(hunitest.TestCase):
    """
    Test the `gh_get_*` helpers via `MockDict`-replayed `_gh_run_and_get_json`.

    Each test writes a self-contained fixture and patches the wrapped
    `_gh_run_and_get_json`, so the helpers can be exercised offline. The
    `helper()` below absorbs the boilerplate.
    """

    def helper(
        self,
        cmd: str,
        raw_result: Any,
        helper_fn: Any,
        helper_args: tuple,
        helper_kwargs: Dict[str, Any],
        expected: Any,
    ) -> None:
        """
        Replay one recorded call through a `gh_get_*` helper.

        :param cmd: command string the helper is expected to issue
        :param raw_result: value `_gh_run_and_get_json` would return
        :param helper_fn: helper to call (e.g., `hlitagh.gh_get_workflows`)
        :param helper_args: positional args for `helper_fn`
        :param helper_kwargs: keyword args for `helper_fn`
        :param expected: value the helper should return after its
            post-processing
        """
        # Prepare inputs.
        fixture_path = os.path.join(self.get_scratch_space(), "fixture.json")
        records = [{"args": [cmd], "kwargs": {}, "result": raw_result}]
        hplayba._save_records(fixture_path, records)
        mock_dict = hplayba.MockDict(fixture_path)
        # Run test.
        with mock_dict.patch(
            "helpers.lib_tasks.lib_tasks_gh._gh_run_and_get_json"
        ):
            actual = helper_fn(*helper_args, **helper_kwargs)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that `gh_get_workflows` sorts by name and stringifies ids.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh workflow list --json id,name --repo {repo_name}"
        raw = [
            {"id": 200, "name": "Slow tests"},
            {"id": 100, "name": "Fast tests"},
        ]
        # Prepare outputs.
        expected = [
            {"id": "100", "name": "Fast tests"},
            {"id": "200", "name": "Slow tests"},
        ]
        # Run test.
        self.helper(
            cmd, raw, hlitagh.gh_get_workflows, (repo_name,), {}, expected
        )

    def test2(self) -> None:
        """
        Test that `gh_get_workflows(sort=False)` preserves GitHub's order.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh workflow list --json id,name --repo {repo_name}"
        raw = [
            {"id": 200, "name": "Slow tests"},
            {"id": 100, "name": "Fast tests"},
        ]
        # Prepare outputs.
        expected = [
            {"id": "200", "name": "Slow tests"},
            {"id": "100", "name": "Fast tests"},
        ]
        # Run test.
        self.helper(
            cmd,
            raw,
            hlitagh.gh_get_workflows,
            (repo_name,),
            {"sort": False},
            expected,
        )

    def test3(self) -> None:
        """
        Test that `gh_get_workflow_details` returns the recorded payload.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        workflow_id = "12345"
        fields = ["conclusion", "status", "url", "workflowName"]
        limit = 1
        # The command format is copied verbatim from `gh_get_workflow_details`.
        # Use single `\` so Python's source-level line continuation collapses
        # the newlines the same way the function does at runtime.
        cmd = f"""
    gh run list \
        --json {",".join(fields)} \
        --repo {repo_name} \
        --branch master \
        --limit {limit} \
        --workflow "{workflow_id}"
    """
        raw = [
            {
                "conclusion": "success",
                "status": "completed",
                "url": "https://github.com/causify-ai/helpers/actions/runs/1",
                "workflowName": "Fast tests",
            }
        ]
        # Prepare outputs.
        expected = raw
        # Run test.
        self.helper(
            cmd,
            raw,
            hlitagh.gh_get_workflow_details,
            (repo_name, workflow_id, fields, limit),
            {},
            expected,
        )

    def test4(self) -> None:
        """
        Test that `gh_get_open_prs` returns the recorded payload.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh pr list --state 'open' --json id --repo {repo_name}"
        raw = [{"id": "PR_kwDO_a"}, {"id": "PR_kwDO_b"}]
        # Prepare outputs.
        expected = raw
        # Run test.
        self.helper(
            cmd, raw, hlitagh.gh_get_open_prs, (repo_name,), {}, expected
        )

    def test5(self) -> None:
        """
        Test that `gh_get_workflow_type_names` returns sorted names.
        """
        # Prepare inputs.
        repo_name = "causify-ai/helpers"
        cmd = f"gh workflow list --json name --repo {repo_name}"
        raw = [{"name": "Slow tests"}, {"name": "Fast tests"}]
        # Prepare outputs.
        expected = ["Fast tests", "Slow tests"]
        # Run test.
        self.helper(
            cmd,
            raw,
            hlitagh.gh_get_workflow_type_names,
            (repo_name,),
            {},
            expected,
        )


# #############################################################################
# Test_gh_get_overall_build_status_for_repo1
# #############################################################################


class Test_gh_get_overall_build_status_for_repo1(hunitest.TestCase):
    """
    Test `gh_get_overall_build_status_for_repo`, which derives its result
    directly from a DataFrame and does not call `_gh_run_and_get_json`.
    """

    def helper(self, conclusions: List[str], expected: str) -> None:
        """
        Build a one-column status DataFrame and check the overall status.

        :param conclusions: per-workflow `conclusion` values
        :param expected: overall status string returned by the helper
        """
        # Prepare inputs.
        repo_df = pd.DataFrame({"conclusion": conclusions})
        # Run test.
        actual = hlitagh.gh_get_overall_build_status_for_repo(
            repo_df, use_colors=False
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that an all-success table reports "Success".
        """
        # Prepare inputs.
        conclusions = ["success", "success"]
        # Prepare outputs.
        expected = "Success"
        # Run test.
        self.helper(conclusions, expected)

    def test2(self) -> None:
        """
        Test that any failure flips the overall status to "Failed".
        """
        # Prepare inputs.
        conclusions = ["success", "failure"]
        # Prepare outputs.
        expected = "Failed"
        # Run test.
        self.helper(conclusions, expected)
