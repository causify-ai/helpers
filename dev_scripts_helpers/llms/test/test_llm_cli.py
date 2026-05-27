import os
import tempfile
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import dev_scripts_helpers.llms.llm_cli as dshllcli


class Test_llm_cli_select(hunitest.TestCase):
    """
    Test llm_cli.py --select functionality.
    """

    def test1(self) -> None:
        """
        Test that --select extracts the correct chunk and passes it to apply_llm.
        """
        # Prepare inputs - create a temporary markdown file
        input_content = """# Chapter 1

Intro text for chapter 1.

## Section 1.1

Content for section 1.1.

## Section 1.2

Content for section 1.2.

# Chapter 2

Content for chapter 2.
"""
        # TODO(ai_gp): Use self.get_scratch_space in all this file instead of tempfile.NamedTemporaryFile.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(input_content)
            input_file = f.name
        try:
            # Mock apply_llm to track what it receives
            with mock.patch(
                'helpers.hllm_cli.apply_llm',
                return_value=("Transformed content", 0.001)
            ) as mock_apply_llm:
                # Create parser and simulate command line
                parser = dshllcli._parse()
                with mock.patch(
                    'sys.argv',
                    ['llm_cli.py', '-i', input_file, '--select', 'Section 1.1:Section 1.2', '-p', 'Transform']
                ):
                    # Run main
                    dshllcli._main(parser)
                # Check that apply_llm was called
                self.assertTrue(mock_apply_llm.called)
                # Get the input that was passed to apply_llm
                call_args = mock_apply_llm.call_args
                input_text = call_args[0][0]
                # Should be the chunk from Section 1.1 to (but not including) Section 1.2
                self.assertIn('Section 1.1', input_text)
                self.assertNotIn('Section 1.2', input_text)
                self.assertNotIn('Chapter 2', input_text)
        finally:
            os.unlink(input_file)

    def test2(self) -> None:
        """
        Test that --select with in-place (no --output) replaces chunk in file.
        """
        # Prepare inputs
        input_content = """# Chapter 1

Intro text.

## Section 1.1

Original content here.

## Section 1.2

More content.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(input_content)
            input_file = f.name
        try:
            # Mock apply_llm to return transformed text
            with mock.patch(
                'helpers.hllm_cli.apply_llm',
                return_value=("## Section 1.1\n\nTransformed content here.", 0.001)
            ):
                # Create parser and simulate command line (no --output means in-place)
                parser = dshllcli._parse()
                with mock.patch(
                    'sys.argv',
                    ['llm_cli.py', '-i', input_file, '--select', 'Section 1.1:', '-p', 'Transform']
                ):
                    dshllcli._main(parser)
            # Check that file was modified
            result = hio.from_file(input_file)
            self.assertIn('Transformed content here', result)
            self.assertIn('Chapter 1', result)  # Should still have the beginning
            self.assertIn('Section 1.2', result)  # Should still have the end
        finally:
            os.unlink(input_file)

    def test3(self) -> None:
        """
        Test that --select with --output writes only the chunk to output.
        """
        # Prepare inputs
        input_content = """# Chapter 1

Intro text.

## Section 1.1

Original content here.

## Section 1.2

More content.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(input_content)
            input_file = f.name
        output_file = None
        try:
            # Mock apply_llm
            with mock.patch(
                'helpers.hllm_cli.apply_llm',
                return_value=("Just the section content", 0.001)
            ):
                # Create output file path
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    output_file = f.name
                # Create parser and simulate command line with --output
                parser = dshllcli._parse()
                with mock.patch(
                    'sys.argv',
                    ['llm_cli.py', '-i', input_file, '--select', 'Section 1.1:Section 1.2',
                     '-p', 'Transform', '-o', output_file]
                ):
                    dshllcli._main(parser)
            # Check output file
            result = hio.from_file(output_file)
            self.assertEqual(result, "Just the section content")
        finally:
            os.unlink(input_file)
            if output_file:
                os.unlink(output_file)
