<!-- toc -->

- [Gdoc Markdown conversion](#gdoc--markdown-conversion)
  * [Converting Gdocs to Markdown](#converting-gdocs-to-markdown)
    + [Other approaches](#other-approaches)
  * [Converting Markdown to Gdoc](#converting-markdown-to-gdoc)

<!-- tocstop -->

# Gdoc <-> Markdown conversion

## Converting Gdocs to Markdown

- Use bullet lists to organize the whole Markdown for consistency with other
  docs. See
  [all.coding_style.how_to_guide.md](/docs/coding/all.coding_style.how_to_guide.md)
  or any other published Markdown format as reference
- Add missing "```" around code blocks. These could be missing in the original
  Google doc. Also adjust code block indentations if needed
- The generated markdown may convert http links as `html` `<span>` objects. This
  hinders the readability of the `md` file. In this case, manually convert to a
  standard `http://` link: -
  `[<span class="underline">https://www.sorrentum.org/</span>](https://www.sorrentum.org/)`
  -> `https://www.sorrentum.org/`

- Remove empty lines manually

  ```markdown
  :'<,'>! perl -ne 'print if /\S/'
  ```

- Run Linter
  - Usage:
    ```bash
    > i lint --files="docs/documentation_meta/all.writing_docs.how_to_guide.md"
    ```
  - What Linter will do:
    - Build TOC automatically
    - Adjust the indentation to improve the Markdown's format (but the
      precondition is that you have properly adjusted the indentation levels).
    - Remove extra empty lines under headings.
    - Adjust text layout.
  - Do not mix manual edits and Linter runs
  - If Linter messes up the text
    - File bugs in `helpers` with examples what Linter does incorrectly
- Last steps
  - Compare the generated markdown file with the original Gdoc from top to
    bottom to ensure accurate rendering.
  - Review the markdown file on GitHub to make sure it looks good, as it may
    slightly differ from the preview in your local markdown editor
- When a gdoc becomes obsolete, delete it

### Other approaches

- Best for a large document
- Approach 1 - Chrome Docs to Markdown extension:
  - Use the [Docs to Markdown](https://github.com/evbacher/gd2md-html/wiki)
    extension
    - Install
      [the extension](https://gsuite.google.com/marketplace/app/docs_to_markdown/700168918607)
      from the G Suite marketplace
    - [User guide](https://github.com/evbacher/gd2md-html/wiki#using-docs-to-markdown)
      for the extension
  - One needs to accept/reject all suggestions in a gdoc as the extension works
    poorly when a document is edited in the suggestion mode
- Approach 2 - Online converter:
  - [Google-docs-to-markdown/](https://mr0grog.github.io/google-docs-to-markdown/)

- Also need to go through
  [Cleaning up converted markdown](#cleaning-up-converted-markdown)
- You might need to remove artifacts manually

## Converting Markdown to Gdoc

- Approach 1:
  - Run
    ```bash
    > pandoc MyFile.md -f markdown -t odt -s -o MyFile.odt
    ```
  - Download the
    [template](https://docs.google.com/document/d/1Z_OdO6f7VYjimgjfGPofsYHyWvyxXrtOVVcvCauJIpI/edit)
    in odt format
  - Run
    ```bash
    > pandoc code_organization.md -f markdown -t odt -s -o code_org.odt --reference-doc /Users/saggese/Downloads/Gdoc\ -\ Template.odt
    ```
  - Open it with TextEdit, copy-paste to Gdoc
- Approach 2:
  - Instead of copy-paste the markdown into Gdocs, you can copy the rendered
    markdown in a Gdoc
    - Gdocs does a good job of maintaining the formatting, levels of the
      headers, the links, and so on
- Approach 3:
  - [https://markdownlivepreview.com/](https://markdownlivepreview.com/)
  - TODO(gp): Check if the roundtrip works
