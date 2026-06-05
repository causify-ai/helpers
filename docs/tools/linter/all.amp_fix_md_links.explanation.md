

<!-- toc -->

- [Fixing link formatting in Markdown files](#fixing-link-formatting-in-markdown-files)
  * [Problem](#problem)
  * [Solution](#solution)
  * [Formatting conventions](#formatting-conventions)

<!-- tocstop -->

# Fixing link formatting in Markdown files

## Problem

- Our Markdown documentation typically contains many links to various files;
  however, the formatting of the links is not always uniform
  - E.g., a link to a figure can follow the HTML standard:
    `<img src="PATH_TO_FIG">`
  - Or it can follow the Markdown standard: `![](PATH_TO_FIG)`
- Links may also become obsolete, for example, if a file gets renamed, moved
  elsewhere or deleted but the Markdown is not updated
- We want the links to have consistent formatting and not to point to
  non-existent files

## Solution

- Add a Linter step [`amp_fix_md_links`](/linters/amp_fix_md_links.py) that
  - Regularizes the format of file links and figure pointers
  - Issues a warning if a link is pointing to a file that does not exist

## Formatting conventions

- We adopt the following conventions regarding the formatting of links in
  Markdown:
  - The format of a link is
    <span>`[/DIR_NAME/FILE_NAME](/DIR_NAME/FILE_NAME)`</span>
    - E.g., <span>`[/dir1/dir2/file.py](/dir1/dir2/file.py)`</span>
    - The link text is the same as the link
      - Unless it is a regular text (not a file path), e.g.,
        <span>`[here](/dir1/dir2/file.py)`</span>
    - The link is an absolute path to the file (not a relative path and not a
      URL)
  - A bare file path <span>`/DIR_NAME/FILE_NAME`</span> is converted into a
    link, which should conform to the conventions described above
    - E.g., <span>`/dir1/dir2/file{dot}py`</span> is converted into
      <span>`[/dir1/dir2/file.py](/dir1/dir2/file.py)`</span>
  - The format of a figure pointer is
    <span>`<img src="figs/DIR_NAME/FILE_NAME">`</span>
    - E.g., <span>`<img src="figs/all.docs.md/file.png">`</span>
    - `DIR_NAME` is the same as the name of the Markdown file where the figure
      pointer is located
    - An additional warning is issued if the actual path to the figure does not
      conform to this format
