---
description: Summarize markdown content into bullet points while preserving header structure
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

## Parse Input
- Read file from `<INPUT>` path
- Extract headers using markdown syntax (# ## ### etc.)

## Determine Header Strategy

**Case A: Input has header structure**
- Extract all headers from the document
- Print structure to console

**Case B: Input is plain text (no headers)**
- Skip header extraction
- Proceed directly to summarization

## Apply Header Level Filter

**If `<MAX_HEADER_LEV>` not specified:**
- Preserve all header levels from original

**If `<MAX_HEADER_LEV>` specified:**
- Keep only headers with level <= `<MAX_HEADER_LEV>`
- Summarize/collapse all deeper sections into chunks (see "Group Into Chunks")
  - Each collapsed section becomes a chunk titled after its header text
    (shortened if needed)
  - Headers nested inside a collapsed section become sub-bullets
- Example: `<MAX_HEADER_LEV>` = 1 results in only H1 headers kept, each H2+
  section becomes a `* <TITLE>` chunk

**For every header kept (header fidelity):**
- Copy the header line verbatim from the source
  - Same `#` level, same text, same numbering, same order
  - Do not rename, shorten, reword, or re-case it
  - Do not renumber it, e.g., a source `# 2. Methods` stays `# 2. Methods`
  - Do not add numbers, e.g., a source `## Data` stays `## Data`
  - Keep gaps and duplicates in the source numbering as they are
- Do not add, merge, split, or reorder headers
  - The only headers removed are the ones deeper than `<MAX_HEADER_LEV>`
- Header fidelity wins over the header rules of `markdown.rules.md` and
  `text.rules.md`
  - E.g., starting at level 1, capitalizing major words, numbering in order

## Calculate Target Length
- Count original word count as `<ORIG_NUM_WORDS>`
- If `<FRACTION>` given: `<TARGET_WORDS>` = `<ORIG_NUM_WORDS>` x `<FRACTION>`
- If `<NUM_WORDS>` given: `<TARGET_WORDS>` = `<NUM_WORDS>`

## Summarize Content
- Convert to chunks of nested bullet points
  - See "Group Into Chunks" and "Compress Content" below
- Follow rules from:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`
  - If they conflict with the chunk format below, the chunk format wins
    - E.g., the `##` chunk titles in "Example 2" of `text.rules.md`
- Constraints:
  - Convert all mathematical formulas to LaTeX format
  - Wrap text at 85 columns
  - Target `<TARGET_WORDS>` word count (within 10% tolerance)
  - Preserve key concepts and important details

## Group Into Chunks
- Split the content under each preserved header into chunks of related
  content
  - If the input has no headers, split the whole text into chunks
- Start each chunk with a title line `* <TITLE>`, with no leading spaces
  - Put the bullets directly under the title, with no blank line in between
  - Separate chunks with one blank line
  - Do not write bullets outside a chunk
- A chunk:
  - Covers one topic or idea
  - Has typically 2-5 first-level bullets
  - Follows the order of the source
- Start a new chunk when the topic changes
  - E.g., from a definition, to why it matters, to its uses, to an example
- Rules for `<TITLE>` (same as slide titles in `slides.rules.md`):
  - Short noun phrase, 2-6 words, in sentence case
  - Names the topic or the claim, not its role
    - **Bad**: `* Overview`, `* Details`, `* Point 2`
    - **Good**: `* Culture > strategy`
  - Use `>` to express priority or comparison
  - Use `: <qualifier>` for a variant of the topic of an earlier chunk
    - E.g., `* Core values: EOS Worldwide example`
  - No numbering, no trailing punctuation, ASCII only
  - Unique within its section
- Use `#` headers only for headers that exist in the source
  - Do not use `#` for chunk titles
  - Headers keep the numbers of the source, while `*` titles are never numbered

## Compress Content
- Keep:
  - Definitions and claims
  - Enumerations, e.g., the list of values
  - Cause-effect relations, e.g., culture wins in the long term
  - The few concrete examples that clarify a claim
- Drop:
  - Quotes and attributions, e.g., "a famous author is credited with ..."
  - Cross-references and links, e.g., "see Chapter 8"
  - Rhetorical asides and hedges, e.g., "keep in mind yours will be different"
  - Exhortations and motivational closing paragraphs
  - Restatements of a claim that a bullet already captures
- Write bullets as fragments, not full sentences:
  - Omit the subject when the chunk title already names it
    - E.g., under `* Core values`, write `Define the culture`, not
      `Core Values define the culture`
  - Do not end a bullet with a period
  - If one sentence makes several claims about one subject, use the subject as
    a parent bullet and one sub-bullet per claim
    - E.g., `A Company` with sub-bullets `Needs to know who it is` and
      `Is defined by the Core Values`
- Turn an enumeration in the source into one flat list of bullets, in source
  order
  - This applies to numbered, bold-numbered, and inline lists
  - Drop the numbers and the bold
- If the source explains one list item at length, put 2-3 sub-bullets under
  that item
  - Use `E.g.,` to introduce a concrete example
  - Use `:` to join a statement and its explanation
- Use `.claude/skills/markdown.summarize/example.md` as the reference
  - It compresses 351 words into 108 (about 31%), not counting the header
  - The 2 closing paragraphs of the input are dropped completely
  - The exact target length comes from `<TARGET_WORDS>`, not from the example

## Output Results
- Print statistics: `<ORIG_NUM_WORDS>` compared to actual output word count
- Write `explanation.<tag>.md` file (overwrite if exists)

## Interactive Follow-up
- Wait for user questions
- Answer questions referencing specific sections of the summary

# Behavior Specifications

## Header Fidelity
- Output headers are identical to the source headers
  - Source numbered, output numbered the same way
    - **Bad**: source `# 2. Methods`, output `# 1. Methods`
    - **Good**: source `# 2. Methods`, output `# 2. Methods`
  - Source not numbered, output not numbered
    - **Bad**: source `## Data`, output `## 1.1. Data`
    - **Good**: source `## Data`, output `## Data`
  - Source `# 2. Methods`, `## 2.1. Data`, `# 4. Results`
    - Output keeps `2.`, `2.1.`, and `4.` (it does not renumber `4.` to `3.`)

## Chunk Format
```markdown
# <Header copied from source>

* First chunk title
- Main point
  - Supporting detail
  - Supporting detail
- Main point

* Second chunk title
- Main point
```

## Edge Cases

| Condition | Behavior |
|-----------|----------|
| No headers in input | Summarize into `* <TITLE>` chunks, no H1/H2 in output |
| `<MAX_HEADER_LEV>` = 1 | Collapse all H2+ into `* <TITLE>` chunks under H1 |
| `<MAX_HEADER_LEV>` > deepest level | Preserve all headers as-is |
| Source headers are not numbered | Output headers are not numbered |
| Source numbering has gaps or duplicates | Copy the numbers as they are |
| Section with a single topic | Emit a single chunk |
| Empty input | Return error message |
| Very short input | Return minimal summary maintaining structure |

# Verification

- [ ] Output word count is close to `<TARGET_WORDS>` (within 10%)
- [ ] Every kept header matches the source: same level, text, number, and order
  - E.g., compare the lines starting with `#` in the input and in the output,
    ignoring fenced code blocks
- [ ] Headers removed only if deeper than `<MAX_HEADER_LEV>`
- [ ] All key information extracted into bullet points
- [ ] Every bullet sits under a `* <TITLE>` chunk title
- [ ] Chunk titles are 2-6 word noun phrases, in sentence case, unnumbered
- [ ] Quotes, cross-references, and rhetorical filler are dropped
- [ ] Text wrapped at 85 columns
- [ ] File written successfully
- [ ] User can ask follow-up questions
