---
description: Read, criticize, and propose improvements for text
model: opus
---

# Goal
- Review and criticize the text (markdown, blog posts, documentation)
- Identify mistakes and improvement opportunities, focusing on factual errors,
  rather than style suggestions
- Propose concrete improvements to content, flow, visual clarity, pacing,
  and audience fit

# Workflow

## Step 1: Read the Material
- Read the text passed by the user carefully

## Step 2: Identify and Rank Mistakes
- Identify mistakes in the passed text

### Definition
- Criteria for mistakes:
  - Factual inaccuracy (wrong information, outdated claims)
  - Logical contradiction or inconsistency
  - Technical error (code doesn't work, command is wrong, API is misrepresented)
  - Broken reference (link is dead, file path is wrong, name is misspelled)
  - Only report issues you are absolutely certain about

- Ranking severity:
  - _High_: Misleads reader or causes confusion
  - _Medium_: Could improve clarity or accuracy
  - _Low_: Minor inconsistency or incomplete statement

### TODOs
- Ignore the TODOs that already exist in the text

## Step 3: Suggest Improvements
- Identify opportunities to improve clarity, structure, or completeness without
  changing facts

### Definition

- Types of improvements:
  - Clarity: Making text easier to understand
  - Completeness: Adding missing context or examples
  - Consistency: Aligning terminology or formatting
  - Readability: Breaking up dense sections or improving flow

- Ranking severity:
  - _High_: Significantly improves comprehension or prevents misunderstanding
  - _Medium_: Moderately improves clarity or adds useful detail
  - _Low_: Minor improvement in readability or polish

## Step 4: Write the Results
- The output format is a vim cfile following `.claude/skills/cfile.rules.md`
  ```markdown
  <full path file>:<line_number>:1 [HIGH/MEDIUM/LOW] Short description of error
  <full path file>:<line_number>:1 [HIGH/MEDIUM/LOW] Why this is wrong and what the correct statement should be
  ...
  ```

- Example
  ```markdown
  msml610/lectures_source/README.md:12 [HIGH] Claims "pip install X" but pip package is named "X-lib"
  msml610/lectures_source/README.md:5 [HIGH] Add example of basic usage after the description
  helpers/docs.md:8 [MEDIUM] Link to API docs is outdated (2023 version, current is 2024)
  ```

- Save this in a file related to the file being processed
  `<DIR>/<FILE>.CRITIZE.md`
  - E.g., `msml610/lectures_source/Lesson03.1-Knowledge_representation.txt`
    -> `msml610/lectures_source/Lesson03.1-Knowledge_representation.CRITICIZE.txt`

## Step 5: Wait for User Approval
- Wait for user to:
  - Select which mistakes and improvements using the index to fix
  - Provide any additional context or corrections
- Once approved, implement the selected changes
