import logging
import os
import tempfile
from typing import Generator, List, Optional

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# Unfortunately we can't check the outcome of some of these functions since we
# don't know in which dir we are running. Thus we just test that the function
# completes and visually inspect the outcome, if possible.


# #############################################################################
# Test_git_submodule1
# #############################################################################


class Test_git_submodule1(hunitest.TestCase):
    def test_get_client_root1(self) -> None:
        actual = hgit.get_client_root(super_module=True)
        _LOG.debug("actual=%s", actual)

    def test_get_client_root2(self) -> None:
        actual = hgit.get_client_root(super_module=False)
        _LOG.debug("actual=%s", actual)

    def test_get_project_dirname1(self) -> None:
        actual = hgit.get_project_dirname()
        _LOG.debug("actual=%s", actual)

    def test_get_branch_name1(self) -> None:
        actual = hgit.get_branch_name()
        _LOG.debug("actual=%s", actual)

    def test_is_inside_submodule1(self) -> None:
        actual = hgit.is_inside_submodule()
        _LOG.debug("actual=%s", actual)

    # Outside CK infra, the following call hangs, so we skip it.
    # TODO(gp): I don't see why it requires our infra.
    @pytest.mark.requires_ck_infra
    def test_is_amp(self) -> None:
        actual = hgit.is_amp()
        _LOG.debug("actual=%s", actual)

    def test_get_path_from_supermodule1(self) -> None:
        actual = hgit.get_path_from_supermodule()
        _LOG.debug("actual=%s", actual)

    def test_get_submodule_paths1(self) -> None:
        actual = hgit.get_submodule_paths()
        _LOG.debug("actual=%s", actual)


# #############################################################################
# Test_git_submodule2
# #############################################################################


class Test_git_submodule2(hunitest.TestCase):
    # def test_get_submodule_hash1(self) -> None:
    #     dir_name = "amp"
    #     _ = hgit._get_submodule_hash(dir_name)

    def test_get_remote_head_hash1(self) -> None:
        dir_name = "."
        actual = hgit.get_head_hash(dir_name)
        _LOG.debug("actual=%s", actual)

    # def test_report_submodule_status1(self) -> None:
    #     dir_names = ["."]
    #     short_hash = True
    #     _ = hgit.report_submodule_status(dir_names, short_hash)

    def test_get_head_hash1(self) -> None:
        dir_name = "."
        actual = hgit.get_head_hash(dir_name)
        _LOG.debug("actual=%s", actual)

    def _helper_group_hashes(
        self,
        head_hash: str,
        remh_hash: str,
        subm_hash: Optional[str],
        expected: str,
    ) -> None:
        actual = hgit._group_hashes(head_hash, remh_hash, subm_hash)
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_group_hashes1(self) -> None:
        head_hash = "a2bfc704"
        remh_hash = "a2bfc704"
        subm_hash = None
        expected = "head_hash = remh_hash = a2bfc704"
        #
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, expected)

    def test_group_hashes2(self) -> None:
        head_hash = "22996772"
        remh_hash = "92167662"
        subm_hash = "92167662"
        expected = """
        head_hash = 22996772
        remh_hash = subm_hash = 92167662
        """
        #
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, expected)

    def test_group_hashes3(self) -> None:
        head_hash = "7ea03eb6"
        remh_hash = "7ea03eb6"
        subm_hash = "7ea03eb6"
        expected = "head_hash = remh_hash = subm_hash = 7ea03eb6"
        #
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, expected)


# #############################################################################
# Test_git_repo_name1
# #############################################################################


class Test_git_repo_name1(hunitest.TestCase):
    def _helper_parse_github_repo_name(
        self,
        repo_name: str,
        expected_host: str,
        expected_repo: str,
    ) -> None:
        host_name, actual_repo = hgit._parse_github_repo_name(repo_name)
        self.assert_equal(host_name, expected_host)
        self.assert_equal(actual_repo, expected_repo)

    def test_parse_github_repo_name1(self) -> None:
        repo_name = "git@github.com:alphamatic/amp"
        self._helper_parse_github_repo_name(repo_name, "github.com", "alphamatic/amp")

    def test_parse_github_repo_name2(self) -> None:
        repo_name = "https://github.com/alphamatic/amp"
        self._helper_parse_github_repo_name(repo_name, "github.com", "alphamatic/amp")

    def test_parse_github_repo_name3(self) -> None:
        repo_name = "git@github.fake.com:alphamatic/amp"
        self._helper_parse_github_repo_name(repo_name, "github.fake.com", "alphamatic/amp")

    def test_parse_github_repo_name4(self) -> None:
        repo_name = "https://github.fake.com/alphamatic/amp"
        self._helper_parse_github_repo_name(repo_name, "github.fake.com", "alphamatic/amp")

    def test_get_repo_full_name_from_dirname1(self) -> None:
        actual = hgit.get_repo_full_name_from_dirname(
            dir_name=".", include_host_name=False
        )
        _LOG.debug("actual=%s", actual)

    def test_get_repo_full_name_from_dirname2(self) -> None:
        actual = hgit.get_repo_full_name_from_dirname(
            dir_name=".", include_host_name=True
        )
        _LOG.debug("actual=%s", actual)

    def test_get_repo_full_name_from_client1(self) -> None:
        actual = hgit.get_repo_full_name_from_client(super_module=True)
        _LOG.debug("actual=%s", actual)

    def test_get_repo_full_name_from_client2(self) -> None:
        actual = hgit.get_repo_full_name_from_client(super_module=False)
        _LOG.debug("actual=%s", actual)


# #############################################################################
# Test_git_path1
# #############################################################################


# Outside CK infra, the following class hangs, so we skip it.
@pytest.mark.requires_ck_infra
class Test_git_path1(hunitest.TestCase):
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_supermodule(),
        reason="Run only in amp as super-module",
    )
    def test_get_path_from_git_root1(self) -> None:
        file_name = "/app/helpers/test/test_hgit.py"
        actual = hgit.get_path_from_git_root(file_name, super_module=True)
        _LOG.debug("get_path_from_git_root()=%s", actual)
        # Check.
        expected = "helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(),
        reason="Run only in amp as sub-module",
    )
    def test_get_path_from_git_root2(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        actual = hgit.get_path_from_git_root(file_name, super_module=True)
        _LOG.debug("get_path_from_git_root()=%s", actual)
        # Check.
        expected = "amp/helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    def test_get_path_from_git_root3(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        git_root = "/app"
        actual = hgit.get_path_from_git_root(
            file_name, super_module=False, git_root=git_root
        )
        # Check.
        expected = "amp/helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    def test_get_path_from_git_root4(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        git_root = "/app/amp"
        actual = hgit.get_path_from_git_root(
            file_name, super_module=False, git_root=git_root
        )
        # Check.
        expected = "helpers/test/test_hgit.py"
        self.assert_equal(actual, expected)

    def test_get_path_from_git_root5(self) -> None:
        file_name = "helpers/test/test_hgit.py"
        git_root = "/app/amp"
        with self.assertRaises(ValueError):
            hgit.get_path_from_git_root(
                file_name, super_module=False, git_root=git_root
            )


# #############################################################################
# Test_git_modified_files1
# #############################################################################


# Outside CK infra, the following class hangs, so we skip it.
@pytest.mark.requires_ck_infra
@pytest.mark.slow(reason="Around 7s")
@pytest.mark.skipif(
    not hgit.is_in_amp_as_supermodule(),
    reason="Run only in amp as super-module",
)
class Test_git_modified_files1(hunitest.TestCase):
    # This will be run before and after each test.
    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        # Run before each test.
        self.set_up_test()
        yield

    def set_up_test(self) -> None:
        """
        All these tests need a reference to Git master branch.
        """
        hgit.fetch_origin_master_if_needed()

    def test_get_modified_files1(self) -> None:
        actual = hgit.get_modified_files()
        _LOG.debug("actual=%s", actual)

    def test_get_previous_committed_files1(self) -> None:
        actual = hgit.get_previous_committed_files()
        _LOG.debug("actual=%s", actual)

    def test_get_modified_files_in_branch1(self) -> None:
        actual = hgit.get_modified_files_in_branch("master")
        _LOG.debug("actual=%s", actual)

    def test_get_summary_files_in_branch1(self) -> None:
        actual = hgit.get_summary_files_in_branch("master")
        _LOG.debug("actual=%s", actual)

    def test_git_log1(self) -> None:
        actual = hgit.git_log()
        _LOG.debug("actual=%s", actual)


# #############################################################################
# Test_find_docker_file1
# #############################################################################


# Outside CK infra, the following class hangs, so we skip it.
@pytest.mark.requires_ck_infra
class Test_find_docker_file1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test for a file `amp/helpers/test/test_hgit.py` that is not from Docker
        (i.e., it doesn't start with `/app`) and exists in the repo.
        """
        amp_dir = hgit.get_amp_abs_path()
        # Use this file since `find_docker_file()` needs to do a `find` in the
        # repo, and we need to have a fixed file structure.
        file_name = hgit.find_file_in_git_tree("test_hgit.py")
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
        )
        expected = ["helpers/test/test_hgit.py"]
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test2(self) -> None:
        """
        Test for a file `/app/amp/helpers/test/test_hgit.py` that is from
        Docker (i.e., it starts with `/app`) and exists in the repo.
        """
        amp_dir = hgit.get_amp_abs_path()
        # Use this file since `find_docker_file()` needs to do a `find` in the
        # repo, and we need to have a fixed file structure.
        file_name = hgit.find_file_in_git_tree("test_hgit.py")
        expected = ["helpers/test/test_hgit.py"]
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
        )
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test3(self) -> None:
        """
        Test for a file `/venv/lib/python3.8/site-packages/invoke/tasks.py`
        that is from Docker (e.g., it starts with `/app`), but doesn't exist in
        the repo.
        """
        file_name = "/venv/lib/python3.8/site-packages/invoke/tasks.py"
        actual = hgit.find_docker_file(file_name)
        expected: List[str] = []
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test4(self) -> None:
        """
        Test for a file `./core/dataflow/utils.py` that is from Docker (i.e.,
        it starts with `/app`), but has multiple copies in the repo.
        """
        amp_dir = hgit.get_amp_abs_path()
        file_name = "/app/amp/core/dataflow/utils.py"
        dir_depth = 1
        candidate_files = [
            "core/dataflow/utils.py",
            "core/foo/utils.py",
            "core/bar/utils.py",
        ]
        candidate_files = [os.path.join(amp_dir, f) for f in candidate_files]
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
            dir_depth=dir_depth,
            candidate_files=candidate_files,
        )
        # Only one candidate file matches basename and one dirname.
        expected = ["core/dataflow/utils.py"]
        self.assert_equal(str(actual), str(expected), purify_text=True)

    def test5(self) -> None:
        amp_dir = hgit.get_amp_abs_path()
        file_name = "/app/amp/core/dataflow/utils.py"
        dir_depth = -1
        candidate_files = [
            "core/dataflow/utils.py",
            "bar/dataflow/utils.py",
            "core/foo/utils.py",
        ]
        candidate_files = [os.path.join(amp_dir, f) for f in candidate_files]
        actual = hgit.find_docker_file(
            file_name,
            root_dir=amp_dir,
            dir_depth=dir_depth,
            candidate_files=candidate_files,
        )
        # Only one file matches `utils.py` using all the 3 dir levels.
        expected = ["core/dataflow/utils.py"]
        self.assert_equal(str(actual), str(expected), purify_text=True)


# #############################################################################
# Test_extract_gh_issue_number_from_branch
# #############################################################################


class Test_extract_gh_issue_number_from_branch(hunitest.TestCase):
    def test_extract_gh_issue_number_from_branch1(self) -> None:
        """
        Tests extraction from a branch name with a specific format.
        """
        branch_name = "CmampTask10725_Add_more_tabs_to_orange_tmux"
        actual = hgit.extract_gh_issue_number_from_branch(branch_name)
        expected = "10725"
        self.assert_equal(str(actual), expected)

    def test_extract_gh_issue_number_from_branch2(self) -> None:
        """
        Tests extraction from another branch name format.
        """
        branch_name = "HelpersTask23_Add_more_tabs_to_orange_tmux"
        actual = hgit.extract_gh_issue_number_from_branch(branch_name)
        expected = "23"
        self.assert_equal(str(actual), expected)

    def test_extract_gh_issue_number_from_branch3(self) -> None:
        """
        Tests extraction from a short branch name format.
        """
        branch_name = "CmTask3434"
        actual = hgit.extract_gh_issue_number_from_branch(branch_name)
        expected = "3434"
        self.assert_equal(str(actual), expected)

    def test_extract_gh_issue_number_from_branch4(self) -> None:
        """
        Tests behavior when no issue number is present in the branch name.
        """
        branch_name = "NoTaskNumberHere"
        actual = hgit.extract_gh_issue_number_from_branch(branch_name)
        expected = "None"
        self.assert_equal(str(actual), expected)


# #############################################################################
# Test_find_git_root1
# #############################################################################


class Test_find_git_root1(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a super repo (e.g. //orange)
    - the repo contains another super repo (e.g. //amp) as submodule (first level)
    - the first level submodule contains another submodule (e.g. //helpers) (second level)

    Directory structure:
    orange/
    |-- .git/
    `-- amp/
        |-- .git (points to ../.git/modules/amp)
        |-- ck.infra/
        `-- helpers_root/
            `-- .git (points to ../../.git/modules/amp/modules/helpers_root)
    """

    def _helper_find_git_root(self, working_dir_attr: str) -> None:
        self.set_up_test()
        working_dir = getattr(self, working_dir_attr)
        with hsystem.cd(working_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create `orange` repo.
        self.repo_dir = os.path.join(temp_dir, "orange")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create `amp` submodule under `orange`.
        self.submodule_dir = os.path.join(self.repo_dir, "amp")
        hio.create_dir(self.submodule_dir, incremental=False)
        submodule_git_file = os.path.join(self.submodule_dir, ".git")
        txt = "gitdir: ../.git/modules/amp"
        hio.to_file(submodule_git_file, txt)
        submodule_git_file_dir = os.path.join(
            self.repo_dir, ".git", "modules", "amp"
        )
        hio.create_dir(submodule_git_file_dir, incremental=False)
        # Create `helpers_root` submodule under `amp`.
        self.subsubmodule_dir = os.path.join(self.submodule_dir, "helpers_root")
        hio.create_dir(self.subsubmodule_dir, incremental=False)
        subsubmodule_git_file = os.path.join(self.subsubmodule_dir, ".git")
        txt = "gitdir: ../../.git/modules/amp/modules/helpers_root"
        hio.to_file(subsubmodule_git_file, txt)
        subsubmodule_git_file_dir = os.path.join(
            self.repo_dir, ".git", "modules", "amp", "modules", "helpers_root"
        )
        hio.create_dir(subsubmodule_git_file_dir, incremental=False)
        # Create `ck.infra` runnable dir under `amp`.
        self.runnable_dir = os.path.join(self.submodule_dir, "ck.infra")
        hio.create_dir(self.runnable_dir, incremental=False)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in the super repo (e.g. //orange)
        """
        self._helper_find_git_root("repo_dir")

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in first level submodule (e.g. //amp)
        """
        self._helper_find_git_root("submodule_dir")

    def test3(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in second level submodule (e.g. //helpers)
        """
        self._helper_find_git_root("subsubmodule_dir")

    def test4(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in a runnable dir (e.g. ck.infra) under the
            first level submodule (e.g. //amp)
        """
        self._helper_find_git_root("runnable_dir")


# #############################################################################
# Test_find_git_root2
# #############################################################################


class Test_find_git_root2(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a super repo (e.g. //cmamp)
    - the repo contains //helpers as submodule

    Directory structure:
    cmamp/
    |-- .git/
    |-- ck.infra/
    `-- helpers_root/
        `-- .git (points to ../.git/modules/helpers_root)
    """

    def _helper_find_git_root(self, working_dir_attr: str) -> None:
        self.set_up_test()
        working_dir = getattr(self, working_dir_attr)
        with hsystem.cd(working_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create `cmamp` repo.
        self.repo_dir = os.path.join(temp_dir, "cmamp")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create `helpers_root` submodule under `cmamp`.
        self.submodule_dir = os.path.join(self.repo_dir, "helpers_root")
        hio.create_dir(self.submodule_dir, incremental=False)
        submodule_git_file = os.path.join(self.submodule_dir, ".git")
        txt = "gitdir: ../.git/modules/helpers_root"
        hio.to_file(submodule_git_file, txt)
        submodule_git_file_dir = os.path.join(
            self.repo_dir, ".git", "modules", "helpers_root"
        )
        hio.create_dir(submodule_git_file_dir, incremental=False)
        # Create `ck.infra` runnable dir under `cmamp`.
        self.runnable_dir = os.path.join(self.repo_dir, "ck.infra")
        hio.create_dir(self.runnable_dir, incremental=False)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in the super repo (e.g. //cmamp)
        """
        self._helper_find_git_root("repo_dir")

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is the submodule (e.g. //helpers)
        """
        self._helper_find_git_root("submodule_dir")

    def test3(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in a runnable dir (e.g. ck.infra)
        """
        self._helper_find_git_root("runnable_dir")


# #############################################################################
# Test_find_git_root3
# #############################################################################


class Test_find_git_root3(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is //helpers

    Directory structure:
    helpers/
    |-- .git/
    `-- arbitrary1/
        `-- arbitrary1a/
    """

    def _helper_find_git_root(self, working_dir_attr: str) -> None:
        self.set_up_test()
        working_dir = getattr(self, working_dir_attr)
        with hsystem.cd(working_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create `helpers` repo.
        self.repo_dir = os.path.join(temp_dir, "helpers")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create arbitrary directory under `helpers`.
        self.arbitrary_dir = os.path.join(
            self.repo_dir, "arbitrary1", "arbitrary1a"
        )
        hio.create_dir(self.arbitrary_dir, incremental=False)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is the root of repo
        """
        self._helper_find_git_root("repo_dir")

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in an arbitrary directory under the repo
        """
        self._helper_find_git_root("arbitrary_dir")


# #############################################################################
# Test_find_git_root4
# #############################################################################


class Test_find_git_root4(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a linked repo

    Directory structure:
    repo/
    `-- .git/
    linked_repo/
    `-- .git (points to /repo/.git)
    """

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create repo.
        self.repo_dir = os.path.join(temp_dir, "repo")
        hio.create_dir(self.repo_dir, incremental=False)
        self.git_dir = os.path.join(self.repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create linked repo.
        self.linked_repo_dir = os.path.join(temp_dir, "linked_repo")
        hio.create_dir(self.linked_repo_dir, incremental=False)
        # Create pointer from linked repo to the actual repo.
        linked_git_file = os.path.join(self.linked_repo_dir, ".git")
        txt = f"gitdir: {self.git_dir}\n"
        hio.to_file(linked_git_file, txt)

    def test1(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is the linked repo
        """
        self.set_up_test()
        with hsystem.cd(self.linked_repo_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)


# #############################################################################
# Test_find_git_root5
# #############################################################################


class Test_find_git_root5(hunitest.TestCase):
    """
    Check that the error is raised when no .git directory is found.

    Directory structure:
    arbitrary_dir/
    broken_repo/
    `-- .git (points to /nonexistent/path/to/gitdir)
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        # `self.get_scratch_space()` does not work in the case as it creates
        # a temp directory within the repo where `.git` exists by default
        # (e.g. /app/helpers/test/outcomes/Test_find_git_root5.test1/tmp.scratch)
        # This preventing the exception from being raised.
        # We need a structure without `.git` for this test.
        self.temp_dir = tempfile.TemporaryDirectory()
        # Create arbitrary directory that is not a git repo.
        self.arbitrary_dir = os.path.join(self.temp_dir.name, "arbitrary_dir")
        hio.create_dir(self.arbitrary_dir, incremental=False)
        # Create arbitrary directory that is a submodule or linked repo that
        #   point to non existing super repo.
        self.repo_dir = os.path.join(self.temp_dir.name, "broken_repo")
        hio.create_dir(self.repo_dir, incremental=False)
        # Create an invalid `.git` file with a non-existent `gitdir`.
        invalid_git_file = os.path.join(self.repo_dir, ".git")
        txt = "gitdir: /nonexistent/path/to/gitdir"
        hio.to_file(invalid_git_file, txt)

    def tear_down_test(self) -> None:
        self.temp_dir.cleanup()

    def test1(self) -> None:
        """
        Check that the error is raised when the caller is in a directory that
        is not either a git repo or a submodule.
        """
        with (
            hsystem.cd(self.arbitrary_dir),
            self.assertRaises(AssertionError) as cm,
        ):
            _ = hgit.find_git_root(".")
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '/'
        !=
        '/'
        No .git directory or file found in any parent directory.
        """
        self.assert_equal(actual, expected, purify_text=True, fuzzy_match=True)

    def test2(self) -> None:
        """
        Check that the error is raised when the caller is in a submodule or
        linked repo that points to non existing super repo.
        """
        with hsystem.cd(self.repo_dir), self.assertRaises(AssertionError) as cm:
            _ = hgit.find_git_root(".")
        actual = str(cm.exception)
        expected = """
        * Failed assertion *
        '/'
        !=
        '/'
        Top-level .git directory not found.
        """
        self.assert_equal(actual, expected, purify_text=True, fuzzy_match=True)


# #############################################################################
# Test_get_files_to_process1
# #############################################################################


class Test_get_files_to_process1(hunitest.TestCase):
    """
    Test get_files_to_process with --files argument (space-separated list).
    """

    def _call_get_files_to_process(
        self,
        *,
        files: str = "",
        from_file: str = "",
        modified: bool = False,
        branch: bool = False,
        last_commit: bool = False,
        all_: bool = False,
        mutually_exclusive: bool = True,
        remove_dirs: bool = False,
        dir_name: Optional[str] = None,
    ) -> List[str]:
        return hgit.get_files_to_process(
            files,
            from_file,
            modified,
            branch,
            last_commit,
            all_,
            mutually_exclusive=mutually_exclusive,
            remove_dirs=remove_dirs,
            dir_name=dir_name,
        )

    def test1(self) -> None:
        """
        Test with a single file in the space-separated list.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        actual = self._call_get_files_to_process(files=file1, dir_name=temp_dir)
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])

    def test2(self) -> None:
        """
        Test with multiple files in the space-separated list.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        file3 = os.path.join(temp_dir, "file3.txt")
        hio.to_file(file1, "content1")
        hio.to_file(file2, "content2")
        hio.to_file(file3, "content3")
        files = f"{file1} {file2} {file3}"
        actual = self._call_get_files_to_process(files=files, dir_name=temp_dir)
        self.assertEqual(len(actual), 3)
        for expected_file in ["file1.txt", "file2.txt", "file3.txt"]:
            self.assertTrue(
                any(expected_file in f for f in actual),
                f"{expected_file} not found in {actual}",
            )

    def test3(self) -> None:
        """
        Test that non-existent files are filtered out.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        nonexistent = os.path.join(temp_dir, "nonexistent.txt")
        hio.to_file(file1, "content1")
        files = f"{file1} {nonexistent}"
        actual = self._call_get_files_to_process(files=files, dir_name=temp_dir)
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])

    def test4(self) -> None:
        """
        Test that empty string is handled correctly when mutually_exclusive=False.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        actual = self._call_get_files_to_process(
            modified=True,
            mutually_exclusive=False,
            dir_name=temp_dir,
        )
        self.assertIsInstance(actual, list)

    def test5(self) -> None:
        """
        Test that --files is mutually exclusive with --modified when mutually_exclusive=True.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        with self.assertRaises(AssertionError):
            self._call_get_files_to_process(
                files=file1,
                modified=True,
                dir_name=temp_dir,
            )

    def test6(self) -> None:
        """
        Test with a directory in the file list and remove_dirs=True.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        dir1 = os.path.join(temp_dir, "dir1")
        hio.to_file(file1, "content1")
        hio.create_dir(dir1, incremental=False)
        files = f"{file1} {dir1}"
        actual = self._call_get_files_to_process(
            files=files,
            remove_dirs=True,
            dir_name=temp_dir,
        )
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])

    def test7(self) -> None:
        """
        Test that 'amp' directory is filtered out.
        """
        temp_dir = self.get_scratch_space()
        file1 = os.path.join(temp_dir, "file1.txt")
        hio.to_file(file1, "content1")
        files = f"{file1} amp"
        actual = self._call_get_files_to_process(
            files=files,
            dir_name=temp_dir,
        )
        self.assertEqual(len(actual), 1)
        self.assertIn("file1.txt", actual[0])

    def test_modified1(self) -> None:
        """
        Retrieve files modified in this client.
        """
        _ = self._call_get_files_to_process(
            modified=True,
            remove_dirs=True,
        )

    @pytest.mark.skipif(
        hgit.get_branch_name() == "master",
        reason="This test makes sense for a branch",
    )
    def test_branch1(self) -> None:
        """
        Retrieved files modified in this client.
        """
        hgit.fetch_origin_master_if_needed()
        _ = self._call_get_files_to_process(
            branch=True,
            remove_dirs=True,
        )

    def test_last_commit1(self) -> None:
        """
        Retrieved files modified in the last commit.
        """
        _ = self._call_get_files_to_process(
            last_commit=True,
            remove_dirs=True,
        )

    def test_files1(self) -> None:
        """
        Pass through files from user.
        """
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_files1.txt")
        hio.to_file(from_file_path, __file__)
        files = self._call_get_files_to_process(
            from_file=from_file_path,
            remove_dirs=True,
        )
        self.assertEqual(files, [__file__])

    def test_files2(self) -> None:
        """
        Pass through files from user.

        Use two types of paths we don't want to process:
          - non-existent python file
          - pattern "/*" that matches no files
        """
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_files2.txt")
        file_list_content = "testfile1.py testfiles1/*"
        hio.to_file(from_file_path, file_list_content)
        files = self._call_get_files_to_process(
            from_file=from_file_path,
            remove_dirs=True,
        )
        self.assertEqual(files, [])

    def test_assert1(self) -> None:
        """
        Test that --modified and --branch together cause an assertion.
        """
        with self.assertRaises(AssertionError) as cm:
            self._call_get_files_to_process(
                modified=True,
                branch=True,
                all_=True,
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        '3'
        ==
        '1'
        You can pick only one option to select files. Selected: --modified, --branch, --all_files
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_assert2(self) -> None:
        """
        Test that --modified and --files together cause an assertion if
        `mutually_exclusive=True`.
        """
        with self.assertRaises(AssertionError) as cm:
            self._call_get_files_to_process(
                from_file=__file__,
                modified=True,
            )
        actual = str(cm.exception)
        expected = r"""
        * Failed assertion *
        '2'
        ==
        '1'
        You can pick only one option to select files. Selected: --from_file, --modified
        """
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test_assert3(self) -> None:
        """
        Test that --modified and --files together don't cause an assertion if
        `mutually_exclusive=False`.
        """
        scratch_dir = self.get_scratch_space()
        from_file_path = os.path.join(scratch_dir, "test_assert3.txt")
        hio.to_file(from_file_path, __file__)
        files = self._call_get_files_to_process(
            from_file=from_file_path,
            modified=True,
            mutually_exclusive=False,
            remove_dirs=True,
        )
        self.assertIn(__file__, files)


# #############################################################################
# Test_find_git_root6
# #############################################################################


class Test_find_git_root6(hunitest.TestCase):
    """
    Check that the function returns the correct git root if:
    - the repo is a worktree

    Directory structure:
    main_repo/
    `-- .git/
        |-- config
        `-- worktrees/
            `-- csfy2/
                |-- HEAD
                `-- config
    csfy2/ (worktree)
    `-- .git (points to /main_repo/.git/worktrees/csfy2)
    """

    def set_up_test(self) -> None:
        temp_dir = self.get_scratch_space()
        # Create main repo with a .git directory.
        self.main_repo_dir = os.path.join(temp_dir, "main_repo")
        hio.create_dir(self.main_repo_dir, incremental=False)
        self.git_dir = os.path.join(self.main_repo_dir, ".git")
        hio.create_dir(self.git_dir, incremental=False)
        # Create worktree git metadata directory.
        self.worktree_git_dir = os.path.join(self.git_dir, "worktrees", "csfy2")
        hio.create_dir(self.worktree_git_dir, incremental=False)
        # Create worktree directory.
        self.worktree_dir = os.path.join(temp_dir, "csfy2")
        hio.create_dir(self.worktree_dir, incremental=False)
        # Create pointer from worktree to the git directory.
        worktree_git_file = os.path.join(self.worktree_dir, ".git")
        txt = f"gitdir: {self.worktree_git_dir}\n"
        hio.to_file(worktree_git_file, txt)

    def test1(self) -> None:
        """
        Check that the function returns the worktree root when called from a worktree.
        """
        self.set_up_test()
        with hsystem.cd(self.worktree_dir):
            git_root = hgit.find_git_root(".")
            # For worktrees, the function should return the worktree root,
            # not the main repository root.
            self.assert_equal(git_root, self.worktree_dir)
