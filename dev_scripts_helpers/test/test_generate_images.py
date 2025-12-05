import base64
import logging
import os

import dev_scripts_helpers.generate_images as dscgenima
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_parse_descriptions
# #############################################################################


class Test_parse_descriptions(hunitest.TestCase):
    """
    Test the _parse_descriptions() function for extracting prompts from text.
    """

    def helper(self, content: str, expected: list) -> None:
        """
        Test helper for _parse_descriptions().

        :param content: input text content with prompts
        :param expected: expected list of extracted prompts
        """
        # Prepare inputs.
        content = hprint.dedent(content)
        # Run test.
        actual = dscgenima._parse_descriptions(content)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """Test parsing single prompt with single-line text."""
        # Prepare inputs.
        content = """
            # Prompt_A
            This is the first prompt text.
            """
        # Prepare outputs.
        expected = ["This is the first prompt text."]
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """Test parsing single prompt with multi-line text."""
        # Prepare inputs.
        content = """
            # Prompt_A
            This is the first line.
            This is the second line.
            This is the third line.
            """
        # Prepare outputs.
        expected = [
            "This is the first line.\nThis is the second line.\nThis is the third line."
        ]
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """Test parsing multiple prompts without blank lines between them."""
        # Prepare inputs.
        content = """
            # Prompt_A
            Text for prompt A.
            # Prompt_B
            Text for prompt B.
            # Prompt_C
            Text for prompt C.
            """
        # Prepare outputs.
        expected = [
            "Text for prompt A.",
            "Text for prompt B.",
            "Text for prompt C.",
        ]
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """Test parsing multiple prompts with blank lines between them."""
        # Prepare inputs.
        content = """
            # Prompt_A
            Text for prompt A.

            # Prompt_B
            Text for prompt B.


            # Prompt_C
            Text for prompt C.
            """
        # Prepare outputs.
        expected = [
            "Text for prompt A.",
            "Text for prompt B.",
            "Text for prompt C.",
        ]
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """Test parsing multiple prompts with multi-line text and blank lines."""
        # Prepare inputs.
        content = """
            # Prompt_A
            Line 1 of prompt A.
            Line 2 of prompt A.

            # Prompt_B
            Line 1 of prompt B.
            Line 2 of prompt B.
            Line 3 of prompt B.

            # Prompt_C
            Single line for prompt C.
            """
        # Prepare outputs.
        expected = [
            "Line 1 of prompt A.\nLine 2 of prompt A.",
            "Line 1 of prompt B.\nLine 2 of prompt B.\nLine 3 of prompt B.",
            "Single line for prompt C.",
        ]
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """Test parsing prompts with blank lines within the text."""
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
            "First paragraph.\n\nSecond paragraph after blank line.",
            "Another prompt.",
        ]
        # Run test.
        self.helper(content, expected)

    def test7(self) -> None:
        """Test parsing empty content."""
        # Prepare inputs.
        content = ""
        # Prepare outputs.
        expected = []
        # Run test.
        self.helper(content, expected)

    def test8(self) -> None:
        """Test that content without prompt headers raises assertion error."""
        # Prepare inputs.
        content = """
            Just some random text
            without any headers
            that should be ignored.
            """
        content = hprint.dedent(content)
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dscgenima._parse_descriptions(content)
        # Verify error message contains information about unprocessed lines.
        error_message = str(cm.exception)
        self.assertIn("Found lines that were not processed", error_message)
        self.assertIn("Just some random text", error_message)

    def test9(self) -> None:
        """Test parsing prompts with underscores in the name."""
        # Prepare inputs.
        content = """
            # Prompt_Name_With_Underscores
            This is the prompt text.
            """
        # Prepare outputs.
        expected = ["This is the prompt text."]
        # Run test.
        self.helper(content, expected)

    def test10(self) -> None:
        """Test parsing prompts with numbers in the name."""
        # Prepare inputs.
        content = """
            # Prompt123
            This is the prompt text.
            # Prompt456
            Another prompt.
            """
        # Prepare outputs.
        expected = ["This is the prompt text.", "Another prompt."]
        # Run test.
        self.helper(content, expected)

    def test11(self) -> None:
        """Test that leading and trailing whitespace is stripped from prompts."""
        # Prepare inputs.
        content = """
            # Prompt_A

              Text with leading spaces.
              More text.

            """
        # Prepare outputs.
        expected = ["Text with leading spaces.\n  More text."]
        # Run test.
        self.helper(content, expected)

    def test12(self) -> None:
        """Test parsing prompt headers with multiple spaces after hash."""
        # Prepare inputs.
        content = """
            #   Prompt_A
            Text for prompt A.
            #    Prompt_B
            Text for prompt B.
            """
        # Prepare outputs.
        expected = ["Text for prompt A.", "Text for prompt B."]
        # Run test.
        self.helper(content, expected)

    def test13(self) -> None:
        """Test complex realistic example with multiple prompts."""
        # Prepare inputs.
        content = """
            # Urban_Landscape
            A futuristic cityscape at sunset with flying cars and neon lights.
            The buildings are tall glass structures reflecting the orange sky.
            Include people walking on elevated sidewalks.

            # Nature_Scene
            A serene forest with a waterfall cascading into a crystal-clear pool.
            Morning mist hovers over the water.


            Rays of sunlight break through the canopy.

            # Abstract_Art
            Geometric shapes in vibrant colors.
            Circles, triangles, and squares overlapping.
            Use bold primary colors: red, blue, yellow.
            """
        # Prepare outputs.
        expected = [
            "A futuristic cityscape at sunset with flying cars and neon lights.\nThe buildings are tall glass structures reflecting the orange sky.\nInclude people walking on elevated sidewalks.",
            "A serene forest with a waterfall cascading into a crystal-clear pool.\nMorning mist hovers over the water.\n\n\nRays of sunlight break through the canopy.",
            "Geometric shapes in vibrant colors.\nCircles, triangles, and squares overlapping.\nUse bold primary colors: red, blue, yellow.",
        ]
        # Run test.
        self.helper(content, expected)

    def test14(self) -> None:
        """Test that text before first header raises assertion error."""
        # Prepare inputs.
        content = """
            Some text before any header.

            # Prompt_A
            This is the prompt text.
            """
        content = hprint.dedent(content)
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dscgenima._parse_descriptions(content)
        # Verify error message.
        error_message = str(cm.exception)
        self.assertIn("Found lines that were not processed", error_message)
        self.assertIn("Some text before any header", error_message)

    def test15(self) -> None:
        """Test parsing content with only blank lines before headers."""
        # Prepare inputs.
        content = """


            # Prompt_A
            This is the prompt text.
            """
        # Prepare outputs.
        expected = ["This is the prompt text."]
        # Run test.
        self.helper(content, expected)


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
        actual = dscgenima._parse_descriptions_with_names(content)
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
            dscgenima._parse_descriptions_with_names(content)
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
            ("Prompt_A", "First paragraph.\n\nSecond paragraph after blank line."),
            ("Prompt_B", "Another prompt."),
        ]
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_encode_image_to_base64
# #############################################################################


class Test_encode_image_to_base64(hunitest.TestCase):
    """
    Test the _encode_image_to_base64() function for encoding images to base64.
    """

    def test1(self) -> None:
        """Test encoding a simple text file to base64."""
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "test_image.txt")
        test_content = "This is a test image content"
        hio.to_file(test_file, test_content)
        # Run test.
        actual = dscgenima._encode_image_to_base64(test_file)
        # Check outputs.
        # Verify it's a valid base64 string.
        decoded = base64.b64decode(actual).decode("utf-8")
        self.assert_equal(decoded, test_content)

    def test2(self) -> None:
        """Test encoding binary content to base64."""
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        test_file = os.path.join(scratch_dir, "test_image.bin")
        # Create simple binary content.
        test_content = bytes([0, 1, 2, 3, 4, 5, 255, 254])
        with open(test_file, "wb") as f:
            f.write(test_content)
        # Run test.
        actual = dscgenima._encode_image_to_base64(test_file)
        # Check outputs.
        # Verify decoding produces original content.
        decoded = base64.b64decode(actual)
        self.assertEqual(decoded, test_content)

    def test3(self) -> None:
        """Test that encoding non-existent file raises assertion error."""
        # Prepare inputs.
        non_existent_file = "/path/to/non/existent/file.png"
        # Run test and check output.
        with self.assertRaises(AssertionError):
            dscgenima._encode_image_to_base64(non_existent_file)


# #############################################################################
# Test_generate_images_from_file
# #############################################################################


class Test_generate_images_from_file(hunitest.TestCase):
    """
    Test the _generate_images_from_file() function with parallel execution.
    """

    def test_parallel_mode_dry_run(self) -> None:
        """Test parallel mode with dry run (no actual API calls)."""
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_prompts.txt")
        dst_dir = os.path.join(scratch_dir, "output")
        # Create test input file with multiple prompts.
        prompts_content = """
# Prompt_A
First test prompt.

# Prompt_B
Second test prompt.
"""
        hio.to_file(input_file, prompts_content)
        # Run test.
        dscgenima._generate_images_from_file(
            prompt=None,
            input_file=input_file,
            dst_dir=dst_dir,
            count=2,
            low_res=True,
            api_key=None,
            reference_image=None,
            dry_run=True,
            from_scratch=True,
            parallel=True,
            num_threads=2,
        )
        # Check outputs.
        # In dry run mode, no files should be created.
        self.assertFalse(os.path.exists(dst_dir))

    def test_sequential_mode_dry_run(self) -> None:
        """Test sequential mode with dry run (no actual API calls)."""
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "test_prompts.txt")
        dst_dir = os.path.join(scratch_dir, "output")
        # Create test input file with multiple prompts.
        prompts_content = """
# Prompt_A
First test prompt.

# Prompt_B
Second test prompt.
"""
        hio.to_file(input_file, prompts_content)
        # Run test.
        dscgenima._generate_images_from_file(
            prompt=None,
            input_file=input_file,
            dst_dir=dst_dir,
            count=2,
            low_res=True,
            api_key=None,
            reference_image=None,
            dry_run=True,
            from_scratch=True,
            parallel=False,
            num_threads=4,
        )
        # Check outputs.
        # In dry run mode, no files should be created.
        self.assertFalse(os.path.exists(dst_dir))

    def test_single_prompt_parallel_dry_run(self) -> None:
        """Test parallel mode with single prompt and dry run."""
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        dst_dir = os.path.join(scratch_dir, "output")
        prompt = "Test prompt for image generation"
        # Run test.
        dscgenima._generate_images_from_file(
            prompt=prompt,
            input_file=None,
            dst_dir=dst_dir,
            count=3,
            low_res=False,
            api_key=None,
            reference_image=None,
            dry_run=True,
            from_scratch=False,
            parallel=True,
            num_threads=2,
        )
        # Check outputs.
        # In dry run mode, no files should be created.
        self.assertFalse(os.path.exists(dst_dir))
