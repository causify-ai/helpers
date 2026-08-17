#!/usr/bin/env python3

# TODO(ai_gp): Add missing logging import and _LOG definition. Template requires `import logging` and `_LOG = logging.getLogger(__name__)` after shebang and before other imports. (testing.rules.md:## Unit Test Code Structure)

import logging
import os

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest
import dev_scripts_helpers.download.download_html_to_md as dshddhtmd

_LOG = logging.getLogger(__name__)


def _run_script(
    html_file: str,
    md_file: str,
    converter: str = "auto",
) -> None:
    """
    Run download_html_to_md.py script via subprocess.

    :param html_file: Path to input HTML file
    :param md_file: Path to output markdown file
    :param converter: Converter mode to use
    """
    script_path = hgit.find_file_in_git_tree("download_html_to_md.py")
    cmd = [
        script_path,
        f"--input {html_file}",
        f"--output {md_file}",
        f"--converter {converter}",
        "--action cleanup",
    ]
    cmd_str = " ".join(cmd)
    hsystem.system(cmd_str)


def _test_html_to_md_conversion(
    test_case: hunitest.TestCase,
    html_content: str,
    expected_md: str,
    *,
    converter: str = "auto",
) -> None:
    """
    Helper to test HTML-to-Markdown conversion end-to-end.

    :param test_case: Test case instance (for assertion and scratch space)
    :param html_content: Raw HTML to convert
    :param expected_md: Expected markdown output
    :param converter: Converter mode ('auto', 'bs', 'readability')
    """
    scratch_dir = test_case.get_scratch_space()
    html_file = os.path.join(scratch_dir, "test.html")
    md_file = os.path.join(scratch_dir, "test.md")
    hio.to_file(html_file, html_content)
    _run_script(html_file, md_file, converter=converter)
    actual = hio.from_file(md_file)
    test_case.assert_equal(actual, expected_md, dedent=True, fuzzy_match=True)


# #############################################################################
# Test_remove_data_uri_images
# #############################################################################

# TODO(ai_gp): Test from outside-in: `_remove_data_uri_images()` is an internal function (starts with underscore). Test public-facing behavior (end-to-end script behavior) before testing implementation helpers. (testing.rules.md:## Test From the Outside-In)

class Test_remove_data_uri_images(hunitest.TestCase):
    """
    Test `_remove_data_uri_images()` function for removing data URI images.
    """

    def helper(self, input_content: str, expected: str) -> None:
        """
        Test helper for `_remove_data_uri_images()`.

        :param input_content: Markdown content to process
        :param expected: Expected output after cleanup
        """
        # Run test.
        actual = dshddhtmd._remove_data_uri_images(input_content)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test removal of SVG theme icon (sun).
        """
        # Prepare inputs.
        input_content = """
        ![](data:image/svg+xml;base64,PHN2ZyBjbGFzcz0idGhlbWUtaWNvbi1zdW4iIHZpZXdib3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBhcmlhLWhpZGRlbj0idHJ1ZSI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iNSI+PC9jaXJjbGU+PC9zdmc+){.theme-icon-sun}
        """
        # Prepare outputs.
        expected = """

        """
        # Run test.
        self.helper(hprint.dedent(input_content), hprint.dedent(expected))

    def test2(self) -> None:
        """
        Test removal of SVG theme icon (moon) with attributes.
        """
        # Prepare inputs.
        input_content = """
        ![](data:image/svg+xml;base64,PHN2ZyBjbGFzcz0idGhlbWUtaWNvbi1tb29uIiB2aWV3Ym94PSIwIDAgMjQgMjQiIGZpbGw9Im5vbmUiIHN0cm9rZT0iY3VycmVudENvbG9yIj48cGF0aCBkPSJNMjEgMTIuNzlBOSA5IDAgMSAxIDExLjIxIDMgNyA3IDAgMCAwIDIxIDEyLjc5eiIgLz48L3N2Zz4=){.theme-icon-moon}
        """
        # Prepare outputs.
        expected = """

        """
        # Run test.
        self.helper(hprint.dedent(input_content), hprint.dedent(expected))

    def test3(self) -> None:
        """
        Test preservation of regular images (not data URIs).
        """
        # Prepare inputs.
        input_content = """
        # Title

        ![Alt text](https://example.com/image.png)

        Some content.
        """
        # Prepare outputs.
        expected = """
        # Title

        ![Alt text](https://example.com/image.png)

        Some content.
        """
        # Run test.
        self.helper(hprint.dedent(input_content), hprint.dedent(expected))

    def test4(self) -> None:
        """
        Test mixed content with data URIs and regular images.
        """
        # Prepare inputs.
        input_content = """
        ![](data:image/svg+xml;base64,abc){.icon}

        # Content

        ![Regular](https://example.com/pic.jpg)

        ![](data:image/svg+xml;base64,def){.icon}
        """
        input_content = hprint.dedent(input_content)
        # Prepare outputs.
        expected = """

        # Content

        ![Regular](https://example.com/pic.jpg)


        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(input_content, expected)

    def test5(self) -> None:
        """
        Test empty input.
        """
        # Prepare inputs.
        input_content = ""
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(input_content, expected)

    def test6(self) -> None:
        """
        Test content without any data URIs.
        """
        # Prepare inputs.
        input_content = """
        # Title

        Regular text content.

        - List item 1
        - List item 2
        """
        # Prepare outputs.
        expected = input_content
        # Run test.
        self.helper(hprint.dedent(input_content), hprint.dedent(expected))

    def test7(self) -> None:
        """
        Test data URI without class attribute.
        """
        # Prepare inputs.
        input_content = """
        ![](data:image/svg+xml;base64,abc)

        Content.
        """
        input_content = hprint.dedent(input_content)
        # Prepare outputs.
        expected = """

        Content.
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(input_content, expected)

    def test8(self) -> None:
        """
        Test inline data URI with alt text.
        """
        # Prepare inputs.
        input_content = """
        ![icon](data:image/svg+xml;base64,abc){.icon}

        Text.
        """
        input_content = hprint.dedent(input_content)
        # Prepare outputs.
        expected = """

        Text.
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(input_content, expected)

    def test9(self) -> None:
        """
        Test multiple consecutive data URIs.
        """
        # Prepare inputs.
        input_content = """
        ![](data:image/svg+xml;base64,abc){.i1}
        ![](data:image/svg+xml;base64,def){.i2}
        ![](data:image/svg+xml;base64,ghi){.i3}

        Text.
        """
        input_content = hprint.dedent(input_content)
        # Prepare outputs.
        expected = """



        Text.
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(input_content, expected)

    def test10(self) -> None:
        """
        Test data URI with special characters in alt text.
        """
        # Prepare inputs.
        input_content = """
        ![Sun & Moon](data:image/svg+xml;base64,abc)

        ![alt](https://example.com/pic.png)
        """
        input_content = hprint.dedent(input_content)
        # Prepare outputs.
        expected = """

        ![alt](https://example.com/pic.png)
        """
        expected = hprint.dedent(expected)
        # Run test.
        self.helper(input_content, expected)


# #############################################################################
# Test_download_html_to_md_py_bs
# #############################################################################

# TODO(ai_gp): Missing edge case test for empty HTML input (boundary condition). Add test for empty HTML string to ensure converter handles empty input gracefully. (testing.rules.md:## What to Test)

class Test_download_html_to_md_py_bs(hunitest.TestCase):
    """
    End-to-end test for script using BeautifulSoup converter.
    """

    # TODO(ai_gp): Factor test code via helper method within this class. Multiple test methods (test1, test2, test3) call the same module-level function with the same converter mode. Create a `helper` method within the class to factor this shared logic. (testing.rules.md:## Factor Test Code via Helper Methods, Not Setup)

    def test1(self) -> None:
        """
        Test script with BeautifulSoup converter on HTML with main tag.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <body>
        <nav>Navigation</nav>
        <main>
            <h1>Title Here</h1>
            <p>Content paragraph</p>
        </main>
        </body>
        </html>
        """
        expected = """
        # Title Here

        Content paragraph
        """
        _test_html_to_md_conversion(self, html_content, expected, converter="bs")

    def test2(self) -> None:
        """
        Test script with main container and nested content.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <body>
        <nav>Navigation</nav>
        <main>
            <h1>Article Title</h1>
            <h2>Section</h2>
            <p>Nested content here</p>
        </main>
        </body>
        </html>
        """
        expected = """
        # Article Title

        ## Section

        Nested content here
        """
        _test_html_to_md_conversion(self, html_content, expected, converter="bs")

    def test3(self) -> None:
        """
        Test script with role='main' selector.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <body>
        <nav>Navigation</nav>
        <div role="main">
            <h2>Documentation</h2>
            <p>Content in role main</p>
        </div>
        </body>
        </html>
        """
        expected = """
        ## Documentation

        Content in role main
        """
        _test_html_to_md_conversion(self, html_content, expected, converter="bs")


# #############################################################################
# Test_download_html_to_md_py_readability
# #############################################################################

# TODO(ai_gp): Missing edge case test for empty HTML input (boundary condition). Add test for empty HTML string to ensure readability converter handles empty input gracefully. (testing.rules.md:## What to Test)

class Test_download_html_to_md_py_readability(hunitest.TestCase):
    """
    End-to-end test for script using readability converter.
    """

    # TODO(ai_gp): Factor test code via helper method within this class. Multiple test methods (test1, test2) call the same module-level function with the same converter mode. Create a `helper` method within the class to factor this shared logic. (testing.rules.md:## Factor Test Code via Helper Methods, Not Setup)

    def test1(self) -> None:
        """
        Test script with readability converter on article-like content.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <head><title>Article</title></head>
        <body>
        <nav>Navigation</nav>
        <article>
            <h1>Article Title</h1>
            <p>This is article content that readability should extract.</p>
            <p>More paragraph content here.</p>
        </article>
        <footer>Footer</footer>
        </body>
        </html>
        """
        expected = """
        Navigation

        # Article Title
        This is article content that readability should extract

        More paragraph content here
        """
        _test_html_to_md_conversion(
            self, html_content, expected, converter="readability"
        )

    def test2(self) -> None:
        """
        Test script with readability converter on dense text content.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <body>
        <div>
            <h2>Documentation Section</h2>
            <p>First paragraph of content.</p>
            <p>Second paragraph with more information.</p>
            <p>Third paragraph continuing the documentation.</p>
        </div>
        </body>
        </html>
        """
        expected = """
        ## Documentation Section
        First paragraph of content
        Second paragraph with more information
        Third paragraph continuing the documentation
        """
        _test_html_to_md_conversion(
            self, html_content, expected, converter="readability"
        )


# #############################################################################
# Test_download_html_to_md_py_auto
# #############################################################################

# TODO(ai_gp): Missing edge case test for empty HTML input (boundary condition). Add test for empty HTML string to ensure auto converter handles empty input gracefully. (testing.rules.md:## What to Test)

class Test_download_html_to_md_py_auto(hunitest.TestCase):
    """
    End-to-end test for script using auto converter mode.
    """

    # TODO(ai_gp): Factor test code via helper method within this class. Multiple test methods (test1, test2, test3) call the same module-level function with the same converter mode. Create a `helper` method within the class to factor this shared logic. (testing.rules.md:## Factor Test Code via Helper Methods, Not Setup)

    def test1(self) -> None:
        """
        Test script with auto mode uses BeautifulSoup first when main exists.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <body>
        <nav>Navigation</nav>
        <main>
            <h1>Auto Mode Test</h1>
            <p>Content found by BS selector</p>
        </main>
        </body>
        </html>
        """
        expected = """
        # Auto Mode Test

        Content found by BS selector
        """
        _test_html_to_md_conversion(self, html_content, expected)

    def test2(self) -> None:
        """
        Test script with auto mode falls back to readability.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <body>
        <div>
            <h2>Fallback Test Section</h2>
            <p>This should be extracted by readability fallback.</p>
            <p>Additional paragraph content for readability to process.</p>
        </div>
        </body>
        </html>
        """
        expected = """
        ## Fallback Test Section
        This should be extracted by readability fallback
        Additional paragraph content for readability to process
        """
        _test_html_to_md_conversion(self, html_content, expected)

    def test3(self) -> None:
        """
        Test script preserves heading structure in markdown.
        """
        # TODO(ai_gp): Add section comments to organize test logic. Test methods should have "# Prepare inputs.", "# Prepare outputs.", and "# Run test." sections for consistent structure. (testing.rules.md:## Use Three Sections in Testing Methods)
        html_content = """
        <html>
        <body>
        <main>
            <h1>Main Heading</h1>
            <h2>Subheading</h2>
            <p>Paragraph text</p>
        </main>
        </body>
        </html>
        """
        expected = """
        # Main Heading

        ## Subheading

        Paragraph text
        """
        _test_html_to_md_conversion(self, html_content, expected, converter="bs")
