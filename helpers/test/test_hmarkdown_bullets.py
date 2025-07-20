import logging
import os
from typing import List

import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_bold_first_level_bullets1
# #############################################################################


class Test_bold_first_level_bullets1(hunitest.TestCase):
    def _test_bold_first_level_bullets(self, text: str, expected: str) -> None:
        """
        Helper to test bold_first_level_bullets function.
        """
        text = hprint.dedent(text)
        actual = hmarkdo.bold_first_level_bullets(text)
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test basic first-level bullet bolding.
        """
        text = r"""
        - First item
          - Sub item
        - Second item
        """
        expected = r"""
        - **First item**
          - Sub item
        - **Second item**
        """
        self._test_bold_first_level_bullets(text, expected)

    def test2(self) -> None:
        """
        Test with mixed content including non-bullet text.
        """
        text = r"""
        Some text here
        - First bullet
        More text
        - Second bullet
          - Nested bullet
        Final text
        """
        expected = r"""
        Some text here
        - **First bullet**
        More text
        - **Second bullet**
          - Nested bullet
        Final text
        """
        self._test_bold_first_level_bullets(text, expected)

    def test3(self) -> None:
        """
        Test with multiple levels of nesting.
        """
        text = r"""
        - Top level
          - Second level
            - Third level
          - Back to second
        - Another top
        """
        expected = r"""
        - **Top level**
          - Second level
            - Third level
          - Back to second
        - **Another top**
        """
        self._test_bold_first_level_bullets(text, expected)

    def test4(self) -> None:
        """
        Test with empty lines between bullets.
        """
        text = r"""
        - First item

        - Second item
          - Sub item

        - Third item
        """
        expected = r"""
        - **First item**

        - **Second item**
          - Sub item

        - **Third item**
        """
        self._test_bold_first_level_bullets(text, expected)

    def test5(self) -> None:
        """
        Test with text that already contains some bold markers.
        """
        text = r"""
        - First **important** point
          - Sub point
        - Second point with emphasis
        """
        expected = r"""
        - First **important** point
          - Sub point
        - **Second point with emphasis**
        """
        self._test_bold_first_level_bullets(text, expected)


# #############################################################################
# Test_colorize_bold_text1
# #############################################################################


class Test_colorize_bold_text1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test basic case with single bold text.
        """
        text = "This is **bold** text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"This is **\red{bold}** text"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test multiple bold sections get different colors.
        """
        text = "**First** normal **Second** text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"**\red{First}** normal **\teal{Second}** text"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test underscore style bold text.
        """
        text = "This is __bold__ text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"This is **\red{bold}** text"
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test text with no bold sections returns unchanged.
        """
        text = "This is plain text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = "This is plain text"
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test mixed bold styles in same text.
        """
        text = "**First** and __Second__ bold"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"**\red{First}** and **\teal{Second}** bold"
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test with abbreviations=False uses full \textcolor syntax.
        """
        text = "This is **bold** text"
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=False)
        expected = r"This is **\textcolor{red}{bold}** text"
        self.assert_equal(actual, expected)

    def test7(self) -> None:
        """
        Test with multiple bullet lists and different colors.
        """
        text = """
        **List 1:**
        - First item
        - Second item

        **List 2:**
        - Another item
        - Final item
        """
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = r"""
        **\red{List 1:}**
        - First item
        - Second item

        **\teal{List 2:}**
        - Another item
        - Final item
        """
        self.assert_equal(actual, expected)

    def test8(self) -> None:
        text = hprint.dedent(
            r"""
        - **\red{Objective}**
        - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **\orange{Key Components}**
        - Model learning: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
        - Utility update: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **\blue{Learning Process}**
        - Collect transitions $(s, \pi(s), r, s')$ during execution
        - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
        - Use dynamic programming to compute $U^\pi(s)$

        - **\violet{Advantages}**
        - More sample-efficient than direct utility estimation
        - Leverages structure of the MDP to generalize better

        - **\pink{Challenges}**
        - Requires accurate model estimation
        - Computational cost of solving Bellman equations repeatedly

        - **\olive{Example}**
        - A thermostat estimates room temperature dynamics and uses them to predict
            comfort level under a fixed heating schedule

        - **\darkgray{Use Case}**
        - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        )
        actual = hmarkdo.colorize_bold_text(text, use_abbreviations=True)
        expected = hprint.dedent(
            r"""
        - **\red{Objective}**
        - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **\orange{Key Components}**
        - Model learning: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
        - Utility update: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **\olive{Learning Process}**
        - Collect transitions $(s, \pi(s), r, s')$ during execution
        - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
        - Use dynamic programming to compute $U^\pi(s)$

        - **\green{Advantages}**
        - More sample-efficient than direct utility estimation
        - Leverages structure of the MDP to generalize better

        - **\cyan{Challenges}**
        - Requires accurate model estimation
        - Computational cost of solving Bellman equations repeatedly

        - **\blue{Example}**
        - A thermostat estimates room temperature dynamics and uses them to predict
            comfort level under a fixed heating schedule

        - **\darkgray{Use Case}**
        - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        )
        self.assert_equal(actual, expected)


# #############################################################################
# Test_format_first_level_bullets1
# #############################################################################


class Test_format_first_level_bullets1(hunitest.TestCase):
    def format_and_compare_markdown(self, text: str, expected: str) -> None:
        text = hprint.dedent(text)
        expected = hprint.dedent(expected)
        #
        actual = hmarkdo.format_first_level_bullets(text)
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test basic case with single first level bullet.
        """
        text = """
        Some text
        - First bullet
        More text"""
        expected = """
        Some text

        - First bullet
        More text"""
        self.format_and_compare_markdown(text, expected)

    def test2(self) -> None:
        """
        Test multiple first level bullets.
        """
        text = """
        - First bullet
        - Second bullet
        - Third bullet"""
        expected = """
        - First bullet

        - Second bullet

        - Third bullet"""
        self.format_and_compare_markdown(text, expected)

    def test3(self) -> None:
        """
        Test mixed first level and indented bullets.
        """
        text = """
        - First level

          - Second level
          - Another second
        - Back to first"""
        expected = """
        - First level
          - Second level
          - Another second

        - Back to first"""
        self.format_and_compare_markdown(text, expected)

    def test4(self) -> None:
        """
        Test mixed content with text and bullets.
        """
        text = """
        Some initial text
        - First bullet
        Some text in between
        - Second bullet
        Final text"""
        expected = """
        Some initial text

        - First bullet
        Some text in between

        - Second bullet
        Final text"""
        self.format_and_compare_markdown(text, expected)

    def test5(self) -> None:
        """
        Test nested bullets with multiple levels.
        """
        text = """
        - Level 1
            - Level 2
                - Level 3
        - Another level 1
            - Level 2 again"""
        expected = """
        - Level 1
            - Level 2
                - Level 3

        - Another level 1
            - Level 2 again"""
        self.format_and_compare_markdown(text, expected)

    def test6(self) -> None:
        """
        Test empty lines handling.
        """
        text = """
        - First bullet

        - Second bullet

        - Third bullet"""
        expected = """
        - First bullet

        - Second bullet

        - Third bullet"""
        self.format_and_compare_markdown(text, expected)

    def test7(self) -> None:
        """
        Test mixed content with bullets and text.
        """
        text = """
        Some text here
        - First bullet
        More text
        - Second bullet
            - Nested bullet
        Final paragraph
        - Last bullet"""
        expected = """
        Some text here

        - First bullet
        More text

        - Second bullet
            - Nested bullet
        Final paragraph

        - Last bullet"""
        self.format_and_compare_markdown(text, expected)

    def test8(self) -> None:
        """
        Test bullets with inline formatting.
        """
        text = """
        - **Bold bullet** point
            - *Italic nested* bullet
        - `Code bullet` here
            - **_Mixed_** formatting"""
        expected = """
        - **Bold bullet** point
            - *Italic nested* bullet

        - `Code bullet` here
            - **_Mixed_** formatting"""
        self.format_and_compare_markdown(text, expected)

    def test9(self) -> None:
        """
        Test bullets with special characters.
        """
        text = """
        - Bullet with (parentheses)
            - Bullet with [brackets]
        - Bullet with {braces}
            - Bullet with $math$"""
        expected = """
        - Bullet with (parentheses)
            - Bullet with [brackets]

        - Bullet with {braces}
            - Bullet with $math$"""
        self.format_and_compare_markdown(text, expected)

    def test10(self) -> None:
        text = hprint.dedent(
            r"""
        - **Objective**

          - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **Key Components**

          - **Model learning**: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
          - **Utility update**: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **Learning Process**

          - Collect transitions $(s, \pi(s), r, s')$ during execution
          - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
          - Use dynamic programming to compute $U^\pi(s)$

        - **Use Case**
          - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        )
        expected = hprint.dedent(
            r"""
        - **Objective**
          - Learn utility estimates $U^\pi(s)$for a fixed policy$\pi$ using an estimated
            model of the environment

        - **Key Components**
          - **Model learning**: Estimate transition probabilities $\Pr(s'|s,a)$ and
            reward function $R(s,a)$ from experience
          - **Utility update**: Solve the Bellman equations for the fixed policy:
            - $U^\pi(s) = R(s, \pi(s)) + \gamma \sum_{s'} \Pr(s'|s, \pi(s)) U^\pi(s')$

        - **Learning Process**
          - Collect transitions $(s, \pi(s), r, s')$ during execution
          - Update model estimates:
            - $\Pr(s'|s,a) \approx$ empirical frequency
            - $R(s,a) \approx$ average observed reward
          - Use dynamic programming to compute $U^\pi(s)$

        - **Use Case**
          - Suitable when environment dynamics are stationary and can be learned from
            interaction
        """
        )
        self.format_and_compare_markdown(text, expected)


# #############################################################################
# Test_process_lines1
# #############################################################################


class Test_process_lines1(hunitest.TestCase):
    # TODO(gp): This doesn't seem correct.
    def test1(self) -> None:
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        txt_in = hio.from_file(input_file_path)
        txt_in = hprint.dedent(txt_in)
        lines = txt_in.split("\n")
        out = []
        for i, line in hmarkdo.process_lines(lines):
            _LOG.debug(hprint.to_str("line"))
            out.append(f"{i}:{line}")
        act = "\n".join(out)
        self.check_string(act, dedent=True, remove_lead_trail_empty_lines=True)


# #############################################################################
# Test_process_code_block1
# #############################################################################


class Test_process_code_block1(hunitest.TestCase):
    def helper_process_code_block(self, txt: str) -> str:
        out: List[str] = []
        in_code_block = False
        lines = txt.split("\n")
        for i, line in enumerate(lines):
            _LOG.debug("%s:line=%s", i, line)
            # Process the code block.
            do_continue, in_code_block, out_tmp = hmarkdo.process_code_block(
                line, in_code_block, i, lines
            )
            out.extend(out_tmp)
            if do_continue:
                continue
            #
            out.append(line)
        return "\n".join(out)

    def test1(self) -> None:
        in_dir_name = self.get_input_dir()
        input_file_path = os.path.join(in_dir_name, "test.txt")
        txt_in = hio.from_file(input_file_path)
        txt_in = hprint.dedent(txt_in, remove_lead_trail_empty_lines_=True)
        act = self.helper_process_code_block(txt_in)
        self.check_string(act, dedent=True, remove_lead_trail_empty_lines=True)
