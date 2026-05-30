import io
import logging
import os
import re
from typing import Optional
from unittest import mock

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.llm_cli as dshlllcl


_LOG = logging.getLogger(__name__)


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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        read_file = output_file if output_file is not None else input_file
        return hio.from_file(read_file)

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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        # Check outputs.
        actual = hio.from_file(output_file)
        expected = """
        This is a test response. How can I assist you today?
        """
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test stdin/stdout with mocked LLM transformation.
        """
        # Prepare inputs.
        input_content = "Test input content"
        argv = [
            "llm_cli.py",
            "--input=-",
            "--output=-",
            "--system_prompt=Transform text",
        ]
        # Run test with mocked LLM.
        with hllmcli.mock_apply_llm():
            with mock.patch("sys.argv", argv):
                with mock.patch("sys.stdin", io.StringIO(input_content)):
                    with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                        parser = dshlllcl._parse()
                        try:
                            dshlllcl._main(parser)
                        except (BrokenPipeError, AttributeError):
                            pass
                        result = mock_stdout.getvalue()
        # Check outputs - filter out warning and ANSI color code lines.
        result_lines = [
            re.sub(r'\x1b\[[0-9;]*m', '', line)
            for line in result.split("\n")
            if "WARNING" not in line and line.strip()
        ]
        actual = "\n".join(result_lines).strip()
        expected = "Test input content has been received. How can I assist you further?"
        self.assert_equal(actual, expected)

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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        # Check outputs.
        # Expected: --input_text provides direct text input and transforms it.
        actual = hio.from_file(output_file)
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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        # Check outputs.
        # Expected: reads system prompt from file and uses it for transformation.
        actual = hio.from_file(output_file)
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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        # Check outputs.
        # Expected: verbosity level controls logging without affecting transformation.
        actual = hio.from_file(output_file)
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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        # Check outputs.
        # Expected: --select extracts chunk and transforms only that part.
        actual = hio.from_file(output_file)
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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        # Check outputs.
        # Expected: --progress_bar enables progress tracking during transformation.
        actual = hio.from_file(output_file)
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
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch("sys.argv", argv):
                dshlllcl._main(parser)
        # Check outputs.
        # Expected: file transformation produces output file.
        self.assertTrue(os.path.exists(output_file))
        actual = hio.from_file(output_file)
        # Verify the LLM mock produces deterministic output.
        self.assertGreater(len(actual), 0)
        self.assertIn("Sure!", actual)


# #############################################################################
# Test_get_input_output_files
# #############################################################################


class Test_get_input_output_files(hunitest.TestCase):
    """
    Test _get_input_output_files() function.
    """

    def test1(self) -> None:
        """Test standard file-to-file input/output."""
        # Prepare inputs.
        input_arg = "/test.md"
        input_text_arg = None
        output_arg = "/out.txt"
        modify_in_place = False
        # Run test.
        input_file, input_text, output_file = dshlllcl._get_input_output_files(
            input_arg,
            input_text_arg,
            output_arg,
            modify_in_place,
        )
        # Check outputs.
        self.assertEqual(input_file, "/test.md")
        self.assertIsNone(input_text)
        self.assertEqual(output_file, "/out.txt")

    def test2(self) -> None:
        """Test stdin input with file output."""
        # Prepare inputs.
        input_arg = "-"
        input_text_arg = None
        output_arg = "/out.txt"
        modify_in_place = False
        # Run test.
        input_file, input_text, output_file = dshlllcl._get_input_output_files(
            input_arg,
            input_text_arg,
            output_arg,
            modify_in_place,
        )
        # Check outputs.
        self.assertEqual(input_file, "-")
        self.assertIsNone(input_text)
        self.assertEqual(output_file, "/out.txt")

    def test3(self) -> None:
        """Test file input with in-place modification (no output)."""
        # Prepare inputs.
        input_arg = "/test.md"
        input_text_arg = None
        output_arg = None
        modify_in_place = True
        # Run test.
        input_file, input_text, output_file = dshlllcl._get_input_output_files(
            input_arg,
            input_text_arg,
            output_arg,
            modify_in_place,
        )
        # Check outputs.
        self.assertEqual(input_file, "/test.md")
        self.assertIsNone(input_text)
        self.assertEqual(output_file, "/test.md")

    def test4(self) -> None:
        """Test file input with stdout output (no output flag)."""
        # Prepare inputs.
        input_arg = "/test.md"
        input_text_arg = None
        output_arg = None
        modify_in_place = False
        # Run test.
        input_file, input_text, output_file = dshlllcl._get_input_output_files(
            input_arg,
            input_text_arg,
            output_arg,
            modify_in_place,
        )
        # Check outputs.
        self.assertEqual(input_file, "/test.md")
        self.assertIsNone(input_text)
        self.assertEqual(output_file, "-")

    def test5(self) -> None:
        """Test direct text input with file output."""
        # Prepare inputs.
        input_arg = None
        input_text_arg = "Hello world"
        output_arg = "/out.txt"
        modify_in_place = False
        # Run test.
        input_file, input_text, output_file = dshlllcl._get_input_output_files(
            input_arg,
            input_text_arg,
            output_arg,
            modify_in_place,
        )
        # Check outputs.
        self.assertIsNone(input_file)
        self.assertEqual(input_text, "Hello world")
        self.assertEqual(output_file, "/out.txt")

    def test6(self) -> None:
        """Test that input_text without output fails."""
        # Prepare inputs.
        input_arg = None
        input_text_arg = "Hello world"
        output_arg = None
        modify_in_place = False
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshlllcl._get_input_output_files(
                input_arg,
                input_text_arg,
                output_arg,
                modify_in_place,
            )

    def test7(self) -> None:
        """Test that empty input arg with None text is treated as no input."""
        # Prepare inputs.
        input_arg = ""
        input_text_arg = None
        output_arg = "/out.txt"
        modify_in_place = False
        # Run test.
        input_file, input_text, output_file = dshlllcl._get_input_output_files(
            input_arg,
            input_text_arg,
            output_arg,
            modify_in_place,
        )
        # Check outputs.
        self.assertIsNone(input_file)
        self.assertIsNone(input_text)
        self.assertEqual(output_file, "/out.txt")

    def test8(self) -> None:
        """Test that empty input_text string fails assertion."""
        # Prepare inputs.
        input_arg = None
        input_text_arg = ""
        output_arg = "/out.txt"
        modify_in_place = False
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshlllcl._get_input_output_files(
                input_arg,
                input_text_arg,
                output_arg,
                modify_in_place,
            )

    def test9(self) -> None:
        """Test that empty output arg fails."""
        # Prepare inputs.
        input_arg = "/test.md"
        input_text_arg = None
        output_arg = ""
        modify_in_place = False
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshlllcl._get_input_output_files(
                input_arg,
                input_text_arg,
                output_arg,
                modify_in_place,
            )


# #############################################################################
# Test_get_expected_num_chars
# #############################################################################


class Test_get_expected_num_chars(hunitest.TestCase):
    """
    Test _get_expected_num_chars() function.
    """

    def test1(self) -> None:
        """Test that progress bar disabled returns None."""
        # Prepare inputs.
        progress_bar = False
        expected_num_chars_arg = None
        input_file = "/test.md"
        input_text = "test"
        # Run test.
        result = dshlllcl._get_expected_num_chars(
            progress_bar,
            expected_num_chars_arg,
            input_file,
            input_text,
        )
        # Check outputs.
        self.assertIsNone(result)

    def test2(self) -> None:
        """Test progress bar with explicit character count."""
        # Prepare inputs.
        progress_bar = True
        expected_num_chars_arg = 1000
        input_file = None
        input_text = None
        # Run test.
        result = dshlllcl._get_expected_num_chars(
            progress_bar,
            expected_num_chars_arg,
            input_file,
            input_text,
        )
        # Check outputs.
        self.assertEqual(result, 1000)

    def test3(self) -> None:
        """Test progress bar calculates from file."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "test.md")
        hio.to_file(input_file, "hello world")
        progress_bar = True
        expected_num_chars_arg = None
        input_text = None
        # Run test.
        result = dshlllcl._get_expected_num_chars(
            progress_bar,
            expected_num_chars_arg,
            input_file,
            input_text,
        )
        # Check outputs.
        self.assertEqual(result, 11)

    def test4(self) -> None:
        """Test progress bar calculates from text."""
        # Prepare inputs.
        progress_bar = True
        expected_num_chars_arg = None
        input_file = None
        input_text = "hello"
        # Run test.
        result = dshlllcl._get_expected_num_chars(
            progress_bar,
            expected_num_chars_arg,
            input_file,
            input_text,
        )
        # Check outputs.
        self.assertEqual(result, 5)

    def test5(self) -> None:
        """Test progress bar calculates from stdin."""
        # Prepare inputs.
        progress_bar = True
        expected_num_chars_arg = None
        input_file = "-"
        input_text = None
        # Run test with mocked stdin.
        with mock.patch("helpers.hselect_input_output.from_file") as mock_read:
            mock_read.return_value = ["line1", "line2"]
            result = dshlllcl._get_expected_num_chars(
                progress_bar,
                expected_num_chars_arg,
                input_file,
                input_text,
            )
        # Check outputs.
        self.assertEqual(result, 11)

    def test6(self) -> None:
        """Test that non-positive character count fails."""
        # Prepare inputs.
        progress_bar = False
        expected_num_chars_arg = 0
        input_file = None
        input_text = None
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshlllcl._get_expected_num_chars(
                progress_bar,
                expected_num_chars_arg,
                input_file,
                input_text,
            )


# #############################################################################
# Test_get_system_prompt
# #############################################################################


class Test_get_system_prompt(hunitest.TestCase):
    """
    Test _get_system_prompt() function.
    """

    def test1(self) -> None:
        """Test loading system prompt from file."""
        # Prepare inputs.
        prompt_file = os.path.join(self.get_scratch_space(), "prompt.txt")
        hio.to_file(prompt_file, "Prompt from file")
        system_prompt_file = prompt_file
        rule = None
        system_prompt = ""
        # Run test.
        result = dshlllcl._get_system_prompt(
            system_prompt_file,
            rule,
            system_prompt,
        )
        # Check outputs.
        self.assertEqual(result, "Prompt from file")

    def test2(self) -> None:
        """Test using system prompt string directly."""
        # Prepare inputs.
        system_prompt_file = None
        rule = None
        system_prompt = "Custom prompt"
        # Run test.
        result = dshlllcl._get_system_prompt(
            system_prompt_file,
            rule,
            system_prompt,
        )
        # Check outputs.
        self.assertEqual(result, "Custom prompt")

    def test3(self) -> None:
        """Test with no prompt options returns empty string."""
        # Prepare inputs.
        system_prompt_file = None
        rule = None
        system_prompt = ""
        # Run test.
        result = dshlllcl._get_system_prompt(
            system_prompt_file,
            rule,
            system_prompt,
        )
        # Check outputs.
        self.assertEqual(result, "")

    def test4(self) -> None:
        """Test that empty system prompt file is treated as None."""
        # Prepare inputs.
        system_prompt_file = ""
        rule = None
        system_prompt = ""
        # Run test.
        result = dshlllcl._get_system_prompt(
            system_prompt_file,
            rule,
            system_prompt,
        )
        # Check outputs.
        self.assertEqual(result, "")

    def test5(self) -> None:
        """Test that multiple prompt options fail."""
        # Prepare inputs.
        prompt_file = os.path.join(self.get_scratch_space(), "prompt.txt")
        hio.to_file(prompt_file, "Prompt")
        system_prompt_file = prompt_file
        rule = None
        system_prompt = "Also a prompt"
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshlllcl._get_system_prompt(
                system_prompt_file,
                rule,
                system_prompt,
            )


# #############################################################################
# Test_process_selected_text
# #############################################################################


class Test_process_selected_text(hunitest.TestCase):
    """
    Test _process_selected_text() function.
    """

    def test1(self) -> None:
        """Test select mode with in-place modification."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "test.md")
        content = "# Header 1\nBefore\n## Section 1\nTarget\n## Section 2\nAfter"
        hio.to_file(input_file, content)
        select = "Section 1:Section 2"
        model = "test-model"
        use_llm_executable = False
        output_file = None
        system_prompt = "Transform"
        modify_in_place = True
        lint = False
        expected_num_chars = None
        dry_run = False
        # Run test.
        with hllmcli.mock_apply_llm():
            cost = dshlllcl._process_selected_text(
                select,
                model,
                use_llm_executable,
                input_file,
                output_file,
                system_prompt,
                modify_in_place,
                lint,
                expected_num_chars,
                dry_run,
            )
        # Check outputs.
        result = hio.from_file(input_file)
        self.assertIn("Before", result)
        self.assertIn("After", result)
        self.assertGreaterEqual(cost, 0.0)

    def test2(self) -> None:
        """Test select mode writing to output file."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "input.md")
        output_file = os.path.join(self.get_scratch_space(), "output.md")
        content = "# Header\nBefore\n## Section A\nTarget\n## Section B\nAfter"
        hio.to_file(input_file, content)
        select = "Section A:Section B"
        model = "test-model"
        use_llm_executable = False
        system_prompt = "Transform"
        modify_in_place = False
        lint = False
        expected_num_chars = None
        dry_run = False
        # Run test.
        with hllmcli.mock_apply_llm():
            dshlllcl._process_selected_text(
                select,
                model,
                use_llm_executable,
                input_file,
                output_file,
                system_prompt,
                modify_in_place,
                lint,
                expected_num_chars,
                dry_run,
            )
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        result = hio.from_file(output_file)
        self.assertGreater(len(result), 0)

    def test3(self) -> None:
        """Test select mode with dry run."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "test.md")
        hio.to_file(input_file, "# H\n## S1\nText\n## S2\nEnd")
        select = "S1:S2"
        model = "test-model"
        use_llm_executable = False
        output_file = None
        system_prompt = "Transform"
        modify_in_place = True
        lint = False
        expected_num_chars = None
        dry_run = True
        # Run test.
        cost = dshlllcl._process_selected_text(
            select,
            model,
            use_llm_executable,
            input_file,
            output_file,
            system_prompt,
            modify_in_place,
            lint,
            expected_num_chars,
            dry_run,
        )
        # Check outputs.
        self.assertEqual(cost, 0.0)
        original = hio.from_file(input_file)
        self.assertIn("Text", original)

    def test4(self) -> None:
        """Test select mode with linting enabled."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "test.md")
        hio.to_file(input_file, "# H\n## S\nContent here\n## E\nEnd")
        output_file = os.path.join(self.get_scratch_space(), "output.md")
        select = "S:E"
        model = "test-model"
        use_llm_executable = False
        system_prompt = "Transform"
        modify_in_place = False
        lint = True
        expected_num_chars = None
        dry_run = False
        # Run test.
        with hllmcli.mock_apply_llm():
            dshlllcl._process_selected_text(
                select,
                model,
                use_llm_executable,
                input_file,
                output_file,
                system_prompt,
                modify_in_place,
                lint,
                expected_num_chars,
                dry_run,
            )
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))


# #############################################################################
# Test_process_full_text
# #############################################################################


class Test_process_full_text(hunitest.TestCase):
    """
    Test _process_full_text() function.
    """

    def test1(self) -> None:
        """Test processing direct text input."""
        # Prepare inputs.
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        model = "test-model"
        use_llm_executable = False
        input_text = "Hello world"
        input_file = None
        system_prompt = "Transform"
        lint = False
        expected_num_chars = None
        dry_run = False
        # Run test.
        with hllmcli.mock_apply_llm():
            cost = dshlllcl._process_full_text(
                model,
                use_llm_executable,
                input_text,
                input_file,
                output_file,
                system_prompt,
                lint,
                expected_num_chars,
                dry_run,
            )
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        result = hio.from_file(output_file)
        self.assertGreater(len(result), 0)
        self.assertGreaterEqual(cost, 0.0)

    def test2(self) -> None:
        """Test processing file input."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "input.txt")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        hio.to_file(input_file, "Test content")
        model = "test-model"
        use_llm_executable = False
        input_text = None
        system_prompt = "Transform"
        lint = False
        expected_num_chars = None
        dry_run = False
        # Run test.
        with hllmcli.mock_apply_llm():
            dshlllcl._process_full_text(
                model,
                use_llm_executable,
                input_text,
                input_file,
                output_file,
                system_prompt,
                lint,
                expected_num_chars,
                dry_run,
            )
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))

    def test3(self) -> None:
        """Test full text processing with dry run."""
        # Prepare inputs.
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        model = "test-model"
        use_llm_executable = False
        input_text = "Test input"
        input_file = None
        system_prompt = "Transform"
        lint = False
        expected_num_chars = None
        dry_run = True
        # Run test.
        cost = dshlllcl._process_full_text(
            model,
            use_llm_executable,
            input_text,
            input_file,
            output_file,
            system_prompt,
            lint,
            expected_num_chars,
            dry_run,
        )
        # Check outputs.
        self.assertEqual(cost, 0.0)
        self.assertFalse(os.path.exists(output_file))

    def test4(self) -> None:
        """Test full text processing with linting."""
        # Prepare inputs.
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        model = "test-model"
        use_llm_executable = False
        input_text = "Test content"
        input_file = None
        system_prompt = "Transform"
        lint = True
        expected_num_chars = None
        dry_run = False
        # Run test.
        with hllmcli.mock_apply_llm():
            dshlllcl._process_full_text(
                model,
                use_llm_executable,
                input_text,
                input_file,
                output_file,
                system_prompt,
                lint,
                expected_num_chars,
                dry_run,
            )
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))


# #############################################################################
# Test_parse
# #############################################################################


class Test_parse(hunitest.TestCase):
    """
    Test _parse() function.
    """

    def test1(self) -> None:
        """Test that parser has all required arguments."""
        # Prepare inputs.
        parse_args = ["-i", "test.txt", "-p", "prompt"]
        # Run test.
        parser = dshlllcl._parse()
        args = parser.parse_args(parse_args)
        # Check outputs.
        self.assertEqual(args.input, "test.txt")
        self.assertEqual(args.system_prompt, "prompt")

    def test2(self) -> None:
        """Test modify_in_place default value."""
        # Prepare inputs.
        parse_args = ["-i", "test.txt", "-p", "prompt"]
        # Run test.
        parser = dshlllcl._parse()
        args = parser.parse_args(parse_args)
        # Check outputs.
        self.assertFalse(args.modify_in_place)

    def test3(self) -> None:
        """Test lint default value."""
        # Prepare inputs.
        parse_args = ["-i", "test.txt", "-p", "prompt"]
        # Run test.
        parser = dshlllcl._parse()
        args = parser.parse_args(parse_args)
        # Check outputs.
        self.assertFalse(args.lint)

    def test4(self) -> None:
        """Test dry_run default value."""
        # Prepare inputs.
        parse_args = ["-i", "test.txt", "-p", "prompt"]
        # Run test.
        parser = dshlllcl._parse()
        args = parser.parse_args(parse_args)
        # Check outputs.
        self.assertFalse(args.dry_run)


# #############################################################################
# Test_main_integration
# #############################################################################


class Test_main_integration(hunitest.TestCase):
    """
    Test _main() function integration.
    """

    def test1(self) -> None:
        """Test _main with full text processing."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "input.txt")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        hio.to_file(input_file, "Test input")
        argv = [
            "llm_cli.py",
            "-i",
            input_file,
            "-o",
            output_file,
            "-p",
            "Test prompt",
        ]
        # Run test.
        with hllmcli.mock_apply_llm():
            with mock.patch("sys.argv", argv):
                parser = dshlllcl._parse()
                dshlllcl._main(parser)
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))
        result = hio.from_file(output_file)
        self.assertGreater(len(result), 0)

    def test2(self) -> None:
        """Test _main with dry run mode."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "input.txt")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        hio.to_file(input_file, "Test input")
        argv = [
            "llm_cli.py",
            "-i",
            input_file,
            "-o",
            output_file,
            "-p",
            "Test prompt",
            "--dry_run",
        ]
        # Run test.
        with mock.patch("sys.argv", argv):
            parser = dshlllcl._parse()
            dshlllcl._main(parser)
        # Check outputs.
        self.assertFalse(os.path.exists(output_file))

    def test3(self) -> None:
        """Test _main with modify_in_place flag."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "input.txt")
        hio.to_file(input_file, "Original content")
        argv = [
            "llm_cli.py",
            "-i",
            input_file,
            "-m",
            "-p",
            "Transform",
        ]
        # Run test.
        with hllmcli.mock_apply_llm():
            with mock.patch("sys.argv", argv):
                parser = dshlllcl._parse()
                dshlllcl._main(parser)
        # Check outputs.
        result = hio.from_file(input_file)
        self.assertNotEqual(result, "Original content")

    def test4(self) -> None:
        """Test _main with --input_text argument."""
        # Prepare inputs.
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        argv = [
            "llm_cli.py",
            "--input_text",
            "Test text",
            "-o",
            output_file,
            "-p",
            "Prompt",
        ]
        # Run test.
        with hllmcli.mock_apply_llm():
            with mock.patch("sys.argv", argv):
                parser = dshlllcl._parse()
                dshlllcl._main(parser)
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))

    def test5(self) -> None:
        """Test _main with --select mode."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "input.md")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        content = "# Header\n## Section A\nContent A\n## Section B\nContent B"
        hio.to_file(input_file, content)
        argv = [
            "llm_cli.py",
            "-i",
            input_file,
            "-o",
            output_file,
            "--select",
            "Section A:Section B",
            "-p",
            "Transform",
        ]
        # Run test.
        with hllmcli.mock_apply_llm():
            with mock.patch("sys.argv", argv):
                parser = dshlllcl._parse()
                dshlllcl._main(parser)
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))

    def test6(self) -> None:
        """Test that INFO logging is suppressed for stdin/stdout."""
        # Prepare inputs.
        input_content = "Test input"
        argv = [
            "llm_cli.py",
            "-i",
            "-",
            "-o",
            "-",
            "-p",
            "Transform",
            "-v",
            "INFO",
        ]
        # Run test.
        with mock.patch("sys.argv", argv):
            with mock.patch("sys.stdin") as mock_stdin:
                mock_stdin.readlines.return_value = [input_content]
                with hllmcli.mock_apply_llm():
                    parser = dshlllcl._parse()
                    try:
                        dshlllcl._main(parser)
                    except (BrokenPipeError, AttributeError):
                        pass

    def test7(self) -> None:
        """Test _main with progress bar enabled."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "input.txt")
        output_file = os.path.join(self.get_scratch_space(), "output.txt")
        hio.to_file(input_file, "Test input content")
        argv = [
            "llm_cli.py",
            "-i",
            input_file,
            "-o",
            output_file,
            "-p",
            "Transform",
            "--progress_bar",
        ]
        # Run test.
        with hllmcli.mock_apply_llm():
            with mock.patch("sys.argv", argv):
                parser = dshlllcl._parse()
                dshlllcl._main(parser)
        # Check outputs.
        self.assertTrue(os.path.exists(output_file))

    def test8(self) -> None:
        """Test select with content both before and after."""
        # Prepare inputs.
        input_file = os.path.join(self.get_scratch_space(), "test.md")
        content = "Before line\n## Start\nTarget\n## End\nAfter line"
        hio.to_file(input_file, content)
        select = "Start:End"
        model = "test"
        use_llm_executable = False
        output_file = None
        system_prompt = "Transform"
        modify_in_place = True
        lint = False
        expected_num_chars = None
        dry_run = False
        # Run test.
        with hllmcli.mock_apply_llm():
            dshlllcl._process_selected_text(
                select,
                model,
                use_llm_executable,
                input_file,
                output_file,
                system_prompt,
                modify_in_place,
                lint,
                expected_num_chars,
                dry_run,
            )
        # Check outputs.
        result = hio.from_file(input_file)
        self.assertIn("Before line", result)
        self.assertIn("After line", result)
