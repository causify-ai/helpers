import logging
import os
import unittest.mock as umock
from typing import Any, List, Tuple

import pytest

import helpers.hdocker as hdocker
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
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
