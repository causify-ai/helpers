Format the text of the blog using the following rules.

## Front Matter (YAML)

Every blog post must start with YAML front matter enclosed in `---`:

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

- **title**: Use double quotes, capitalize major words
- **authors**: List format with username(s)
- **date**: Use YYYY-MM-DD format
- **description**: Usually left empty or contains a brief description
- **categories**: Common categories include:
  - Business
  - Causal AI
  - Startup
  - Causal News
  - Causal ELI5

## TL;DR Section

Immediately after the front matter, add a TL;DR (or TLDR):

```markdown
TL;DR Your punchy one-liner summary that captures the essence of the post.

<!-- more -->
```

- Keep it very short and impactful (one sentence)
- Use a colon after TL;DR or TLDR
- Always follow with `<!-- more -->` tag on a new line with a blank line before it

## Introduction

- Begin with one or more paragraphs introducing the topic
- Write in prose format - avoid bullet points in the introduction
- Set up the context and the problem being addressed
- Use a direct, conversational tone
- Keep paragraphs short and punchy

## Body Structure

- **Section Headings**
  - Use `##` for main sections with clear, descriptive titles
  - Use `###` for subsections
  - Capitalize major words in headings

- **Content Style**
  - Write in a direct, conversational tone
  - Keep paragraphs short (2-4 sentences typically)
  - Separate paragraphs with a single blank line
  - Use frequent examples to illustrate points

## Lists

- Use `-` (dash) consistently for unordered lists
- Indent sub-items with two spaces
- Use ordered lists (`1.`, `2.`, etc.) when sequence matters
- Lists often follow a brief introductory sentence ending with a colon

Example:
```markdown
The main advantages are:

- **First advantage**: Description here
- **Second advantage**: Description here
  - Sub-point with details
  - Another sub-point
```

## Emphasis and Formatting

- **Bold text** (`**text**`):
  - Use for key terms and important concepts
  - Use at the start of list items for headers/labels
  - Use for strong emphasis

- *Italic text* (`_text_`):
  - Use for questions and hypothetical scenarios
  - Use for terms being defined or emphasized
  - Use for "what if" scenarios

- **Inline code** (`` `code` ``):
  - Use for technical terms, variable names, or code snippets

## Tables

Use standard Markdown tables for comparisons:

```markdown
| Column 1 | Column 2 | Column 3 |
| :------- | :------- | :------- |
| Data 1   | Data 2   | Data 3   |
```

- Use left-aligned columns (`:-------`)
- Keep column headers bold where appropriate

## Links

- Use standard Markdown format: `[text](URL)`
- Link to external references and sources
- Use descriptive link text

## Mathematical Notation

When mathematical formulas are needed:

- Inline math: `$E = mc^2$`
- Block math:
  ```markdown
  $$
  E = mc^2
  $$
  ```

## Conclusion

- Often ends with a call to action or summary
- May reference Causify and invite engagement
- Keep it actionable and forward-looking

## General Style Guidelines

- Maintain consistent spacing between sections
- Use blank lines to separate different content blocks
- Keep the tone professional but conversational
- Be direct and avoid unnecessary jargon
- Use concrete examples to illustrate abstract concepts
- Aim for clarity and brevity
