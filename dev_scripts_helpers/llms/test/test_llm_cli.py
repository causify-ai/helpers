import os
from unittest import mock

import helpers.hio as hio
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
        # Prepare inputs - create a temporary markdown file
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
        # Mock apply_llm to track what it receives
        with mock.patch(
            "helpers.hllm_cli.apply_llm",
            return_value=("Transformed content", 0.001),
        ) as mock_apply_llm:
            # Create parser and simulate command line
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
                # Run main
                dshlllcl._main(parser)
            # Check that apply_llm was called
            self.assertTrue(mock_apply_llm.called)
            # Get the input that was passed to apply_llm
            call_args = mock_apply_llm.call_args
            input_text = call_args[0][0]
            # Should be the chunk from Section 1.1 to (but not including) Section 1.2
            self.assertIn("Section 1.1", input_text)
            self.assertNotIn("Section 1.2", input_text)
            self.assertNotIn("Chapter 2", input_text)

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
        # Mock apply_llm to return transformed text
        with mock.patch(
            "helpers.hllm_cli.apply_llm",
            return_value=("## Section 1.1\n\nTransformed content here.", 0.001),
        ):
            # Create parser and simulate command line (no --output means in-place)
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
        # Check that file was modified
        result = hio.from_file(input_file)
        self.assertIn("Transformed content here", result)
        self.assertIn("Chapter 1", result)  # Should still have the beginning
        self.assertIn("Section 1.2", result)  # Should still have the end

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
        # Mock apply_llm
        with mock.patch(
            "helpers.hllm_cli.apply_llm",
            return_value=("Just the section content", 0.001),
        ):
            # Create parser and simulate command line with --output
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
        # Check output file
        result = hio.from_file(output_file)
        self.assertEqual(result, "Just the section content")
