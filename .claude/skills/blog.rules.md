This document contains all the rules that must be followed when writing a blog

# Blog Document Structure

## Front Matter (YAML)
- Every blog post must start with YAML front matter enclosed in `---`:
  ```markdown
  ---
  title: "Your Blog Post Title"
  authors:
    - gpsaggese
  date: YYYY-MM-DD
  description:
  categories:
    - Category Name
  ---
  ```
  where
  - **title**: Use double quotes, capitalize major words
  - **authors**: List format with username(s)
    - Must match the list in `website/docs/.authors.yml`
  - **date**: Use YYYY-MM-DD format
  - **description**: Usually left empty
  - **draft**: `true` or `false` (use `true` for unpublished drafts)
  - **categories**:
    - Must match the categories defined in `website/mkdocs.yml`

## TL;DR Section
- Immediately after the front matter, add a TL;DR (or TLDR):
  ```markdown
  TL;DR Your punchy one-liner summary that captures the essence of the post.

  <!-- more -->
  ```

- Keep it very short and impactful (one sentence)
- Use a colon after TL;DR or TLDR
- Always follow with `<!-- more -->` tag on a new line with a blank line before
  it

## References to GitHub Files
- When referring to files in the repo, use a verbatim with a link
  to the GitHub repo
  - E.g.,
  ```
  [`helpers/hcache_simple.py`](https://github.com/causify-ai/helpers/blob/master/helpers/hcache_simple.py)
  ```

# Visuals

## Add Visuals to Blog Posts
- When adding visuals (diagrams, images, screenshots) to a blog post:
  - Insert the visual in the right place within the blog content
  - Add a text explanation before or after the visual that concisely explains
    its relevance to the surrounding content
  - Ensure the visual is properly formatted using standard markdown or the
    appropriate code block (mermaid, graphviz, tikz)

## Types of Visuals
- Illustrations can be:

### A mermaid graph
- E.g.,
  ```mermaid
  ...
  ```

### A graphviz graph
- Follow the template `.claude/templates/graphviz.template.md`
- E.g.,
  ```graphviz
  ...
  ```

###A Tikz graph
- Follow the template `.claude/templates/tikz.template.md`
  - E.g.,
    ```tikz
    ...
    ```

### A screenshot from a website
- Use `website_screenshot.py` to take snapshots of notebooks
- Crop to use only what is needed

### A custom image
- Follow the template `.claude/templates/image.template.md`

# Writing Style

## Formatting Rules
- Follow the rules in
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Tone and Audience
- Avoid slang and overly casual language
- Maintain a professional and informative tone
- Aim for approximately 800–1,200 words
- Include examples or real-world applications where relevant
- Write for an audience that may be new to the topic but interested in learning
- The blog should be engaging, informative, and suitable for publication on a
  professional website or LinkedIn

## Formatting and Clarity
- Maintain consistent spacing between sections
- Use blank lines to separate different content blocks
- Keep the tone professional but conversational
- Be direct and avoid unnecessary jargon
- Use concrete examples to illustrate abstract concepts
- Aim for clarity and brevity

## Beautify
- Run a command to format the code for proper visualization
  ```
  > prettier --tab-width 4 <FILE> -w
  ```

