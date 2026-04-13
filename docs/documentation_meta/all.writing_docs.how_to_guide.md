<!-- toc -->

- [Conventions](#conventions)
  * [Make no assumptions on the user's knowledge](#make-no-assumptions-on-the-users-knowledge)
  * [Verify that things worked](#verify-that-things-worked)
  * [Always use Linter](#always-use-linter)
  * [Add a table of contents](#add-a-table-of-contents)
- [Add one level 1 heading](#add-one-level-1-heading)
- [Use 80 columns formatting for md files](#use-80-columns-formatting-for-md-files)
  * [Use good vs bad](#use-good-vs-bad)
  * [Use an empty line after heading](#use-an-empty-line-after-heading)
  * [Bullet lists](#bullet-lists)
  * [Use the right syntax highlighting](#use-the-right-syntax-highlighting)
  * [Indent `code` style](#indent-code-style)
  * [Embed screenshots only when strictly necessary](#embed-screenshots-only-when-strictly-necessary)
  * [Improve your written English](#improve-your-written-english)
  * [Make sure your markdown looks good](#make-sure-your-markdown-looks-good)
  * [Do not overcapitalize headings](#do-not-overcapitalize-headings)
  * [Update the `Last review` tag](#update-the-last-review-tag)
  * [Comment the code structure](#comment-the-code-structure)
  * [Convention for file names](#convention-for-file-names)
  * [Use active voice](#use-active-voice)
  * [Use simple short sentences](#use-simple-short-sentences)
  * [Format for easy reading](#format-for-easy-reading)
  * [Keep it visual](#keep-it-visual)
  * [Mind your spelling](#mind-your-spelling)
  * [Be efficient](#be-efficient)
  * [Do not add fluff](#do-not-add-fluff)
- [Resources](#resources)

<!-- tocstop -->

# Writing Docs

## Summary
- This document describes how to write markdown for:
  - Internal documentation
  - Blog entries
  - Tutorials

- This document is geared towards humans, while the style guide 
  [`//helpers/docs/code_guidelines/all.coding_style_guidelines.reference.md`]
  is for non-human users (e.g., `linter` and `ai_review.py`)

## Meta
- Each of the suggestions below should be a level 3 heading so that it's easy to
  point to it with a link

## Conventions

### Layout Rules

- Visual Structure
  - Use clear headings
  - Use nested bullets for hierarchy
    - 1 idea per bullet
  - Separate sections logically

- Clarity
  - Use simple language
  - Define terms immediately
  - Avoid ambiguous phrasing

- Headings
  - Use `#` for main topics
  - Use `##` for subtopics
  - Keep headings short and descriptive

- Bullets
  - `-` for main bullets
  - Indent for sub-bullets
  - Each bullet = 1 idea

- Diagrams
  - Use diagrams instead of wordy explanations
  - Use `mermaid`, `graphviz`, or `tikz` fenced code blocks
  - Prefer flowcharts, sequence diagrams, or graphs

### Make no assumptions on the user's knowledge

- Nothing is obvious to somebody who doesn't know

### Hold user's hand

- Add ways to verify if a described process worked
  - E.g., "do this and that, if this and that is correct should see this"
- Have a trouble-shooting procedure
  - One approach is to always start from scratch

### Always use Linter

- Most cosmetic suggestions are handled by our Linter
  - Run it after changes
  - Use `i lint --files="your_file_name"`

- Avoid mixing manual edits and Linter runs
  - Run Linter and commit changes separately

- Add a table of contents
  - Markdown doesn't auto-generate TOC
  - Run Linter to build TOC and place it at the top

- If Linter errors occur, file an issue with examples

### Format of each doc

- There should be only one level 1 header with the title of the document
  - The title is used by `mkdocs`
- There should be a summary with a short summary in bullets of the document

- Good:
  ```text
  <!-- toc -->
  <!-- tocstop -->

  # <Title>

  ## Summary
  - This document contains ...

  ## Resources

  ## Last review
  - GP on 2024-04-20
  - Paul on 2024-03-10
  ```

### Use 80 columns formatting for markdown files

- The `linter` takes care of reflowing the text
- `vim` has a `:gq` command to reflow the comments
- There are plugins for PyCharm and VisualStudio

### Use good vs bad

- Make examples of "good" ways of doing something and contrast them with "bad"
  ways using the following format, e.g.,

  ````
  - Good:
    ```markdown
    ...
    ```

  - Bad:
    ```markdown
    ...
    ```
  ````

### Use an empty line after heading

- Leave an empty line after a heading to make it more visible, e.g.,

  - Good
  ```markdown
  # Very important title
  - Less important text
  ```

  - Bad
  ```markdown
  # Coming through! I've big important things to do!
  - ... and his big important wheels got STUCK!
  ```

- Our Linter automatically takes care of this

### Bullet lists

- Use bullet lists since they represent the thought process, force people to
  focus on short sentences (instead of rambling wall-of-text), and relation
  between sentences
- E.g.,
  ```markdown
  - This is thought #1
    - This is related to thought #1
  - This is thought #2
    - Well, that was cool!
    - But this is even better
  ```
- Use `-` instead of `*` or circles
- Linter automatically enforces this

### Use the right syntax highlighting

- When using a block of code use the write syntax highlighting
  - Code (```python)
  - Dirs (e.g.,` /home/users`)
  - Command lines (e.g., `> git push` or `docker> pytest`)
  - Bash
    ```bash
    > git push
    ```
  - Python
    ```python
    if __name__ == "__main__":
        predict_the_future()
        print("done!")
    ```
  - Markdown
    ```markdown
    ...
    ```
  - Nothing
    ```verbatim
    ....
    ```

### Indent `code` style

- GitHub / Pandoc seems to render incorrectly a code block unless it's indented
  over the previous line

### Embed screenshots only when strictly necessary

- Avoid to use screenshots whenever possible and use copy-paste of text with the
  right highlighting
- Sometimes you need to use screenshots (e.g., plots, website interface)

### Improve your written English

- Use English spell-checker
- Type somewhere where you can use several choices:
  - [Grammarly](https://www.grammarly.com/)
  - ChatGPT
  - [LanguageTool](https://www.languagetool.org/)
- This is super-useful to improve your English since you see the error and the
  correction
  - Otherwise you will keep making the same mistakes forever

### Make sure your markdown looks good

- Compare your markdown with others already published

- You can:
  - Check in the code in a branch and use GitHub to render it
  - Use IDEs to edit, which also renders it side-by-side

### Capitalize headings

- Headings titles should be like `Data Schema` not `Data schema`
  - This is automatically enforced by the `linter`

### Update the `Last review` tag

- When you read/refresh a file update the last line of the text
  ```verbatim
  ## Last review
    - GP on 2024-04-20
    - Paul on 2024-03-10
  ```

### Comment the code structure

- When you want to describe and comment the code structure do something like
  this
  ```
  > tree.sh -p data_schema
  data_schema/
  |-- dataset_schema_versions/
  |   `-- dataset_schema_v3.json
    Description of the current schema
  |-- test/
  |   |-- __init__.py
  |   `-- test_dataset_schema_utils.py
  |-- __init__.py
  |-- changelog.txt
    Changelog for dataset schema updates
  |-- dataset_schema_utils.py
    Utilities to parse schema
  `-- validate_dataset_signature.py*
    Script to test a schema
  ```

### Convention for file names

- Each file name should have a format like
  `docs/{component}/{audience}.{topic}.{diataxis_tag}.md`
  - E.g., `docs/documentation_meta/all.diataxis.explanation.md`
- Where
  - `component` is one of the software components (e.g., `datapull`, `dataflow`)
  - `audience` is the target audience (e.g., `all`, `ck`)
  - `topic` is the topic of the file
  - The topic of a "how to guide" should have a verb-object format
    - E.g., `docs/oms/broker/ck.generate_broker_test_data.how_to_guide.md`
  - The topic of a "reference" is often just a name
    - E.g., `docs/oms/broker/ck.binance_terms.reference.md`

// From https://opensource.com/article/20/3/documentation

### Use active voice

- Use active voice most of the time and use passive voice sparingly
- Active voice is shorter than passive voice
- Readers convert passive voice to active voice

- Good: "You can change these configuration by ..."
- Bad: "These configurations can be changed by ..."

### Format for easy reading

- Use headings, bullet points, and links to break up information into chunks
  instead of long explanatory paragraphs

### Keep it visual

- Use tables and diagrams, together with text, whenever possible

### Be efficient

- Nobody wants to read meandering paragraphs in documentation
- Engineers want to get technical information as efficiently as possible
- Do not add "fluff"
- Do not explain things in a repetitive way
- Focus on how we do, why we do, rather than writing AI-generated essays

### Do not add redundancy

- Always point to documentation on the web instead of summarizing it
- If you want to summarize some doc (e.g., so that people don't have to read too
  much), add it to a different document instead of mixing with our documentation

## Resources

- [https://opensource.com/article/20/3/documentation](https://opensource.com/article/20/3/documentation)
- [Markdown cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)
- [Google guide to Markdown](https://github.com/google/styleguide/blob/gh-pages/docguide/style.md)
  - TODO(gp): Make sure it's compatible with our Linter

## Last review
- GP on 2025-07-15
