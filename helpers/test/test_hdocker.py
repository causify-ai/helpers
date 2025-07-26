import logging
import os
import unittest.mock as umock
from typing import List, Optional, Tuple

import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_replace_shared_root_path1
# #############################################################################


class Test_replace_shared_root_path1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test replacing shared root path.
        """
        # Mock `hserver.get_shared_data_dirs()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared1": "/shared_folder1",
            "/data/shared2": "/shared_folder2",
        }
        with umock.patch.object(
            hserver, "get_shared_data_dirs", return_value=mock_mapping
        ):
            # Test replacing shared root path.
            path1 = "/data/shared1/asset1"
            act1 = hdocker.replace_shared_root_path(path1)
            exp1 = "/shared_folder1/asset1"
            self.assertEqual(act1, exp1)
            #
            path2 = "/data/shared2/asset2"
            act2 = hdocker.replace_shared_root_path(path2)
            exp2 = "/shared_folder2/asset2"
            self.assertEqual(act2, exp2)
            #
            path3 = 'object("/data/shared2/asset2/item")'
            act3 = hdocker.replace_shared_root_path(path3)
            exp3 = 'object("/shared_folder2/asset2/item")'
            self.assertEqual(act3, exp3)

    def test2(self) -> None:
        """
        Test replacing shared root path with the `replace_ecs_tokyo` parameter.
        """
        # Mock `hserver.get_shared_data_dirs()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared": "/shared_folder",
        }
        with umock.patch.object(
            hserver, "get_shared_data_dirs", return_value=mock_mapping
        ):
            # Test if `ecs_tokyo` is replaced if `replace_ecs_tokyo = True`.
            path1 = 'object("/data/shared/ecs_tokyo/asset2/item")'
            replace_ecs_tokyo = True
            act1 = hdocker.replace_shared_root_path(
                path1, replace_ecs_tokyo=replace_ecs_tokyo
            )
            exp1 = 'object("/shared_folder/ecs/asset2/item")'
            self.assertEqual(act1, exp1)
            # Test if `ecs_tokyo` is not replaced if `replace_ecs_tokyo` is not
            # defined.
            path2 = 'object("/data/shared/ecs_tokyo/asset2/item")'
            act2 = hdocker.replace_shared_root_path(path2)
            exp2 = 'object("/shared_folder/ecs_tokyo/asset2/item")'
            self.assertEqual(act2, exp2)


# #############################################################################
# Test_convert_to_docker_path1
# #############################################################################


class Test_convert_to_docker_path1(hunitest.TestCase):
    @staticmethod
    def convert_caller_to_callee_docker_path(
        in_file_path: str,
        is_caller_host: bool,
        use_sibling_container_for_callee: bool,
        check_if_exists: bool,
    ) -> Tuple[str, str]:
        """
        Prepare inputs and call the function to convert a file name to Docker
        paths.

        :return: A tuple containing
            - docker_file_path: the Docker file path
            - mount: the Docker mount string
        """
        (
            source_host_path,
            callee_mount_path,
            mount,
        ) = hdocker.get_docker_mount_info(
            is_caller_host, use_sibling_container_for_callee
        )
        docker_file_path = hdocker.convert_caller_to_callee_docker_path(
            in_file_path,
            source_host_path,
            callee_mount_path,
            check_if_exists=check_if_exists,
            is_input=True,
            is_caller_host=is_caller_host,
            use_sibling_container_for_callee=use_sibling_container_for_callee,
        )
        return docker_file_path, mount

    def helper(
        self,
        in_file_path: str,
        is_caller_host: bool,
        use_sibling_container_for_callee: bool,
        check_if_exists: bool,
        exp_docker_file_path: str,
        exp_mount: str,
    ) -> None:
        """
        Test converting a file name to Docker paths.
        """
        # Run test.
        docker_file_path, mount = self.convert_caller_to_callee_docker_path(
            in_file_path,
            is_caller_host,
            use_sibling_container_for_callee,
            check_if_exists,
        )
        # Check output.
        self.assert_equal(docker_file_path, exp_docker_file_path)
        self.assert_equal(mount, exp_mount)

    def test1(self) -> None:
        """
        Test converting a file name to Docker paths.
        """
        # - Prepare inputs.
        dir_name = self.get_input_dir()
        in_file_path = os.path.join(dir_name, "tmp.llm_transform.in.txt")
        is_caller_host = True
        use_sibling_container_for_callee = True
        check_if_exists = False
        # - Prepare outputs.
        helpers_root_path = hgit.find_helpers_root()
        exp_docker_file_path = os.path.join(
            helpers_root_path,
            "helpers/test/outcomes",
            "Test_convert_to_docker_path1.test1/input",
            "tmp.llm_transform.in.txt",
        )
        exp_mount = "type=bind,source=/app,target=/app"
        self.helper(
            in_file_path,
            is_caller_host,
            use_sibling_container_for_callee,
            check_if_exists,
            exp_docker_file_path,
            exp_mount,
        )

    def test2(self) -> None:
        """
        Test converting a file name of an existing file to a Docker path.
        """
        # - Prepare inputs.
        dir_name = self.get_input_dir()
        # Create a file.
        # E.g., in_file_path='/app/helpers/test/outcomes/Test_convert_to_docker_path1.test2/input/input.md'
        in_file_path = os.path.join(dir_name, "tmp.input.md")
        hio.to_file(in_file_path, "empty")
        _LOG.debug(hprint.to_str("in_file_path"))
        is_caller_host = True
        use_sibling_container_for_callee = True
        check_if_exists = True
        # - Prepare outputs.
        helpers_root_path = hgit.find_helpers_root()
        exp_docker_file_path = os.path.join(
            helpers_root_path,
            "helpers/test/outcomes",
            "Test_convert_to_docker_path1.test2/input",
            "tmp.input.md",
        )
        exp_mount = "type=bind,source=/app,target=/app"
        self.helper(
            in_file_path,
            is_caller_host,
            use_sibling_container_for_callee,
            check_if_exists,
            exp_docker_file_path,
            exp_mount,
        )


# #############################################################################
# Test_is_path1
# #############################################################################


class Test_is_path1(hunitest.TestCase):
    def helper(self, path: str, expected: bool) -> None:
        """
        Test helper for is_path function.
        """
        # Run test.
        actual = hdocker.is_path(path)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test_file_with_extension(self) -> None:
        """
        Test paths with file extensions.
        """
        # Prepare inputs.
        test_cases = [
            ("file.txt", True),
            ("document.pdf", True),
            ("script.py", True),
            ("data.csv", True),
            ("image.jpg", True),
            ("config.json", True),
            ("readme.md", True),
        ]
        # Run tests.
        for path, expected in test_cases:
            self.helper(path, expected)

    def test_absolute_paths(self) -> None:
        """
        Test absolute paths.
        """
        # Prepare inputs.
        test_cases = [
            ("/path/to/file.py", True),
            ("/usr/bin/python", True),
            ("/etc/config", True),
            ("/home/user", True),
            ("/", True),
            ("/data/shared", True),
        ]
        # Check outputs.
        for path, expected in test_cases:
            self.helper(path, expected)

    def test_relative_paths(self) -> None:
        """
        Test relative paths starting with ./ or ../.
        """
        # Prepare inputs and run tests.
        test_cases = [
            ("./file.txt", True),
            ("../data.csv", True),
            ("./folder/subfolder", True),
            ("../parent/file", True),
            ("./", True),
            ("../", True),
        ]
        # Run tests.
        for path, expected in test_cases:
            self.helper(path, expected)

    def test_trailing_slash_paths(self) -> None:
        """
        Test paths ending with slash (indicating directories).
        """
        # Prepare inputs and run tests.
        test_cases = [
            ("folder/", True),
            ("data/", True),
            ("my_directory/", True),
            ("nested/folder/", True),
        ]
        # Run tests.
        for path, expected in test_cases:
            self.helper(path, expected)

    def test_non_path_strings(self) -> None:
        """
        Test strings that should not be considered paths.
        """
        # Prepare inputs and run tests.
        test_cases = [
            ("readme", False),
            ("hello", False),
            ("command", False),
            ("data", False),
            ("test", False),
            ("python", False),
            ("docker", False),
            ("", False),
        ]
        # Run tests.
        for path, expected in test_cases:
            self.helper(path, expected)

    def test_edge_cases(self) -> None:
        """
        Test edge cases and complex scenarios.
        """
        # Prepare inputs and run tests.
        test_cases = [
            # - Files with multiple extensions.
            ("file.tar.gz", True),
            ("backup.sql.bz2", True),
            # - Hidden files.
            (".hidden", True),
            (".gitignore", True),
            # - Complex paths.
            ("./nested/folder/file.txt", True),
            ("../parent/folder/", True),
            ("/absolute/path/file.py", True),
            # - Files without extension in paths.
            # True because it contains a slash
            ("folder/README", True),
            # True because starts with ./
            ("./config", True),
            # True because starts with /
            ("/usr/bin/python", True),
            # - Strings that might be confused with paths.
            # True because has extension.
            ("folder.name", True),
            # False because no extension, slash, or path prefix.
            ("file-name", False),
            # False because no extension, slash, or path prefix.
            ("under_score", False),
        ]
        # Run tests.
        for path, expected in test_cases:
            self.helper(path, expected)


# #############################################################################
# Test_convert_all_paths_from_caller_to_callee_docker_path1
# #############################################################################


class Test_convert_all_paths_from_caller_to_callee_docker_path1(
    hunitest.TestCase
):
    def helper(
        self,
        cmd_opts: List[str],
        expected_output: List[str],
        *,
        is_caller_host: bool = True,
        use_sibling_container_for_callee: bool = True,
        create_files: Optional[List[str]] = None,
    ) -> None:
        """
        Helper for `convert_all_paths_from_caller_to_callee_docker_path()`.
        """
        # Prepare inputs.
        if create_files:
            # Create temporary files for testing existing file paths.
            for file_path in create_files:
                dir_name = os.path.dirname(file_path)
                if dir_name:
                    hio.create_dir(dir_name, incremental=True)
                hio.to_file(file_path, "test content")
        # Get docker mount info for the test.
        (
            caller_mount_path,
            callee_mount_path,
            _,
        ) = hdocker.get_docker_mount_info(
            is_caller_host, use_sibling_container_for_callee
        )
        # Run test.
        actual = hdocker.convert_all_paths_from_caller_to_callee_docker_path(
            cmd_opts,
            caller_mount_path,
            callee_mount_path,
            is_caller_host,
            use_sibling_container_for_callee,
        )
        # Check outputs.
        self.assert_equal(actual, expected_output)

    def test_mixed_options_with_paths_and_non_paths(self) -> None:
        """
        Test converting mixed command options with paths and non-paths.
        """
        # Prepare inputs.
        cmd_opts = [
            "--verbose",
            "file.txt",  # Path-like (has extension)
            "--output",
            "./output.log",  # Path-like (relative path)
            "command",  # Not a path
            "/absolute/path",  # Path-like (absolute)
            "--flag",
            "folder/",  # Path-like (trailing slash)
        ]
        expected_output = [
            "--verbose",
            "/app/file.txt",  # Converted
            "--output",
            "/app/output.log",  # Converted
            "command",  # Not converted
            "/app/absolute/path",  # Converted
            "--flag",
            "/app/folder/",  # Converted
        ]

        # Run test and check outputs.
        self.helper(cmd_opts, expected_output)

    def test_existing_files_get_converted(self) -> None:
        """
        Test that existing files are converted even without path-like appearance.
        """
        # Prepare inputs.
        temp_dir = self.get_scratch_space()
        existing_file = os.path.join(temp_dir, "testfile")
        cmd_opts = [
            "--input",
            existing_file,  # Will exist, should be converted
            "nonexistent",  # Doesn't exist and not path-like, won't be converted
        ]
        expected_output = [
            "--input",
            f"/app/{os.path.relpath(existing_file, hgit.find_git_root())}",  # Converted
            "nonexistent",  # Not converted
        ]

        # Run test and check outputs.
        self.helper(cmd_opts, expected_output, create_files=[existing_file])

    def test_path_like_strings_without_existing_files(self) -> None:
        """
        Test that path-like strings are converted even if files don't exist.
        """
        # Prepare inputs.
        cmd_opts = [
            "script.py",  # Path-like (extension) but doesn't exist
            "../config.json",  # Path-like (relative) but doesn't exist
            "/usr/bin/tool",  # Path-like (absolute) but doesn't exist
            "plain_word",  # Not path-like and doesn't exist
        ]
        expected_output = [
            "/app/script.py",  # Converted (has extension)
            "/app/config.json",  # Converted (relative path)
            "/app/usr/bin/tool",  # Converted (absolute path)
            "plain_word",  # Not converted
        ]

        # Run test and check outputs.
        self.helper(cmd_opts, expected_output)

    def test_empty_command_options(self) -> None:
        """
        Test handling of empty command options list.
        """
        # Prepare inputs.
        cmd_opts = []
        expected_output = []

        # Run test and check outputs.
        self.helper(cmd_opts, expected_output)

    def test_only_non_path_options(self) -> None:
        """
        Test command options with no paths.
        """
        # Prepare inputs.
        cmd_opts = [
            "--verbose",
            "--debug",
            "command",
            "argument",
            "--flag",
        ]
        expected_output = [
            "--verbose",
            "--debug",
            "command",
            "argument",
            "--flag",
        ]

        # Run test and check outputs.
        self.helper(cmd_opts, expected_output)

    def test_only_path_options(self) -> None:
        """
        Test command options with only paths.
        """
        # Prepare inputs.
        cmd_opts = [
            "input.txt",
            "./config.yaml",
            "/var/log/app.log",
            "data/",
            "../output.json",
        ]
        expected_output = [
            "/app/input.txt",
            "/app/config.yaml",
            "/app/var/log/app.log",
            "/app/data/",
            "/app/output.json",
        ]

        # Run test and check outputs.
        self.helper(cmd_opts, expected_output)

    def test_complex_paths_with_extensions(self) -> None:
        """
        Test complex paths with multiple extensions and special cases.
        """
        # Prepare inputs.
        cmd_opts = [
            "archive.tar.gz",  # Multiple extensions
            ".hidden",  # Hidden file
            "backup.sql.bz2",  # Multiple extensions
            ".gitignore",  # Hidden config file
        ]
        expected_output = [
            "/app/archive.tar.gz",
            "/app/.hidden",
            "/app/backup.sql.bz2",
            "/app/.gitignore",
        ]

        # Run test and check outputs.
        self.helper(cmd_opts, expected_output)

    def test_sibling_vs_child_container_modes(self) -> None:
        """
        Test different container modes (sibling vs child).
        """
        # Prepare inputs.
        cmd_opts = ["input.txt", "output/"]

        # Test sibling container mode.
        expected_sibling = ["/app/input.txt", "/app/output/"]
        self.helper(
            cmd_opts,
            expected_sibling,
            is_caller_host=True,
            use_sibling_container_for_callee=True,
        )

        # Test child container mode.
        expected_child = ["/app/input.txt", "/app/output/"]
        self.helper(
            cmd_opts,
            expected_child,
            is_caller_host=True,
            use_sibling_container_for_callee=False,
        )
