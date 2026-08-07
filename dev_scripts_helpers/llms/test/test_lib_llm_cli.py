import os
from typing import Optional

import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.lib_llm_cli as dshllllcl


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
        dshllllcl._process_selected_text(
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

    def helper(
        self,
        input_content: str,
        select: str,
        system_prompt: str,
        expected: str,
        *,
        output_file: str = "",
    ) -> None:
        """
        Run `_process_selected_text()` with mocked LLM and check the output.

        :param input_content: markdown text to write to the scratch input
            file
        :param select: value passed to select parameter
        :param system_prompt: system prompt to use
        :param expected: expected content of the output file after the run
        :param output_file: if given, writes to it; otherwise uses in-place
            editing
        """
        # Run test.
        actual = _run_lib_llm_cli_with_mock(
            input_content=input_content,
            select=select,
            system_prompt=system_prompt,
            scratch_space=self.get_scratch_space(),
            output_file=output_file,
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

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
        # Run test.
        self.helper(input_content, select, system_prompt, expected)

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
        # Run test.
        self.helper(input_content, select, system_prompt, expected)

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
        # Run test.
        self.helper(
            input_content,
            select,
            system_prompt,
            expected,
            output_file=output_file,
        )


# #############################################################################
# Test_get_system_prompt
# #############################################################################


class Test_get_system_prompt(hunitest.TestCase):
    """
    Test `_get_system_prompt()` function.
    """

    def helper(
        self,
        system_prompt_file: str,
        rule: str,
        system_prompt: str,
        expected: str,
        *,
        expand_referenced_files: bool = True,
    ) -> None:
        """
        Check `_get_system_prompt()`'s output.

        :param system_prompt_file: path to file containing system prompt
        :param rule: rule specification to use as system prompt
        :param system_prompt: system prompt passed directly as a string
        :param expected: expected resolved system prompt
        :param expand_referenced_files: whether to expand `@file`
            references in the resolved system prompt
        """
        # Run test.
        actual = dshllllcl._get_system_prompt(
            system_prompt_file,
            rule,
            system_prompt,
            expand_referenced_files=expand_referenced_files,
        )
        # Check outputs.
        self.assertEqual(actual, expected)

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
        self.helper(system_prompt_file, rule, system_prompt, expected)

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
        self.helper(system_prompt_file, rule, system_prompt, expected)

    def test3(self) -> None:
        """
        Test that `@file` references are expanded by default.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        ref_file = os.path.join(
            scratch_space, "get_system_prompt_expand_test.md"
        )
        hio.to_file(ref_file, "referenced content")
        system_prompt_file = ""
        rule = ""
        system_prompt = "Follow @get_system_prompt_expand_test.md"
        # Prepare outputs.
        expected = (
            "Follow <!-- From get_system_prompt_expand_test.md -->\n"
            "referenced content"
        )
        # Run test.
        self.helper(system_prompt_file, rule, system_prompt, expected)

    def test4(self) -> None:
        """
        Test that `@file` expansion can be disabled.
        """
        # Prepare inputs.
        scratch_space = self.get_scratch_space()
        ref_file = os.path.join(
            scratch_space, "get_system_prompt_noexpand_test.md"
        )
        hio.to_file(ref_file, "referenced content")
        system_prompt_file = ""
        rule = ""
        system_prompt = "Follow @get_system_prompt_noexpand_test.md"
        # Prepare outputs: reference is left untouched.
        expected = system_prompt
        # Run test.
        self.helper(
            system_prompt_file,
            rule,
            system_prompt,
            expected,
            expand_referenced_files=False,
        )


# #############################################################################
# Test_limit_input_text
# #############################################################################


class Test_limit_input_text(hunitest.TestCase):
    """
    Test `_limit_input_text()` function.
    """

    def helper(self, text: str, max_chars: int, expected: str) -> None:
        """
        Check `_limit_input_text()`'s output.

        :param text: input text to limit
        :param max_chars: maximum number of characters
        :param expected: expected limited text
        """
        # Run test.
        actual = dshllllcl._limit_input_text(text, max_chars)
        # Check outputs.
        self.assertEqual(actual, expected)

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
        self.helper(text, max_chars, expected)

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
        self.helper(text, max_chars, expected)


# #############################################################################
# Test_get_input_output_files
# #############################################################################


class Test_get_input_output_files(hunitest.TestCase):
    """
    Test `_get_input_output_files()` function.
    """

    def helper(
        self,
        input_arg: str,
        input_text_arg: str,
        output_arg: str,
        modify_in_place: bool,
        expected: str,
    ) -> None:
        """
        Check `_get_input_output_files()`'s output.

        :param input_arg: input file path or '-' for stdin
        :param input_text_arg: input text from command line
        :param output_arg: output file path or '-' for stdout
        :param modify_in_place: whether to modify input file in place
        :param expected: expected `(input_file, input_text, output_file)`
            tuple, as a string
        """
        # Run test.
        actual = dshllllcl._get_input_output_files(
            input_arg,
            input_text_arg,
            output_arg,
            modify_in_place,
        )
        # Check outputs.
        self.assert_equal(str(actual), expected)

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
        expected = str(("test.txt", "", "-"))
        # Run test.
        self.helper(
            input_arg, input_text_arg, output_arg, modify_in_place, expected
        )

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
        expected = str(("", "Test input", "output.txt"))
        # Run test.
        self.helper(
            input_arg, input_text_arg, output_arg, modify_in_place, expected
        )
