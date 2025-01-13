import logging

import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import helpers.lib_tasks_lint as hlitalin
import helpers.test.test_lib_tasks as httestlib

_LOG = logging.getLogger(__name__)


class Test_lint_check_if_it_was_run(hunitest.TestCase):
    """
    Test `lint_check_if_it_was_run()`.
    """

    def test1(self) -> None:
        # Build a mock context.
        ctx = httestlib._build_mock_context_returning_ok()
        # Stash the leftover changes from the previous tests.
        cmd = "git stash --include-untracked"
        hsystem.system(cmd)
        # Simple check that the function does not fail.
        _ = hlitalin.lint_check_if_it_was_run(ctx)
        # Pop the stashed changes to restore the original state.
        cmd = "git stash pop"
        # Do not abort on error because the stash may be empty.
        hsystem.system(cmd, abort_on_error=False)
