import pytest

import helpers.hunit_test as hunitest
import linters.amp_fix_comments as lamficom


class Test_fix_comment_style(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test no changes are applied to non-comments.

        - Given line is not a comment
        - When function runs
        - Then line is not changed
        """
        lines = ["test.method()"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)

    def test2(self) -> None:
        """
        Test first letter is capitalized.

        - Given comment starts with small letter
        - When function runs
        - Then comment starts with a capital letter
        """
        lines = ["# do this."]
        expected = ["# Do this."]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test3(self) -> None:
        """
        Test comment is ended with a `.`

        - Given comment doesn't end with .
        - When function runs
        - Then comment ends with .
        """
        lines = ["# Do this"]
        expected = ["# Do this."]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    @pytest.mark.skip(
        reason="""Inline comments are not allowed, as they are hard to maintain
        """
    )
    def test4(self) -> None:
        """
        Test inline comments are processed.

        - Given line with code and a comment
        - And code doesn't end with .
        - When function runs
        - Then code is not changed
        - And comment ends with .
        """
        lines = ["test.method() # do this"]
        expected = ["test.method() # Do this."]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test5(self) -> None:
        """
        Test spaces are not updated.

        - Given line with a comment that doesn't start with a space
        - And lint has no trailing .
        - When function runs
        - Then line has a trailing .
        - And comment doesn't start with a space
        """
        lines = ["#Do this"]
        expected = ["#Do this."]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test6(self) -> None:
        """
        Test shebang lines are not changed.

        - Given shebang line
        - When function runs
        - Then line is not updated
        """
        lines = expected = ["#!/usr/bin/env python"]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test7(self) -> None:
        """
        Test strings are not changed.

        - Given comment inside a string
        - When function runs
        - Then line is not updated
        """
        lines = expected = [r'comment_regex = r"(.*)#\s*(.*)\s*"']

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test8(self) -> None:
        """
        Test strings are not changed.

        - Given comment inside a string
        - When function runs
        - Then line is not updated
        """
        lines = expected = ['line = f"{match.group(1)}# {comment}"']

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test9(self) -> None:
        """
        Test seperator lines are not changed.

        - Given seperator line
        - When function runs
        - Then line is not updated
        """
        lines = expected = [
            "# #############################################################################"
        ]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test10(self) -> None:
        """
        Test no changes are applied to empty comments.

        - Given line is an empty comment
        - When function runs
        - Then line is not changed
        """
        lines = ["#"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)

    def test11(self) -> None:
        """
        Test no changes are applied to comments that end in punctation.

        - Given line is a comment that ends with ?
        - When function runs
        - Then line is not changed
        """
        lines = ["# TODO(test): Should this be changed?"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)

    def test12(self) -> None:
        """
        Test no changes are applied to comments that start in a number.

        - Given line that starts in a number
        - When function runs
        - Then line is not changed
        """
        lines = ["# -1 is interpreted by joblib like for all cores."]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)

    def test13(self) -> None:
        """
        Test no changes are applied to comments that start with '##'.

        - Given line that starts with '##'
        - When function runs
        - Then line is not changed
        """
        lines = ["## iNVALD"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)

    def test14(self) -> None:
        """
        Test no changes are applied to comments that start with 'pylint'.
        """
        lines = ["# pylint: disable=unused-argument"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)

    def test15(self) -> None:
        """
        Test no changes are applied to comments that start with 'type'.
        """
        lines = ["# type: noqa"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)

    def test16(self) -> None:
        """
        Test no changes are applied to comments with one word.
        """
        lines = expected = ["# oneword"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test17(self) -> None:
        """
        Test no changes are applied to comments with urls.
        """
        lines = expected = [
            ["# https://github.com/"],
            ["# https://google.com/"],
            ["# reference: https://facebook.com"],
        ]
        for line, e in zip(lines, expected):
            actual = lamficom._fix_comment_style(line)
            self.assertEqual(e, actual)

    def test18(self) -> None:
        """
        Test no changes are applied to comments that are valid python
        statements.
        """
        lines = expected = ["# print('hello')"]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test19(self) -> None:
        lines = expected = [
            "# We need a matrix `c` for which `c*c^T = r`.",
            "# We can use # the Cholesky decomposition, or the we can construct `c`",
            "# from the eigenvectors and eigenvalues.",
            "# Compute the eigenvalues and eigenvectors.",
        ]

        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(expected, actual)

    def test20(self) -> None:
        """
        Test no changes are applied to indented comments that start with
        'pylint'.
        """
        lines = ["  # pylint: disable=unused-argument"]
        actual = lamficom._fix_comment_style(lines)
        self.assertEqual(lines, actual)


class Test_extract_comments(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test multi-line comments extracted successfully.
        """
        content = """
        # comment one
        # comment two
        """
        expected = [
            lamficom._LinesWithComment(
                start_line=2,
                end_line=3,
                multi_line_comment=[
                    "        # comment one",
                    "        # comment two",
                ],
            )
        ]
        actual = lamficom._extract_comments(content.split("\n"))
        self.assertEqual(expected, actual)

    def test2(self) -> None:
        """
        Test single line comments extracted successfully.
        """
        content = """
        # comment one
        """
        expected = [
            lamficom._LinesWithComment(
                start_line=2,
                end_line=2,
                multi_line_comment=["        # comment one"],
            )
        ]
        actual = lamficom._extract_comments(content.split("\n"))
        self.assertEqual(expected, actual)

    def test3(self) -> None:
        """
        Test single & multi-line comments extracted successfully.
        """
        content = """
        # comment one
        # comment two
        test.method()
        # comment three
        """
        expected = [
            lamficom._LinesWithComment(
                start_line=2,
                end_line=3,
                multi_line_comment=[
                    "        # comment one",
                    "        # comment two",
                ],
            ),
            lamficom._LinesWithComment(
                start_line=5,
                end_line=5,
                multi_line_comment=["        # comment three"],
            ),
        ]
        actual = lamficom._extract_comments(content.split("\n"))
        self.assertEqual(expected, actual)


class Test_reflow_comment(hunitest.TestCase):
    @pytest.mark.skip
    def test1(self) -> None:
        """
        Test long comment is updated.
        """
        long_line = (
            "# This is a super long message that has too much information in it. "
            "Although inline comments are cool, this sentence should not be this long."
        )
        comment = lamficom._LinesWithComment(
            start_line=1,
            end_line=1,
            multi_line_comment=[long_line],
        )
        expected = lamficom._LinesWithComment(
            start_line=comment.start_line,
            end_line=comment.end_line,
            multi_line_comment=[
                "# This is a super long message that has too much information in it. Although",
                "# inline comments are cool, this sentence should not be this long.",
            ],
        )
        actual = lamficom._reflow_comment(comment)
        self.assertEqual(expected, actual)

    def test2(self) -> None:
        """
        Test markdown lists are respected.
        """
        comment = lamficom._LinesWithComment(
            start_line=1,
            end_line=2,
            multi_line_comment=["# - Hello", "# - How are you?"],
        )
        expected = comment
        actual = lamficom._reflow_comment(comment)
        self.assertEqual(expected, actual)

    def test3(self) -> None:
        """
        Test indentation is preserved.
        """
        comment = lamficom._LinesWithComment(
            start_line=1,
            end_line=1,
            multi_line_comment=["    # indented"],
        )
        expected = comment
        actual = lamficom._reflow_comment(comment)
        self.assertEqual(expected, actual)

    def test4(self) -> None:
        """
        Test a single comment with inconsistent whitespace raises error.
        """
        comment = lamficom._LinesWithComment(
            start_line=1,
            end_line=2,
            multi_line_comment=["# - Hello", "    # - How are you?"],
        )
        with self.assertRaises(AssertionError):
            lamficom._reflow_comment(comment)


class Test_replace_comments_in_lines(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test replace comments in lines.
        """
        code_line = "method.test()"
        old_comment = "# old comment"
        new_comment = "# new comment"

        lines = [code_line, old_comment]
        updated_comments = [
            lamficom._LinesWithComment(
                start_line=2, end_line=2, multi_line_comment=[new_comment]
            )
        ]

        expected = [code_line, new_comment]
        actual = lamficom._replace_comments_in_lines(
            lines=lines, comments=updated_comments
        )
        self.assertEqual(expected, actual)


class Test_reflow_comments_in_lines(hunitest.TestCase):
    @pytest.mark.skip
    def test1(self) -> None:
        content = """
        test.method_before()
        # This is a super long message that has too much information in it. Although inline comments are cool, this sentence should not be this long.
        test.method_after()
        # - a list item
        # - another list item
        """.split(
            "\n"
        )
        expected = """
        test.method_before()
        # This is a super long message that has too much information in it. Although
        # inline comments are cool, this sentence should not be this long.
        test.method_after()
        # - a list item
        # - another list item
        """.split(
            "\n"
        )
        actual = lamficom._reflow_comments_in_lines(lines=content)
        self.assertEqual(expected, actual)


class Test_reflow_comments(hunitest.TestCase):
    @pytest.mark.skip
    def test_1(self) -> None:
        """
        Test combination of too short and too long lines.
        """
        original = [
            "# Create decorated functions with different caches and store pointers of these "
            + "functions. Note that we need to build the functions in the constructor since we",
            "# need to have a single instance of the decorated"
            + " functions. On the other side,",
            "# e.g., if we created these functions in `__call__`, they will be recreated at "
            + "every invocation, creating a new memory cache at every invocation.",
        ]
        expected = [
            "# Create decorated functions with different caches and store pointers of these",
            "# functions. Note that we need to build the functions in the constructor since we",
            "# need to have a single instance of the decorated functions. On the other side,",
            "# e.g., if we created these functions in `__call__`, they will be recreated at",
            "# every invocation, creating a new memory cache at every invocation.",
        ]
        result = lamficom._reflow_comments_in_lines(original)
        self.assertEqual(result, expected)
