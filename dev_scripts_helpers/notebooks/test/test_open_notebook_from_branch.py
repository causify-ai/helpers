import os

import dev_scripts_helpers.notebooks.open_notebook_from_branch as dsnoonfb
import helpers.hunit_test as hunitest

# #############################################################################
# Test_normalize_branch
# #############################################################################


class Test_normalize_branch(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._normalize_branch()`.
    """

    def test1(self) -> None:
        """
        Test that the `origin/` prefix is removed.
        """
        # Prepare inputs.
        branch = "origin/UmdTask788_Racket_sports"
        # Run test.
        actual = dsnoonfb._normalize_branch(branch)
        # Check outputs.
        expected = "UmdTask788_Racket_sports"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a branch without remote is not changed.
        """
        # Prepare inputs.
        branch = "UmdTask788_Racket_sports"
        # Run test.
        actual = dsnoonfb._normalize_branch(branch)
        # Check outputs.
        expected = branch
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that only the leading `origin/` is removed.
        """
        # Prepare inputs.
        branch = "origin/feature/origin/fix"
        # Run test.
        actual = dsnoonfb._normalize_branch(branch)
        # Check outputs.
        expected = "feature/origin/fix"
        self.assert_equal(actual, expected)


# #############################################################################
# Test_get_notebook_rel_path
# #############################################################################


class Test_get_notebook_rel_path(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._get_notebook_rel_path()`.
    """

    def test1(self) -> None:
        """
        Test that a path missing locally is assumed relative to the git root.
        """
        # Prepare inputs.
        notebook = "no_such_dir_xyz/notebooks/nb.ipynb"
        git_root = "/git/root"
        # Run test.
        actual = dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        expected = notebook
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that an absolute path is converted to be relative to the git root.
        """
        # Prepare inputs.
        git_root = "/git/root"
        notebook = os.path.join(git_root, "project/notebooks/nb.ipynb")
        # Run test.
        actual = dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        expected = "project/notebooks/nb.ipynb"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that a file that is not a notebook is rejected.
        """
        # Prepare inputs.
        notebook = "project/notebooks/nb.py"
        git_root = "/git/root"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        self.assertIn("is not a notebook", str(cm.exception))

    def test4(self) -> None:
        """
        Test that an absolute path outside the git root is rejected.
        """
        # Prepare inputs.
        notebook = "/other/dir/nb.ipynb"
        git_root = "/git/root"
        # Run test.
        with self.assertRaises(AssertionError) as cm:
            dsnoonfb._get_notebook_rel_path(notebook, git_root)
        # Check outputs.
        self.assertIn("is outside the git root", str(cm.exception))


# #############################################################################
# Test_parse_worktree_list
# #############################################################################


class Test_parse_worktree_list(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._parse_worktree_list()`.
    """

    def helper(self, branch: str, expected: object) -> None:
        # Prepare inputs.
        txt = """
        worktree /src/repo
        HEAD 1111111111111111111111111111111111111111
        branch refs/heads/master

        worktree /src/repo_worktree_788
        HEAD 2222222222222222222222222222222222222222
        branch refs/heads/UmdTask788_Racket_sports

        worktree /src/repo_detached
        HEAD 3333333333333333333333333333333333333333
        detached
        """
        txt = "\n".join(line.strip() for line in txt.split("\n"))
        # Run test.
        actual = dsnoonfb._parse_worktree_list(txt, branch)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test that the worktree of a branch is found.
        """
        self.helper("UmdTask788_Racket_sports", "/src/repo_worktree_788")

    def test2(self) -> None:
        """
        Test that the main client is found as the worktree of its branch.
        """
        self.helper("master", "/src/repo")

    def test3(self) -> None:
        """
        Test that a branch without worktree returns `None`.
        """
        self.helper("UmdTask999_Other", None)

    def test4(self) -> None:
        """
        Test that a branch name that is a prefix of another one is not matched.
        """
        self.helper("UmdTask788", None)


# #############################################################################
# Test_get_default_worktree_dir
# #############################################################################


class Test_get_default_worktree_dir(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._get_default_worktree_dir()`.
    """

    def test1(self) -> None:
        """
        Test that the dir uses the issue number, like `git_create_issue_and_branch`.
        """
        # Prepare inputs.
        branch = "UmdTask788_Racket_sports_Change_color_of_heatmaps"
        git_root = "/src/umd_classes1"
        # Run test.
        actual = dsnoonfb._get_default_worktree_dir(branch, git_root=git_root)
        # Check outputs.
        expected = "/src/umd_classes1_worktree_788"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that a branch without issue number uses the branch name.
        """
        # Prepare inputs.
        branch = "feature/fix_bug"
        git_root = "/src/umd_classes1"
        # Run test.
        actual = dsnoonfb._get_default_worktree_dir(branch, git_root=git_root)
        # Check outputs.
        expected = "/src/umd_classes1_worktree_feature_fix_bug"
        self.assert_equal(actual, expected)


# #############################################################################
# Test_get_notebook_url
# #############################################################################


class Test_get_notebook_url(hunitest.TestCase):
    """
    Test `open_notebook_from_branch._get_notebook_url()`.
    """

    def test1(self) -> None:
        """
        Test the URL of a notebook inside the container.
        """
        # Prepare inputs.
        rel_notebook = "research/Racket/notebooks/racket_shot_probability.ipynb"
        # Run test.
        actual = dsnoonfb._get_notebook_url(rel_notebook, 8888)
        # Check outputs.
        expected = (
            "http://localhost:8888/lab/tree/git_root/research/Racket/"
            "notebooks/racket_shot_probability.ipynb"
        )
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that special characters in the path are escaped.
        """
        # Prepare inputs.
        rel_notebook = "my dir/nb #1.ipynb"
        # Run test.
        actual = dsnoonfb._get_notebook_url(rel_notebook, 8889)
        # Check outputs.
        expected = (
            "http://localhost:8889/lab/tree/git_root/my%20dir/nb%20%231.ipynb"
        )
        self.assert_equal(actual, expected)
