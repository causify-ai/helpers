import logging
import os
from typing import List
from unittest import mock

import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

pytest.importorskip("llm")
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

    def helper(
        self,
        argv: List[str],
        expected: str,
        *,
        output_basename: str = "",
        dedent: bool = False,
    ) -> None:
        """
        Run `llm_cli.py` with a mocked LLM and check the output.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :param expected: expected content of the output
        :param output_basename: if provided, reads and checks the content
            of this file in the scratch space; otherwise checks the empty
            string returned when no output file is produced
        :param dedent: if True, dedent `expected` before comparing
        """
        # Run test.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename=output_basename,
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=dedent)

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

<<<<<<< HEAD
=======
    def helper(
        self, argv: List[str], output_basename: str, expected: str
    ) -> None:
        """
        Run `llm_cli.py` with a mocked LLM and check the output file.

        :param argv: command-line argument list to inject via
            `mock.patch("sys.argv", ...)`
        :param output_basename: basename of the output file to read and
            check
        :param expected: expected content of the output file
        """
        # Run test.
        actual = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename=output_basename,
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))
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
        # Prepare outputs.
        expected = """
        4cefdd211c4f3a83dbb505a8269b0df9
        """
<<<<<<< HEAD
        # Run test and check outputs.
        self.helper(argv, expected, output_basename="output.md", dedent=True)
=======
        # Run test.
        self.helper(argv, "output.md", expected)
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))

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
        # Prepare outputs.
        expected = "28cc170b019a2f19c81096da11d44835"
<<<<<<< HEAD
        # Run test and check outputs.
        self.helper(argv, expected, output_basename="output.txt")
=======
        # Run test.
        self.helper(argv, "output.txt", expected)
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))

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
        # Prepare outputs.
        # Expected: --modify_in_place modifies file in-place with
        # transformed content, so the output file is the input file itself.
        expected = "3cf0b39c3f35475ec51020426b19f8ca"
        output_basename = os.path.basename(input_file)
        # Run test and check outputs.
        self.helper(argv, expected, output_basename=output_basename)

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
        # Prepare outputs.
        expected = """
        64e37ab448ad7f67cd85825553bb1a6c
        """
<<<<<<< HEAD
        # Run test and check outputs.
        self.helper(argv, expected, output_basename="output.txt", dedent=True)
=======
        # Run test.
        self.helper(argv, "output.txt", expected)
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))

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
        # Prepare outputs.
        expected = """
        24deded3cba2982bbc822f6c159020b3
        """
<<<<<<< HEAD
        # Run test and check outputs.
        self.helper(argv, expected, output_basename="output.txt", dedent=True)
=======
        # Run test.
        self.helper(argv, "output.txt", expected)
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))

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
        # Prepare outputs.
        expected = """
        e90271897868ca4acf82b3c77a14a996
        """
<<<<<<< HEAD
        # Run test and check outputs.
        self.helper(argv, expected, output_basename="output.txt", dedent=True)
=======
        # Run test.
        self.helper(argv, "output.txt", expected)
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))

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
        # Prepare outputs.
        expected = "9053c4164b6a086e755eea157ecaa6f2"
<<<<<<< HEAD
        # Run test and check outputs.
        self.helper(argv, expected, output_basename="output.txt")
=======
        # Run test.
        self.helper(argv, "output.txt", expected)
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))

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
<<<<<<< HEAD
        # Prepare outputs.
        # Verify the LLM mock produces deterministic output.
        expected = "8ab2fffdb92e144a56658973a32a54a0"
        # Run test and check outputs (avoids actual API calls).
        self.helper(argv, expected, output_basename="output.txt")
        # Check outputs.
        # Expected: file transformation produces output file.
=======
        # Prepare outputs: deterministic digest from the LLM mock.
        expected = "8ab2fffdb92e144a56658973a32a54a0"
        # Run test with mocked LLM to avoid actual API calls.
        self.helper(argv, "output.txt", expected)
        # Check outputs: file transformation produces output file.
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))
        self.assertTrue(os.path.exists(output_file))

    def test11(self) -> None:
        """
        Test that `@file` references in the system prompt are expanded by
        default.
        """
        # Prepare inputs.
        input_file = self._create_test_input_file("Test input")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        ref_file = os.path.join(
            self.get_scratch_space(), "llm_cli_expand_test.md"
        )
        hio.to_file(ref_file, "referenced content")
        argv = [
            "llm_cli.py",
            f"--input={input_file}",
            f"--output={output_file}",
            "--system_prompt=Follow @llm_cli_expand_test.md",
        ]
        # Run test with mocked LLM.
        expanded = _run_llm_cli_with_mock(
            argv,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        # Run again with expansion disabled.
        argv_no_expand = argv + ["--no_expand_referenced_files"]
        not_expanded = _run_llm_cli_with_mock(
            argv_no_expand,
            scratch_space=self.get_scratch_space(),
            output_basename="output.txt",
        )
        # Check outputs: expanding the reference changes the effective
        # system prompt, so the mocked digest differs from the unexpanded run.
        self.assertNotEqual(expanded, not_expanded)
