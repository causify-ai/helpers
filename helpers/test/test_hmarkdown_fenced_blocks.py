import logging
import pprint
from typing import Dict, List

import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_replace_fenced_blocks_with_tags1
# #############################################################################


class Test_replace_fenced_blocks_with_tags1(hunitest.TestCase):
    def helper(
        self, text: str, expected_lines: List[str], expected_map: Dict[str, str]
    ) -> None:
        """
        Test replacing fenced code blocks with tags.
        """
        lines = hprint.dedent(text, remove_lead_trail_empty_lines_=True)
        lines = lines.split("\n")
        # Call function.
        actual_lines, fence_map = hmarkdo.replace_fenced_blocks_with_tags(lines)
        # Check output.
        fence_map_as_str = pprint.pformat(fence_map)
        expected_map_as_str = pprint.pformat(expected_map)
        self.assert_equal(fence_map_as_str, expected_map_as_str)
        #
        actual_lines = "\n".join(actual_lines)
        expected_lines = hprint.dedent(
            expected_lines, remove_lead_trail_empty_lines_=True
        )
        self.assert_equal(actual_lines, expected_lines)

    def helper_round_trip(self, text: str) -> None:
        """
        Test the round trip.
        """
        # Do the round trip.
        lines = text.split("\n")
        actual_lines, fence_map = hmarkdo.replace_fenced_blocks_with_tags(lines)
        act_text = hmarkdo.replace_tags_with_fenced_blocks(
            actual_lines, fence_map
        )
        # Check output.
        act_text = "\n".join(act_text)
        self.assert_equal(act_text, text)

    def test1(self) -> None:
        """
        Test replacing fenced code blocks with tags.
        """
        # Prepare inputs.
        text = """
        Some text before
        ```python
        def foo():
            return 42
        ```
        Text between blocks
        ````
        Plain code block
        ````
        Some text after
        """
        # Prepare outputs.
        expected_lines = """
        Some text before
        <fenced_block1>
        Text between blocks
        <fenced_block2>
        Some text after
        """
        # Check fence map.
        expected_map = {
            "1": "```python\ndef foo():\n    return 42\n```",
            "2": "````\nPlain code block\n````",
        }
        self.helper(text, expected_lines, expected_map)

    def test2(self) -> None:
        """
        Test nested fenced blocks.
        """
        text = """
        ````
        Outer block
        ```python
        def nested():
            pass
        ```
        Still outer
        ````
        """
        expected_lines = """
        <fenced_block1>
        """
        expected_map = {
            "1": "````\nOuter block\n```python\ndef nested():\n    pass\n```\nStill outer\n````"
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test3(self) -> None:
        """
        Test empty fenced blocks.
        """
        text = """
        Before
        ```
        ```
        After
        ```python
        ```
        End
        """
        expected_lines = """
        Before
        <fenced_block1>
        After
        <fenced_block2>
        End
        """
        expected_map = {"1": "```\n```", "2": "```python\n```"}
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test4(self) -> None:
        """
        Test blocks with different fence lengths.
        """
        text = """
        Start
        ```
        Three
        ```
        Middle
        `````
        Five
        `````
        End
        """
        expected_lines = """
        Start
        <fenced_block1>
        Middle
        <fenced_block2>
        End
        """
        expected_map = {"1": "```\nThree\n```", "2": "`````\nFive\n`````"}
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test5(self) -> None:
        """
        Test blocks with language specifiers.
        """
        text = """
        ```python
        def foo(): pass
        ```
        ```bash
        echo hello
        ```
        ```javascript
        console.log('hi');
        ```
        """
        expected_lines = """
        <fenced_block1>
        <fenced_block2>
        <fenced_block3>
        """
        expected_map = {
            "1": "```python\ndef foo(): pass\n```",
            "2": "```bash\necho hello\n```",
            "3": "```javascript\nconsole.log('hi');\n```",
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)

    def test6(self) -> None:
        """
        Test blocks with indentation.
        """
        text = """
        Outside
         ```
         Indented block
          More indent
         ```
           ```python
           def foo():
               pass
           ```
        End
        """
        expected_lines = """
        Outside
        <fenced_block1>
        <fenced_block2>
        End
        """
        expected_map = {
            "1": " ```\n Indented block\n  More indent\n ```",
            "2": "   ```python\n   def foo():\n       pass\n   ```",
        }
        self.helper(text, expected_lines, expected_map)
        #
        self.helper_round_trip(text)