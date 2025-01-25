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


def _execute_func_call(func_call: str) -> None:
    """
    Execute a function call, e.g., `func_call = "hgit.get_modified_files()"`.
    """
    act = eval(func_call)
    _LOG.debug("\n-> %s=\n  '%s'", func_call, act)


class Test_git_submodule1(hunitest.TestCase):
    def test_get_client_root1(self) -> None:
        func_call = "hgit.get_client_root(super_module=True)"
        _execute_func_call(func_call)

    def test_get_client_root2(self) -> None:
        func_call = "hgit.get_client_root(super_module=False)"
        _execute_func_call(func_call)

    def test_get_project_dirname1(self) -> None:
        func_call = "hgit.get_project_dirname()"
        _execute_func_call(func_call)

    def test_get_branch_name1(self) -> None:
        _ = hgit.get_branch_name()

    def test_is_inside_submodule1(self) -> None:
        func_call = "hgit.is_inside_submodule()"
        _execute_func_call(func_call)

    # Outside CK infra, the following call hangs, so we skip it.
    @pytest.mark.requires_ck_infra
    def test_is_amp(self) -> None:
        func_call = "hgit.is_amp()"
        _execute_func_call(func_call)

    def test_get_path_from_supermodule1(self) -> None:
        func_call = "hgit.get_path_from_supermodule()"
        _execute_func_call(func_call)

    def test_get_submodule_paths1(self) -> None:
        func_call = "hgit.get_submodule_paths()"
        _execute_func_call(func_call)


class Test_git_submodule2(hunitest.TestCase):
    # def test_get_submodule_hash1(self) -> None:
    #     dir_name = "amp"
    #     _ = hgit._get_submodule_hash(dir_name)

    def test_get_remote_head_hash1(self) -> None:
        dir_name = "."
        _ = hgit.get_head_hash(dir_name)

    # def test_report_submodule_status1(self) -> None:
    #     dir_names = ["."]
    #     short_hash = True
    #     _ = hgit.report_submodule_status(dir_names, short_hash)

    def test_get_head_hash1(self) -> None:
        dir_name = "."
        _ = hgit.get_head_hash(dir_name)

    def test_group_hashes1(self) -> None:
        head_hash = "a2bfc704"
        remh_hash = "a2bfc704"
        subm_hash = None
        exp = "head_hash = remh_hash = a2bfc704"
        #
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, exp)

    def test_group_hashes2(self) -> None:
        head_hash = "22996772"
        remh_hash = "92167662"
        subm_hash = "92167662"
        exp = """
        head_hash = 22996772
        remh_hash = subm_hash = 92167662
        """
        #
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, exp)

    def test_group_hashes3(self) -> None:
        head_hash = "7ea03eb6"
        remh_hash = "7ea03eb6"
        subm_hash = "7ea03eb6"
        exp = "head_hash = remh_hash = subm_hash = 7ea03eb6"
        #
        self._helper_group_hashes(head_hash, remh_hash, subm_hash, exp)

    def _helper_group_hashes(
        self, head_hash: str, remh_hash: str, subm_hash: Optional[str], exp: str
    ) -> None:
        act = hgit._group_hashes(head_hash, remh_hash, subm_hash)
        self.assert_equal(act, exp, fuzzy_match=True)


class Test_git_repo_name1(hunitest.TestCase):
    def test_parse_github_repo_name1(self) -> None:
        repo_name = "git@github.com:alphamatic/amp"
        host_name, repo_name = hgit._parse_github_repo_name(repo_name)
        self.assert_equal(host_name, "github.com")
        self.assert_equal(repo_name, "alphamatic/amp")

    def test_parse_github_repo_name2(self) -> None:
        repo_name = "https://github.com/alphamatic/amp"
        hgit._parse_github_repo_name(repo_name)
        host_name, repo_name = hgit._parse_github_repo_name(repo_name)
        self.assert_equal(host_name, "github.com")
        self.assert_equal(repo_name, "alphamatic/amp")

    def test_parse_github_repo_name3(self) -> None:
        repo_name = "git@github.fake.com:alphamatic/amp"
        host_name, repo_name = hgit._parse_github_repo_name(repo_name)
        self.assert_equal(host_name, "github.fake.com")
        self.assert_equal(repo_name, "alphamatic/amp")

    def test_parse_github_repo_name4(self) -> None:
        repo_name = "https://github.fake.com/alphamatic/amp"
        host_name, repo_name = hgit._parse_github_repo_name(repo_name)
        self.assert_equal(host_name, "github.fake.com")
        self.assert_equal(repo_name, "alphamatic/amp")

    def test_get_repo_full_name_from_dirname1(self) -> None:
        func_call = "hgit.get_repo_full_name_from_dirname(dir_name='.', include_host_name=False)"
        _execute_func_call(func_call)

    def test_get_repo_full_name_from_dirname2(self) -> None:
        func_call = "hgit.get_repo_full_name_from_dirname(dir_name='.', include_host_name=True)"
        _execute_func_call(func_call)

    def test_get_repo_full_name_from_client1(self) -> None:
        func_call = "hgit.get_repo_full_name_from_client(super_module=True)"
        _execute_func_call(func_call)

    def test_get_repo_full_name_from_client2(self) -> None:
        func_call = "hgit.get_repo_full_name_from_client(super_module=False)"
        _execute_func_call(func_call)

    def test_get_repo_name1(self) -> None:
        short_name = "amp"
        mode = "short_name"
        act = hgit.get_repo_name(short_name, mode)
        exp = "alphamatic/amp"
        self.assert_equal(act, exp)

    def test_get_repo_name2(self) -> None:
        full_name = "alphamatic/amp"
        mode = "full_name"
        act = hgit.get_repo_name(full_name, mode)
        exp = "amp"
        self.assert_equal(act, exp)

    # Outside CK infra, the following call hangs, so we skip it.
    @pytest.mark.requires_ck_infra
    def test_get_all_repo_names1(self) -> None:
        if not hgit.is_in_amp_as_supermodule():
            _LOG.warning(
                "Skipping this test, since it can run only in amp as super-module"
            )
            return
        mode = "short_name"
        act = hgit.get_all_repo_names(mode)
        exp = ["amp", "cmamp", "helpers", "tutorials"]
        self.assert_equal(str(act), str(exp))

    # Outside CK infra, the following call hangs, so we skip it.
    @pytest.mark.requires_ck_infra
    def test_get_all_repo_names2(self) -> None:
        if not hgit.is_in_amp_as_supermodule():
            _LOG.warning(
                "Skipping this test, since it can run only in amp as super-module"
            )
            return
        mode = "full_name"
        act = hgit.get_all_repo_names(mode)
        exp = [
            "alphamatic/amp",
            "causify-ai/cmamp",
            "causify-ai/helpers",
            "causify-ai/tutorials",
        ]
        self.assert_equal(str(act), str(exp))

    def test_get_repo_name_rountrip1(self) -> None:
        """
        Test round-trip transformation for get_repo_name().
        """
        # Get the short name for all the repos.
        mode = "short_name"
        all_repo_short_names = hgit.get_all_repo_names(mode)
        # Round trip.
        for repo_short_name in all_repo_short_names:
            repo_full_name = hgit.get_repo_name(repo_short_name, "short_name")
            repo_short_name_tmp = hgit.get_repo_name(repo_full_name, "full_name")
            self.assert_equal(repo_short_name, repo_short_name_tmp)


# Outside CK infra, the following class hangs, so we skip it.
@pytest.mark.requires_ck_infra
class Test_git_path1(hunitest.TestCase):
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_supermodule(),
        reason="Run only in amp as super-module",
    )
    def test_get_path_from_git_root1(self) -> None:
        file_name = "/app/helpers/test/test_hgit.py"
        act = hgit.get_path_from_git_root(file_name, super_module=True)
        _LOG.debug("get_path_from_git_root()=%s", act)
        # Check.
        exp = "helpers/test/test_hgit.py"
        self.assert_equal(act, exp)

    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(), reason="Run only in amp as sub-module"
    )
    def test_get_path_from_git_root2(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        act = hgit.get_path_from_git_root(file_name, super_module=True)
        _LOG.debug("get_path_from_git_root()=%s", act)
        # Check.
        exp = "amp/helpers/test/test_hgit.py"
        self.assert_equal(act, exp)

    def test_get_path_from_git_root3(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        git_root = "/app"
        act = hgit.get_path_from_git_root(
            file_name, super_module=False, git_root=git_root
        )
        # Check.
        exp = "amp/helpers/test/test_hgit.py"
        self.assert_equal(act, exp)

    def test_get_path_from_git_root4(self) -> None:
        file_name = "/app/amp/helpers/test/test_hgit.py"
        git_root = "/app/amp"
        act = hgit.get_path_from_git_root(
            file_name, super_module=False, git_root=git_root
        )
        # Check.
        exp = "helpers/test/test_hgit.py"
        self.assert_equal(act, exp)

    def test_get_path_from_git_root5(self) -> None:
        file_name = "helpers/test/test_hgit.py"
        git_root = "/app/amp"
        with self.assertRaises(ValueError):
            hgit.get_path_from_git_root(
                file_name, super_module=False, git_root=git_root
            )


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
        func_call = "hgit.get_modified_files()"
        _execute_func_call(func_call)

    def test_get_previous_committed_files1(self) -> None:
        func_call = "hgit.get_previous_committed_files()"
        _execute_func_call(func_call)

    def test_get_modified_files_in_branch1(self) -> None:
        func_call = "hgit.get_modified_files_in_branch('master')"
        _execute_func_call(func_call)

    def test_get_summary_files_in_branch1(self) -> None:
        func_call = "hgit.get_summary_files_in_branch('master')"
        _execute_func_call(func_call)

    def test_git_log1(self) -> None:
        func_call = "hgit.git_log()"
        _execute_func_call(func_call)


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


class Test_extract_gh_issue_number_from_branch(hunitest.TestCase):
    def test_extract_gh_issue_number_from_branch1(self) -> None:
        """
        Tests extraction from a branch name with a specific format.
        """
        branch_name = "CmampTask10725_Add_more_tabs_to_orange_tmux"
        act = hgit.extract_gh_issue_number_from_branch(branch_name)
        exp = "10725"
        self.assert_equal(str(act), exp)

    def test_extract_gh_issue_number_from_branch2(self) -> None:
        """
        Tests extraction from another branch name format.
        """
        branch_name = "HelpersTask23_Add_more_tabs_to_orange_tmux"
        act = hgit.extract_gh_issue_number_from_branch(branch_name)
        exp = "23"
        self.assert_equal(str(act), exp)

    def test_extract_gh_issue_number_from_branch3(self) -> None:
        """
        Tests extraction from a short branch name format.
        """
        branch_name = "CmTask3434"
        act = hgit.extract_gh_issue_number_from_branch(branch_name)
        exp = "3434"
        self.assert_equal(str(act), exp)

    def test_extract_gh_issue_number_from_branch4(self) -> None:
        """
        Tests behavior when no issue number is present in the branch name.
        """
        branch_name = "NoTaskNumberHere"
        act = hgit.extract_gh_issue_number_from_branch(branch_name)
        exp = "None"
        self.assert_equal(str(act), exp)


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
        txt = f"gitdir: ../.git/modules/amp"
        hio.to_file(submodule_git_file, txt)
        submodule_git_file_dir = os.path.join(
            self.repo_dir, ".git", "modules", "amp"
        )
        hio.create_dir(submodule_git_file_dir, incremental=False)
        # Create `helpers_root` submodule under `amp`.
        self.subsubmodule_dir = os.path.join(self.submodule_dir, "helpers_root")
        hio.create_dir(self.subsubmodule_dir, incremental=False)
        subsubmodule_git_file = os.path.join(self.subsubmodule_dir, ".git")
        txt = f"gitdir: ../../.git/modules/amp/modules/helpers_root"
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
        self.set_up_test()
        with hsystem.cd(self.repo_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in first level submodule (e.g. //amp)
        """
        self.set_up_test()
        with hsystem.cd(self.submodule_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def test3(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in second level submodule (e.g. //helpers)
        """
        self.set_up_test()
        with hsystem.cd(self.subsubmodule_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def test4(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in a runnable dir (e.g. ck.infra) under the
            first level submodule (e.g. //amp)
        """
        self.set_up_test()
        with hsystem.cd(self.runnable_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)


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
        txt = f"gitdir: ../.git/modules/helpers_root"
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
        self.set_up_test()
        with hsystem.cd(self.repo_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is the submodule (e.g. //helpers)
        """
        self.set_up_test()
        with hsystem.cd(self.submodule_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def test3(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in a runnable dir (e.g. ck.infra)
        """
        self.set_up_test()
        with hsystem.cd(self.runnable_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)


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
        self.set_up_test()
        with hsystem.cd(self.repo_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)

    def test2(self) -> None:
        """
        Check that the function returns the correct git root if
        - the caller is in an arbitrary directory under the repo
        """
        self.set_up_test()
        with hsystem.cd(self.arbitrary_dir):
            git_root = hgit.find_git_root(".")
            self.assert_equal(git_root, self.repo_dir)


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
        with hsystem.cd(self.arbitrary_dir), self.assertRaises(
            AssertionError
        ) as cm:
            _ = hgit.find_git_root(".")
        act = str(cm.exception)
        exp = """
        * Failed assertion *
        '/'
        !=
        '/'
        No .git directory or file found in any parent directory.
        """
        self.assert_equal(act, exp, purify_text=True, fuzzy_match=True)

    def test2(self) -> None:
        """
        Check that the error is raised when the caller is in a submodule or
        linked repo that points to non existing super repo.
        """
        with hsystem.cd(self.repo_dir), self.assertRaises(AssertionError) as cm:
            _ = hgit.find_git_root(".")
        act = str(cm.exception)
        exp = f"""
        * Failed assertion *
        '/'
        !=
        '/'
        Top-level .git directory not found.
        """
        self.assert_equal(act, exp, purify_text=True, fuzzy_match=True)
