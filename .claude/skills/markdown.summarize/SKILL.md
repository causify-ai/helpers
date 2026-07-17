---
description: Summarize a markdown text, keeping the same header structure
model: sonnet
---

# Goal
- The user will pass:
  - Text `<INPUT>`
  - A number of words `<NUM_WORDS>` (specified as an integer) or a fraction of
    the size `<FRACTION>` (specified as a float between 0 and 1)
  - Max level of header `<MAX_HEADER_LEV>`

- You will content in markdown, keeping the same header structure

# Workflow

## Step 1: Read Content
- Read the file `<INPUT>` passed by the user

## Step 2: Extract the Header Section

- Extract the header sections based on `<INPUT>` and on `<MAX_HEADER_LEV>`

### Extract the Header Structure from `<INPUT>`

- Extract the header structure from the `<INPUT>`
- Print it

### No Header Structure
- If there is no structure (i.e., the passed text is just a chunk of text) then
  do not use any headers

### No `<MAX_HEADER_LEV>`
- If there is a structure, use the same structure of the chapter and subchapter
  in markdown headers, if the user has not specified `<MAX_HEADER_LEV>`
  - Use numbers of chapter (e.g., 1.) and subchapters (e.g., 1.1)

- An example of the output is:
  ```
  # 1. Hello

  ## 1.1. Hello world

  - Point
    - Subpoint
    - Subpoint
  - Point

  ## 1.2. Good bye world

  # 2. Hello again
  ```

### Use `<MAX_HEADER_LEV>`
- If the user specifies a `<MAX_HEADER_LEV>`, then keep only the structure of
  the paper that has header level lower than `<MAX_HEADER_LEV>`

- For instance if `<MAX_HEADER_LEV>` = 1, then all the text in H1 header needs
  to be summarized, and the output is like:
  ```
  # 1. Hello

  - Point
    - Subpoint
    - Subpoint
  - Point

  # 2. Hello again
  ```

### Print Header Structure

- Print the structure of the headers to follow


## Summarize Content in Bullet Points
- Write a summary in nested bullet points of `<INPUT>` using the rules in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

- All math formulas must be as Latex formulas

- Count the words of the content `<ORIG_NUM_WORDS>`
- Target the length of the entire output to be around `<NUM_WORDS>`, where
  `<NUM_WORDS>` is given by the user or as `<NUM_WORDS> * <FRACTION>`
- Print the number of words after the summary

- Format the text wrapped in 80 columns

## Keep the Structure

## Write Output
- Print the explanation on the screen
- Write a file `<FILE>` `explanation.<tag>.md` with the explanation 
  - If the file already exists, don't read it but just overwrite it

## Answer Follow-up Questions
- Do not do anything else, but wait for the user to ask questions
- Answer any questions the user asks about the content just read, referencing
  specific sections or concepts from the chapter summary
