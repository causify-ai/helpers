import os

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_utils as hltltaut


# #############################################################################
# Test_get_files_to_process1
# #############################################################################


class Test_get_files_to_process1(hunitest.TestCase):
    """
    We can't check the outcome so we just execute the code.
    """

    def test_modified1(self) -> None:
        """
        Retrieve files modified in this client.
        """
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        all_ = False
        from_file = ""
        mutually_exclusive = True
        remove_dirs = True
        # Run test.
        _ = hgit.get_files_to_process(
            modified,
            branch,
            last_commit,
            all_,
            from_file,
            mutually_exclusive,
            remove_dirs,
        )
        # No check since we don't know what is modified.

    @pytest.mark.skipif(
        hgit.get_branch_name() == "master",
        reason="This test makes sense for a branch",
    )
    def test_branch1(self) -> None:
        """
        Retrieved files modified in this client.
        """
        # Prepare inputs: This test needs a reference to Git master branch.
        hgit.fetch_origin_master_if_needed()
        modified = False
        branch = True
        last_commit = False
        all_ = False
        from_file = ""
        mutually_exclusive = True
        remove_dirs = True
        # Run test.
        _ = hgit.get_files_to_process(
            modified,
            branch,
            last_commit,
            all_,
            from_file,
            mutually_exclusive,
            remove_dirs,
        )
        # No check since we don't know what is modified.

    def test_last_commit1(self) -> None:
        """
        Retrieved files modified in the last commit.
        """
        # Prepare inputs.
        modified = False
        branch = False
        last_commit = True
        all_ = False
        from_file = ""
        mutually_exclusive = True
        remove_dirs = True
        # Run test.
        _ = hgit.get_files_to_process(
            modified,
            branch,
            last_commit,
            all_,
            from_file,
            mutually_exclusive,
            remove_dirs,
        )
        # No check since we don't know what is modified.

    def test_files1(self) -> None:
        """
        Pass through files from user.
        """
        # Prepare inputs.
        modified = False
        branch = False
        last_commit = False
        all_ = False
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_files1.txt")
        hio.to_file(from_file_path, __file__)
        mutually_exclusive = True
        remove_dirs = True
        # Run test.
        files = hgit.get_files_to_process(
            modified,
            branch,
            last_commit,
            all_,
            from_file_path,
            mutually_exclusive,
            remove_dirs,
        )
        # Check outputs.
        self.assertEqual(files, [__file__])

    def test_files2(self) -> None:
        """
        Pass through files from user.

        Use two types of paths we don't want to process:
          - non-existent python file
          - pattern "/*" that matches no files
        """
        # Prepare inputs.
        modified = False
        branch = False
        last_commit = False
        all_ = False
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_files2.txt")
        file_list_content = "testfile1.py testfiles1/*"
        hio.to_file(from_file_path, file_list_content)
        mutually_exclusive = True
        remove_dirs = True
        # Run test.
        files = hgit.get_files_to_process(
            modified,
            branch,
            last_commit,
            all_,
            from_file_path,
            mutually_exclusive,
            remove_dirs,
        )
        # Check outputs.
        self.assertEqual(files, [])

    def test_assert1(self) -> None:
        """
        Test that --modified and --branch together cause an assertion.
        """
        # Prepare inputs.
        modified = True
        branch = True
        last_commit = False
        all_ = True
        from_file = ""
        mutually_exclusive = True
        remove_dirs = True
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hgit.get_files_to_process(
                modified,
                branch,
                last_commit,
                all_,
                from_file,
                mutually_exclusive,
                remove_dirs,
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        '3'
        ==
        '1'
        Specify only one among --modified, --branch, --last-commit, --all_files, and --from_file
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_assert2(self) -> None:
        """
        Test that --modified and --files together cause an assertion if
        `mutually_exclusive=True`.
        """
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        all_ = False
        from_file = __file__
        mutually_exclusive = True
        remove_dirs = True
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            hgit.get_files_to_process(
                modified,
                branch,
                last_commit,
                all_,
                from_file,
                mutually_exclusive,
                remove_dirs,
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        '2'
        ==
        '1'
        Specify only one among --modified, --branch, --last-commit, --all_files, and --from_file
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_assert3(self) -> None:
        """
        Test that --modified and --files together don't cause an assertion if
        `mutually_exclusive=False`.
        """
        # Prepare inputs.
        modified = True
        branch = False
        last_commit = False
        all_ = False
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_assert3.txt")
        hio.to_file(from_file_path, __file__)
        mutually_exclusive = False
        remove_dirs = True
        # Run test.
        files = hgit.get_files_to_process(
            modified,
            branch,
            last_commit,
            all_,
            from_file_path,
            mutually_exclusive,
            remove_dirs,
        )
        # TODO(ai_gp): use self.assert_equal(expected
        # Check outputs.
        self.assertIn(__file__, files)


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
