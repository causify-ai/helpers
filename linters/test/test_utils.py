import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.utils as liutils


class TestGetPythonFiles(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that there are Python files.
        """
        root_dir = hgit.get_client_root(super_module=False)
        files = liutils.get_python_files_to_lint(root_dir)
        self.assertGreater(len(files), 0)

    def test2(self) -> None:
        """
        Test that all files are Python files.
        """
        root_dir = hgit.get_client_root(super_module=False)
        files = liutils.get_python_files_to_lint(root_dir)
        python_files = [file for file in files if file.endswith(".py")]
        self.assertEqual(len(files), len(python_files))

    def test3(self) -> None:
        """
        Test that test Python files are excluded.
        """
        root_dir = hgit.get_client_root(super_module=False)
        files = liutils.get_python_files_to_lint(root_dir)
        test_files = [file for file in files if "/test/" in file]
        self.assertEqual(len(test_files), 0)

    def test4(self) -> None:
        """
        Test that jupytext Python files are excluded.
        """
        root_dir = hgit.get_client_root(super_module=False)
        files = liutils.get_python_files_to_lint(root_dir)
        paired_jupytext_files = [
            file for file in files if hio.is_paired_jupytext_python_file(file)
        ]
        self.assertEqual(len(paired_jupytext_files), 0)

    def test5(self) -> None:
        """
        Test that Python files from exceptions list are excluded.
        """
        root_dir = hgit.get_client_root(super_module=False)
        files = liutils.get_python_files_to_lint(root_dir)
        exceptions = liutils.FILES_TO_EXCLUDE
        exceptions_files = [file for file in files if file in exceptions]
        self.assertEqual(len(exceptions_files), 0)
