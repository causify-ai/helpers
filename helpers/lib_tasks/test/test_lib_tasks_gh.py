import contextlib
import datetime
import io
import json
import logging
import unittest.mock as umock
from typing import Any, Dict, List, Tuple

import invoke.exceptions as invexc
import pandas as pd
import pytest

import helpers.hdaemon as hdaemon
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hplayback as hplayba
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_gh as hltltagh
import helpers.lib_tasks.lib_tasks_utils as hltltaut
import helpers.lib_tasks.test.test_lib_tasks as httestlib

_LOG = logging.getLogger(__name__)

# pylint: disable=protected-access


# #############################################################################
# TestLibTasks1
# #############################################################################


class Test_get_gh_issue_title(hunitest.TestCase):
    """
    Test `_get_gh_issue_title()`.
    """

    @pytest.mark.skip("CmTask #2362.")
    def test1(self) -> None:
        """
        Test `_get_gh_issue_title()` basic case.
        """
        # Prepare inputs.
        issue_id = 1
        repo = "amp"
        # Prepare outputs.
        expected = (
            "AmpTask1_Bridge_Python_and_R",
            "https://github.com/alphamatic/amp/issues/1",
        )
        # Run test.
        actual = hltltagh._get_gh_issue_title(issue_id, repo)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    @pytest.mark.skipif(
        not hgit.is_in_helpers_as_supermodule(),
        reason="""Skip unless helpers is the supermodule. Fails when updating submodules;
            passes in fast tests super-repo run. See CmTask10845.""",
    )
    def test4(self) -> None:
        """
        Test `_get_gh_issue_title()` with current repo.
        """
        cmd = "invoke gh_login"
        hsystem.system(cmd)
        issue_id = 1
        repo = "current"
        _ = hltltagh._get_gh_issue_title(issue_id, repo)


class Test_get_org_name(hunitest.TestCase):
    """
    Test `_get_org_name()`.
    """

    def test1(self) -> None:
        """
        Test `_get_org_name()` when org_name is provided.
        """
        # Prepare inputs.
        org_name = "test-org"
        # Prepare outputs.
        expected = "test-org"
        # Run test.
        result = hltltagh._get_org_name(org_name)
        # Check outputs.
        self.assertEqual(result, expected)

    @umock.patch.object(hgit, "get_repo_full_name_from_dirname")
    def test2(self, mock_get_repo: umock.Mock) -> None:
        """
        Test `_get_org_name()` when org_name is empty (infers from repo).
        """
        # Setup mocks.
        mock_get_repo.return_value = "causify-ai/helpers"
        # Prepare inputs.
        org_name = ""
        # Prepare outputs.
        expected = "causify-ai"
        # Run test.
        result = hltltagh._get_org_name(org_name)
        # Check outputs.
        self.assertEqual(result, expected)
        mock_get_repo.assert_called_once_with(".", include_host_name=False)


# #############################################################################
# TestGhOrgTeamFunctions
# #############################################################################


class Test_gh_get_org_team_names(hunitest.TestCase):
    """
    Test `gh_get_org_team_names()`.
    """

    def test1(self) -> None:
        """
        Test `gh_get_org_team_names()` with sorted team names.
        """
        # Prepare inputs.
        org_name = "test-org"
        sort = True
        # Prepare outputs.
        expected = ["dev_backend", "dev_frontend", "qa_team"]
        # Run test.
        with (
            umock.patch.object(hltltagh, "_get_org_name") as mock_get_org_name,
            umock.patch.object(hltltagh, "_gh_run_and_get_json") as mock_gh_run,
        ):
            mock_get_org_name.return_value = "test-org"
            mock_gh_run.return_value = [
                {"slug": "dev_backend", "id": 1},
                {"slug": "dev_frontend", "id": 2},
                {"slug": "qa_team", "id": 3},
            ]
            result = hltltagh.gh_get_org_team_names(org_name, sort=sort)
        # Check outputs.
        self.assertEqual(result, expected)
        mock_get_org_name.assert_called_once_with(org_name)
        mock_gh_run.assert_called_once_with(
            "gh api /orgs/test-org/teams --paginate"
        )


class Test_gh_get_team_member_names(hunitest.TestCase):
    """
    Test `gh_get_team_member_names()`.
    """

    def test1(self) -> None:
        """
        Test `gh_get_team_member_names()` with member list.
        """
        # Prepare inputs.
        team_name = "dev_team"
        org_name = "test-org"
        # Prepare outputs.
        expected = ["user1", "user2", "user3"]
        # Run test.
        with (
            umock.patch.object(hltltagh, "_get_org_name") as mock_get_org_name,
            umock.patch.object(hltltagh, "_gh_run_and_get_json") as mock_gh_run,
        ):
            mock_get_org_name.return_value = "test-org"
            mock_gh_run.return_value = [
                {"login": "user1", "id": 101},
                {"login": "user2", "id": 102},
                {"login": "user3", "id": 103},
            ]
            result = hltltagh.gh_get_team_member_names(
                team_name, org_name=org_name
            )
        # Check outputs.
        self.assertEqual(result, expected)
        mock_get_org_name.assert_called_once_with(org_name)
        mock_gh_run.assert_called_once_with(
            "gh api /orgs/test-org/teams/dev_team/members --paginate"
        )


# #############################################################################
# TestGhGetWorkflows
# #############################################################################


class Test_gh_get_workflows(hunitest.TestCase):
    """
    Test `gh_get_workflows()` against the committed real-`gh` fixture.

    Loads `helpers/lib_tasks/test/input/test_lib_tasks_gh/_gh_run_and_get_json.json`,
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

    def _patch(self) -> Any:
        """
        Return a `unittest.mock.patch` context that swaps in the shared
        `MockDict` for `_gh_run_and_get_json()`.
        """
        return self._mock.patch(
            "helpers.lib_tasks.lib_tasks_gh._gh_run_and_get_json"
        )

    def test1(self) -> None:
        """
        Test that `gh_get_workflows()` stringifies ids and sorts by name.
        """
        # Prepare inputs.
        repo = self._REPO
        # Run test.
        with self._patch():
            workflows = hltltagh.gh_get_workflows(repo)
        # Check outputs.
        # Each entry exposes exactly `id` and `name`.
        for w in workflows:
            self.assertEqual(set(w.keys()), {"id", "name"})
        # Ids are stringified even though `gh` returns them as ints.
        self.assertTrue(all(isinstance(w["id"], str) for w in workflows))
        # Names are sorted lexicographically.
        names = [w["name"] for w in workflows]
        self.assertEqual(names, sorted(names))

    def test2(self) -> None:
        """
        Test that `gh_get_workflows(sort=False)` preserves `gh`'s order.
        """
        # Prepare inputs.
        repo = self._REPO
        sort = False
        # Run test.
        with self._patch():
            workflows = hltltagh.gh_get_workflows(repo, sort=sort)
            raw = self._mock(f"gh workflow list --json id,name --repo {repo}")
        # Check outputs.
        self.assertEqual(
            [w["name"] for w in workflows], [r["name"] for r in raw]
        )
        # Ids are still stringified.
        self.assertTrue(all(isinstance(w["id"], str) for w in workflows))


# #############################################################################
# TestGhGetOpenPrs
# #############################################################################


class Test_gh_get_open_prs(hunitest.TestCase):
    """
    Test `gh_get_open_prs()` against the committed real-`gh` fixture.

    Loads `helpers/lib_tasks/test/input/test_lib_tasks_gh/_gh_run_and_get_json.json`,
    patches `_gh_run_and_get_json()` with a `MockDict` of its recorded calls,
    and asserts properties of the helper's post-processing of the real
    `gh` output.
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

    def _patch(self) -> Any:
        """
        Return a `unittest.mock.patch` context that swaps in the shared
        `MockDict` for `_gh_run_and_get_json()`.
        """
        return self._mock.patch(
            "helpers.lib_tasks.lib_tasks_gh._gh_run_and_get_json"
        )

    def test1(self) -> None:
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


# #############################################################################
# TestGhGetWorkflowTypeNames
# #############################################################################


class Test_gh_get_workflow_type_names(hunitest.TestCase):
    """
    Test `gh_get_workflow_type_names()` against the committed real-`gh` fixture.

    Loads `helpers/lib_tasks/test/input/test_lib_tasks_gh/_gh_run_and_get_json.json`,
    patches `_gh_run_and_get_json()` with a `MockDict` of its recorded calls,
    and asserts properties of the helper's post-processing of the real
    `gh` output.
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

    def _patch(self) -> Any:
        """
        Return a `unittest.mock.patch` context that swaps in the shared
        `MockDict` for `_gh_run_and_get_json()`.
        """
        return self._mock.patch(
            "helpers.lib_tasks.lib_tasks_gh._gh_run_and_get_json"
        )

    def test1(self) -> None:
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


# #############################################################################
# TestGhGetWorkflowDetails
# #############################################################################


class Test_gh_get_workflow_details(hunitest.TestCase):
    """
    Test `gh_get_workflow_details()` against the committed real-`gh` fixture.

    Loads `helpers/lib_tasks/test/input/test_lib_tasks_gh/_gh_run_and_get_json.json`,
    patches `_gh_run_and_get_json()` with a `MockDict` of its recorded calls,
    and asserts properties of the helper's post-processing of the real
    `gh` output.
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

    def _patch(self) -> Any:
        """
        Return a `unittest.mock.patch` context that swaps in the shared
        `MockDict` for `_gh_run_and_get_json()`.
        """
        return self._mock.patch(
            "helpers.lib_tasks.lib_tasks_gh._gh_run_and_get_json"
        )

    def test1(self) -> None:
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


# #############################################################################
# Test_gh_get_overall_build_status_for_repo1
# #############################################################################


class Test_gh_get_overall_build_status_for_repo(hunitest.TestCase):
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


# #############################################################################
# Test_gh_login
# #############################################################################


class Test_gh_login(hunitest.TestCase):
    """
    Test `gh_login()`.
    """

    def test1(self) -> None:
        """
        Test that an existing PAT file triggers a token-login command.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        account = "test-org"

        def _exists(path: str) -> bool:
            return path.endswith("github_pat.test-org.txt")

        # Run test.
        with (
            umock.patch("helpers.lib_tasks.lib_tasks_utils.report_task"),
            umock.patch("os.path.expanduser", side_effect=lambda p: p),
            umock.patch("os.path.exists", side_effect=_exists),
        ):
            hltltagh.gh_login(ctx, account=account, print_status=False)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = ["gh auth login --with-token <~/.ssh/github_pat.test-org.txt"]
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test that a missing PAT file skips login but `print_status` still
        reports auth status before and after the (skipped) login attempt.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        account = "test-org"
        # Run test.
        with (
            umock.patch("helpers.lib_tasks.lib_tasks_utils.report_task"),
            umock.patch("os.path.expanduser", side_effect=lambda p: p),
            umock.patch("os.path.exists", return_value=False),
        ):
            hltltagh.gh_login(ctx, account=account, print_status=True)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = ["gh auth status", "gh auth status"]
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# GH runs fixtures
# #############################################################################


def _build_runs(
    runs: List[Tuple[str, str, str, str, int]],
) -> List[Dict[str, Any]]:
    """
    Build the run objects `gh run list --json` returns.

    :param runs: runs ordered newest-first, each as
        `(workflow, status, conclusion, branch, run_id)`
    :return: run objects, all created at 22:00 and updated at 22:10 UTC
    """
    created_at = "2026-07-28T22:00:00Z"
    updated_at = "2026-07-28T22:10:00Z"
    gh_runs = [
        {
            "name": workflow,
            "status": status,
            "conclusion": conclusion,
            "databaseId": run_id,
            "headBranch": branch,
            "createdAt": created_at,
            "updatedAt": updated_at,
        }
        for workflow, status, conclusion, branch, run_id in runs
    ]
    return gh_runs


def _build_runs_json(runs: List[Tuple[str, str, str, str, int]]) -> str:
    """
    Build the text printed by `gh run list --json` for the given runs.

    :param runs: see `_build_runs()`
    :return: JSON text with the list of runs
    """
    txt = json.dumps(_build_runs(runs))
    return txt


def _remove_colors(txt: str) -> str:
    """
    Remove the ANSI color codes from a printed report.

    :param txt: printed report
    :return: `txt` without ANSI color codes
    """
    txt = hprint.remove_non_printable_chars(txt)
    return txt


# #############################################################################
# Test_format_days_ago
# #############################################################################


class Test_format_days_ago(hunitest.TestCase):
    """
    Test `format_days_ago()`.
    """

    def test1(self) -> None:
        """
        Test that a run from 3 days and 1 hour ago is 3 days old.
        """
        # Prepare inputs.
        now = datetime.datetime.now(datetime.UTC)
        dt = now - datetime.timedelta(days=3, hours=1)
        # Prepare outputs.
        expected = "3 days ago"
        # Run test.
        actual = hltltagh.format_days_ago(dt)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_get_latest_runs_per_workflow
# #############################################################################


class Test_get_latest_runs_per_workflow(hunitest.TestCase):
    """
    Test `get_latest_runs_per_workflow()`.
    """

    def helper(
        self,
        gh_output: str,
        branch: str,
        expected_latest_runs: str,
        expected_in_progress: str,
    ) -> None:
        """
        Run the function on a fixed `gh run list --json` output.

        :param gh_output: text printed by `gh`
        :param branch: branch to report
        :param expected_latest_runs: expected `workflow -> (run id, conclusion)`
        :param expected_in_progress: expected sorted workflows in progress
        """
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, gh_output)
        ):
            latest_runs, in_progress = hltltagh.get_latest_runs_per_workflow(
                branch
            )
        # Check outputs.
        actual_latest_runs = {
            workflow: (run["databaseId"], run["conclusion"])
            for workflow, run in latest_runs.items()
        }
        self.assert_equal(str(actual_latest_runs), expected_latest_runs)
        self.assert_equal(str(sorted(in_progress)), expected_in_progress)

    def test1(self) -> None:
        """
        Test that only the runs of the requested branch are used.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "success", "feature", 4),
            ("Fast tests", "completed", "failure", "master", 3),
            ("Slow tests", "completed", "failure", "feature", 2),
            ("Slow tests", "completed", "success", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        branch = "master"
        # Prepare outputs.
        expected_latest_runs = (
            "{'Fast tests': (3, 'failure'), 'Slow tests': (1, 'success')}"
        )
        expected_in_progress = "[]"
        # Run test.
        self.helper(
            gh_output, branch, expected_latest_runs, expected_in_progress
        )

    def test2(self) -> None:
        """
        Test that the latest completed run of each workflow wins, also when
        the workflows have a different number of runs.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "failure", "master", 5),
            ("Slow tests", "completed", "success", "master", 4),
            ("Fast tests", "completed", "success", "master", 3),
            ("Fast tests", "completed", "failure", "master", 2),
        ]
        gh_output = _build_runs_json(runs)
        branch = "master"
        # Prepare outputs.
        expected_latest_runs = (
            "{'Fast tests': (5, 'failure'), 'Slow tests': (4, 'success')}"
        )
        expected_in_progress = "[]"
        # Run test.
        self.helper(
            gh_output, branch, expected_latest_runs, expected_in_progress
        )

    def test3(self) -> None:
        """
        Test that, when the newest run is in progress, the older completed run
        gives the verdict and the workflow is marked as in progress.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "in_progress", "", "master", 3),
            ("Fast tests", "completed", "success", "master", 2),
            ("Fast tests", "completed", "failure", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        branch = "master"
        # Prepare outputs.
        expected_latest_runs = "{'Fast tests': (2, 'success')}"
        expected_in_progress = "['Fast tests']"
        # Run test.
        self.helper(
            gh_output, branch, expected_latest_runs, expected_in_progress
        )

    def test4(self) -> None:
        """
        Test that an empty `gh` output gives an empty result.
        """
        # Prepare inputs.
        gh_output = ""
        branch = "master"
        # Prepare outputs.
        expected_latest_runs = "{}"
        expected_in_progress = "[]"
        # Run test.
        self.helper(
            gh_output, branch, expected_latest_runs, expected_in_progress
        )

    def test5(self) -> None:
        """
        Test that a workflow with only runs in progress has no verdict but is
        marked as in progress.
        """
        # Prepare inputs.
        runs = [
            ("Slow tests", "queued", "", "master", 2),
            ("Slow tests", "in_progress", "", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        branch = "master"
        # Prepare outputs.
        expected_latest_runs = "{}"
        expected_in_progress = "['Slow tests']"
        # Run test.
        self.helper(
            gh_output, branch, expected_latest_runs, expected_in_progress
        )

    def test6(self) -> None:
        """
        Test that a cancelled run is the verdict of a workflow, since it is
        the latest completed run.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "cancelled", "master", 2),
            ("Fast tests", "completed", "success", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        branch = "master"
        # Prepare outputs.
        expected_latest_runs = "{'Fast tests': (2, 'cancelled')}"
        expected_in_progress = "[]"
        # Run test.
        self.helper(
            gh_output, branch, expected_latest_runs, expected_in_progress
        )

    def test7(self) -> None:
        """
        Test that the `gh` command asks for JSON, does not filter by branch
        and targets the passed repo and limit.
        """
        # Prepare inputs.
        branch = "master"
        repo_full_name_with_host = "github.com/causify-ai/helpers"
        limit = 50
        # Prepare outputs.
        expected = (
            "gh run list --limit 50"
            " --json=name,status,conclusion,databaseId,updatedAt,createdAt,headBranch"
            " --repo github.com/causify-ai/helpers"
        )
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, "")
        ) as mock_system:
            hltltagh.get_latest_runs_per_workflow(
                branch,
                repo_full_name_with_host=repo_full_name_with_host,
                limit=limit,
            )
        # Check outputs.
        actual = mock_system.call_args.args[0]
        self.assert_equal(actual, expected)


# #############################################################################
# Test_get_failed_workflows
# #############################################################################


class Test_get_failed_workflows(hunitest.TestCase):
    """
    Test `get_failed_workflows()`.
    """

    def helper(
        self, runs: List[Tuple[str, str, str, str, int]], expected: str
    ) -> None:
        """
        Run the function on the latest runs built from `runs`.

        :param runs: see `_build_runs()`
        :param expected: expected sorted names of the failed workflows
        """
        # Run test.
        latest_runs = hltltagh.group_runs_by_workflow(_build_runs(runs))
        actual = hltltagh.get_failed_workflows(latest_runs)
        # Check outputs.
        self.assert_equal(str(actual), expected)

    def test1(self) -> None:
        """
        Test that a `failure` conclusion is reported as a failure.
        """
        # Prepare inputs.
        runs = [
            ("Slow tests", "completed", "failure", "master", 2),
            ("Fast tests", "completed", "success", "master", 1),
        ]
        # Prepare outputs.
        expected = "['Slow tests']"
        # Run test.
        self.helper(runs, expected)

    def test2(self) -> None:
        """
        Test that `cancelled`, `skipped` and `startup_failure` are not
        reported as a failure.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "cancelled", "master", 3),
            ("Slow tests", "completed", "skipped", "master", 2),
            ("Superslow tests", "completed", "startup_failure", "master", 1),
        ]
        # Prepare outputs.
        expected = "[]"
        # Run test.
        self.helper(runs, expected)


# #############################################################################
# Test_build_table_rows
# #############################################################################


class Test_build_table_rows(hunitest.TestCase):
    """
    Test `build_table_rows()` formatted with `format_table()`.
    """

    def test1(self) -> None:
        """
        Test the marker of a workflow with a newer run in progress and the log
        of a failed workflow.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "success", "master", 2),
            ("Slow tests", "completed", "failure", "master", 1),
        ]
        latest_runs = hltltagh.group_runs_by_workflow(_build_runs(runs))
        in_progress = {"Fast tests"}
        log_files = {"Slow tests": "tmp.failure.slow_tests.master.txt"}
        # Prepare outputs.
        expected = """
        | Workflow   | Status                          | Time  | Duration | Date       | Log                               |
        |------------|---------------------------------|-------|----------|------------|-----------------------------------|
        | Fast tests | success (newer run in progress) | 22:10 | 10m      | N days ago | -                                 |
        | Slow tests | failure                         | 22:10 | 10m      | N days ago | tmp.failure.slow_tests.master.txt |
        """
        # Run test.
        with umock.patch.object(
            hltltagh, "format_days_ago", return_value="N days ago"
        ):
            rows = hltltagh.build_table_rows(latest_runs, in_progress, log_files)
        actual = hltltagh.format_table(rows)
        # Check outputs.
        actual = _remove_colors(actual)
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_format_table
# #############################################################################


class Test_format_table(hunitest.TestCase):
    """
    Test `format_table()`.
    """

    def test1(self) -> None:
        """
        Test that `max_col_width` truncates the cells that are too wide.
        """
        # Prepare inputs.
        rows = [
            ["Workflow", "Log"],
            ["Fast tests", "tmp.failure.fast_tests.txt"],
        ]
        max_col_width = 8
        # Prepare outputs.
        expected = """
        | Workfl | Log    |
        |--------|--------|
        | Fast t | tmp.fa |
        """
        # Run test.
        actual = hltltagh.format_table(rows, max_col_width=max_col_width)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_gh_workflow_list
# #############################################################################


class Test_gh_workflow_list(hunitest.TestCase):
    """
    Test `gh_workflow_list()`.
    """

    def helper(
        self,
        gh_output: str,
        filter_by_branch: str,
        expected_stdout: str,
        expected_cmds: str,
        expected_exit_code: int,
        *,
        filter_by_completed: str = "all",
        git_branch: str = "HelpersTask1_Feature",
    ) -> None:
        """
        Run the task on a fixed `gh run list --json` output.

        :param gh_output: text printed by `gh`
        :param filter_by_branch: branch to report, see `gh_workflow_list()`
        :param expected_stdout: expected printed report
        :param expected_cmds: expected shell commands run to download a failed log
            and to reproduce the failed tests
        :param expected_exit_code: 0 if the task returns, otherwise the code of
            the `invoke` exit it raises
        :param filter_by_completed: see `gh_workflow_list()`
        :param git_branch: name of the current Git branch
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        repo_full_name_with_host = "github.com/causify-ai/helpers"
        stdout = io.StringIO()

        def _call() -> None:
            hltltagh.gh_workflow_list(
                ctx,
                filter_by_branch=filter_by_branch,
                filter_by_completed=filter_by_completed,
            )

        # Run test.
        with (
            umock.patch.object(hltltaut, "report_task"),
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=(repo_full_name_with_host, "helpers"),
            ),
            umock.patch.object(
                hltltagh, "format_days_ago", return_value="N days ago"
            ),
            umock.patch.object(hgit, "get_branch_name", return_value=git_branch),
            umock.patch.object(
                hgit, "find_helpers_root", return_value="/helpers_root"
            ),
            umock.patch.object(
                hsystem, "system_to_string", return_value=(0, gh_output)
            ),
            umock.patch.object(hsystem, "system") as mock_system,
            contextlib.redirect_stdout(stdout),
        ):
            if expected_exit_code == 0:
                _call()
            else:
                with self.assertRaises(invexc.Exit) as cm:
                    _call()
                self.assertEqual(cm.exception.code, expected_exit_code)
        # Check outputs.
        actual_cmds = [call.args[0] for call in mock_system.call_args_list]
        self.assert_equal("\n".join(actual_cmds), expected_cmds, dedent=True)
        actual_stdout = _remove_colors(stdout.getvalue())
        self.assert_equal(actual_stdout, expected_stdout, dedent=True)

    def test1(self) -> None:
        """
        Test that `filter_by_branch="all"` lists the runs of every branch with
        no verdict, so a failure does not give a non-zero exit.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "failure", "feature", 2),
            ("Fast tests", "completed", "success", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "all"
        # Prepare outputs.
        expected_stdout = """
        | Workflow   | Branch  | Status  | Time  | Duration | Date       |
        |------------|---------|---------|-------|----------|------------|
        | Fast tests | feature | failure | 22:10 | 10m      | N days ago |
        | Fast tests | master  | success | 22:10 | 10m      | N days ago |
        """
        expected_cmds = ""
        expected_exit_code = 0
        # Run test and check outputs.
        self.helper(
            gh_output,
            filter_by_branch,
            expected_stdout,
            expected_cmds,
            expected_exit_code,
        )

    def test2(self) -> None:
        """
        Test that a workflow whose latest completed run succeeded is reported
        as ok with a zero exit code.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "success", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "master"
        # Prepare outputs.
        expected_stdout = """
        | Workflow   | Status  | Time  | Duration | Date       | Log |
        |------------|---------|-------|----------|------------|-----|
        | Fast tests | success | 22:10 | 10m      | N days ago | -   |
        Workflow 'Fast tests' for 'master' is ok
        """
        expected_cmds = ""
        expected_exit_code = 0
        # Run test and check outputs.
        self.helper(
            gh_output,
            filter_by_branch,
            expected_stdout,
            expected_cmds,
            expected_exit_code,
        )

    def test3(self) -> None:
        """
        Test that a failed workflow downloads its log, reproduces the failed
        tests and makes the task exit with code 1.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "failure", "master", 7),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "master"
        # Prepare outputs.
        expected_stdout = """
        | Workflow   | Status  | Time  | Duration | Date       | Log                               |
        |------------|---------|-------|----------|------------|-----------------------------------|
        | Fast tests | failure | 22:10 | 10m      | N days ago | tmp.failure.fast_tests.master.txt |
        # Log is in 'tmp.failure.fast_tests.master.txt'
        """
        expected_cmds = """
        gh run view 7 --log-failed >tmp.failure.fast_tests.master.txt
        /helpers_root/dev_scripts_helpers/system_tools/remove_escape_chars.py -i tmp.failure.fast_tests.master.txt
        invoke pytest_repro --file-name tmp.failure.fast_tests.master.txt --script-name ./tmp.pytest_repro.fast_tests.sh
        """
        expected_exit_code = 1
        # Run test and check outputs.
        self.helper(
            gh_output,
            filter_by_branch,
            expected_stdout,
            expected_cmds,
            expected_exit_code,
        )

    def test4(self) -> None:
        """
        Test that `filter_by_branch="master"` on a feature branch keeps
        `master` in the messages and in the log file name (bug: the Git branch
        used to overwrite the filtered branch).
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "success", "HelpersTask1_Feature", 8),
            ("Fast tests", "completed", "failure", "master", 7),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "master"
        git_branch = "HelpersTask1_Feature"
        # Prepare outputs.
        expected_stdout = """
        | Workflow   | Status  | Time  | Duration | Date       | Log                               |
        |------------|---------|-------|----------|------------|-----------------------------------|
        | Fast tests | failure | 22:10 | 10m      | N days ago | tmp.failure.fast_tests.master.txt |
        # Log is in 'tmp.failure.fast_tests.master.txt'
        """
        expected_cmds = """
        gh run view 7 --log-failed >tmp.failure.fast_tests.master.txt
        /helpers_root/dev_scripts_helpers/system_tools/remove_escape_chars.py -i tmp.failure.fast_tests.master.txt
        invoke pytest_repro --file-name tmp.failure.fast_tests.master.txt --script-name ./tmp.pytest_repro.fast_tests.sh
        """
        expected_exit_code = 1
        # Run test and check outputs.
        self.helper(
            gh_output,
            filter_by_branch,
            expected_stdout,
            expected_cmds,
            expected_exit_code,
            git_branch=git_branch,
        )

    def test5(self) -> None:
        """
        Test that `filter_by_branch="current_branch"` reports the runs of the
        current Git branch.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "failure", "master", 8),
            ("Fast tests", "completed", "success", "HelpersTask1_Feature", 7),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "current_branch"
        git_branch = "HelpersTask1_Feature"
        # Prepare outputs.
        expected_stdout = """
        | Workflow   | Status  | Time  | Duration | Date       | Log |
        |------------|---------|-------|----------|------------|-----|
        | Fast tests | success | 22:10 | 10m      | N days ago | -   |
        Workflow 'Fast tests' for 'HelpersTask1_Feature' is ok
        """
        expected_cmds = ""
        expected_exit_code = 0
        # Run test and check outputs.
        self.helper(
            gh_output,
            filter_by_branch,
            expected_stdout,
            expected_cmds,
            expected_exit_code,
            git_branch=git_branch,
        )

    def test6(self) -> None:
        """
        Test that `cancelled` and `startup_failure` runs are shown but do not
        make the task exit with a non-zero code.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "cancelled", "master", 2),
            ("Slow tests", "completed", "startup_failure", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "master"
        # Prepare outputs.
        expected_stdout = """
        | Workflow   | Status          | Time  | Duration | Date       | Log |
        |------------|-----------------|-------|----------|------------|-----|
        | Fast tests | cancelled       | 22:10 | 10m      | N days ago | -   |
        | Slow tests | startup_failure | 22:10 | 10m      | N days ago | -   |
        """
        expected_cmds = ""
        expected_exit_code = 0
        # Run test and check outputs.
        self.helper(
            gh_output,
            filter_by_branch,
            expected_stdout,
            expected_cmds,
            expected_exit_code,
        )

    def test7(self) -> None:
        """
        Test that `filter_by_completed` keeps only the workflows with that
        conclusion.
        """
        # Prepare inputs.
        runs = [
            ("Fast tests", "completed", "success", "master", 2),
            ("Slow tests", "completed", "failure", "master", 1),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "master"
        filter_by_completed = "failure"
        # Prepare outputs.
        expected_stdout = """
        | Workflow   | Status  | Time  | Duration | Date       | Log                               |
        |------------|---------|-------|----------|------------|-----------------------------------|
        | Slow tests | failure | 22:10 | 10m      | N days ago | tmp.failure.slow_tests.master.txt |
        # Log is in 'tmp.failure.slow_tests.master.txt'
        """
        expected_cmds = """
        gh run view 1 --log-failed >tmp.failure.slow_tests.master.txt
        /helpers_root/dev_scripts_helpers/system_tools/remove_escape_chars.py -i tmp.failure.slow_tests.master.txt
        invoke pytest_repro --file-name tmp.failure.slow_tests.master.txt --script-name ./tmp.pytest_repro.slow_tests.sh
        """
        expected_exit_code = 1
        # Run test and check outputs.
        self.helper(
            gh_output,
            filter_by_branch,
            expected_stdout,
            expected_cmds,
            expected_exit_code,
            filter_by_completed=filter_by_completed,
        )

    def test8(self) -> None:
        """
        Test that a warning is issued and nothing is printed when no run
        matches the filters.
        """
        # Prepare inputs.
        gh_output = ""
        filter_by_branch = "master"
        # Prepare outputs.
        # Log message format: "LEVEL:logger.name:message".
        expected_log = (
            "WARNING:helpers.lib_tasks.lib_tasks_gh:No workflow runs found for "
            "filter_by_branch=master filter_by_completed=all"
        )
        # Run test.
        with self.assertLogs(hltltagh._LOG, level="WARNING") as cm:
            self.helper(gh_output, filter_by_branch, "", "", 0)
        # Check outputs.
        self.assert_equal("\n".join(cm.output), expected_log)

    def test9(self) -> None:
        """
        Test that `daemon=True` schedules the periodic report, and that the
        scheduled callback clears the screen and does not exit when a
        workflow failed.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        runs = [
            ("Fast tests", "completed", "failure", "master", 7),
        ]
        gh_output = _build_runs_json(runs)
        filter_by_branch = "master"
        interval = 30
        daemon = True
        # Run test.
        with (
            umock.patch.object(hltltaut, "report_task"),
            umock.patch.object(
                hdaemon, "run_periodic_daemon_mode"
            ) as mock_daemon,
        ):
            hltltagh.gh_workflow_list(
                ctx,
                filter_by_branch=filter_by_branch,
                daemon=daemon,
                interval=interval,
            )
        # Check outputs.
        mock_daemon.assert_called_once()
        run_fn, actual_interval = mock_daemon.call_args.args
        self.assertEqual(actual_interval, interval)
        self.assertEqual(
            mock_daemon.call_args.kwargs["window_name_str"], "*GH_WATCH*"
        )
        # Exercise the scheduled callback with a failed workflow: it must
        # return, so that the daemon keeps running.
        with (
            umock.patch("subprocess.run") as mock_subprocess,
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            umock.patch.object(
                hsystem, "system_to_string", return_value=(0, gh_output)
            ),
            umock.patch.object(hsystem, "system"),
            umock.patch.object(hgit, "find_helpers_root", return_value="/"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            run_fn()
        mock_subprocess.assert_called_once_with("clear", shell=True, check=False)


# #############################################################################
# Test_gh_watch
# #############################################################################


class Test_gh_watch(hunitest.TestCase):
    """
    Test `gh_watch()`.
    """

    def test1(self) -> None:
        """
        Test that `gh_watch()` runs `gh_workflow_list()` in daemon mode with
        the passed interval.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        interval = 30
        # Run test.
        with umock.patch.object(hltltagh, "gh_workflow_list") as mock_list:
            hltltagh.gh_watch(ctx, interval=interval)
        # Check outputs.
        mock_list.assert_called_once_with(ctx, daemon=True, interval=interval)


# #############################################################################
# Test_gh_workflow_run
# #############################################################################


class Test_gh_workflow_run(hunitest.TestCase):
    """
    Test `gh_workflow_run()`.
    """

    def test1(self) -> None:
        """
        Test that `workflows="all"` runs both fast and slow test workflows.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branch = "master"
        workflows = "all"
        # Prepare outputs.
        expected = [
            (
                "gh workflow run fast_tests.yml --ref master"
                " --repo github.com/causify-ai/helpers"
            ),
            (
                "gh workflow run slow_tests.yml --ref master"
                " --repo github.com/causify-ai/helpers"
            ),
        ]
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
        ):
            hltltagh.gh_workflow_run(ctx, branch=branch, workflows=workflows)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test that a specific workflow uses the current branch name.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        branch = "current_branch"
        workflows = "custom_workflow"
        # Prepare outputs.
        expected = [
            (
                "gh workflow run custom_workflow.yml --ref feature_x"
                " --repo github.com/causify-ai/helpers"
            )
        ]
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hgit, "get_branch_name", return_value="feature_x"
            ),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
        ):
            hltltagh.gh_workflow_run(ctx, branch=branch, workflows=workflows)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test that a non-default `repo_short_name` changes the `--repo`
        value in the constructed command.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/amp", "amp"),
            ) as mock_get_repo,
        ):
            hltltagh.gh_workflow_run(
                ctx,
                branch="master",
                workflows="fast_tests",
                repo_short_name="amp",
            )
        # Check outputs.
        mock_get_repo.assert_called_once_with("amp")
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = [
            (
                "gh workflow run fast_tests.yml --ref master"
                " --repo github.com/causify-ai/amp"
            )
        ]
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test__check_if_pr_exists
# #############################################################################


class Test__check_if_pr_exists(hunitest.TestCase):
    """
    Test `_check_if_pr_exists()`.
    """

    def helper(self, return_code: int, expected: bool) -> None:
        """
        Check that `_check_if_pr_exists()` maps a `gh pr diff` return code
        to a boolean.

        :param return_code: return code `hsystem.system()` is mocked to
            return
        :param expected: expected boolean result
        """
        # Prepare inputs.
        title = "HelpersTask123_Fix_bug"
        # Run test.
        with umock.patch.object(
            hsystem, "system", return_value=return_code
        ) as mock_system:
            actual = hltltagh._check_if_pr_exists(title)
        # Check outputs.
        self.assertEqual(actual, expected)
        mock_system.assert_called_once_with(
            f"gh pr diff {title}", abort_on_error=False
        )

    def test1(self) -> None:
        """
        Test that return code 0 means the PR exists.
        """
        # Prepare inputs.
        return_code = 0
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(return_code, expected)

    def test2(self) -> None:
        """
        Test that a nonzero return code means the PR does not exist.
        """
        # Prepare inputs.
        return_code = 1
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(return_code, expected)


# #############################################################################
# Test_gh_create_pr
# #############################################################################


class Test_gh_create_pr(hunitest.TestCase):
    """
    Test `gh_create_pr()`.
    """

    def test1(self) -> None:
        """
        Test that a nonexistent PR is created with the branch's issue
        number appended to the body.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hgit,
                "get_branch_name",
                return_value="HelpersTask123_Fix_bug",
            ),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            umock.patch.object(
                hltltagh, "_check_if_pr_exists", return_value=False
            ),
            umock.patch.object(
                hgit,
                "extract_gh_issue_number_from_branch",
                return_value=123,
            ),
        ):
            hltltagh.gh_create_pr(ctx, body="Desc", draft=True)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = [
            (
                "gh pr create --repo github.com/causify-ai/helpers --draft "
                "--title HelpersTask123_Fix_bug "
                "--body-file tmp.gh_create_pr.body.txt"
            )
        ]
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test that an already-existing PR is not recreated.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hgit, "get_branch_name", return_value="ExistingPR"
            ),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            umock.patch.object(
                hltltagh, "_check_if_pr_exists", return_value=True
            ),
        ):
            hltltagh.gh_create_pr(ctx)
        # Check outputs.
        self.assertEqual(list(ctx.run.mock_calls), [])

    def test3(self) -> None:
        """
        Test that `dry_run=True` never issues the underlying `ctx.run`
        call.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hgit,
                "get_branch_name",
                return_value="HelpersTask123_Fix_bug",
            ),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            umock.patch.object(
                hltltagh, "_check_if_pr_exists", return_value=False
            ),
            umock.patch.object(
                hgit,
                "extract_gh_issue_number_from_branch",
                return_value=None,
            ),
        ):
            hltltagh.gh_create_pr(ctx, dry_run=True)
        # Check outputs.
        self.assertEqual(list(ctx.run.mock_calls), [])


# #############################################################################
# Test_gh_publish_buildmeister_dashboard_to_s3
# #############################################################################


class Test_gh_publish_buildmeister_dashboard_to_s3(hunitest.TestCase):
    """
    Test `gh_publish_buildmeister_dashboard_to_s3()`.
    """

    def helper(self, mark_as_latest: bool, expected_calls: int) -> None:
        """
        Run the task and check how many files got copied to S3.

        :param mark_as_latest: value passed to the task
        :param expected_calls: expected number of `copy_file_to_s3` calls
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        html_file = "/repo/tmp.notebooks/Master_buildmeister_dashboard.01.html"
        # Run test.
        with (
            umock.patch.object(hserver, "is_inside_ci", return_value=True),
            umock.patch.object(
                hgit, "find_file_in_git_tree", return_value="run_notebook.py"
            ),
            umock.patch.object(hgit, "get_amp_abs_path", return_value="/repo"),
            umock.patch.object(hsystem, "system"),
            umock.patch.object(hio, "listdir", return_value=[html_file]),
            umock.patch("helpers.hs3.copy_file_to_s3") as mock_copy,
        ):
            hltltagh.gh_publish_buildmeister_dashboard_to_s3(
                ctx, mark_as_latest=mark_as_latest
            )
        # Check outputs.
        self.assertEqual(mock_copy.call_count, expected_calls)

    def test1(self) -> None:
        """
        Test that `mark_as_latest=True` copies both the latest and the
        timestamped file.
        """
        # Prepare inputs.
        mark_as_latest = True
        # Prepare outputs.
        expected_calls = 2
        # Run test.
        self.helper(mark_as_latest, expected_calls)

    def test2(self) -> None:
        """
        Test that `mark_as_latest=False` only copies the timestamped file.
        """
        # Prepare inputs.
        mark_as_latest = False
        # Prepare outputs.
        expected_calls = 1
        # Run test.
        self.helper(mark_as_latest, expected_calls)

    def test3(self) -> None:
        """
        Test that a non-default `repo_short_name` is resolved via
        `_get_repo_full_name_from_cmd()`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        html_file = "/repo/tmp.notebooks/Master_buildmeister_dashboard.01.html"
        # Run test.
        with (
            umock.patch.object(hserver, "is_inside_ci", return_value=True),
            umock.patch.object(
                hgit, "find_file_in_git_tree", return_value="run_notebook.py"
            ),
            umock.patch.object(hgit, "get_amp_abs_path", return_value="/repo"),
            umock.patch.object(hsystem, "system"),
            umock.patch.object(hio, "listdir", return_value=[html_file]),
            umock.patch("helpers.hs3.copy_file_to_s3"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/amp", "amp"),
            ) as mock_get_repo,
        ):
            hltltagh.gh_publish_buildmeister_dashboard_to_s3(
                ctx, repo_short_name="amp"
            )
        # Check outputs.
        mock_get_repo.assert_called_once_with("amp")


# #############################################################################
# Test_gh_delete_workflow_runs
# #############################################################################


class Test_gh_delete_workflow_runs(hunitest.TestCase):
    """
    Test `gh_delete_workflow_runs()`.
    """

    def helper(
        self,
        run_ids: List[str],
        *,
        dry_run: bool = False,
        confirmation: bool = True,
        user_input: str = "yes",
    ) -> Any:
        """
        Run the task with the given run ids and confirmation setup.

        :param run_ids: run ids `get_workflow_run_ids()` is mocked to
            return
        :param dry_run: value passed to the task
        :param confirmation: value passed to the task
        :param user_input: value the confirmation prompt is mocked to
            receive
        :return: the mock `ctx` the task was run with
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            umock.patch.object(
                hltltagh,
                "gh_get_workflows",
                return_value=[{"id": "42", "name": "Fast tests"}],
            ),
            umock.patch.object(
                hltltagh, "get_workflow_run_ids", return_value=run_ids
            ),
            umock.patch("builtins.input", return_value=user_input),
        ):
            hltltagh.gh_delete_workflow_runs(
                ctx,
                "Fast tests",
                dry_run=dry_run,
                confirmation=confirmation,
            )
        return ctx

    def test1(self) -> None:
        """
        Test that no matching runs skips deletion entirely.
        """
        # Prepare inputs.
        run_ids: List[str] = []
        # Run test.
        ctx = self.helper(run_ids)
        # Check outputs.
        self.assertEqual(list(ctx.run.mock_calls), [])

    def test2(self) -> None:
        """
        Test that declining the confirmation prompt skips deletion.
        """
        # Prepare inputs.
        run_ids = ["1", "2"]
        # Run test.
        ctx = self.helper(run_ids, user_input="no")
        # Check outputs.
        self.assertEqual(list(ctx.run.mock_calls), [])

    def test3(self) -> None:
        """
        Test that confirmed deletion issues one `gh api -X DELETE` call per
        run id.
        """
        # Prepare inputs.
        run_ids = ["1", "2"]
        # Run test.
        ctx = self.helper(run_ids, confirmation=False)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = [
            "gh api -X DELETE /repos/causify-ai/helpers/actions/runs/1",
            "gh api -X DELETE /repos/causify-ai/helpers/actions/runs/2",
        ]
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test that `dry_run=True` never issues the underlying `ctx.run`
        call.
        """
        # Prepare inputs.
        run_ids = ["1"]
        # Run test.
        ctx = self.helper(run_ids, dry_run=True, confirmation=False)
        # Check outputs.
        self.assertEqual(list(ctx.run.mock_calls), [])

    def test5(self) -> None:
        """
        Test that a non-default `repo_short_name` is resolved and used to
        build the `gh api` run path.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/amp", "amp"),
            ) as mock_get_repo,
            umock.patch.object(
                hltltagh,
                "gh_get_workflows",
                return_value=[{"id": "42", "name": "Fast tests"}],
            ),
            umock.patch.object(
                hltltagh, "get_workflow_run_ids", return_value=["1"]
            ),
        ):
            hltltagh.gh_delete_workflow_runs(
                ctx,
                "Fast tests",
                confirmation=False,
                repo_short_name="amp",
            )
        # Check outputs.
        mock_get_repo.assert_called_once_with("amp")
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = [
            "gh api -X DELETE /repos/causify-ai/amp/actions/runs/1",
        ]
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test_gh_create_mock_fixture
# #############################################################################


class Test_gh_create_mock_fixture(hunitest.TestCase):
    """
    Test `gh_create_mock_fixture()`.
    """

    def helper(self, workflows: List[Dict[str, str]]) -> Any:
        """
        Run the task and return the `gh_get_*` mocks used to record the
        fixture.

        :param workflows: value `gh_get_workflows()` is mocked to return
        :return: `(mock_open_prs, mock_type_names, mock_details)`
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hgit,
                "get_repo_full_name_from_dirname",
                return_value="causify-ai/helpers",
            ),
            umock.patch.object(
                hplayba, "recording", return_value=contextlib.nullcontext()
            ),
            umock.patch.object(hltltagh, "gh_get_open_prs") as mock_open_prs,
            umock.patch.object(
                hltltagh, "gh_get_workflow_type_names"
            ) as mock_type_names,
            umock.patch.object(
                hltltagh, "gh_get_workflows", return_value=workflows
            ),
            umock.patch.object(
                hltltagh, "gh_get_workflow_details"
            ) as mock_details,
        ):
            hltltagh.gh_create_mock_fixture(ctx)
        return mock_open_prs, mock_type_names, mock_details

    def test1(self) -> None:
        """
        Test that a non-empty workflow list also records workflow details.
        """
        # Prepare inputs.
        workflows = [{"id": "42", "name": "Fast tests"}]
        # Run test.
        _, _, mock_details = self.helper(workflows)
        # Check outputs.
        mock_details.assert_called_once_with(
            "causify-ai/helpers",
            "42",
            ["conclusion", "status", "url", "workflowName"],
            1,
        )

    def test2(self) -> None:
        """
        Test that an empty workflow list skips recording workflow details.
        """
        # Prepare inputs.
        workflows: List[Dict[str, str]] = []
        # Run test.
        _, _, mock_details = self.helper(workflows)
        # Check outputs.
        mock_details.assert_not_called()
