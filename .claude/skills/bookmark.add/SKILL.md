---
description: Find the research idea or blog file related to given links and add a TODO
---

# Goal
- Given one or more links `<LINKS>`, find which file(s) among the following are
  related to each link, and add a TODO to the most related file:
  - `research/ideas/*.md`
  - `website/docs/blog/posts/*.md`
  ```text
  // TODO(gp): incorporate the link <LINK> to <TOPIC>
  ```

# Workflow

## Step 1: Collect Material
- Read the title / content of each link in `<LINKS>` (use `WebFetch` if the
  URL alone is not descriptive enough to judge topic)
- List all candidate files:
  - `research/ideas/*.md`
  - `website/docs/blog/posts/*.md`

## Step 2: Match Links to Files
- For each link, compare its topic against the content of each candidate file
  (title, headers, first paragraph) and rank candidates by relevance
- Pick the single best-matching file for each link
  - If several files are close in relevance, list them and ask the user
    which one to use
  - If no file is a plausible match (topic not covered anywhere), do not
    force a match: report this to the user instead of guessing

## Step 3: Add the TODO
- In the matched file, add one line:
  ```text
  // TODO(gp): incorporate the link <LINK> to <TOPIC>
  ```
  where `<TOPIC>` is a short (< 15 words) description of what part of the
  link is relevant (e.g., a technique, a result, a quote)
- Placement:
  - If the file already has a top-of-file `// TODO(gp): ...` block, add the
    new TODO as an adjacent line in that block
  - Otherwise, add it near the section of the file the link is most related
    to (e.g., right above the relevant bullet point or paragraph)
- Do not change any other content of the file
- If multiple links map to the same file, add one TODO line per link

## Step 4: Report
- Print, for each link, which file it was added to and the exact TODO line
  that was inserted
- For any link that could not be matched, report that explicitly instead of
  silently skipping it
