import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.documentation_utils as dshdocut


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
        actual = dshdocut.remove_span_with_multiple_attributes(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of span with id and class attributes.
        """
        # Prepare inputs.
        content = 'Before <span id="foo" class="bar">middle</span> after'
        # Prepare outputs.
        expected = 'Before  after'
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
        expected = 'First  and  end'
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
        actual = dshdocut.remove_label_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of label span with double quotes.
        """
        # Prepare inputs.
        content = 'Text <span class="label">Part I</span> more'
        # Prepare outputs.
        expected = 'Text Part I more'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of label span with single quotes.
        """
        # Prepare inputs.
        content = "Text <span class='label'>Chapter 1</span> continues"
        # Prepare outputs.
        expected = 'Text Chapter 1 continues'
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
        actual = dshdocut.remove_keep_together_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of keep-together span with double quotes.
        """
        # Prepare inputs.
        content = 'Before <span class="keep-together">causation</span> after'
        # Prepare outputs.
        expected = 'Before causation after'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of keep-together span with single quotes.
        """
        # Prepare inputs.
        content = "Text <span class='keep-together'>together</span> text"
        # Prepare outputs.
        expected = 'Text together text'
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
        actual = dshdocut.remove_html_link_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of span with .html id.
        """
        # Prepare inputs.
        content = 'Text <span id="ch12.html"></span> after'
        # Prepare outputs.
        expected = 'Text  after'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of span with complex .html id.
        """
        # Prepare inputs.
        content = 'Start <span id="part03.html_part-3"></span> end'
        # Prepare outputs.
        expected = 'Start  end'
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
        actual = dshdocut.remove_pre_span_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of pre span with double quotes.
        """
        # Prepare inputs.
        content = 'Code: <span class="pre">`is_on_sale`</span> ends'
        # Prepare outputs.
        expected = 'Code: `is_on_sale` ends'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of pre span with single quotes.
        """
        # Prepare inputs.
        content = "Function <span class='pre'>my_func</span> defined"
        # Prepare outputs.
        expected = 'Function my_func defined'
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
        actual = dshdocut.remove_anchor_tags(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of simple anchor tag.
        """
        # Prepare inputs.
        content = 'Text <a href="#link">Part III</a> end'
        # Prepare outputs.
        expected = 'Text Part III end'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test removal of anchor with multiple attributes.
        """
        # Prepare inputs.
        content = 'Link <a href="#part03.html_part-3" data-type="xref">Reference</a> here'
        # Prepare outputs.
        expected = 'Link Reference here'
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test multiple anchor tags in content.
        """
        # Prepare inputs.
        content = '<a href="#1">First</a> and <a href="#2">Second</a> links'
        # Prepare outputs.
        expected = 'First and Second links'
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
        actual = dshdocut.remove_backticks_in_math(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of backticks from math expression.
        """
        # Prepare inputs.
        content = 'Formula: $`Y(1)`$ end'
        # Prepare outputs.
        expected = 'Formula: $Y(1)$ end'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test multiple math expressions with backticks.
        """
        # Prepare inputs.
        content = 'First: $`X`$ and second: $`Y(1)`$ math'
        # Prepare outputs.
        expected = 'First: $X$ and second: $Y(1)$ math'
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test that math without backticks is not affected.
        """
        # Prepare inputs.
        content = 'Formula: $Y(1)$ clean'
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
        actual = dshdocut.remove_junk(content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test combined junk removal with multiple HTML artifacts.
        """
        # Prepare inputs.
        content = 'Text <span class="label">Part I.</span> and <a href="#ch1">Chapter 1</a> end'
        # Prepare outputs.
        expected = 'Text Part I. and Chapter 1 end'
        # Run test.
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test complete cleanup of real HTML-generated markdown.
        """
        # Prepare inputs.
        content = 'Start <span class="label">Intro</span> with <span id="ch1.html"></span> and <a href="#link">reference</a> end'
        # Prepare outputs.
        expected = 'Start Intro with  and reference end'
        # Run test.
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test clean content remains unchanged.
        """
        # Prepare inputs.
        content = 'Clean markdown text without any HTML tags'
        # Prepare outputs.
        expected = content
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
        actual = dshdocut.standardize_filename(filename)
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
