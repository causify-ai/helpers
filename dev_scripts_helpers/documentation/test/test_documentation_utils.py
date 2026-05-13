import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.documentation_utils as dshddout


# #############################################################################
# Test_remove_span_with_multiple_attributes
# #############################################################################


class Test_remove_span_with_multiple_attributes(hunitest.TestCase):
    """
    Test the `remove_span_with_multiple_attributes()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_span_with_multiple_attributes()`.

        :param content: Input markdown content
        :param expected: Expected output after removing spans
        """
        # Prepare inputs and outputs.
        # Run test.
        actual = dshddout.remove_span_with_multiple_attributes(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of span with id and class attributes.
        """
        # Prepare inputs.
        content = 'Before <span id="foo" class="bar">middle</span> after'
        # Prepare outputs.
        expected = "Before  after"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test that single-attribute spans are not removed.
        """
        # Prepare inputs.
        content = 'Text with <span class="single">content</span> here'
        # Prepare outputs: single-attribute span is not removed by `remove_span_with_multiple_attributes()`.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test multiple multi-attribute spans.
        """
        # Prepare inputs.
        content = 'First <span id="a" class="b">x</span> and <span data-x="1" data-y="2">y</span> end'
        # Prepare outputs.
        expected = "First  and  end"
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_label_span_tags
# #############################################################################


class Test_remove_label_span_tags(hunitest.TestCase):
    """
    Test the `remove_label_span_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_label_span_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_label_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of label span with double quotes.
        """
        # Prepare inputs.
        content = 'Text <span class="label">Part I</span> more'
        # Prepare outputs.
        expected = "Text Part I more"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of label span with single quotes.
        """
        # Prepare inputs.
        content = "Text <span class='label'>Chapter 1</span> continues"
        # Prepare outputs.
        expected = "Text Chapter 1 continues"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that non-label spans are not removed.
        """
        # Prepare inputs.
        content = 'Text <span class="other">preserved</span> here'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_keep_together_span_tags
# #############################################################################


class Test_remove_keep_together_span_tags(hunitest.TestCase):
    """
    Test the `remove_keep_together_span_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_keep_together_span_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_keep_together_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of keep-together span with double quotes.
        """
        # Prepare inputs.
        content = 'Before <span class="keep-together">causation</span> after'
        # Prepare outputs.
        expected = "Before causation after"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of keep-together span with single quotes.
        """
        # Prepare inputs.
        content = "Text <span class='keep-together'>together</span> text"
        # Prepare outputs.
        expected = "Text together text"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that other spans are not affected.
        """
        # Prepare inputs.
        content = 'Text <span class="other">value</span> end'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_html_link_span_tags
# #############################################################################


class Test_remove_html_link_span_tags(hunitest.TestCase):
    """
    Test the `remove_html_link_span_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_html_link_span_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_html_link_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of span with .html id.
        """
        # Prepare inputs.
        content = 'Text <span id="ch12.html"></span> after'
        # Prepare outputs.
        expected = "Text  after"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of span with complex .html id.
        """
        # Prepare inputs.
        content = 'Start <span id="part03.html_part-3"></span> end'
        # Prepare outputs.
        expected = "Start  end"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that spans without .html id are preserved.
        """
        # Prepare inputs.
        content = 'Text <span id="nothtml">content</span> here'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_pre_span_tags
# #############################################################################


class Test_remove_pre_span_tags(hunitest.TestCase):
    """
    Test the `remove_pre_span_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_pre_span_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_pre_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of pre span with double quotes.
        """
        # Prepare inputs.
        content = 'Code: <span class="pre">`is_on_sale`</span> ends'
        # Prepare outputs.
        expected = "Code: `is_on_sale` ends"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of pre span with single quotes.
        """
        # Prepare inputs.
        content = "Function <span class='pre'>my_func</span> defined"
        # Prepare outputs.
        expected = "Function my_func defined"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that other class spans are not removed.
        """
        # Prepare inputs.
        content = 'Text <span class="code">not_pre</span> here'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_bold_span_tags
# #############################################################################


class Test_remove_bold_span_tags(hunitest.TestCase):
    """
    Test the `remove_bold_span_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_bold_span_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_bold_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test conversion of bold span with double quotes.
        """
        # Prepare inputs.
        content = 'Text <span class="b">HBR Press Quantity Sales Discounts</span> more'
        # Prepare outputs.
        expected = "Text **HBR Press Quantity Sales Discounts** more"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test conversion of bold span with single quotes.
        """
        # Prepare inputs.
        content = "Start <span class='b'>bold text</span> end"
        # Prepare outputs.
        expected = "Start **bold text** end"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that other class spans are not converted.
        """
        # Prepare inputs.
        content = 'Text <span class="other">not bold</span> here'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_italic_span_tags
# #############################################################################


class Test_remove_italic_span_tags(hunitest.TestCase):
    """
    Test the `remove_italic_span_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_italic_span_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_italic_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test conversion of italic span with double quotes.
        """
        # Prepare inputs.
        content = 'Text <span class="i">What Technology Wants</span> continues'
        # Prepare outputs.
        expected = "Text _What Technology Wants_ continues"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test conversion of italic span with single quotes.
        """
        # Prepare inputs.
        content = "Begin <span class='i'>italic text</span> end"
        # Prepare outputs.
        expected = "Begin _italic text_ end"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that other class spans are not converted.
        """
        # Prepare inputs.
        content = 'Text <span class="other">not italic</span> here'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_convert_section_div_headers
# #############################################################################


class Test_convert_section_div_headers(hunitest.TestCase):
    """
    Test the `convert_section_div_headers()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `convert_section_div_headers()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.convert_section_div_headers(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test section2 div promotes `# Title` to `## Title`.
        """
        # Prepare inputs.
        content = '<div class="section2">\n\n# The Magic of Prediction\n'
        # Prepare outputs.
        expected = '<div class="section2">\n\n## The Magic of Prediction\n'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test section3 div promotes `# Title` to `### Title`.
        """
        # Prepare inputs.
        content = '<div class="section3">\n\n# The Magic of Prediction\n'
        # Prepare outputs.
        expected = '<div class="section3">\n\n### The Magic of Prediction\n'
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test section4 div promotes `# Title` to `#### Title`.
        """
        # Prepare inputs.
        content = '<div class="section4">\n\n# Sub Section\n'
        # Prepare outputs.
        expected = '<div class="section4">\n\n#### Sub Section\n'
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test single-quoted class attribute is matched.
        """
        # Prepare inputs.
        content = "<div class='section2'>\n\n# Title\n"
        # Prepare outputs.
        expected = "<div class='section2'>\n\n## Title\n"
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """
        Test section div with additional attributes is matched.
        """
        # Prepare inputs.
        content = '<div id="x" class="section2">\n\n# Title\n'
        # Prepare outputs.
        expected = '<div id="x" class="section2">\n\n## Title\n'
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """
        Test non-section divs (e.g., chapter) are not affected.
        """
        # Prepare inputs.
        content = '<div class="chapter">\n\n# Chapter 1\n'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test7(self) -> None:
        """
        Test multiple section divs with different levels are converted.
        """
        # Prepare inputs.
        content = (
            '<div class="section2">\n\n# First\n\n'
            '<div class="section3">\n\n# Second\n'
        )
        # Prepare outputs.
        expected = (
            '<div class="section2">\n\n## First\n\n'
            '<div class="section3">\n\n### Second\n'
        )
        # Run test.
        self.helper(content, expected)

    def test8(self) -> None:
        """
        Test content without section divs is unchanged.
        """
        # Prepare inputs.
        content = "Plain content\n\n# Title\n"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test9(self) -> None:
        """
        Test a `#` not preceded by a section div is unchanged.
        """
        # Prepare inputs.
        content = '<div class="section2">\n\nSome text first\n\n# Title\n'
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_div_tags
# #############################################################################


class Test_remove_div_tags(hunitest.TestCase):
    """
    Test the `remove_div_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_div_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_div_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of div with class attribute.
        """
        # Prepare inputs.
        content = 'Before <div class="section2">section content</div> after'
        # Prepare outputs.
        expected = "Before section content after"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of div with single-quoted attribute.
        """
        # Prepare inputs.
        content = "Start <div class='section2'>div content</div> end"
        # Prepare outputs.
        expected = "Start div content end"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test removal of div with id attribute.
        """
        # Prepare inputs.
        content = 'Text <div id="ch001.html_ch001">chapter</div> end'
        # Prepare outputs.
        expected = "Text chapter end"
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test removal of div with both id and class attributes.
        """
        # Prepare inputs.
        content = 'X <div id="copy001.html" class="copyrights">body</div> Y'
        # Prepare outputs.
        expected = "X body Y"
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """
        Test removal of div with style attribute.
        """
        # Prepare inputs.
        content = '<div class="titlepage" style="margin-top: 0em;">page</div>'
        # Prepare outputs.
        expected = "page"
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """
        Test removal of div with no attributes.
        """
        # Prepare inputs.
        content = "Before <div>plain</div> after"
        # Prepare outputs.
        expected = "Before plain after"
        # Run test.
        self.helper(content, expected)

    def test7(self) -> None:
        """
        Test removal of nested divs preserves inner content.
        """
        # Prepare inputs.
        content = '<div class="outer"><div class="inner">deep</div></div>'
        # Prepare outputs.
        expected = "deep"
        # Run test.
        self.helper(content, expected)

    def test8(self) -> None:
        """
        Test removal of div with nested non-div HTML tags.
        """
        # Prepare inputs.
        content = 'Start <div class="section2"><p>para</p></div> end'
        # Prepare outputs.
        expected = "Start <p>para</p> end"
        # Run test.
        self.helper(content, expected)

    def test9(self) -> None:
        """
        Test that content without divs is unchanged.
        """
        # Prepare inputs.
        content = "Plain markdown without any div tags"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test10(self) -> None:
        """
        Test removal of div tags spanning multiple lines.
        """
        # Prepare inputs.
        content = '<div class="chapter">\n\nParagraph.\n\n</div>'
        # Prepare outputs.
        expected = "\n\nParagraph.\n\n"
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_anchor_tags
# #############################################################################


class Test_remove_anchor_tags(hunitest.TestCase):
    """
    Test the `remove_anchor_tags()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_anchor_tags()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_anchor_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of simple anchor tag.
        """
        # Prepare inputs.
        content = 'Text <a href="#link">Part III</a> end'
        # Prepare outputs.
        expected = "Text Part III end"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of anchor with multiple attributes.
        """
        # Prepare inputs.
        content = 'Link <a href="#part03.html_part-3" data-type="xref">Reference</a> here'
        # Prepare outputs.
        expected = "Link Reference here"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test multiple anchor tags in content.
        """
        # Prepare inputs.
        content = '<a href="#1">First</a> and <a href="#2">Second</a> links'
        # Prepare outputs.
        expected = "First and Second links"
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test anchor tag with nested HTML tags (e.g., superscript for footnotes).
        """
        # Prepare inputs.
        content = 'Text <a href="#notes.html_ch2en1" id="ch002.html_ch2n1"><sup>1</sup></a> here'
        # Prepare outputs.
        expected = "Text <sup>1</sup> here"
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_backticks_in_math
# #############################################################################


class Test_remove_backticks_in_math(hunitest.TestCase):
    """
    Test the `remove_backticks_in_math()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_backticks_in_math()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.remove_backticks_in_math(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of backticks from math expression.
        """
        # Prepare inputs.
        content = "Formula: $`Y(1)`$ end"
        # Prepare outputs.
        expected = "Formula: $Y(1)$ end"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test multiple math expressions with backticks.
        """
        # Prepare inputs.
        content = "First: $`X`$ and second: $`Y(1)`$ math"
        # Prepare outputs.
        expected = "First: $X$ and second: $Y(1)$ math"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that math without backticks is not affected.
        """
        # Prepare inputs.
        content = "Formula: $Y(1)$ clean"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_collapse_blank_lines
# #############################################################################


class Test_collapse_blank_lines(hunitest.TestCase):
    """
    Test the `collapse_blank_lines()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `collapse_blank_lines()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.collapse_blank_lines(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test single blank line is preserved.
        """
        # Prepare inputs.
        content = "line1\n\nline2"
        # Prepare outputs.
        expected = "line1\n\nline2"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test two consecutive blank lines collapse to one.
        """
        # Prepare inputs.
        content = "line1\n\n\nline2"
        # Prepare outputs.
        expected = "line1\n\nline2"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test many consecutive blank lines collapse to one.
        """
        # Prepare inputs.
        content = "line1\n\n\n\n\n\nline2"
        # Prepare outputs.
        expected = "line1\n\nline2"
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test blank lines containing only spaces are also collapsed.
        """
        # Prepare inputs.
        content = "line1\n   \n\t\n  \nline2"
        # Prepare outputs.
        expected = "line1\n\nline2"
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """
        Test content without blank lines is unchanged.
        """
        # Prepare inputs.
        content = "line1\nline2\nline3"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """
        Test multiple separate runs of blank lines are each collapsed.
        """
        # Prepare inputs.
        content = "a\n\n\nb\n\n\n\nc"
        # Prepare outputs.
        expected = "a\n\nb\n\nc"
        # Run test.
        self.helper(content, expected)

    def test7(self) -> None:
        """
        Test leading blank lines are collapsed.
        """
        # Prepare inputs.
        content = "\n\n\nfirst line"
        # Prepare outputs.
        expected = "\n\nfirst line"
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_merge_consecutive_same_level_headers
# #############################################################################


class Test_merge_consecutive_same_level_headers(hunitest.TestCase):
    """
    Test the `merge_consecutive_same_level_headers()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `merge_consecutive_same_level_headers()`.

        :param content: Input markdown content
        :param expected: Expected output
        """
        # Run test.
        actual = dshddout.merge_consecutive_same_level_headers(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test three consecutive level-1 headers separated by blank lines.
        """
        # Prepare inputs.
        content = "# 1\n\n# Introduction\n\n# _Machine Intelligence_"
        # Prepare outputs.
        expected = "# 1 Introduction _Machine Intelligence_"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test two consecutive level-2 headers separated by a blank line.
        """
        # Prepare inputs.
        content = "## Part\n\n## One"
        # Prepare outputs.
        expected = "## Part One"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test headers at different levels are left untouched.
        """
        # Prepare inputs.
        content = "# A\n\n## B\n\n# C"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test a solitary header is preserved exactly as written.
        """
        # Prepare inputs.
        content = "# Only one header"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """
        Test non-blank content between headers prevents merging.
        """
        # Prepare inputs.
        content = "# A\n\nSome paragraph text\n\n# B"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """
        Test merging preserves following content and its surrounding blank line.
        """
        # Prepare inputs.
        content = "# A\n\n# B\n\nbody text"
        # Prepare outputs.
        expected = "# A B\n\nbody text"
        # Run test.
        self.helper(content, expected)

    def test7(self) -> None:
        """
        Test directly adjacent same-level headers (no blank lines) merge.
        """
        # Prepare inputs.
        content = "# A\n# B"
        # Prepare outputs.
        expected = "# A B"
        # Run test.
        self.helper(content, expected)

    def test8(self) -> None:
        """
        Test multiple blank lines between same-level headers still merge.
        """
        # Prepare inputs.
        content = "# A\n\n\n\n# B"
        # Prepare outputs.
        expected = "# A B"
        # Run test.
        self.helper(content, expected)

    def test9(self) -> None:
        """
        Test two independent runs of same-level headers each merge separately.
        """
        # Prepare inputs.
        content = "# A\n\n# B\n\nbody\n\n## X\n\n## Y"
        # Prepare outputs.
        expected = "# A B\n\nbody\n\n## X Y"
        # Run test.
        self.helper(content, expected)

    def test10(self) -> None:
        """
        Test content without any headers is unchanged.
        """
        # Prepare inputs.
        content = "Just some\nplain text\nover multiple lines."
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_remove_junk
# #############################################################################


class Test_remove_junk(hunitest.TestCase):
    """
    Test the `remove_junk()` function.
    """

    def helper(self, content: str, expected: str) -> None:
        """
        Test helper for `remove_junk()`.

        :param content: Input markdown content
        :param expected: Expected output after all removals
        """
        # Run test.
        actual = dshddout.remove_junk(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test combined junk removal with multiple HTML artifacts.
        """
        # Prepare inputs.
        content = 'Text <span class="label">Part I.</span> and <a href="#ch1">Chapter 1</a> end'
        # Prepare outputs.
        expected = "Text Part I. and Chapter 1 end"
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test complete cleanup of real HTML-generated markdown.
        """
        # Prepare inputs.
        content = 'Start <span class="label">Intro</span> with <span id="ch1.html"></span> and <a href="#link">reference</a> end'
        # Prepare outputs.
        expected = "Start Intro with  and reference end"
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test clean content remains unchanged.
        """
        # Prepare inputs.
        content = "Clean markdown text without any HTML tags"
        # Prepare outputs.
        expected = content
        # Run test.
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test removal of bold and italic span tags with formatting conversion.
        """
        # Prepare inputs.
        content = 'Check <span class="b">HBR Press Quantity Sales Discounts</span> and <span class="i">What Technology Wants</span> here'
        # Prepare outputs.
        expected = "Check **HBR Press Quantity Sales Discounts** and _What Technology Wants_ here"
        # Run test.
        self.helper(content, expected)

    def test5(self) -> None:
        """
        Test section div promotes header level and div is then removed.
        """
        # Prepare inputs.
        content = '<div class="section2">\n\n# KEY POINTS\n\nbody\n\n</div>'
        # Prepare outputs.
        expected = "\n\n## KEY POINTS\n\nbody\n\n"
        # Run test.
        self.helper(content, expected)

    def test6(self) -> None:
        """
        Test section3 div promotes header to level 3 and div is removed.
        """
        # Prepare inputs.
        content = '<div class="section3">\n\n# Subsection\n\n</div>'
        # Prepare outputs.
        expected = "\n\n### Subsection\n\n"
        # Run test.
        self.helper(content, expected)


# #############################################################################
# Test_standardize_filename
# #############################################################################


class Test_standardize_filename(hunitest.TestCase):
    """
    Test the `standardize_filename()` function.
    """

    def helper(self, filename: str, expected: str) -> None:
        """
        Test helper for `standardize_filename()`.

        :param filename: Input filename to standardize
        :param expected: Expected standardized filename
        """
        # Run test.
        actual = dshddout.standardize_filename(filename)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test standardization of book filename with multiple authors.
        """
        # Prepare inputs.
        filename = "Ajay Agrawal, Joshua Gans, Avi Goldfarb - Prediction Machines_ The Simple Economics of Artificial Intelligence (2018, Harvard Business Review Press) - libgen.li.epub"
        # Prepare outputs.
        expected = "2018.Agrawal_et_al.Prediction_Machines_The_Simple_Economics_of_Artificial_Intelligence.epub"
        # Run test.
        self.helper(filename, expected)

    def test2(self) -> None:
        """
        Test standardization of single author filename.
        """
        # Prepare inputs.
        filename = "John Smith - Advanced Python (2020, Tech Press) - source.pdf"
        # Prepare outputs.
        expected = "2020.Smith.Advanced_Python.pdf"
        # Run test.
        self.helper(filename, expected)

    def test3(self) -> None:
        """
        Test standardization with special characters in title.
        """
        # Prepare inputs.
        filename = "Alice Johnson - The Art of Programming: A Guide (2019, Books Inc).txt"
        # Prepare outputs.
        expected = "2019.Johnson.The_Art_of_Programming_A_Guide.txt"
        # Run test.
        self.helper(filename, expected)

    def test4(self) -> None:
        """
        Test standardization with minimal metadata.
        """
        # Prepare inputs.
        filename = "Bob - Simple Title.docx"
        # Prepare outputs.
        expected = "Bob.Simple_Title.docx"
        # Run test.
        self.helper(filename, expected)

    def test5(self) -> None:
        """
        Test standardization with three authors.
        """
        # Prepare inputs.
        filename = "Alice Author, Bob Builder, Charlie Carter - Three Authors Book (2021, Pub Co).epub"
        # Prepare outputs.
        expected = "2021.Author_et_al.Three_Authors_Book.epub"
        # Run test.
        self.helper(filename, expected)
