---
description: Find mistakes and provide improvements for a text
---

# Purpose
Review text files (markdown, blog posts, documentation) and identify mistakes
and improvement opportunities. This skill separates factual errors from style
suggestions and prioritizes issues by severity.

# When to Use
- Reviewing a written document for accuracy and clarity
- Checking blog posts, tutorials, or documentation before publication
- Auditing code comments or docstrings for correctness
- Validating claims or technical statements in text
- Improving prose quality and readability

# When NOT to Use
- Proofreading only for typos and grammar (use a spell-checker instead)
- Reformatting code (use a code formatter)
- Making subjective style preferences without clear rationale

# Execution Steps

## Step 1: Identify and Rank Mistakes
Read the text carefully and identify factual errors, incorrect statements, or
broken logic.

**Criteria for mistakes:**

- Factual inaccuracy (wrong information, outdated claims)
- Logical contradiction or inconsistency
- Technical error (code doesn't work, command is wrong, API is misrepresented)
- Broken reference (link is dead, file path is wrong, name is misspelled)
- Only report issues you are absolutely certain about

**Ranking severity:**

- **Critical**: Blocks understanding, causes wrong action, or is factually false
- **High**: Misleads reader or causes confusion
- **Medium**: Could improve clarity or accuracy
- **Low**: Minor inconsistency or incomplete statement

**Output format:**
```markdown
# Mistakes

- <file>:<line_number> [CRITICAL/HIGH/MEDIUM/LOW] Short description of error
- <file>:<line_number> [CRITICAL/HIGH/MEDIUM/LOW] Why this is wrong and what the correct statement should be
```

Example:
```markdown
# Mistakes

- README.md:12 [CRITICAL] Claims "pip install X" but pip package is named "X-lib"
- tutorial.md:45 [HIGH] Says Python 3.9 is required, but code uses 3.11+ syntax
- docs.md:8 [MEDIUM] Link to API docs is outdated (2023 version, current is 2024)
```

## Step 2: Suggest Improvements
Identify opportunities to improve clarity, structure, or completeness without
changing facts.

**Types of improvements:**

- Clarity: Making text easier to understand
- Completeness: Adding missing context or examples
- Consistency: Aligning terminology or formatting
- Readability: Breaking up dense sections or improving flow

**Ranking severity:**

- **High**: Significantly improves comprehension or prevents misunderstanding
- **Medium**: Moderately improves clarity or adds useful detail
- **Low**: Minor improvement in readability or polish

**Output format:**
```markdown
# Improvements

- <file>:<line_number> [HIGH/MEDIUM/LOW] Specific suggestion for how to improve
```

Example:
```markdown
# Improvements

- README.md:5 [HIGH] Add example of basic usage after the description
- tutorial.md:22 [MEDIUM] Break this paragraph into two—too much information in one block
- docs.md:15 [MEDIUM] Define "caching strategy" before using the term
```

## Step 3: Wait for User Approval
Present both sections to the user. Wait for them to:

- Select which mistakes to fix
- Select which improvements to implement
- Provide any additional context or corrections

Once approved, implement the selected changes using the Edit or Read tools as
appropriate.
