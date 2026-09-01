---
description: Fix errors slides without changing their structure
model: haiku
---

# Goal
- Given a file with slides or user content, fix errors and imprecisions in the
  slides without changing their structure

# Workflow

## Read the Rules
- Read `.claude/skills/slides.rules.md` and follow strictly the conventions and
  rules
- A slide title is prepended with `*` and has hierarchical bullets
  - E.g.,
    ```
    * How Can a Node Be Influenced by Its Children?

    - A **descendant can influence its ancestor** indirectly through _"explaining
      away"_
      - Evidence about the descendant can change what you believe about the
        ancestor through dependent paths
      - Information flows both ways in Bayesian networks
    ```

## Leave Structure Unchanged
- Do not change the structure of the text (e.g., in terms of title, bullet structure,
  div fenced blocks)
- Maintain the content of the existing text
- Do not introduce new formatting violations while fixing grammar (e.g.,
  punctuation is owned by `.claude/skills/slides.fix_formatting/SKILL.md`);
  follow `slides.rules.md` as read in Step 1

## Fix Mistakes
- Fix English grammar
- Fix any conceptual mistake only if you are sure about the correction
