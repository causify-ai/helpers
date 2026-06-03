import logging
import os
from typing import List, Optional, cast
from unittest import mock

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.llm_cli as dshlllcl


_LOG = logging.getLogger(__name__)


def _run_llm_cli_with_mock(
    argv: List[str],
    *,
    scratch_space: str,
    output_basename: Optional[str] = None,
) -> str:
    """
    Run `dshlllcl._main()` with a mocked LLM and patched `sys.argv`.

    :param argv: command-line argument list to inject via `mock.patch("sys.argv", ...)`
    :param scratch_space: base directory for file operations
    :param output_basename: if provided, reads and returns output file content
    :return: content of output file if output_basename is provided, else None
    """
    with hllmcli.mock_apply_llm():
        parser = dshlllcl._parse()
        with mock.patch("sys.argv", argv):
            dshlllcl._main(parser)
    if output_basename is not None:
        output_file = os.path.join(scratch_space, output_basename)
        ret = hio.from_file(output_file)
    else:
        ret = ""
    return ret


# #############################################################################
# Test_llm_cli_select
# #############################################################################


class Test_llm_cli_select(hunitest.TestCase):
    """
    Test llm_cli.py --select functionality.
    """

    def _run_select(
        self,
        input_content: str,
        select: str,
        system_prompt: str,
        *,
        output_file: Optional[str] = None,
    ) -> str:
        """
        Write input, run llm_cli with --select, return resulting content.

        :param input_content: markdown text to write to the scratch input file
        :param select: value passed to --select (e.g. 'Section 1.1:Section 1.2')
        :param system_prompt: value passed to -p
        :param output_file: if given, passes -o and reads from it; otherwise
            reads back from the in-place input file
        :return: content of the output file after the run
        """
        input_file = os.path.join(self.get_scratch_space(), "test_input.md")
        hio.to_file(input_file, hprint.dedent(input_content))
        argv = [
            "llm_cli.py",
            "-i",
            input_file,
            "--select",
            select,
            "-p",
            system_prompt,
        ]
        if output_file is not None:
            argv += ["-o", output_file]
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename=os.path.basename(output_file)
            if output_file
            else None,
        )
        if actual is None:
            actual = hio.from_file(input_file)
        return actual

    def test1(self) -> None:
        """
        Test that --select extracts the correct chunk and passes it to apply_llm.
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
        actual = self._run_select(input_content, select, system_prompt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that --select with in-place (no --output) replaces chunk in file.
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
        actual = self._run_select(input_content, select, system_prompt)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that --select with --output writes only the chunk to output.
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
        actual = self._run_select(
            input_content, select, system_prompt, output_file=output_file
        )
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_llm_cli_py
# #############################################################################


class Test_llm_cli_py(hunitest.TestCase):
    """
    End-to-end tests for llm_cli.py executable.
    """

    def _get_script_path(self) -> str:
        """
        Get path to the llm_cli.py script.

        :return: Path to llm_cli.py
        """
        return hgit.find_file_in_git_tree("llm_cli.py")

    def _create_test_input_file(
        self, content: str, extension: str = ".md"
    ) -> str:
        """
        Create a test input file in scratch space.

        :param content: Content to write to file
        :param extension: File extension (default: .md)
        :return: Path to created file
        """
        input_file = os.path.join(
            self.get_scratch_space(), f"test_input{extension}"
        )
        hio.to_file(input_file, hprint.dedent(content))
        return input_file

    def test1(self) -> None:
        """
        Test basic help output.
        """
        # Prepare inputs.
        script_path = self._get_script_path()
        # Run test.
        _, result = hsystem.system_to_string(f"{script_path} --help")
        _LOG.debug("result=%s", result)

    def test2(self) -> None:
        """
        Test file-to-file transformation with mocked LLM.
        """
        # Prepare inputs.
        input_content = """
        This is test input.
        """
        input_file = self._create_test_input_file(input_content)
        output_file = os.path.join(self.get_scratch_space(), "output.md")
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            f"--output={output_file}",
            "--system_prompt=Test prompt",
        ]
        # Run test with mocked LLM.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.md",
        )
        actual = cast(str, actual)
        expected = """
        This is a test response. How can I assist you today?
        """
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test --input_text argument with mocked LLM transformation.
        """
        # Prepare inputs.
        input_text = "Test text from argument"
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        argv = [
            "llm_cli.py",
            f"--input_text={input_text}",
            f"--output={output_file}",
            "--system_prompt=Test prompt",
        ]
        # Run test with mocked LLM.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        actual = cast(str, actual)
        expected = "Sure! Could you please provide more details about the argument you're referring to, or specify the context or topics you'd like to explore? This will help me tailor the test text accordingly."
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test modify-in-place mode with mocked LLM transformation.
        """
        # Prepare inputs.
        input_content = """
        Original content.
        """
        input_file = self._create_test_input_file(input_content)
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            "--modify_in_place",
            "--system_prompt=Transform",
        ]
        # Run test with mocked LLM.
        _run_llm_cli_with_mock(argv, scratch_space=self.get_scratch_space())
        # Check outputs.
        # Expected: --modify_in_place modifies file in-place with transformed content.
        actual = hio.from_file(input_file)
        expected = "Sure! What topic or theme would you like the original content to focus on?"
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test system prompt loaded from file with mocked LLM transformation.
        """
        # Prepare inputs.
        input_file = self._create_test_input_file("Test input")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        prompt_file = os.path.join(self.get_scratch_space(), "prompt.txt")
        hio.to_file(prompt_file, "Custom system prompt")
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            f"--output={output_file}",
            f"--system_prompt_file={prompt_file}",
        ]
        # Run test with mocked LLM.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        actual = cast(str, actual)
        expected = """
        Test output
        """
        self.assert_equal(actual, expected, dedent=True)

    def test7(self) -> None:
        """
        Test verbosity argument with mocked LLM transformation.
        """
        # Prepare inputs.
        input_file = self._create_test_input_file("Test input")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            f"--output={output_file}",
            "--system_prompt=Test",
            "-v",
            "DEBUG",
        ]
        # Run test with mocked LLM.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        actual = cast(str, actual)
        expected = """
        Test input received! How can I assist you today?
        """
        self.assert_equal(actual, expected, dedent=True)

    def test8(self) -> None:
        """
        Test select mode (chunk extraction) with mocked LLM transformation.
        """
        # Prepare inputs.
        input_content = """
        # Section 1
        Content 1

        # Section 2
        Content 2

        # Section 3
        Content 3
        """
        input_file = self._create_test_input_file(input_content)
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            f"--output={output_file}",
            "--select=Section 2:Section 3",
            "--system_prompt=Process",
        ]
        # Run test with mocked LLM.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        actual = cast(str, actual)
        expected = """
        It seems like you've mentioned "Section 2" and "Content 2" without providing additional details. Could you please elaborate on what you're looking for or provide context? This way, I can assist you more effectively!
        """
        self.assert_equal(actual, expected, dedent=True)

    def test9(self) -> None:
        """
        Test progress bar argument with mocked LLM transformation.
        """
        # Prepare inputs.
        input_file = self._create_test_input_file("Test input")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            f"--output={output_file}",
            "--system_prompt=Transform",
            "--progress_bar",
        ]
        # Run test with mocked LLM.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        actual = cast(str, actual)
        expected = "Sure! Please provide the input you'd like me to test or work with, and I'll be happy to assist you."
        self.assert_equal(actual, expected)

    def test10(self) -> None:
        """
        Test file input from real file (e2e without dry run).
        """
        # Prepare inputs.
        input_content = """
        Simple test content.
        """
        input_file = self._create_test_input_file(input_content)
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            f"--output={output_file}",
            "--system_prompt=Simple prompt",
        ]
        # Run test with mocked LLM to avoid actual API calls.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        # Check outputs.
        # Expected: file transformation produces output file.
        self.assertTrue(os.path.exists(output_file))
        # Verify the LLM mock produces deterministic output.
        actual = cast(str, actual)
        self.assertGreater(len(actual), 0)
        self.assertIn("Sure!", actual)
