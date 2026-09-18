import contextlib
import logging
import unittest.mock as umock
from typing import Any, Dict, List

import pandas as pd
import pytest

import helpers.hdaemon as hdaemon
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hplayback as hplayba
import helpers.hserver as hserver
import helpers.hsystem as hsystem
import helpers.htable as htable
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_gh as hltltagh
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
        #
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
            result = hltltagh.gh_get_team_member_names(team_name, org_name=org_name)
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
        self.assertEqual([w["name"] for w in workflows], [r["name"] for r in raw])
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
            umock.patch(
                "helpers.lib_tasks.lib_tasks_utils.report_task"
            ),
            umock.patch("os.path.expanduser", side_effect=lambda p: p),
            umock.patch("os.path.exists", side_effect=_exists),
        ):
            hltltagh.gh_login(ctx, account=account, print_status=False)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = [
            "gh auth login --with-token <~/.ssh/github_pat.test-org.txt"
        ]
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
            umock.patch(
                "helpers.lib_tasks.lib_tasks_utils.report_task"
            ),
            umock.patch("os.path.expanduser", side_effect=lambda p: p),
            umock.patch("os.path.exists", return_value=False),
        ):
            hltltagh.gh_login(ctx, account=account, print_status=True)
        # Check outputs.
        actual = [call.args[0] for call in ctx.run.mock_calls]
        expected = ["gh auth status", "gh auth status"]
        self.assert_equal(str(actual), str(expected))


# Columns of the table returned by `_get_workflow_table()`.
_WORKFLOW_TABLE_COLS = [
    "completed",
    "status",
    "workflow",
    "branch",
    "event",
    "id",
    "elapsed",
    "age",
]


# #############################################################################
# Test__get_workflow_table
# #############################################################################


# TODO(ai_gp): Factor out common code

class Test__get_workflow_table(hunitest.TestCase):
    """
    Test `_get_workflow_table()`.
    """

    def test1(self) -> None:
        """
        Test that `gh run list` tab-separated output is parsed and the
        redundant `name` column is dropped.
        """
        # Prepare inputs.
        txt = "\n".join(
            [
                "completed\tsuccess\tTitle1\tFast tests\tmaster\tpush\t1\t1m\t2m",
                "in_progress\t\tTitle2\tSlow tests\tmaster\tpush\t2\t2m\t3m",
            ]
        )
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, txt)
        ):
            table = hltltagh._get_workflow_table()
        # Check outputs.
        actual = {
            "completed": table.get_column("completed"),
            "status": table.get_column("status"),
            "workflow": table.get_column("workflow"),
            "id": table.get_column("id"),
        }
        expected = {
            "completed": ["completed", "in_progress"],
            "status": ["success", ""],
            "workflow": ["Fast tests", "Slow tests"],
            "id": ["1", "2"],
        }
        self.assert_equal(str(actual), str(expected))
        # The `name` column was dropped.
        with self.assertRaises(AssertionError):
            table.get_column("name")

    def test2(self) -> None:
        """
        Test that the branch and the limit are passed to `gh run list`.
        """
        # Prepare inputs.
        txt = "completed\tsuccess\tTitle1\tFast tests\tbranch1\tpush\t1\t1m\t2m"
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, txt)
        ) as mock_system:
            hltltagh._get_workflow_table(
                "github.com/causify-ai/helpers", branch_name="branch1"
            )
        # Check outputs.
        actual = mock_system.call_args.args[0]
        expected = (
            "export NO_COLOR=1; gh run list --limit 100"
            " --repo github.com/causify-ai/helpers --branch branch1"
        )
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that no branch is passed to `gh run list` when it is not
        specified.
        """
        # Prepare inputs.
        txt = "completed\tsuccess\tTitle1\tFast tests\tmaster\tpush\t1\t1m\t2m"
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, txt)
        ) as mock_system:
            hltltagh._get_workflow_table()
        # Check outputs.
        actual = mock_system.call_args.args[0]
        expected = "export NO_COLOR=1; gh run list --limit 100"
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test that an empty `gh run list` output gives an empty table.
        """
        # Prepare inputs.
        branch_name = "branch1"
        # Run test.
        with umock.patch.object(
            hsystem, "system_to_string", return_value=(0, "")
        ):
            table = hltltagh._get_workflow_table(branch_name=branch_name)
        # Check outputs.
        self.assertEqual(table.size(), (0, 8))


# #############################################################################
# Test_gh_workflow_list
# #############################################################################


class Test_gh_workflow_list(hunitest.TestCase):
    """
    Test `gh_workflow_list()`.
    """

    def test1(self) -> None:
        """
        Test that `filter_by_branch="all"` prints the table and returns
        before the per-workflow status loop.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        table = htable.Table.from_text(
            [
                "completed",
                "status",
                "workflow",
                "branch",
                "event",
                "id",
                "elapsed",
                "age",
            ],
            "completed\tsuccess\tFast tests\tmaster\tpush\t1\t1m\t2m",
            delimiter="\t",
        )
        filter_by_branch = "all"
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh, "_get_workflow_table", return_value=table
            ),
            umock.patch.object(hltltagh, "_print_table") as mock_print,
        ):
            hltltagh.gh_workflow_list(ctx, filter_by_branch=filter_by_branch)
        # Check outputs.
        mock_print.assert_called_once_with(table)

    def test2(self) -> None:
        """
        Test that `daemon=True` schedules the periodic report instead of
        running it once, and the scheduled callback clears the screen and
        re-invokes the report with `daemon=False`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        interval = 30
        daemon = True
        # Run test.
        with umock.patch.object(
            hdaemon, "run_periodic_daemon_mode"
        ) as mock_daemon:
            hltltagh.gh_workflow_list(ctx, daemon=daemon, interval=interval)
        # Check outputs.
        mock_daemon.assert_called_once()
        run_fn, actual_interval = mock_daemon.call_args.args
        self.assertEqual(actual_interval, interval)
        self.assertEqual(
            mock_daemon.call_args.kwargs["window_name_str"], "*GH_WATCH*"
        )
        # Exercise the scheduled callback.
        with (
            umock.patch("subprocess.run") as mock_subprocess,
            umock.patch.object(hltltagh, "gh_workflow_list") as mock_recurse,
        ):
            run_fn()
        mock_subprocess.assert_called_once_with("clear", shell=True)
        mock_recurse.assert_called_once()

    def test3(self) -> None:
        """
        Test that a non-default `repo_short_name` is resolved and passed
        to `_get_workflow_table()`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        table = htable.Table.from_text(
            [
                "completed",
                "status",
                "workflow",
                "branch",
                "event",
                "id",
                "elapsed",
                "age",
            ],
            "completed\tsuccess\tFast tests\tmaster\tpush\t1\t1m\t2m",
            delimiter="\t",
        )
        filter_by_branch = "all"
        repo_short_name = "amp"
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/amp", repo_short_name),
            ) as mock_get_repo,
            umock.patch.object(
                hltltagh, "_get_workflow_table", return_value=table
            ) as mock_get_table,
            umock.patch.object(hltltagh, "_print_table"),
        ):
            hltltagh.gh_workflow_list(
                ctx, filter_by_branch=filter_by_branch, repo_short_name=repo_short_name
            )
        # Check outputs.
        mock_get_repo.assert_called_once_with(repo_short_name)
        mock_get_table.assert_called_once_with(
            "github.com/causify-ai/amp", branch_name=None
        )

    def test4(self) -> None:
        """
        Test that the branch filter is pushed down to `_get_workflow_table()`.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        table = htable.Table([], _WORKFLOW_TABLE_COLS)
        filter_by_branch = "master"
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            umock.patch.object(
                hltltagh, "_get_workflow_table", return_value=table
            ) as mock_get_table,
        ):
            hltltagh.gh_workflow_list(ctx, filter_by_branch=filter_by_branch)
        # Check outputs.
        mock_get_table.assert_called_once_with(
            "github.com/causify-ai/helpers", branch_name=filter_by_branch
        )

    def test5(self) -> None:
        """
        Test that a warning is issued and nothing is printed when no run
        matches the filters.
        """
        # Prepare inputs.
        ctx = httestlib._build_mock_context_returning_ok()
        table = htable.Table([], _WORKFLOW_TABLE_COLS)
        filter_by_branch = "all"
        # Run test.
        with (
            umock.patch.object(hltltagh, "gh_login"),
            umock.patch.object(
                hltltagh,
                "_get_repo_full_name_from_cmd",
                return_value=("github.com/causify-ai/helpers", "helpers"),
            ),
            umock.patch.object(
                hltltagh, "_get_workflow_table", return_value=table
            ),
            umock.patch.object(hltltagh, "_print_table") as mock_print,
            self.assertLogs(hltltagh._LOG, level="WARNING") as cm,
        ):
            hltltagh.gh_workflow_list(ctx, filter_by_branch=filter_by_branch)
        # Check outputs.
        mock_print.assert_not_called()
        # Log message format: "LEVEL:logger.name:message"
        # Use fuzzy matching to handle variable logger name/timestamp formats.
        actual_log = cm.output[0]
        expected_log = ".*No workflow runs found.*"
        self.assert_equal(actual_log, expected_log, fuzzy_match=True)


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
            "gh workflow run fast_tests.yml --ref master"
            " --repo github.com/causify-ai/helpers",
            "gh workflow run slow_tests.yml --ref master"
            " --repo github.com/causify-ai/helpers",
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
            "gh workflow run custom_workflow.yml --ref feature_x"
            " --repo github.com/causify-ai/helpers"
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
            hltltagh.gh_workflow_run(
                ctx, branch=branch, workflows=workflows
            )
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
            "gh workflow run fast_tests.yml --ref master"
            " --repo github.com/causify-ai/amp"
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
            "gh pr create --repo github.com/causify-ai/helpers --draft "
            "--title HelpersTask123_Fix_bug "
            "--body-file tmp.gh_create_pr.body.txt"
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
