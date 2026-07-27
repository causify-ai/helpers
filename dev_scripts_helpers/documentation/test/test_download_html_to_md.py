#!/usr/bin/env python3


import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import dev_scripts_helpers.documentation.download_html_to_md as dshdhtomd


# #############################################################################
# Test_remove_data_uri_images
# #############################################################################


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
        actual = dshdhtomd._remove_data_uri_images(input_content)
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
# Test_convert_using_bs
# #############################################################################


class Test_convert_using_bs(hunitest.TestCase):
    """
    Test `_convert_using_bs()` function for BeautifulSoup extraction.
    """

    def helper(
        self,
        html_content: str,
        expected_contains: str,
    ) -> None:
        """
        Test helper for `_convert_using_bs()`.

        :param html_content: HTML content to process
        :param expected_contains: Expected substring in extracted content
        """
        # Run test.
        actual = dshdhtomd._convert_using_bs(html_content)
        # Check outputs: verify extracted content contains expected text.
        self.assertIn(expected_contains, actual)

    def test1(self) -> None:
        """
        Test extraction with <main> tag selector.
        """
        # Prepare inputs.
        html_content = """
        <html>
        <head><title>Page</title></head>
        <body>
        <nav>Navigation content</nav>
        <main>
            <h1>Main Content</h1>
            <p>Article content here</p>
        </main>
        <footer>Footer</footer>
        </body>
        </html>
        """
        expected_contains = "Main Content"
        # Run test.
        self.helper(html_content, expected_contains)

    def test2(self) -> None:
        """
        Test extraction with [role='main'] selector.
        """
        # Prepare inputs.
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
        expected_contains = "Documentation"
        # Run test.
        self.helper(html_content, expected_contains)

    def test3(self) -> None:
        """
        Test extraction with [data-content] selector.
        """
        # Prepare inputs.
        html_content = """
        <html>
        <body>
        <div data-content="true">
            <h3>Article Title</h3>
            <p>Data content here</p>
        </div>
        </body>
        </html>
        """
        expected_contains = "Article Title"
        # Run test.
        self.helper(html_content, expected_contains)

    def test4(self) -> None:
        """
        Test extraction with .content class selector.
        """
        # Prepare inputs.
        html_content = """
        <html>
        <body>
        <div class="sidebar">Sidebar</div>
        <div class="content">
            <h2>Main Heading</h2>
            <p>Content with class</p>
        </div>
        </body>
        </html>
        """
        expected_contains = "Main Heading"
        # Run test.
        self.helper(html_content, expected_contains)

    def test5(self) -> None:
        """
        Test with no matching selector returns empty string.
        """
        # Prepare inputs.
        html_content = """
        <html>
        <body>
        <p>Just text without main content container</p>
        </body>
        </html>
        """
        # Run test.
        actual = dshdhtomd._convert_using_bs(html_content)
        # Check outputs: should return empty when no selector matches.
        self.assert_equal(actual, "")

    def test6(self) -> None:
        """
        Test extraction with nested content.
        """
        # Prepare inputs.
        html_content = """
        <html>
        <body>
        <main>
            <article>
                <h1>Article</h1>
                <section>
                    <h2>Section</h2>
                    <p>Nested content</p>
                </section>
            </article>
        </main>
        </body>
        </html>
        """
        expected_contains = "Nested content"
        # Run test.
        self.helper(html_content, expected_contains)


# #############################################################################
# Test_convert_using_readability
# #############################################################################


class Test_convert_using_readability(hunitest.TestCase):
    """
    Test `_convert_using_readability()` function for readability extraction.
    """

    def test1(self) -> None:
        """
        Test extraction with article-like content requires readability library.
        """
        try:
            import readability  # noqa: F401  # type: ignore
        except ImportError:
            self.skipTest("readability library not installed")
        # Prepare inputs.
        html_content = """
        <html>
        <head><title>Article</title></head>
        <body>
        <nav>Navigation</nav>
        <article>
            <h1>Article Title</h1>
            <p>This is the article content that readability should extract.</p>
            <p>More paragraph content here.</p>
        </article>
        <footer>Footer</footer>
        </body>
        </html>
        """
        # Run test.
        actual = dshdhtomd._convert_using_readability(html_content)
        # Check outputs: should extract article content.
        self.assertIsNotNone(actual)
        self.assertGreater(len(actual), 0)

    def test2(self) -> None:
        """
        Test extraction with dense text content requires readability library.
        """
        try:
            import readability  # noqa: F401  # type: ignore
        except ImportError:
            self.skipTest("readability library not installed")
        # Prepare inputs: simulate a documentation page.
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
        # Run test.
        actual = dshdhtomd._convert_using_readability(html_content)
        # Check outputs: should extract something.
        self.assertIsNotNone(actual)
        self.assertGreater(len(actual), 0)


# #############################################################################
# Test_convert_using_python
# #############################################################################


class Test_convert_using_python(hunitest.TestCase):
    """
    Test `_convert_using_python()` function with different converter modes.
    """

    def _check_dependencies(self) -> None:
        """
        Skip test if required dependencies are not installed.
        """
        try:
            import markdownify  # noqa: F401  # type: ignore
        except ImportError:
            self.skipTest("markdownify library not installed")

    def helper(
        self,
        html_content: str,
        converter: str,
        expected_keywords: list,
    ) -> None:
        """
        Test helper for `_convert_using_python()`.

        :param html_content: HTML content to convert
        :param converter: Converter mode ("bs", "readability", "auto")
        :param expected_keywords: List of keywords expected in markdown output
        """
        self._check_dependencies()
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        html_file = os.path.join(scratch_dir, "test.html")
        md_file = os.path.join(scratch_dir, "test.md")
        # Write test HTML file.
        hio.to_file(html_file, html_content)
        # Run test.
        dshdhtomd._convert_using_python(
            html_file,
            md_file,
            converter=converter,
        )
        # Check outputs.
        self.assertTrue(os.path.exists(md_file), "Markdown file should exist")
        actual = hio.from_file(md_file)
        for keyword in expected_keywords:
            self.assertIn(keyword, actual)

    def test1(self) -> None:
        """
        Test conversion with 'bs' converter on HTML with main tag.
        """
        # Prepare inputs.
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
        converter = "bs"
        expected_keywords = ["Title Here", "Content paragraph"]
        # Run test.
        self.helper(html_content, converter, expected_keywords)

    def test2(self) -> None:
        """
        Test conversion with 'readability' converter requires readability.
        """
        self._check_dependencies()
        try:
            import readability  # noqa: F401  # type: ignore
        except ImportError:
            self.skipTest("readability library not installed")
        # Prepare inputs.
        html_content = """
        <html>
        <body>
        <article>
            <h1>Article Title</h1>
            <p>Article content goes here with substantial text.</p>
            <p>More content in the article section.</p>
        </article>
        </body>
        </html>
        """
        converter = "readability"
        expected_keywords = ["Article"]
        # Run test.
        self.helper(html_content, converter, expected_keywords)

    def test3(self) -> None:
        """
        Test conversion with 'auto' mode uses BeautifulSoup first.
        """
        # Prepare inputs: HTML with main container (BS will find it).
        html_content = """
        <html>
        <body>
        <main>
            <h1>Auto Mode Test</h1>
            <p>Content found by BS selector</p>
        </main>
        </body>
        </html>
        """
        converter = "auto"
        expected_keywords = ["Auto Mode Test"]
        # Run test.
        self.helper(html_content, converter, expected_keywords)

    def test4(self) -> None:
        """
        Test conversion with 'auto' mode falls back to readability.
        """
        self._check_dependencies()
        try:
            import readability  # noqa: F401  # type: ignore
        except ImportError:
            self.skipTest("readability library not installed")
        # Prepare inputs: HTML without main container (auto falls back to
        # readability).
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
        converter = "auto"
        scratch_dir = self.get_scratch_space()
        html_file = os.path.join(scratch_dir, "test.html")
        md_file = os.path.join(scratch_dir, "test.md")
        hio.to_file(html_file, html_content)
        dshdhtomd._convert_using_python(
            html_file,
            md_file,
            converter=converter,
        )
        # Check outputs.
        self.assertTrue(os.path.exists(md_file))
        actual = hio.from_file(md_file)
        self.assertGreater(len(actual), 0, "Should produce some output")

    def test5(self) -> None:
        """
        Test conversion preserves heading structure in markdown.
        """
        # Prepare inputs.
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
        converter = "bs"
        expected_keywords = ["# Main Heading", "## Subheading"]
        # Run test.
        self.helper(html_content, converter, expected_keywords)
