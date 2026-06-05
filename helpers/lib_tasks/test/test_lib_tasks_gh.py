import logging
import unittest.mock as umock
from typing import Any, List

import pandas as pd
import pytest

import helpers.hgit as hgit
import helpers.hplayback as hplayba
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_gh as hltltagh

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
        actual = hltltagh._get_gh_issue_title(issue_id, repo)
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
        _ = hltltagh._get_gh_issue_title(issue_id, repo)

    def test_get_org_name1(self) -> None:
        """
        Test _get_org_name when org_name is provided.
        """
        org_name = "test-org"
        result = hltltagh._get_org_name(org_name)
        expected = "test-org"
        self.assertEqual(result, expected)

    @umock.patch.object(hgit, "get_repo_full_name_from_dirname")
    def test_get_org_name2(self, mock_get_repo: umock.Mock) -> None:
        """
        Test _get_org_name when org_name is empty (infers from repo).
        """
        mock_get_repo.return_value = "causify-ai/helpers"
        result = hltltagh._get_org_name("")
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

    @umock.patch.object(hltltagh, "_gh_run_and_get_json")
    @umock.patch.object(hltltagh, "_get_org_name")
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
        result = hltltagh.gh_get_org_team_names("test-org", sort=True)
        # Verify result.
        expected = ["dev_backend", "dev_frontend", "qa_team"]
        self.assertEqual(result, expected)
        # Verify mocks were called correctly.
        mock_get_org_name.assert_called_once_with("test-org")
        mock_gh_run.assert_called_once_with(
            "gh api /orgs/test-org/teams --paginate"
        )

    @umock.patch.object(hltltagh, "_gh_run_and_get_json")
    @umock.patch.object(hltltagh, "_get_org_name")
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
        result = hltltagh.gh_get_team_member_names(
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
    Test the `gh_get_*` helpers against the committed real-`gh` fixture.

    Each test loads
    `helpers/lib_tasks/test/input/test_lib_tasks_gh/_gh_run_and_get_json.json`,
    patches `_gh_run_and_get_json()` with a `MockDict` of its recorded calls,
    and asserts properties of the helper's post-processing of the real
    `gh` output. Refresh the fixture with:

        i gh_create_mock_fixture

    Property-based assertions (not exact-value comparisons) so cosmetic
    drift in `gh` (e.g., a new workflow added) does not break tests, but
    schema drift (renamed fields, changed types) does.
    """

    # Repo recorded into the fixture; helpers must be called with this name so
    # the patched `_gh_run_and_get_json()` lookup hits a recorded entry.
    _REPO = "causify-ai/helpers"

    @classmethod
    def setUpClass(cls) -> None:
        """
        Load the committed fixture once per class run.

        `MockDict` is stateless after construction, so one instance is safely
        shared across tests.
        """
        super().setUpClass()
        cls._mock = hplayba.MockDict(hltltagh._GH_FIXTURE_FILE)

    def test_gh_get_workflows_sorts_and_stringifies(self) -> None:
        """
        Test that `gh_get_workflows()` stringifies ids and sorts by name.
        """
        # Run test.
        with self._patch():
            workflows = hltltagh.gh_get_workflows(self._REPO)
        # Check outputs.
        # Each entry exposes exactly `id` and `name`.
        for w in workflows:
            self.assertEqual(set(w.keys()), {"id", "name"})
        # Ids are stringified even though `gh` returns them as ints.
        self.assertTrue(all(isinstance(w["id"], str) for w in workflows))
        # Names are sorted lexicographically.
        names = [w["name"] for w in workflows]
        self.assertEqual(names, sorted(names))

    def test_gh_get_workflows_unsorted_preserves_recorded_order(self) -> None:
        """
        Test that `gh_get_workflows(sort=False)` preserves `gh`'s order.
        """
        # Run test.
        with self._patch():
            workflows = hltltagh.gh_get_workflows(self._REPO, sort=False)
        # Check outputs.
        # The recorded raw response is the authority for ordering.
        raw = self._mock(f"gh workflow list --json id,name --repo {self._REPO}")
        self.assertEqual([w["name"] for w in workflows], [r["name"] for r in raw])
        # Ids are still stringified.
        self.assertTrue(all(isinstance(w["id"], str) for w in workflows))

    def test_gh_get_open_prs_returns_recorded_payload(self) -> None:
        """
        Test that `gh_get_open_prs()` returns the recorded list of PR ids.
        """
        # Run test.
        with self._patch():
            prs = hltltagh.gh_get_open_prs(self._REPO)
        # Check outputs.
        self.assertIsInstance(prs, list)
        for pr in prs:
            self.assertEqual(set(pr.keys()), {"id"})
            self.assertIsInstance(pr["id"], str)
            # `gh` PR ids are GraphQL global ids prefixed with `PR_`.
            self.assertTrue(pr["id"].startswith("PR_"))

    def test_gh_get_workflow_type_names_sorted_no_duplicates(self) -> None:
        """
        Test that `gh_get_workflow_type_names()` returns sorted unique names.
        """
        # Run test.
        with self._patch():
            names = hltltagh.gh_get_workflow_type_names(self._REPO)
        # Check outputs.
        self.assertIsInstance(names, list)
        self.assertTrue(all(isinstance(n, str) for n in names))
        # Sorted lexicographically.
        self.assertEqual(names, sorted(names))
        # No duplicates (the helper asserts internally; mirror it here).
        self.assertEqual(len(names), len(set(names)))

    def test_gh_get_workflow_details_replays_recorded_chain(self) -> None:
        """
        Test that `gh_get_workflow_details()` replays the recorded chain.

        The fixture was captured by passing `workflows[0]["id"]` from
        `gh_get_workflows(repo)` into `gh_get_workflow_details()`. We
        replay that exact chain so the patched lookup hits the recorded
        entry.
        """
        # Run test.
        with self._patch():
            workflows = hltltagh.gh_get_workflows(self._REPO, sort=False)
            workflow_id = workflows[0]["id"]
            details = hltltagh.gh_get_workflow_details(
                self._REPO,
                workflow_id,
                ["conclusion", "status", "url", "workflowName"],
                1,
            )
        # Check outputs.
        self.assertIsInstance(details, list)
        # Each run entry exposes the requested fields.
        for run in details:
            self.assertEqual(
                set(run.keys()),
                {"conclusion", "status", "url", "workflowName"},
            )

    def _patch(self) -> Any:
        """
        Return a `unittest.mock.patch` context that swaps in the shared
        `MockDict` for `_gh_run_and_get_json()`.
        """
        return self._mock.patch(
            "helpers.lib_tasks.lib_tasks_gh._gh_run_and_get_json"
        )


# #############################################################################
# Test_gh_get_overall_build_status_for_repo1
# #############################################################################


class Test_gh_get_overall_build_status_for_repo1(hunitest.TestCase):
    """
    Test `gh_get_overall_build_status_for_repo()`, which derives its result
    directly from a DataFrame and does not call `_gh_run_and_get_json()`.
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
        actual = hltltagh.gh_get_overall_build_status_for_repo(
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
