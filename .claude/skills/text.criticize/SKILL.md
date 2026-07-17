---
description: Read, criticize, and propose improvements for text
model: opus
---

# Goal
- Review text files (markdown, blog posts, documentation) and identify mistakes
  and improvement opportunities, focusing on factual errors, rather than style
  suggestions

# Workflow

## Step 1: Identify and Rank Mistakes
- Read the text carefully and identify factual errors, incorrect statements, or
  broken logic

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

### Output format
- The output format is like:
  ```markdown
  # Mistakes

  1. <file>:<line_number> [HIGH/MEDIUM/LOW] Short description of error
  2. <file>:<line_number> [HIGH/MEDIUM/LOW] Why this is wrong and what the correct statement should be
  ...
  ```


  ```markdown
  # Mistakes

  1. README.md:12 [HIGH] Claims "pip install X" but pip package is named "X-lib"
  2. tutorial.md:45 [HIGH] Says Python 3.9 is required, but code uses 3.11+ syntax
  3. docs.md:8 [MEDIUM] Link to API docs is outdated (2023 version, current is 2024)
  ```

- Save this in a file related to the file being processed
  `<DIR>/<FILE>.MISTAKES.md`
  - E.g., `msml610/lectures_source/Lesson03.1-Knowledge_representation.txt`
    -> `msml610/lectures_source/Lesson03.1-Knowledge_representation.MISTAKES.txt`

## Step 2: Suggest Improvements
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

### Output format
- The output format is like:
  ```markdown
  # Improvements

  1. <file>:<line_number> [HIGH/MEDIUM/LOW] Specific suggestion for how to improve
  2. ...
  ```

- Example:
  ```markdown
  # Improvements

  1. README.md:5 [HIGH] Add example of basic usage after the description
  2. tutorial.md:22 [MEDIUM] Break this paragraph into two—too much information in one block
  3. docs.md:15 [MEDIUM] Define "caching strategy" before using the term
  ```

- Save this in a file related to the file being processed
  `<DIR>/<FILE>.IMPROVEMENTS.md`
  - E.g., `msml610/lectures_source/Lesson03.1-Knowledge_representation.txt`
    -> `msml610/lectures_source/Lesson03.1-Knowledge_representation.IMPROVEMENTS.txt`

## Step 3: Wait for User Approval
- Wait for user to:
  - Select which mistakes and improvements using the index to fix
  - Provide any additional context or corrections
- Once approved, implement the selected changes
