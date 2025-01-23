import logging
import os

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_fix_md_links as lafimdli

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_fix_links
# #############################################################################


class Test_fix_links(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test fixing link formatting in a Markdown file.
        """
        # Create a Markdown file with a variety of links.
        txt_incorrect = self._get_txt_with_incorrect_links()
        file_name = "test.md"
        file_path = self._write_input_file(txt_incorrect, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = "\n".join(
            ["# linter warnings", ""]
            + out_warnings
            + ["", "# linted file", ""]
            + updated_lines
        )
        self.check_string(output)

    def test2(self) -> None:
        """
        Test dealing with internal links in a Markdown file.
        """
        # Create a Markdown file with internal links, including TOC.
        txt_internal_links = """
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
        file_name = "test.md"
        file_path = self._write_input_file(txt_internal_links, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = "\n".join(
            ["# linter warnings", ""]
            + out_warnings
            + ["", "# linted file", ""]
            + updated_lines
        )
        self.check_string(output)

    def test3(self) -> None:
        """
        Test the mix of Markdown and HTML-style links.
        """
        input_content = """
    Markdown link: [Valid Markdown Link](docs/markdown_example.md)

    HTML-style link: <a href="docs/html_example.md">Valid HTML Link</a>

    Broken Markdown link: [Broken Markdown Link](missing_markdown.md)

    Broken HTML link: <a href="missing_html.md">Broken HTML Link</a>

    External Markdown link: [External Markdown Link](https://example.com)

    External HTML link: <a href="https://example.com">External HTML Link</a>

    Nested HTML link with Markdown: <a href="[Example](nested.md)">Invalid Nested</a>
        """
        file_name = "test_combined.md"
        file_path = self._write_input_file(input_content, file_name)
        # Run.
        _, updated_lines, out_warnings = lafimdli.fix_links(file_path)
        # Check.
        output = "\n".join(
            ["# linter warnings", ""]
            + out_warnings
            + ["", "# linted file", ""]
            + updated_lines
        )
        self.check_string(output)

    def _get_txt_with_incorrect_links(self) -> str:
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
  - [`cryptokaizen-data-tokyo.preprod`](https://ap-northeast-1.console.aws.amazon.com/s3/buckets/cryptokaizen-data-tokyo.preprod)

- Markdown-style link to a file that does not exist
  - [File not found](/helpersssss/hhhhgit.py)

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
        return txt_incorrect

    def _write_input_file(self, txt: str, file_name: str) -> str:
        """
        Write test content to the file.

        :param txt: the content of the file
        :param file_name: the name of the file
        :return: the path to the file with the test content
        """
        # Get the path to the scratch space.
        dir_name = self.get_scratch_space()
        # Compile the path to the test content file.
        file_path = os.path.join(dir_name, file_name)
        file_path = os.path.abspath(file_path)
        # Create the file.
        hio.to_file(file_path, txt)
        return file_path
