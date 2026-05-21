---
description: Fix the input / output variables of a test
---

# Goal
- Transform test method so that:
  - The inputs and outputs are strings with """ and dedent
  - The output being checked with `self.assert_equal()`
  - Follow the directions in `.claude/skills/testing.rules.md`
    - `# Format Test Inputs`
    - `# Checking Test Outputs`

- Factor out as much code as possible in helper functions
  - Follow the directions in `.claude/skills/testing.rules.md`
    - `## Use Helper Methods When You Have Repetitive Tests`

# Example
- Before
  ```
  class Test_add_navigation_slides(hunitest.TestCase):
    """
    Test the `_add_navigation_slides()` function.
    """

    def helper(
        self, lines: List[str], max_level: int, expected_contains: str
    ) -> None:
        """
        Helper method to test _add_navigation_slides function.

        :param lines: input lines
        :param max_level: maximum header level
        :param expected_contains: substring that should be in output
        """
        actual = dshdprno._add_navigation_slides(
            lines, max_level, sanity_check=False
        )
        actual_str = "\n".join(actual)
        self.assertIn(expected_contains, actual_str)

    def test1(self) -> None:
        """
        Test navigation slides added for headers.
        """
        lines = [
            "# Part 1",
            "Content here",
            "## Section 1.1",
            "More content",
        ]
        # Should add navigation slide before first header
        actual = dshdprno._add_navigation_slides(lines, max_level=2)
        self.assertGreaterEqual(len(actual), len(lines))

    def test2(self) -> None:
        """
        Test navigation with single level headers only.
        """
        lines = [
            "# Main Title",
            "Content",
        ]
        actual = dshdprno._add_navigation_slides(lines, max_level=1)
        actual_str = "\n".join(actual)
        # Should contain the main title
        self.assertIn("Main Title", actual_str)
  ```

- After
  ```
  class Test_add_navigation_slides(hunitest.TestCase):
    """
    Test the `_add_navigation_slides()` function.
    """

    def helper(
        self, input_text: str, max_level: int, expected: str
    ) -> None:
        """
        Helper method to test _add_navigation_slides function.

        :param input_text: input text with dedent applied
        :param max_level: maximum header level
        :param expected: expected output with dedent applied
        """
        # Prepare inputs.
        input_text = hprint.dedent(input_text)
        lines = input_text.strip().split("\n")
        expected = hprint.dedent(expected)
        # Run test.
        actual = dshdprno._add_navigation_slides(lines, max_level)
        actual_str = "\n".join(actual)
        # Check outputs.
        self.assert_equal(actual_str, expected)

    def test1(self) -> None:
        """
        Test navigation slides added for headers.
        """
        # Prepare inputs.
        input_text = """
            # Part 1
            Content here
            ## Section 1.1
            More content
            """
        max_level = 2
        # Prepare outputs.
        expected = """
            # Part 1
            Content here
            ## Section 1.1
            More content
            """
        # Run test.
        self.helper(input_text, max_level, expected)

    def test2(self) -> None:
        """
        Test navigation with single level headers only.
        """
        # Prepare inputs.
        input_text = """
            # Main Title
            Content
            """
        max_level = 1
        # Prepare outputs.
        expected = """
            # Main Title
            Content
            """
        # Run test.
        self.helper(input_text, max_level, expected)
    ```

- Do not change the intent of the test

# Verify
- Run the tests to make sure that the tests are passing
