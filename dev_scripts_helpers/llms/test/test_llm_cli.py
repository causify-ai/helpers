import os
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

    def test1(self) -> None:
        """
        Test that --select extracts the correct chunk and passes it to apply_llm.
        """
        # Prepare inputs
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
        input_content = hprint.dedent(input_content)
        input_file = os.path.join(self.get_scratch_space(), "test_input.md")
        hio.to_file(input_file, input_content)
        # Prepare outputs
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
        # Run test
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch(
                "sys.argv",
                [
                    "llm_cli.py",
                    "-i",
                    input_file,
                    "--select",
                    "Section 1.1:Section 1.2",
                    "-p",
                    "Transform",
                ],
            ):
                dshlllcl._main(parser)
        # Check outputs
        actual = hio.from_file(input_file)
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that --select with in-place (no --output) replaces chunk in file.
        """
        # Prepare inputs
        input_content = """
        # Chapter 1

        Intro text.

        ## Section 1.1

        Original content here.

        ## Section 1.2

        More content.
        """
        input_content = hprint.dedent(input_content)
        input_file = os.path.join(self.get_scratch_space(), "test_input.md")
        hio.to_file(input_file, input_content)
        # Prepare outputs
        expected = """
        # Chapter 1

        Intro text.

        2b13c254159543fd2eba46aef124463b
        ## Section 1.2

        More content.
        """
        expected = hprint.dedent(expected)
        # Run test
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch(
                "sys.argv",
                [
                    "llm_cli.py",
                    "-i",
                    input_file,
                    "--select",
                    "Section 1.1:",
                    "-p",
                    "Transform",
                ],
            ):
                dshlllcl._main(parser)
        # Check outputs
        actual = hio.from_file(input_file)
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that --select with --output writes only the chunk to output.
        """
        # Prepare inputs
        input_content = """
        # Chapter 1

        Intro text.

        ## Section 1.1

        Original content here.

        ## Section 1.2

        More content.
        """
        input_content = hprint.dedent(input_content)
        input_file = os.path.join(self.get_scratch_space(), "test_input.md")
        hio.to_file(input_file, input_content)
        output_file = os.path.join(self.get_scratch_space(), "test_output.txt")
        # Prepare outputs
        expected = """
        2b13c254159543fd2eba46aef124463b
        """
        expected = hprint.dedent(expected)
        # Run test
        with hllmcli.mock_apply_llm():
            parser = dshlllcl._parse()
            with mock.patch(
                "sys.argv",
                [
                    "llm_cli.py",
                    "-i",
                    input_file,
                    "--select",
                    "Section 1.1:Section 1.2",
                    "-p",
                    "Transform",
                    "-o",
                    output_file,
                ],
            ):
                dshlllcl._main(parser)
        # Check outputs
        actual = hio.from_file(output_file)
        self.assert_equal(actual, expected)
