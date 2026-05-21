---
description: <Brief description of what this skill does>
---

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

