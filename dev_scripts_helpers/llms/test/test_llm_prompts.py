import logging

import pytest

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_convert_to_vim_cfile1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_convert_to_vim_cfile1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test converting a simple error message to vim cfile format.
        """
        txt = "57: The docstring should use more detailed type annotations"
        in_file = "test.py"
        actual = dshlllpr._convert_to_vim_cfile_str(txt, in_file)
        expected = (
            "test.py:57: The docstring should use more detailed type annotations"
        )
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test converting a line range error message to vim cfile format.
        """
        txt = "98-104: Simplify the hash computation logic"
        in_file = "test.py"
        actual = dshlllpr._convert_to_vim_cfile_str(txt, in_file)
        expected = "test.py:98: Simplify the hash computation logic"
        self.assertEqual(actual, expected)


# #############################################################################
# Test_prompt_tags1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_prompt_tags1(hunitest.TestCase):

    def test1(self) -> None:
        prompt_tags = dshlllpr.get_prompt_tags()
        _LOG.debug(hprint.to_str("prompt_tags"))
        #
        self.assertGreater(len(prompt_tags), 0)
