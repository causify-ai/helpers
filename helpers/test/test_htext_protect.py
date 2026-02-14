import logging

import helpers.hprint as hprint
import helpers.htext_protect as htexprot
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__extract_protected_content
# #############################################################################


class Test__extract_protected_content(hunitest.TestCase):
    """
    Test the extract_protected_content function.
    """

    def helper(
        self,
        txt: str,
        file_type: str,
        expected_txt: str,
        expected_map_size: int,
    ) -> None:
        """
        Test helper for extract_protected_content.

        :param txt: Input text to process
        :param file_type: File type ('md', 'txt', or 'tex')
        :param expected_txt: Expected output text with placeholders
        :param expected_map_size: Expected number of protected items
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual_lines, protected_map = htexprot.extract_protected_content(
            lines, file_type
        )
        # Check outputs.
        actual = "\n".join(actual_lines)
        expected = hprint.dedent(
            expected_txt, remove_lead_trail_empty_lines_=True
        )
        self.assert_equal(actual, expected)
        self.assertEqual(len(protected_map), expected_map_size)

    def test1(self) -> None:
        """
        Test extracting single fenced block with content.
        """
        # Prepare inputs.
        txt = """
        Some text here.
        ```python
        def foo():
            return 42
        ```
        More text.
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        Some text here.
        ```python
        <<<PROTECTED_BLOCK_001>>>
        ```
        More text.
        """
        expected_map_size = 1
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test2(self) -> None:
        """
        Test extracting multiple fenced blocks.
        """
        # Prepare inputs.
        txt = """
        Text.
        ```python
        code1
        ```
        Middle.
        ```javascript
        code2
        ```
        End.
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        Text.
        ```python
        <<<PROTECTED_BLOCK_001>>>
        ```
        Middle.
        ```javascript
        <<<PROTECTED_BLOCK_002>>>
        ```
        End.
        """
        expected_map_size = 2
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test3(self) -> None:
        """
        Test extracting empty fenced block.
        """
        # Prepare inputs.
        txt = """
        Text before.
        ```python
        ```
        Text after.
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        Text before.
        ```python
        <<<PROTECTED_BLOCK_001>>>
        ```
        Text after.
        """
        expected_map_size = 1
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test4(self) -> None:
        """
        Test extracting fenced blocks with different languages.
        """
        # Prepare inputs.
        txt = """
        ```python
        python_code
        ```
        ```javascript
        js_code
        ```
        ```bash
        bash_code
        ```
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        ```python
        <<<PROTECTED_BLOCK_001>>>
        ```
        ```javascript
        <<<PROTECTED_BLOCK_002>>>
        ```
        ```bash
        <<<PROTECTED_BLOCK_003>>>
        ```
        """
        expected_map_size = 3
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test5(self) -> None:
        """
        Test extracting HTML single-line comment.
        """
        # Prepare inputs.
        txt = """
        Text before.
        <!-- This is a comment -->
        Text after.
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        Text before.
        <<<PROTECTED_COMMENT_001>>>
        Text after.
        """
        expected_map_size = 1
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test6(self) -> None:
        """
        Test extracting HTML multi-line comment.
        """
        # Prepare inputs.
        txt = """
        Text before.
        <!-- This is
        a multi-line
        comment -->
        Text after.
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        Text before.
        <<<PROTECTED_COMMENT_001>>>
        Text after.
        """
        expected_map_size = 1
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test7(self) -> None:
        """
        Test extracting LaTeX comment.
        """
        # Prepare inputs.
        txt = """
        Some LaTeX text.
        % This is a LaTeX comment
        More text.
        """
        file_type = "tex"
        # Prepare outputs.
        expected = """
        Some LaTeX text.
        <<<PROTECTED_COMMENT_001>>>
        More text.
        """
        expected_map_size = 1
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test8(self) -> None:
        """
        Test extracting math block.
        """
        # Prepare inputs.
        txt = """
        Text before.
        $$
        E = mc^2
        $$
        Text after.
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        Text before.
        $$
        <<<PROTECTED_MATH_001>>>
        $$
        Text after.
        """
        expected_map_size = 1
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test9(self) -> None:
        """
        Test fenced block not extracted for tex files.
        """
        # Prepare inputs.
        txt = """
        LaTeX text.
        ```
        This should not be extracted for tex files
        ```
        More text.
        """
        file_type = "tex"
        # Prepare outputs.
        expected = """
        LaTeX text.
        ```
        This should not be extracted for tex files
        ```
        More text.
        """
        expected_map_size = 0
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)

    def test10(self) -> None:
        """
        Test mixed content (fenced blocks + comments + normal text).
        """
        # Prepare inputs.
        txt = """
        # Title
        Some text.
        ```python
        code here
        ```
        <!-- Comment -->
        $$
        math here
        $$
        End.
        """
        file_type = "md"
        # Prepare outputs.
        expected = """
        # Title
        Some text.
        ```python
        <<<PROTECTED_BLOCK_001>>>
        ```
        <<<PROTECTED_COMMENT_002>>>
        $$
        <<<PROTECTED_MATH_003>>>
        $$
        End.
        """
        expected_map_size = 3
        # Run test.
        self.helper(txt, file_type, expected, expected_map_size)


# #############################################################################
# Test__restore_protected_content
# #############################################################################


class Test__restore_protected_content(hunitest.TestCase):
    """
    Test the restore_protected_content function.
    """

    def helper(
        self,
        txt: str,
        protected_map: dict,
        expected_txt: str,
    ) -> None:
        """
        Test helper for restore_protected_content.

        :param txt: Input text with placeholders
        :param protected_map: Mapping of placeholders to original content
        :param expected_txt: Expected output with restored content
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        # Run test.
        actual_lines = htexprot.restore_protected_content(lines, protected_map)
        # Check outputs.
        actual = "\n".join(actual_lines)
        expected = hprint.dedent(
            expected_txt, remove_lead_trail_empty_lines_=True
        )
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test restoring single placeholder.
        """
        # Prepare inputs.
        txt = """
        Text before.
        ```python
        <<<PROTECTED_BLOCK_001>>>
        ```
        Text after.
        """
        protected_map = {
            "<<<PROTECTED_BLOCK_001>>>": "def foo():\n    return 42"
        }
        # Prepare outputs.
        expected = """
        Text before.
        ```python
        def foo():
            return 42
        ```
        Text after.
        """
        # Run test.
        self.helper(txt, protected_map, expected)

    def test2(self) -> None:
        """
        Test restoring multiple placeholders.
        """
        # Prepare inputs.
        txt = """
        ```python
        <<<PROTECTED_BLOCK_001>>>
        ```
        <<<PROTECTED_COMMENT_002>>>
        ```
        <<<PROTECTED_BLOCK_003>>>
        ```
        """
        protected_map = {
            "<<<PROTECTED_BLOCK_001>>>": "code1",
            "<<<PROTECTED_COMMENT_002>>>": "<!-- comment -->",
            "<<<PROTECTED_BLOCK_003>>>": "code2",
        }
        # Prepare outputs.
        expected = """
        ```python
        code1
        ```
        <!-- comment -->
        ```
        code2
        ```
        """
        # Run test.
        self.helper(txt, protected_map, expected)

    def test3(self) -> None:
        """
        Test restoring multi-line content from single placeholder.
        """
        # Prepare inputs.
        txt = """
        Text.
        <<<PROTECTED_COMMENT_001>>>
        More text.
        """
        protected_map = {
            "<<<PROTECTED_COMMENT_001>>>": "<!-- Line 1\nLine 2\nLine 3 -->"
        }
        # Prepare outputs.
        expected = """
        Text.
        <!-- Line 1
        Line 2
        Line 3 -->
        More text.
        """
        # Run test.
        self.helper(txt, protected_map, expected)

    def test4(self) -> None:
        """
        Test with empty map (no-op).
        """
        # Prepare inputs.
        txt = """
        Text line 1.
        Text line 2.
        Text line 3.
        """
        protected_map = {}
        # Prepare outputs.
        expected = """
        Text line 1.
        Text line 2.
        Text line 3.
        """
        # Run test.
        self.helper(txt, protected_map, expected)

    def test5(self) -> None:
        """
        Test restoring empty content.
        """
        # Prepare inputs.
        txt = """
        Before.
        ```
        <<<PROTECTED_BLOCK_001>>>
        ```
        After.
        """
        protected_map = {"<<<PROTECTED_BLOCK_001>>>": ""}
        # Prepare outputs.
        expected = """
        Before.
        ```

        ```
        After.
        """
        # Run test.
        self.helper(txt, protected_map, expected)


# #############################################################################
# Test_extract_restore_roundtrip
# #############################################################################


class Test_extract_restore_roundtrip(hunitest.TestCase):
    """
    Test that extract followed by restore is identity operation.
    """

    def helper(self, txt: str, file_type: str) -> None:
        """
        Test helper for roundtrip (extract then restore).

        :param txt: Input text
        :param file_type: File type ('md', 'txt', or 'tex')
        """
        # Prepare inputs.
        lines = txt.split("\n")
        lines = hprint.dedent(lines, remove_lead_trail_empty_lines_=True)
        original = "\n".join(lines)
        # Run test.
        extracted_lines, protected_map = htexprot.extract_protected_content(
            lines, file_type
        )
        restored_lines = htexprot.restore_protected_content(
            extracted_lines, protected_map
        )
        # Check outputs.
        actual = "\n".join(restored_lines)
        self.assert_equal(actual, original)

    def test1(self) -> None:
        """
        Test roundtrip with fenced blocks.
        """
        # Prepare inputs.
        txt = """
        # Title
        Some text.
        ```python
        def foo():
            return 42
        ```
        More text.
        """
        file_type = "md"
        # Run test.
        self.helper(txt, file_type)

    def test2(self) -> None:
        """
        Test roundtrip with mixed content.
        """
        # Prepare inputs.
        txt = """
        Text.
        ```python
        code
        ```
        <!-- Comment -->
        $$
        E = mc^2
        $$
        End.
        """
        file_type = "md"
        # Run test.
        self.helper(txt, file_type)

    def test3(self) -> None:
        """
        Test roundtrip with LaTeX comments.
        """
        # Prepare inputs.
        txt = """
        LaTeX text.
        % Comment 1
        More text.
        % Comment 2
        End.
        """
        file_type = "tex"
        # Run test.
        self.helper(txt, file_type)

    def test4(self) -> None:
        """
        Test roundtrip with no protected content.
        """
        # Prepare inputs.
        txt = """
        Just regular text.
        No special content here.
        Just plain paragraphs.
        """
        file_type = "md"
        # Run test.
        self.helper(txt, file_type)
