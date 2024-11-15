import logging
import unittest.mock as umock

import helpers.hdocker as hdocker
import helpers.hprint as hprint
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
        # Mock `henv.execute_repo_config_code()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared1": "/shared_folder1",
            "/data/shared2": "/shared_folder2",
        }
        with umock.patch.object(
            hdocker.henv, "execute_repo_config_code", return_value=mock_mapping
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
        # Mock `henv.execute_repo_config_code()` to return a dummy mapping.
        mock_mapping = {
            "/data/shared": "/shared_folder",
        }
        with umock.patch.object(
            hdocker.henv, "execute_repo_config_code", return_value=mock_mapping
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
# Test_run_dockerized_prettier1
# #############################################################################

import os
import helpers.hio as hio
from typing import List

class Test_run_dockerized_prettier1(hunitest.TestCase):

    def create_test_file(self) -> str:
        file_path = os.path.join(self.get_scratch_space(), "input.txt")
        txt = """
- A
  - B
      - C
        """
        txt = hprint.remove_empty_lines(txt)
        hio.to_file(file_path, txt)
        return file_path

    @staticmethod
    def get_expected_output() -> str:
        txt = """
- A
  - B
    - C
"""
        txt = hprint.remove_empty_lines(txt)
        return txt

    def test1(self) -> None:
        cmd_opts: List[str] = []
        cmd_opts.append("--parser markdown")
        cmd_opts.append("--prose-wrap always")
        tab_width = 2
        cmd_opts.append(f"--tab-width {tab_width}")
        # Run `prettier` in a Docker container.
        in_file_path = self.create_test_file()
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
        force_rebuild = False
        use_sudo = True
        run_inside_docker = True
        hdocker.run_dockerized_prettier(cmd_opts, in_file_path,
                                        out_file_path,
                                        force_rebuild, use_sudo,
                                        run_inside_docker)
        # Check.
        act = hio.from_file(out_file_path)
        exp = self.get_expected_output()
        self.assert_equal(act, exp)