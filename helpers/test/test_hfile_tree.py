import logging
import os

import helpers.hfile_tree as hfiltree
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_generate_tree
# #############################################################################


class Test_generate_tree(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test generating default tree.
        """
        # Prepare inputs.
        path = self.devops_dir
        depth = 0
        include_tests = False
        include_python = False
        only_dirs = False
        output = ""
        # Call tested function.
        actual = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        # Check output.
        expected = "\n".join(
            [
                "devops",
                "- compose",
                "- docker_build",
                "  - create_users.sh",
                "  - pip_list.txt",
                "- docker_run",
            ]
        )
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test generating default tree with depth.
        """
        # Prepare inputs.
        path = self.devops_dir
        depth = 1
        include_tests = False
        include_python = False
        only_dirs = False
        output = ""
        # Call tested function.
        actual = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        # Check output.
        expected = "\n".join(
            [
                "devops",
                "- compose",
                "- docker_build",
                "- docker_run",
            ]
        )
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test generating tree including test files and dirs.
        """
        # Prepare inputs.
        path = self.devops_dir
        depth = 0
        include_tests = True
        include_python = False
        only_dirs = False
        output = ""
        # Call tested function.
        actual = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        # Check output.
        expected = "\n".join(
            [
                "devops",
                "- compose",
                "- docker_build",
                "- docker_run",
                "- test",
                "  - test_docker.py",
            ]
        )
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test generating tree including python files.
        """
        # Prepare inputs.
        path = self.devops_dir
        depth = 0
        include_tests = False
        include_python = True
        only_dirs = False
        output = ""
        # Call tested function.
        actual = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        # Check output.
        expected = "\n".join(
            [
                "devops",
                "- __init__.py",
                "- compose",
                "- docker_build",
                "- docker_run",
                "  - execute.py",
                "- user_credentials.py",
            ]
        )
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test generating tree with only directories.
        """
        # Prepare inputs.
        path = self.devops_dir
        depth = 0
        include_tests = False
        include_python = False
        only_dirs = True
        output = ""
        # Call tested function.
        actual = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        # Check output.
        expected = "\n".join(
            [
                "devops",
                "- compose",
                "- docker_build",
                "- docker_run",
            ]
        )
        self.assertEqual(actual, expected)

    def test6(self) -> None:
        """
        Test generating tree including tests, python files, and only
        directories.
        """
        # Prepare inputs.
        path = self.devops_dir
        depth = 0
        include_tests = True
        include_python = True
        only_dirs = True
        output = ""
        # Call tested function.
        actual = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        # Check output.
        expected = "\n".join(
            [
                "devops",
                "- __init__.py",
                "- compose",
                "- docker_build",
                "- docker_run",
                "  - execute.py",
                "- test",
                "  - test_docker.py",
                "- user_credentials.py",
            ]
        )
        self.assertEqual(actual, expected)

    def test7(self) -> None:
        """
        Test writing tree to file.
        """
        # Prepare inputs.
        scratch = self.get_scratch_space()
        path = self.devops_dir
        depth = 0
        include_tests = False
        include_python = False
        only_dirs = False
        output = os.path.join(scratch, "TREE.md")
        # Call tested function.
        _ = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        with open(output, encoding="utf-8") as f:
            actual = f.read()
        # Check output.
        expected = (
            "\n".join(
                [
                    "<!-- tree:start:devops -->",
                    "devops",
                    "- compose",
                    "- docker_build",
                    "  - create_users.sh",
                    "  - pip_list.txt",
                    "- docker_run",
                    "<!-- tree:end -->",
                ]
            )
            + "\n"
        )
        self.assertEqual(actual, expected)

    def test8(self) -> None:
        """
        Test updating tree on existing file, preserving comments.
        """
        # Prepare inputs.
        scratch = self.get_scratch_space()
        path = self.devops_dir
        depth = 0
        include_tests = False
        include_python = False
        only_dirs = False
        output = os.path.join(scratch, "TREE.md")
        # Create existing file.
        content = (
            "\n".join(
                [
                    "<!-- tree:start:devops -->",
                    "devops",
                    "- compose    # compose-comment",
                    "- docker_build",
                    "  - pip_list.txt    # pip-comment",
                    "<!-- tree:end -->",
                ]
            )
            + "\n"
        )
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        # Call tested function.
        _ = hfiltree.generate_tree(
            path=path,
            depth=depth,
            include_tests=include_tests,
            include_python=include_python,
            only_dirs=only_dirs,
            output=output,
        )
        with open(output, encoding="utf-8") as f:
            actual = f.read()
        # Check output.
        expected = (
            "\n".join(
                [
                    "<!-- tree:start:devops -->",
                    "devops",
                    "- compose    # compose-comment",
                    "- docker_build",
                    "  - create_users.sh",
                    "  - pip_list.txt    # pip-comment",
                    "- docker_run",
                    "<!-- tree:end -->",
                ]
            )
            + "\n"
        )
        self.assertEqual(actual, expected)

    def setUp(self) -> None:
        """
        Create a `devops` directory in scratch space.

        Scratch directory layout:
        ```
        devops
        - __init__.py
        - user_credentials.py
        -  compose
        - docker_run
          - execute.py
        - docker_build
          - create_users.sh
          - pip_list.txt
        - test
          - TestDocker
          - test_docker.py
        ```
        """
        super().setUp()
        scratch = self.get_scratch_space()
        self.devops_dir = os.path.join(scratch, "devops")
        os.mkdir(self.devops_dir)
        structure = {
            "": ["__init__.py", "user_credentials.py"],
            "compose": [],
            "docker_run": ["execute.py"],
            "docker_build": ["create_users.sh", "pip_list.txt"],
            "test": ["TestDocker", "test_docker.py"],
        }
        # Create empty dirs and files.
        for subdir, files in structure.items():
            folder = (
                os.path.join(self.devops_dir, subdir)
                if subdir
                else self.devops_dir
            )
            if subdir:
                os.mkdir(folder)
            for name in files:
                open(os.path.join(folder, name), "w").close()
