import os
import pty
import select
import tty

import invoke.runners as irunner

import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_utils as hltltaut

# #############################################################################
# TestLibTasksRemoveSpaces1
# #############################################################################


class TestLibTasksRemoveSpaces1(hunitest.TestCase):
    """
    Test helper for `_to_single_line_cmd()`.
    """

    def test1(self) -> None:
        """
        Convert multi-line command to single line.
        """
        # Prepare inputs.
        txt = r"""
            IMAGE=*****.dkr.ecr.us-east-1.amazonaws.com/amp_test:dev \
                docker-compose \
                --file $GIT_ROOT/devops/compose/docker-compose_as_submodule.yml \
                run \
                --rm \
                -l user=$USER_NAME \
                --entrypoint bash \
                user_space
            """
        # Prepare outputs.
        expected = (
            "IMAGE=*****.dkr.ecr.us-east-1.amazonaws.com/amp_test:dev"
            " docker-compose --file"
            " $GIT_ROOT/devops/compose/docker-compose_as_submodule.yml"
            " run --rm -l user=$USER_NAME --entrypoint bash user_space"
        )
        # Run test.
        actual = hltltaut._to_single_line_cmd(txt)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=False)


# #############################################################################
# Test_patch_invoke_bytes_to_read
# #############################################################################


class Test_patch_invoke_bytes_to_read(hunitest.TestCase):
    """
    Test `hltltaut._patch_invoke_bytes_to_read()` function.
    """

    def test1(self) -> None:
        """
        Count the bytes waiting on a tty without raising `SystemError`.

        Python 3.14 raises `SystemError: buffer overflow` in the unpatched
        `invoke` function.
        """
        # Prepare inputs.
        master_fd, slave_fd = pty.openpty()
        tty.setcbreak(slave_fd)
        os.write(master_fd, b"x")
        select.select([slave_fd], [], [], 5)
        # Run test.
        with os.fdopen(slave_fd) as slave:
            actual = irunner.bytes_to_read(slave)  # type: ignore
        os.close(master_fd)
        # Check outputs.
        self.assertEqual(actual, 1)
