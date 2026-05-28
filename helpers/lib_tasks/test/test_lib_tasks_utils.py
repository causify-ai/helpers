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
