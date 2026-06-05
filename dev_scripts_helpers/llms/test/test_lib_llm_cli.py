import os
from typing import Optional

import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.lib_llm_cli as dshlibllmcli


def _run_lib_llm_cli_with_mock(
    *,
    input_content: str,
    select: str,
    system_prompt: str,
    scratch_space: str,
    output_file: Optional[str] = None,
) -> str:
    """
    Run library function `_process_selected_text()` with mocked LLM.

    :param input_content: markdown text to write to the scratch input file
    :param select: value passed to select parameter
    :param system_prompt: system prompt to use
    :param scratch_space: base directory for file operations
    :param output_file: if given, writes to it; otherwise uses in-place editing
    :return: content of the output file after the run
    """
    input_file = os.path.join(scratch_space, "test_input.md")
    hio.to_file(input_file, hprint.dedent(input_content))
    with hllmcli.mock_apply_llm():
        if output_file:
            output_path = output_file
            modify_in_place = False
        else:
            output_path = ""
            modify_in_place = True
        dshlibllmcli._process_selected_text(
            select,
            model="test-model",
            backend="mock",
            input_file=input_file,
            output_file=output_path,
            system_prompt=system_prompt,
            modify_in_place=modify_in_place,
            max_chars=0,
            lint=False,
            expected_num_chars=0,
            dry_run=False,
        )
    if modify_in_place:
        return hio.from_file(input_file)
    else:
        return hio.from_file(output_path)


# #############################################################################
# Test_selected_text
# #############################################################################


class Test_selected_text(hunitest.TestCase):
    """
    Test lib_llm_cli.py selected text processing.
    """

    def test1(self) -> None:
        """
        Test that select extracts and transforms the correct chunk.
        """
        # Prepare inputs.
        input_content = """
        # Chapter 1

        Intro text for chapter 1.

        ## Section 1.1

        Content for section 1.1.

        ## Section 1.2

        Content for section 1.2.

        # Chapter 2

        Content for chapter 2.
        """
        select = "Section 1.1:Section 1.2"
        system_prompt = "Transform"
        # Prepare outputs.
        expected = """
        # Chapter 1

        Intro text for chapter 1.

        286e0267d56f417f178adbeae419944a
        ## Section 1.2

        Content for section 1.2.

        # Chapter 2

        Content for chapter 2.
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = _run_lib_llm_cli_with_mock(
            input_content=input_content,
            select=select,
            system_prompt=system_prompt,
            scratch_space=self.get_scratch_space(),
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that select with in-place editing replaces chunk correctly.
        """
        # Prepare inputs.
        input_content = """
        # Chapter 1

        Intro text.

        ## Section 1.1

        Original content here.

        ## Section 1.2

        More content.
        """
        select = "Section 1.1:"
        system_prompt = "Transform"
        # Prepare outputs.
        expected = """
        # Chapter 1

        Intro text.

        2b13c254159543fd2eba46aef124463b
        ## Section 1.2

        More content.
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = _run_lib_llm_cli_with_mock(
            input_content=input_content,
            select=select,
            system_prompt=system_prompt,
            scratch_space=self.get_scratch_space(),
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that select with output file writes only the chunk.
        """
        # Prepare inputs.
        input_content = """
        # Chapter 1

        Intro text.

        ## Section 1.1

        Original content here.

        ## Section 1.2

        More content.
        """
        select = "Section 1.1:Section 1.2"
        system_prompt = "Transform"
        output_file = os.path.join(self.get_scratch_space(), "test_output.txt")
        # Prepare outputs.
        expected = """
        2b13c254159543fd2eba46aef124463b
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = _run_lib_llm_cli_with_mock(
            input_content=input_content,
            select=select,
            system_prompt=system_prompt,
            scratch_space=self.get_scratch_space(),
            output_file=output_file,
        )
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_get_system_prompt
# #############################################################################


class Test_get_system_prompt(hunitest.TestCase):
    """
    Test `_get_system_prompt()` function.
    """

    def test1(self) -> None:
        """
        Test getting system prompt from string argument.
        """
        # Prepare inputs.
        system_prompt_file = ""
        rule = ""
        system_prompt = "Test prompt"
        # Prepare outputs.
        expected = "Test prompt"
        # Run test.
        actual = dshlibllmcli._get_system_prompt(
            system_prompt_file,
            rule,
            system_prompt,
        )
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test getting system prompt from file.
        """
        # Prepare inputs.
        prompt_file = os.path.join(self.get_scratch_space(), "prompt.txt")
        hio.to_file(prompt_file, "File-based prompt")
        system_prompt_file = prompt_file
        rule = ""
        system_prompt = ""
        # Prepare outputs.
        expected = "File-based prompt"
        # Run test.
        actual = dshlibllmcli._get_system_prompt(
            system_prompt_file,
            rule,
            system_prompt,
        )
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_limit_input_text
# #############################################################################


class Test_limit_input_text(hunitest.TestCase):
    """
    Test `_limit_input_text()` function.
    """

    def test1(self) -> None:
        """
        Test that text shorter than limit is not truncated.
        """
        # Prepare inputs.
        text = "Short text"
        max_chars = 100
        # Prepare outputs.
        expected = "Short text"
        # Run test.
        actual = dshlibllmcli._limit_input_text(text, max_chars)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that text longer than limit is truncated.
        """
        # Prepare inputs.
        text = "This is a longer text that will be truncated"
        max_chars = 10
        # Prepare outputs.
        expected = "This is a "
        # Run test.
        actual = dshlibllmcli._limit_input_text(text, max_chars)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_get_input_output_files
# #############################################################################


class Test_get_input_output_files(hunitest.TestCase):
    """
    Test `_get_input_output_files()` function.
    """

    def test1(self) -> None:
        """
        Test input file, output to stdout.
        """
        # Prepare inputs.
        input_arg = "test.txt"
        input_text_arg = ""
        output_arg = ""
        modify_in_place = False
        # Prepare outputs.
        expected_input_file = "test.txt"
        expected_input_text = ""
        expected_output_file = "-"
        # Run test.
        actual_input_file, actual_input_text, actual_output_file = (
            dshlibllmcli._get_input_output_files(
                input_arg,
                input_text_arg,
                output_arg,
                modify_in_place,
            )
        )
        # Check outputs.
        self.assertEqual(actual_input_file, expected_input_file)
        self.assertEqual(actual_input_text, expected_input_text)
        self.assertEqual(actual_output_file, expected_output_file)

    def test2(self) -> None:
        """
        Test input text with output file specified.
        """
        # Prepare inputs.
        input_arg = ""
        input_text_arg = "Test input"
        output_arg = "output.txt"
        modify_in_place = False
        # Prepare outputs.
        expected_input_file = ""
        expected_input_text = "Test input"
        expected_output_file = "output.txt"
        # Run test.
        actual_input_file, actual_input_text, actual_output_file = (
            dshlibllmcli._get_input_output_files(
                input_arg,
                input_text_arg,
                output_arg,
                modify_in_place,
            )
        )
        # Check outputs.
        self.assertEqual(actual_input_file, expected_input_file)
        self.assertEqual(actual_input_text, expected_input_text)
        self.assertEqual(actual_output_file, expected_output_file)
