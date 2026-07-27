---
description: Summarize markdown content preserving header structure and converting to bullet points
model: sonnet
---

# Interface Specification

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `<INPUT>` | file path or text | Yes | Markdown file or text chunk to summarize |
| `<NUM_WORDS>` | integer | No* | Target output word count |
| `<FRACTION>` | float (0-1) | No* | Alternative to `<NUM_WORDS>`: fraction of original size |
| `<MAX_HEADER_LEV>` | integer | No | Max header level to preserve (default: preserve all levels) |
| `<TAG>` | string | No | Tag for output filename (default: derived from input) |

- Exactly one of `<NUM_WORDS>` or `<FRACTION>` must be specified.

## Outputs

| Item | Format | Description |
|------|--------|-------------|
| Console output | Text | Header structure preview + summary + statistics |
| Output file | Markdown | `explanation.<tag>.md` (overwrites if exists) |
| Word count | Integer | Original and target word counts printed to console |

# Workflow

## 1. Parse Input
- Read file from `<INPUT>` path
- Extract headers using markdown syntax (# ## ### etc.)

## 2. Determine Header Strategy

**Case A: Input has header structure**
- Extract all headers from the document
- Print structure to console

**Case B: Input is plain text (no headers)**
- Skip header extraction
- Proceed directly to summarization

## 3. Apply Header Level Filter

**If `<MAX_HEADER_LEV>` not specified:**
- Preserve all header levels from original
- Prefix headers with chapter numbers (e.g., `# 1. Title`, `## 1.1. Subtitle`)

**If `<MAX_HEADER_LEV>` specified:**
- Keep only headers with level ≤ `<MAX_HEADER_LEV>`
- Summarize/collapse all deeper sections into bullet points
- Example: `<MAX_HEADER_LEV>` = 1 → only H1 headers kept, all H2+ become bullets

## 4. Calculate Target Length
- Count original word count → `<ORIG_NUM_WORDS>`
- If `<FRACTION>` given: `<TARGET_WORDS>` = `<ORIG_NUM_WORDS>` × `<FRACTION>`
- If `<NUM_WORDS>` given: `<TARGET_WORDS>` = `<NUM_WORDS>`

## 5. Summarize Content
- Convert to nested bullet points
- Follow rules from:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`
- Constraints:
  - All mathematical formulas → LaTeX format
  - Wrap text at 80 columns
  - Target `<TARGET_WORDS>` word count (±10% tolerance)
  - Preserve key concepts and important details

## 6. Output Results
- Print statistics: `<ORIG_NUM_WORDS>` → actual output word count
- Write `explanation.<tag>.md` file (overwrite if exists)

## 7. Interactive Follow-up
- Wait for user questions
- Answer questions referencing specific sections of the summary

# Behavior Specifications

## Header Numbering
```markdown
# 1. Main Topic
## 1.1. Subtopic A
## 1.2. Subtopic B
# 2. Main Topic 2
```

## Bullet Point Format
```markdown
# 1. Topic

- Main point
  - Supporting detail
  - Supporting detail
- Main point
```

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| No headers in input | Summarize as plain text, no H1/H2 in output |
| `<MAX_HEADER_LEV>` = 1 | Collapse all H2+ into bullets under H1 |
| `<MAX_HEADER_LEV>` > deepest level | Preserve all headers as-is |
| Empty input | Return error message |
| Very short input | Return minimal summary maintaining structure |

# Success Criteria

- [ ] Output word count ≈ `<TARGET_WORDS>` (within 10%)
- [ ] Header structure preserved (or filtered by `<MAX_HEADER_LEV>`)
- [ ] All key information extracted into bullet points
- [ ] Text wrapped at 80 columns
- [ ] File written successfully
- [ ] User can ask follow-up questions
