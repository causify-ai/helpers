import logging
import os
from typing import List

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import linters.amp_fix_md_links as lafimdli

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_fix_links
# #############################################################################


def _get_output_string(out_warnings: List[str], updated_lines: List[str]) -> str:
    """
    Get the canonical output string for a test.
    """
    warnings = "\n".join(out_warnings)
    lines = "\n".join(updated_lines)
    output = f"""
# linter warnings
{warnings}

# linted file
{lines}"""
    output: str = hprint.dedent(output)
    return output


# #############################################################################
# Test_fix_links
# #############################################################################


class Test_fix_links(hunitest.TestCase):

    def write_input_file(self, txt: str, file_name: str) -> str:
        """
        Write test content to a file in the scratch space.

        :param txt: the content of the file
        :param file_name: the name of the file
        :return: the path to the file with the test content
        """
        txt = hprint.dedent(txt)
        # Get file path to write.
        dir_name = self.get_scratch_space()
        file_path = os.path.join(dir_name, file_name)
        file_path = os.path.abspath(file_path)
        # Create the file.
        hio.to_file(file_path, txt)
        return file_path

    # TODO(gp): To outsource. Break into smaller tests. If one of these fails,
    # it's hard to debug.
    def test1(self) -> None:
        """
        Test fixing link formatting in a Markdown file.
        """
        # Prepare inputs.
        txt_incorrect = r"""
        - Markdown-style link with a text label
          - [Here](/helpers/hdbg.py)

        - Markdown-style link with a text label in backticks
          - [`hdbg`](/helpers/hdbg.py)

        - Markdown-style link with a path label
          - [/helpers/hdbg.py](/helpers/hdbg.py)

        - Markdown-style link with a path label in backticks
          - [`/helpers/hdbg.py`](/helpers/hdbg.py)

        - Markdown-style link with a path label with a dot at the start
          - [./helpers/test/test_hdbg.py](./helpers/test/test_hdbg.py)

        - Markdown-style link with a path label without the slash at the start
          - [helpers/test/test_hdbg.py](helpers/test/test_hdbg.py)

        - Markdown-style link with a path label in backticks without the slash at the start
          - [`helpers/test/test_hdbg.py`](helpers/test/test_hdbg.py)

        - Markdown-style link with the link only in square brackets
          - [/helpers/hgit.py]()

        - Markdown-style link with an http GH company link
          - [helpers/hgit.py](https://github.com/causify-ai/helpers/blob/master/helpers/hgit.py)

        - Markdown-style link with an http GH company link and a text label
          - [Here](https://github.com/causify-ai/helpers/blob/master/helpers/hgit.py)

        - Markdown-style link with an http external link
          - [AirFlow UI](http://172.30.2.44:8090/home).

        - Markdown-style link with backticks in the square brackets and external http link
          - [`foobar`](https://ap-northeast-1.console.aws.amazon.com/s3/buckets/foobar)

        - Markdown-style link to a file that does not exist
          - [File not found](/helpersssss/hhhhgit.py)

        - Markdown-style link with a directory beginning with a dot
          - [`fast_tests.yml`](/.github/workflows/fast_tests.yml)

        - File path without the backticks
          - /helpers/test/test_hdbg.py

        - File path with the backticks
          - `/helpers/test/test_hdbg.py`

        - File path with the backticks and a dot at the start
          - `./helpers/test/test_hdbg.py`

        - File path with the backticks and no slash at the start
          - `helpers/test/test_hdbg.py`

        - File path without the dir
          - `README.md`

        - File path of a hidden file
          - .github/workflows/build_image.yml.DISABLED

        - Non-file path
          - ../../../../amp/helpers:/app/helpers

        - Non-file path text with slashes in it
          - Code in Markdown/LaTeX files (e.g., mermaid code).

        - File path that does not exist
          - `/helpersssss/hhhhgit.py`

        - File path inside triple ticks:
        ```bash
        With backticks: `helpers/hgit.py`
        Without backticks: helpers/hgit.py
        ```

        - HTML-style figure pointer
          - <img src="import_check/example/output/basic.png">

        - HTML-style figure pointer with an attribute
          <img src="import_check/example/output/basic.png" style="" />

        - HTML-style figure pointer with a slash at the start
          - <img src="/import_check/example/output/basic.png">

        - HTML-style figure pointer that does not exist
          - <img src="/iiimport_check/example/output/basicccc.png">

        - Markdown-style figure pointer
          - ![](import_check/example/output/basic.png)

        - Markdown-style figure pointer with an attribute
          - ![](import_check/example/output/basic.png){width="6.854779090113736in"
        height="1.2303444881889765in"}

        - Markdown-style figure pointer with a slash at the start
          - ![](/import_check/example/output/basic.png)

        - Markdown-style figure pointer with a dir changes at the start
          - ![](../../import_check/example/output/basic.png)

        - Markdown-style figure pointer that does not exist
          - ![](/iiimport_check/example/output/basicccc.png)
        """
        file_name = "test.md"
        file_path = self.write_input_file(txt_incorrect, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = _get_output_string(out_warnings, updated_lines)
        self.check_string(output, purify_text=True)

    def test2(self) -> None:
        """
        Test dealing with internal links in a Markdown file, including TOC.
        """
        # Prepare inputs.
        txt_internal_links = r"""
        <!--ts-->
          * [Best practices for writing plotting functions](#best-practices-for-writing-plotting-functions)
              * [Cosmetic requirements](#cosmetic-requirements)

        <!--te-->

        <!-- toc -->

        - [Best practices for writing plotting functions](#best-practices-for-writing-plotting-functions)
          * [Cosmetic requirements](#cosmetic-requirements)

        <!-- tocstop -->


        [Data Availability](#data-availability)
        """
        #
        file_name = "test.md"
        file_path = self.write_input_file(txt_internal_links, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = _get_output_string(out_warnings, updated_lines)
        self.check_string(output, purify_text=True)

    # TODO(gp): To outsource. Break into smaller tests. If one of these fails,
    # it's hard to debug.
    def test3(self) -> None:
        """
        Test the mix of Markdown and HTML-style links.
        """
        # Prepare inputs.
        input_content = r"""
        Markdown link: [Valid Markdown Link](docs/markdown_example.md)

        HTML-style link: <a href="docs/html_example.md">Valid HTML Link</a>

        Broken Markdown link: [Broken Markdown Link](missing_markdown.md)

        Broken HTML link: <a href="missing_html.md">Broken HTML Link</a>

        External Markdown link: [External Markdown Link](https://example.com)

        External HTML link: <a href="https://example.com">External HTML Link</a>

        Nested HTML link with Markdown: <a href="[Example](nested.md)">Invalid Nested</a>
        """
        file_name = "test_combined.md"
        file_path = self.write_input_file(input_content, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = _get_output_string(out_warnings, updated_lines)
        self.check_string(output, purify_text=True)

    def test4(self) -> None:
        """
        Test links with a filepath with a tag ("/image.png") to check for its
        preservation.
        """
        # Prepare inputs.
        input_content = r"""

        <img src="figs/ck.github_projects_process.reference_figs/image1.png"
            style="width:6.5in;height:0.31944in" />

        """
        file_name = "test_excerpt.md"
        file_path = self.write_input_file(input_content, file_name)
        # Run.
        _, updated_lines, _ = lafimdli.fix_links(file_path)
        # Check.
        actual = "\n".join(updated_lines)
        expected = r"""

        <img src="figs/ck.github_projects_process.reference_figs/image1.png"
            style="width:6.5in;height:0.31944in" />

        """
        self.assert_equal(actual, expected, fuzzy_match=True, purify_text=True)

    def test5(self) -> None:
        """
        Test Markdown file references to another Markdown file and its headers.
        """
        # Prepare inputs.
        reference_file_md_content = r"""
        # Reference test file

        - [Introduction](#introduction)
        - [Hyphen test](#hyphen-test)

        ## Introduction

        A test header with one word in the reference file.

        ## Hyphen test

        A test to check two words header in the reference file.
        """
        reference_file_name = "reference.md"
        reference_file_link = self.write_input_file(
            reference_file_md_content, reference_file_name
        )
        #
        test_md_content = rf"""
        Markdown link: [Valid Markdown and header Link]({reference_file_link}#introduction)

        Markdown link: [InValid Markdown Link](docs/markdown_exam.md#introduction)

        Markdown link: [Invalid header in the Markdown Link]({reference_file_link}#introduce)

        Markdown link: [Valid Markdown and header Link]({reference_file_link}#hyphen-test)
        """
        test_file_name = "valid_header_test.md"
        test_file_link = self.write_input_file(test_md_content, test_file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(test_file_link)
        # Check.
        output = _get_output_string(out_warnings, updated_lines)
        self.check_string(output, purify_text=True)

    def test6(self) -> None:
        """
        Test the URI links are not incorrectly prefixed with a '/'.
        """
        input_content = """
          Website: [Website](http://example.com)

          Secure site: [Secure](https://example.com)

          Email: [Email](mailto:user@example.com)

          FTP: [FTP](ftp://files.example.com)

          Tel: [Call](tel:+1234567890)
          """
        file_name = "test_links.md"
        file_path = self.write_input_file(input_content, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = _get_output_string(out_warnings, updated_lines)
        self.check_string(output, purify_text=True)

    def test7(self) -> None:
        """
        Test if in-repo and out-of-repo links are parsed correctly.
        """
        # Prepare inputs.
        txt_incorrect = r"""
            - [Fix Markdown links](https://github.com/causify-ai/helpers/blob/master/linters/amp_fix_md_links.py)
            - [LLM Tutorial](https://github.com/causify-ai/tutorials/blob/master/llms/tutorial-openai_new.ipynb)
        """
        file_name = "test.md"
        file_path = self.write_input_file(txt_incorrect, file_name)
        # Run.
        _, updated_lines, _ = lafimdli.fix_links(file_path)
        # Check.
        expected = [
            "- [Fix Markdown links](/linters/amp_fix_md_links.py)",
            "- [LLM Tutorial](https://github.com/causify-ai/tutorials/blob/master/llms/tutorial-openai_new.ipynb)",
        ]
        self.assertEqual(expected, updated_lines)

    def test8(self) -> None:
        """
        Test single bare link conversion to Markdown-style link.
        """
        # Prepare inputs.
        text = r"""
        https://gspread-pandas.readthedocs.io/en/latest/configuration.html
        """
        file_name = "test_bare_links.md"
        file_path = self.write_input_file(text, file_name)
        # Run.
        _, actual, _ = lafimdli.fix_links(file_path)
        # Check.
        expected = [
            "[https://gspread-pandas.readthedocs.io/en/latest/configuration.html](https://gspread-pandas.readthedocs.io/en/latest/configuration.html)",
        ]
        self.assertEqual(expected, actual)

    def test9(self) -> None:
        """
        Test bulleted bare link conversion to Markdown-style link.
        """
        # Prepare inputs.
        text = r"""
        - Http://gspread-pandas.readthedocs.io/en/latest/configuration.html
        """
        file_name = "test_bare_links.md"
        file_path = self.write_input_file(text, file_name)
        # Run.
        _, actual, _ = lafimdli.fix_links(file_path)
        # Check.
        expected = [
            "- [http://gspread-pandas.readthedocs.io/en/latest/configuration.html](http://gspread-pandas.readthedocs.io/en/latest/configuration.html)",
        ]
        self.assertEqual(expected, actual)

    def test10(self) -> None:
        """
        Test multiple bare links conversion to Markdown-style links.
        """
        # Prepare inputs.
        text = r"""
        http://github.com/google/styleguide/blob/gh-pages/docguide/style.md
        - Https://github.com/causify-ai/tutorials/blob/master/llms/tutorial-openai_new.ipynb
        """
        file_name = "test_bare_links.md"
        file_path = self.write_input_file(text, file_name)
        # Run.
        _, actual, _ = lafimdli.fix_links(file_path)
        # Check.
        expected = [
            "[http://github.com/google/styleguide/blob/gh-pages/docguide/style.md](http://github.com/google/styleguide/blob/gh-pages/docguide/style.md)",
            "- [https://github.com/causify-ai/tutorials/blob/master/llms/tutorial-openai_new.ipynb](https://github.com/causify-ai/tutorials/blob/master/llms/tutorial-openai_new.ipynb)",
        ]
        self.assertEqual(expected, actual)

    def test11(self) -> None:
        """
        Test that links inside fenced code blocks are not modified.
        """
        # Prepare inputs.
        text = r"""
        Links inside fenced block that should not be formatted:
        ```
        https://example.com/inside-fenced-block
        http://github.com/user/repo
        ```

        Another fenced block with different language:
        ```python
        url = "https://example.com/python-url"
        response = requests.get("https://api.github.com/users")
        ```
        """
        file_name = "test_fenced_blocks.md"
        file_path = self.write_input_file(text, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = _get_output_string(out_warnings, updated_lines)
        self.check_string(output, purify_text=True)

    def test12(self) -> None:
        """
        Test that URLs inside quotation marks are not converted to Markdown-
        style links.
        """
        # Prepare inputs.
        text = r"""
        URL in quotation marks: "https://example.com/path".

        Image with URL in src attribute: <img width="505" alt="" src="https://github.com/user/repo/assets/12345/abcdef-ghijk-lmnop" />

        URL in HTML attribute: <div data-url="https://api.example.com/endpoint"></div>
        """
        file_name = "test_quoted_urls.md"
        file_path = self.write_input_file(text, file_name)
        # Run.
        _, actual, _ = lafimdli.fix_links(file_path)
        # Check.
        expected = [
            'URL in quotation marks: "https://example.com/path".',
            "",
            'Image with URL in src attribute: <img width="505" alt="" src="https://github.com/user/repo/assets/12345/abcdef-ghijk-lmnop" />',
            "",
            'URL in HTML attribute: <div data-url="https://api.example.com/endpoint"></div>',
        ]
        self.assertEqual(expected, actual)


# #############################################################################
# Test_make_path_absolute
# #############################################################################


class Test_make_path_absolute(hunitest.TestCase):

    def test_make_path_absolute1(self) -> None:
        """
        Test file path to retain directory name beginning with a dot.
        """
        file_path = "/.github/workflows/sprint_iteration.yml"
        expected = "/.github/workflows/sprint_iteration.yml"
        # Run.
        actual = lafimdli._make_path_absolute(file_path)
        # Check.
        self.assertEqual(actual, expected)

    def test_make_path_absolute2(self) -> None:
        """
        Test to make file path absolute.
        """
        file_path = "./.github/workflows/sprint_iteration.yml"
        expected = "/.github/workflows/sprint_iteration.yml"
        # Run.
        actual = lafimdli._make_path_absolute(file_path)
        # Check.
        self.assertEqual(actual, expected)

    def test_make_path_absolute3(self) -> None:
        """
        Test to make file path absolute.
        """
        file_path = "../.github/workflows/sprint_iteration.yml"
        expected = "/.github/workflows/sprint_iteration.yml"
        # Run.
        actual = lafimdli._make_path_absolute(file_path)
        # Check.
        self.assertEqual(actual, expected)

    def test_make_path_absolute4(self) -> None:
        """
        Test to make file path absolute.
        """
        file_path = "../../.github/workflows/sprint_iteration.yml"
        expected = "/.github/workflows/sprint_iteration.yml"
        # Run.
        actual = lafimdli._make_path_absolute(file_path)
        # Check.
        self.assertEqual(actual, expected)
