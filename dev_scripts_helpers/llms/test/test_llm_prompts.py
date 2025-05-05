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


# #############################################################################
# Test_run_prompt1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci() or hserver.is_dev_csfy(),
    reason="Disabled because of CmampTask10710",
)
class Test_run_prompt1(hunitest.TestCase):

    # TODO(gp): Add one tests for each prompt.

    def test_code_fix_from_imports1(self) -> None:
        prompt_tag = "code_fix_from_imports"
        txt = """
        from bs4 import BeautifulSoup

        start_soup = BeautifulSoup(start_response.content, "html.parser")
        """
        exp_output = """
        import bs4

        start_soup = bs4.BeautifulSoup(start_response.content, "html.parser")
        """
        self._run_prompt(prompt_tag, txt, exp_output)

    def test_code_fix_star_before_optional_parameters1(self) -> None:
        prompt_tag = "code_fix_star_before_optional_parameters"
        txt = """
        def transform(input: str, value: str, output: Optional[str] = None) -> str:
            print(f"input={input}, value={value}, output={output}")

        transform("input", "value")
        transform("input", "value", "output")
        """
        exp_output = """
        def transform(input: str, value: str, *, output: Optional[str] = None) -> str:
            print(f"input={input}, value={value}, output={output}")

        transform("input", "value")
        transform("input", "value", output="output")
        """
        self._run_prompt(prompt_tag, txt, exp_output)

    def _run_prompt(
        self, prompt_tag: str, input_txt: str, exp_output: str
    ) -> None:
        # Prepare the input.
        input_txt = hprint.dedent(input_txt)
        model = "gpt-4o"
        in_file_name = "test.py"
        out_file_name = "test.py"
        # Run the prompt.
        act_output = dshlllpr.run_prompt(
            prompt_tag,
            input_txt,
            model,
            in_file_name=in_file_name,
            out_file_name=out_file_name,
        )
        # Check the output.
        exp_output = hprint.dedent(exp_output)
        self.assert_equal(act_output, exp_output, fuzzy_match=True)
