import os
import logging
import os
import unittest.mock as umock
from typing import Any, List

import pytest

import helpers.hdocker as hdocker
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


def _create_test_file(self_: Any, txt: str, extension: str) -> str:
    file_path = os.path.join(self_.get_scratch_space(), f"input.{extension}")
    txt = hprint.dedent(txt, remove_empty_leading_trailing_lines=True)
    _LOG.debug("txt=\n%s", txt)
    hio.to_file(file_path, txt)
    return file_path


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_run_dockerized_prettier1(hunitest.TestCase):
    """
    Test running the `prettier` command inside a Docker container.
    """

    def test1(self) -> None:
        txt = """
        - A
          - B
              - C
                """
        exp = """
        - A
          - B
            - C
        """
        self._helper(txt, exp)

    def test2(self) -> None:
        txt = r"""
        *  Good time management

        1. choose the right tasks
            -   avoid non-essential tasks
        """
        exp = r"""
        - Good time management

        1. choose the right tasks
           - avoid non-essential tasks
        """
        self._helper(txt, exp)

    def _helper(self, txt: str, exp: str) -> None:
        """
        Test running the `prettier` command in a Docker container.

        This test creates a test file, runs the `prettier` command inside a
        Docker container with specified command options, and checks if the
        output matches the expected result.
        """
        cmd_opts: List[str] = []
        cmd_opts.append("--parser markdown")
        cmd_opts.append("--prose-wrap always")
        tab_width = 2
        cmd_opts.append(f"--tab-width {tab_width}")
        # Run `prettier` in a Docker container.
        in_file_path = _create_test_file(self, txt, extension="txt")
        out_file_path = os.path.join(self.get_scratch_space(), "output.txt")
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        hdocker.run_dockerized_prettier(
            cmd_opts,
            in_file_path,
            out_file_path,
            force_rebuild,
            use_sudo,
        )
        # Check.
        act = hio.from_file(out_file_path)
        act = hprint.dedent(act, remove_empty_leading_trailing_lines=True)
        exp = hprint.dedent(exp, remove_empty_leading_trailing_lines=True)
        self.assert_equal(act, exp)


# #############################################################################
# Test_run_dockerized_pandoc1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_run_dockerized_pandoc1(hunitest.TestCase):
    """
    Test running the `pandoc` command inside a Docker container.
    """

    def test1(self) -> None:
        txt = """
        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        exp = r"""
        -   [Good](#good){#toc-good}
            -   [Bad](#bad){#toc-bad}

        # Good

        -   Good time management
            1.  choose the right tasks

            -   Avoid non-essential tasks

        ## Bad

        -   Hello
            -   World
        """
        self._helper(txt, exp)

    def _helper(self, txt: str, exp: str) -> None:
        """
        Test running the `prettier` command in a Docker container.

        This test creates a test file, runs the `prettier` command inside a
        Docker container with specified command options, and checks if the
        output matches the expected result.
        """
        cmd_opts: List[str] = []
        # Generate the table of contents.
        cmd_opts.append("-s --toc")
        # Run `pandoc` in a Docker container.
        in_file_path = _create_test_file(self, txt, extension="md")
        out_file_path = os.path.join(self.get_scratch_space(), "output.md")
        use_sudo = hdocker.get_use_sudo()
        hdocker.run_dockerized_pandoc(
            cmd_opts,
            in_file_path,
            out_file_path,
            use_sudo,
        )
        # Check.
        act = hio.from_file(out_file_path)
        act = hprint.dedent(act, remove_empty_leading_trailing_lines=True)
        exp = hprint.dedent(exp, remove_empty_leading_trailing_lines=True)
        self.assert_equal(act, exp)


# #############################################################################
# Test_run_markdown_toc1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_run_markdown_toc1(hunitest.TestCase):
    """
    Test running the `markdown-toc` command inside a Docker container.
    """

    def test1(self) -> None:
        txt = """
        <!-- toc -->
        
        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        exp = r"""
        <!-- toc -->

        - [Good](#good)
          * [Bad](#bad)

        <!-- tocstop -->

        # Good
        - Good time management
          1. choose the right tasks
            - Avoid non-essential tasks

        ## Bad
        -  Hello
            - World
        """
        self._helper(txt, exp)

    def _helper(self, txt: str, exp: str) -> None:
        """
        Test running the `markdown-toc` command in a Docker container.
        """
        cmd_opts: List[str] = []
        # Run `markdown-toc` in a Docker container.
        in_file_path = _create_test_file(self, txt, extension="md")
        force_rebuild = False
        use_sudo = hdocker.get_use_sudo()
        hdocker.run_dockerized_markdown_toc(
            cmd_opts,
            in_file_path,
            force_rebuild,
            use_sudo,
        )
        # Check.
        act = hio.from_file(in_file_path)
        act = hprint.dedent(act, remove_empty_leading_trailing_lines=True)
        exp = hprint.dedent(exp, remove_empty_leading_trailing_lines=True)
        self.assert_equal(act, exp)
