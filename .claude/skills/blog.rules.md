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
- Do not use emdash or other AI artifacts
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
- Follow the instructions from `.claude/skills/visuals.rules.md`

## Screenshots of Commands
- When documenting command-line tools or demonstrating CLI output, capture 
  screenshots using:
  ```bash
  > capture_iterm_command.py --command "CMD" --output_file XYZ.png
  ```
- Save screenshots in a `<FILE>.figs/` directory with descriptive filenames:
  - Use pattern: `fig<N>.<DESCRIPTION>.png`
  - E.g., `fig1.help_output.png`, `fig2.demo_run.png`
- Link screenshots in the blog post markdown:
  ```markdown
  ![Description of screenshot](./<BLOG_NAME>.figs/fig1.help_output.png)
  ```

## Screenshots of Browser Content
- When documenting web applications, UIs, or browser-based tools, capture 
  screenshots using:
  ```bash
  > capture_browser_screenshot.py --url "https://example.com" --output_file XYZ.png
  ```
- Save screenshots in a `<FILE>.figs/` directory with descriptive filenames:
  - Use pattern: `fig<N>.<DESCRIPTION>.png`
  - E.g., `fig1.dashboard_overview.png`, `fig2.form_submission.png`
- Link screenshots in the blog post markdown:
  ```markdown
  ![Description of screenshot](./<BLOG_NAME>.figs/fig1.dashboard_overview.png)
  ```

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
