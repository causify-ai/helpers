import os
from unittest import mock

import pytest

pytest.importorskip("openai")

import dev_scripts_helpers.documentation.generate_images as dshdgeim
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest


# #############################################################################
# Test_parse_descriptions_with_names
# #############################################################################


class Test_parse_descriptions_with_names(hunitest.TestCase):
    """
    Test the _parse_descriptions_with_names() function for extracting prompts with names.
    """

    def helper(self, content: str, expected: list) -> None:
        """
        Test helper for _parse_descriptions_with_names().

        :param content: input text content with prompts
        :param expected: expected list of tuples (prompt_name, prompt_text)
        """
        # Prepare inputs.
        content = hprint.dedent(content)
        # Run test.
        actual = dshdgeim._parse_descriptions_with_names(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """Test parsing single prompt with name extraction."""
        # Prepare inputs.
        content = """
        # Prompt_A
        This is the first prompt text.
        """
        # Prepare outputs.
        expected = [("Prompt_A", "This is the first prompt text.")]
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """Test parsing multiple prompts with names."""
        # Prepare inputs.
        content = """
        # Urban_Landscape
        A futuristic cityscape at sunset.

        # Nature_Scene
        A serene forest with a waterfall.

        # Abstract_Art
        Geometric shapes in vibrant colors.
        """
        # Prepare outputs.
        expected = [
            ("Urban_Landscape", "A futuristic cityscape at sunset."),
            ("Nature_Scene", "A serene forest with a waterfall."),
            ("Abstract_Art", "Geometric shapes in vibrant colors."),
        ]
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """Test parsing prompts with multi-line text."""
        # Prepare inputs.
        content = """
        # Prompt_A
        Line 1 of prompt A.
        Line 2 of prompt A.

        # Prompt_B
        Line 1 of prompt B.
        """
        # Prepare outputs.
        expected = [
            ("Prompt_A", "Line 1 of prompt A.\nLine 2 of prompt A."),
            ("Prompt_B", "Line 1 of prompt B."),
        ]
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """Test parsing prompts with underscores and numbers in names."""
        # Prepare inputs.
        content = """
        # Prompt_Name_123
        This is the prompt text.
        # Another_Prompt_456
        Another prompt.
        """
        # Prepare outputs.
        expected = [
            ("Prompt_Name_123", "This is the prompt text."),
            ("Another_Prompt_456", "Another prompt."),
        ]
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """Test parsing empty content."""
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """Test that content without prompt headers raises assertion error."""
        # Prepare inputs.
        content = """
        Just some random text
        without any headers.
        """
        content = hprint.dedent(content)
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshdgeim._parse_descriptions_with_names(content)
        # Verify error message contains information about unprocessed lines.
        error_message = str(cm.exception)
        self.assertIn("Found lines that were not processed", error_message)
        self.assertIn("Just some random text", error_message)

    def test7(self) -> None:
        """Test parsing prompts with blank lines within text."""
        # Prepare inputs.
        content = """
        # Prompt_A
        First paragraph.

        Second paragraph after blank line.

        # Prompt_B
        Another prompt.
        """
        # Prepare outputs.
        expected = [
            (
                "Prompt_A",
                "First paragraph.\n\nSecond paragraph after blank line.",
            ),
            ("Prompt_B", "Another prompt."),
        ]
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_generate_images
# #############################################################################


class Test_generate_images(hunitest.TestCase):
    """
    Test the `_generate_images()` function in dry-run mode (no API calls).
    """

    def test1(self) -> None:
        """
        Test happy path: dry run with a named prompt does not call the
        OpenAI API.
        """
        # Prepare inputs.
        dst_dir = self.get_scratch_space()
        # Run test.
        with mock.patch("openai.OpenAI") as mock_openai:
            dshdgeim._generate_images(
                "my_prompt",
                "a description",
                2,
                dst_dir,
                dry_run=True,
            )
        # Check outputs.
        mock_openai.assert_not_called()

    def test2(self) -> None:
        """
        Test edge case: dry run updates the progress bar once per image.
        """
        # Prepare inputs.
        dst_dir = self.get_scratch_space()
        progress_bar = mock.MagicMock()
        # Run test.
        dshdgeim._generate_images(
            "my_prompt",
            "a description",
            3,
            dst_dir,
            progress_bar=progress_bar,
            dry_run=True,
        )
        # Check outputs.
        self.assertEqual(progress_bar.update.call_count, 3)

    def test3(self) -> None:
        """
        Test edge case: an unsupported model raises a fatal error.
        """
        # Prepare inputs.
        dst_dir = self.get_scratch_space()
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdgeim._generate_images(
                "my_prompt",
                "a description",
                1,
                dst_dir,
                model_name="unsupported-model",
                dry_run=True,
            )


# #############################################################################
# Test_generate_images_from_file
# #############################################################################


class Test_generate_images_from_file(hunitest.TestCase):
    """
    Test the `_generate_images_from_file()` function in dry-run mode.
    """

    def test1(self) -> None:
        """
        Test happy path: prompt from the command line generates the
        requested number of images (dry run).
        """
        # Prepare inputs.
        dst_dir = os.path.join(self.get_scratch_space(), "images")
        # Run test.
        dshdgeim._generate_images_from_file(
            "a simple prompt",
            "",
            "",
            dst_dir,
            2,
            dry_run=True,
            no_backup=True,
        )
        # Check outputs.
        self.assertTrue(os.path.isdir(dst_dir))

    def test2(self) -> None:
        """
        Test happy path: prompts read from an input file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "prompts.txt")
        content = """
        # Prompt_A
        First prompt text.

        # Prompt_B
        Second prompt text.
        """
        content = hprint.dedent(content)
        hio.to_file(input_file, content)
        dst_dir = os.path.join(scratch_dir, "images")
        # Run test.
        dshdgeim._generate_images_from_file(
            "",
            input_file,
            "",
            dst_dir,
            1,
            dry_run=True,
            no_backup=True,
        )
        # Check outputs.
        self.assertTrue(os.path.isdir(dst_dir))

    def test3(self) -> None:
        """
        Test edge case: neither a prompt nor an input file is provided.
        """
        # Prepare inputs.
        dst_dir = os.path.join(self.get_scratch_space(), "images")
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdgeim._generate_images_from_file(
                "", "", "", dst_dir, 1, dry_run=True
            )

    def test4(self) -> None:
        """
        Test edge case: count outside the allowed [1, 10] range raises an
        assertion error.
        """
        # Prepare inputs.
        dst_dir = os.path.join(self.get_scratch_space(), "images")
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dshdgeim._generate_images_from_file(
                "prompt", "", "", dst_dir, 11, dry_run=True
            )

    def test5(self) -> None:
        """
        Test happy path: a known style is prepended to the description.
        """
        # Prepare inputs.
        dst_dir = os.path.join(self.get_scratch_space(), "images")
        captured = {}

        def _capture(
            _prompt_name: str,
            description: str,
            *_args: object,
            **_kwargs: object,
        ) -> None:
            captured["description"] = description

        # Run test.
        with mock.patch.object(
            dshdgeim, "_generate_images", side_effect=_capture
        ):
            dshdgeim._generate_images_from_file(
                "a prompt",
                "",
                "style1",
                dst_dir,
                1,
                dry_run=True,
                no_backup=True,
            )
        # Check outputs.
        self.assertIn("minimalist flat-illustration style", captured["description"])
        self.assertIn("a prompt", captured["description"])

    def test6(self) -> None:
        """
        Test edge case: an invalid style raises a `ValueError`.
        """
        # Prepare inputs.
        dst_dir = os.path.join(self.get_scratch_space(), "images")
        # Run test and check output.
        with self.assertRaises(ValueError):
            dshdgeim._generate_images_from_file(
                "a prompt", "", "invalid_style", dst_dir, 1, dry_run=True
            )


# #############################################################################
# Test_generate_images_py_main
# #############################################################################


class Test_generate_images_py_main(hunitest.TestCase):
    """
    Test `_main()` called directly (in-process) with mocked `sys.argv`.
    """

    def test1(self) -> None:
        """
        Test happy path: `--dry_run` avoids real API calls end-to-end.
        """
        # Prepare inputs.
        dst_dir = os.path.join(self.get_scratch_space(), "images")
        argv = [
            "generate_images.py",
            "a prompt",
            "--dst_dir",
            dst_dir,
            "--dry_run",
            "--no_backup",
        ]
        parser = dshdgeim._parse()
        # Run test.
        with mock.patch("sys.argv", argv):
            dshdgeim._main(parser)
        # Check outputs.
        self.assertTrue(os.path.isdir(dst_dir))
