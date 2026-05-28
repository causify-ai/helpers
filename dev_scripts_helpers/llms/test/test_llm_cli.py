import os
from typing import Optional
from unittest import mock

import helpers.hio as hio
import helpers.hllm_cli as hllmcli
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.llm_cli as dshlllcl


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
