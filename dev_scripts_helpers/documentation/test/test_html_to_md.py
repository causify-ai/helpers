#!/usr/bin/env python3

import os
import re
import sys

import helpers.hprint as hprint
import helpers.hunit_test as hunitest


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
        actual = _remove_data_uri_images(input_content)
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
        input_content = (
            "![](data:image/svg+xml;base64,abc){.icon}\n"
            "\n"
            "# Content\n"
            "\n"
            "![Regular](https://example.com/pic.jpg)\n"
            "\n"
            "![](data:image/svg+xml;base64,def){.icon}\n"
        )
        # Prepare outputs.
        expected = (
            "\n"
            "\n"
            "# Content\n"
            "\n"
            "![Regular](https://example.com/pic.jpg)\n"
            "\n"
            "\n"
        )
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
        input_content = "![](data:image/svg+xml;base64,abc)\n\nContent.\n"
        # Prepare outputs.
        expected = "\n\nContent.\n"
        # Run test.
        self.helper(input_content, expected)

    def test8(self) -> None:
        """
        Test inline data URI with alt text.
        """
        # Prepare inputs.
        input_content = "![icon](data:image/svg+xml;base64,abc){.icon}\n\nText.\n"
        # Prepare outputs.
        expected = "\n\nText.\n"
        # Run test.
        self.helper(input_content, expected)

    def test9(self) -> None:
        """
        Test multiple consecutive data URIs.
        """
        # Prepare inputs.
        input_content = (
            "![](data:image/svg+xml;base64,abc){.i1}\n"
            "![](data:image/svg+xml;base64,def){.i2}\n"
            "![](data:image/svg+xml;base64,ghi){.i3}\n"
            "\n"
            "Text.\n"
        )
        # Prepare outputs.
        expected = "\n\n\n\nText.\n"
        # Run test.
        self.helper(input_content, expected)

    def test10(self) -> None:
        """
        Test data URI with special characters in alt text.
        """
        # Prepare inputs.
        input_content = (
            "![Sun & Moon](data:image/svg+xml;base64,abc)\n"
            "\n"
            "![alt](https://example.com/pic.png)\n"
        )
        # Prepare outputs.
        expected = "\n\n![alt](https://example.com/pic.png)\n"
        # Run test.
        self.helper(input_content, expected)
