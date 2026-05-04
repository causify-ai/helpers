import logging
from typing import List, Tuple

import helpers.hprint as hprint
import helpers.hmarkdown_div_blocks as hmadiblo
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _prepare_div_block_inputs(txt: str, expected: str) -> Tuple[List[str], str]:
    txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
    expected = hprint.dedent(expected, remove_lead_trail_empty_lines_=False)
    if expected.startswith("\n"):
        expected = expected[1:]
    if expected.endswith("\n"):
        expected = expected[:-1]
    lines = txt.split("\n")
    return lines, expected


# #############################################################################
# Test_add_prettier_ignore_to_div_blocks
# #############################################################################


class Test_add_prettier_ignore_to_div_blocks(hunitest.TestCase):
    """
    Test the function to add prettier-ignore comments around div blocks.
    """

    def helper(self, txt: str, expected: str) -> None:
        # Prepare inputs.
        lines, expected = _prepare_div_block_inputs(txt, expected)
        # Run test.
        actual_lines = hmadiblo.add_prettier_ignore_to_div_blocks(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test_simple_div_block(self) -> None:
        """
        Test a simple div block with two colons.
        """
        txt = """
        ::::
        :::
        """
        # Add a leading empty line in expected since function adds it.
        expected = """

        <!-- prettier-ignore-start -->
        ::::
        :::
        <!-- prettier-ignore-end -->

        """
        self.helper(txt, expected)

    def test_div_block_with_attributes(self) -> None:
        """
        Test a div block with column attributes.
        """
        txt = """
        ::::
        ::::{.column width=40%}
        """
        expected = """

        <!-- prettier-ignore-start -->
        ::::
        ::::{.column width=40%}
        <!-- prettier-ignore-end -->

        """
        self.helper(txt, expected)

    def test_multiple_div_blocks(self) -> None:
        """
        Test multiple div blocks in the same content.
        """
        txt = """
        Some text before

        ::::
        ::::{.column width=40%}

        Middle text

        :::columns
        ::::{.column width=60%}

        Some text after
        """
        expected = """
        Some text before


        <!-- prettier-ignore-start -->
        ::::
        ::::{.column width=40%}
        <!-- prettier-ignore-end -->


        Middle text


        <!-- prettier-ignore-start -->
        :::columns
        ::::{.column width=60%}
        <!-- prettier-ignore-end -->


        Some text after
        """
        self.helper(txt, expected)

    def test_no_div_blocks(self) -> None:
        """
        Test content with no div blocks.
        """
        txt = """
        Some normal text
        with no div blocks
        at all
        """
        expected = """
        Some normal text
        with no div blocks
        at all
        """
        self.helper(txt, expected)

    def test_unclosed_div_block(self) -> None:
        """
        Test a div block that is not closed.
        """
        txt = """
        Some text

        ::::

        More text
        """
        expected = """
        Some text

        ::::

        More text
        """
        self.helper(txt, expected)


# #############################################################################
# Test_remove_prettier_ignore_from_div_blocks
# #############################################################################


class Test_remove_prettier_ignore_from_div_blocks(hunitest.TestCase):
    """
    Test the function to remove prettier-ignore comments from div blocks.
    """

    def helper(self, txt: str, expected: str) -> None:
        # Prepare inputs.
        lines, expected = _prepare_div_block_inputs(txt, expected)
        # Run test.
        actual_lines = hmadiblo.remove_prettier_ignore_from_div_blocks(lines)
        actual = "\n".join(actual_lines)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test_remove_simple_block(self) -> None:
        """
        Test removing prettier-ignore from a simple div block.
        """
        txt = """

        <!-- prettier-ignore-start -->
        ::::
        :::
        <!-- prettier-ignore-end -->

        """
        expected = """
        ::::
        :::
        """
        self.helper(txt, expected)

    def test_remove_block_with_content(self) -> None:
        """
        Test removing prettier-ignore from a div block with content.
        """
        txt = """
        Some text before

        <!-- prettier-ignore-start -->
        ::::
        ::::{.column width=40%}
        <!-- prettier-ignore-end -->

        Some text after
        """
        expected = """
        Some text before
        ::::
        ::::{.column width=40%}
        Some text after
        """
        self.helper(txt, expected)

    def test_remove_multiple_blocks(self) -> None:
        """
        Test removing prettier-ignore from multiple div blocks.
        """
        txt = """
        Text before

        <!-- prettier-ignore-start -->
        ::::
        ::::{.column width=40%}
        <!-- prettier-ignore-end -->

        Middle text

        <!-- prettier-ignore-start -->
        :::columns
        ::::{.column width=60%}
        <!-- prettier-ignore-end -->

        Text after
        """
        expected = """
        Text before
        ::::
        ::::{.column width=40%}
        Middle text
        :::columns
        ::::{.column width=60%}
        Text after
        """
        self.helper(txt, expected)

    def test_no_prettier_ignore_comments(self) -> None:
        """
        Test content with no prettier-ignore comments.
        """
        txt = """
        Some normal text
        with no prettier-ignore comments
        at all
        """
        expected = """
        Some normal text
        with no prettier-ignore comments
        at all
        """
        self.helper(txt, expected)


# #############################################################################
# Test_add_remove_prettier_ignore_roundtrip
# #############################################################################


class Test_add_remove_prettier_ignore_roundtrip(hunitest.TestCase):
    """
    Test that adding and removing prettier-ignore comments is a roundtrip.
    """

    def helper(self, txt: str) -> None:
        # Prepare inputs.
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True)
        lines = txt.split("\n")
        # Run test.
        # Add prettier-ignore comments.
        lines_with_comments = hmadiblo.add_prettier_ignore_to_div_blocks(lines)
        # Remove prettier-ignore comments.
        lines_restored = hmadiblo.remove_prettier_ignore_from_div_blocks(
            lines_with_comments
        )
        actual = "\n".join(lines_restored)
        expected = txt
        # Check outputs.
        self.assert_equal(actual, expected)

    def test_roundtrip_simple(self) -> None:
        """
        Test that add and remove operations are inverses for simple div block.
        """
        txt = """
        ::::
        :::
        """
        self.helper(txt)

    def test_roundtrip_complex1(self) -> None:
        """
        Test roundtrip for content with multiple div blocks and text.
        """
        txt = """
        Text1

        ::::
        ::::{.column width=40%}

        Text2

        :::columns
        ::::{.column width=60%}

        Text3
        """
        self.helper(txt)

    def test_roundtrip_complex2(self) -> None:
        """
        Test roundtrip for content with multiple div blocks and text.
        """
        txt = """
        Text1
        :::
        ::::{.column width=40%}
        Text2
        ::::
        ::::{.column width=40%}
        Text3
        :::columns
        ::::{.column width=60%}
        Text4
        """
        self.helper(txt)

    def test_roundtrip_complex3(self) -> None:
        """
        Test roundtrip for content with multiple div blocks and text.
        """
        txt = """
        Text1

        :::
        ::::{.column width=40%}

        Text2
        ::::
        ::::{.column width=40%}

        Text3
        :::columns
        ::::{.column width=60%}
        Text4
        """
        self.helper(txt)
