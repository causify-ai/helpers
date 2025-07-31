"""
Import as:

import helpers.hmarkdown_toc as hmarkdo
"""

import re


def remove_table_of_contents(txt: str) -> str:
    """
    Remove the table of contents from the text of a markdown file.

    The table of contents is stored between
    ```
    <!-- toc -->
    ...
    <!-- tocstop -->
    ```

    :param txt: Input markdown text
    :return: Text with table of contents removed
    """
    txt = re.sub(r"<!-- toc -->.*?<!-- tocstop -->", "", txt, flags=re.DOTALL)
    return txt
