import logging
import os
from typing import List
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
    output_basename: str = "",
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
    if output_basename:
        output_file = os.path.join(scratch_space, output_basename)
        ret = hio.from_file(output_file)
    else:
        ret = ""
    return ret


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
        expected = """
        4cefdd211c4f3a83dbb505a8269b0df9
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
        expected = "28cc170b019a2f19c81096da11d44835"
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
        expected = "3cf0b39c3f35475ec51020426b19f8ca"
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
        expected = """
        64e37ab448ad7f67cd85825553bb1a6c
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
        expected = """
        24deded3cba2982bbc822f6c159020b3
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
        expected = """
        e90271897868ca4acf82b3c77a14a996
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
        expected = "9053c4164b6a086e755eea157ecaa6f2"
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
        expected = "8ab2fffdb92e144a56658973a32a54a0"
        self.assert_equal(actual, expected)
