---
description: Write a blog for a tool in helpers
model: haiku
---

# Goal
- Given a tool `<TOOL>` in `helpers`, write a short blog presenting this
  tool

# Workflow

## Read and Follow the Rules to Write a Blog
- Read context about rules from `.claude/skills/blog.rules.md`

- When writing follow the rules from:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Gather Source Material
- Find the related documentation, such as
  - the source code
    - E.g., `helpers/hcache_simple.py`
  - the testing code
    - E.g., `helpers/test/test_hcache_simple.py`
  - README describing the tool
    - E.g., `docs/tools/helpers/all.hcache_simple.explanation.md`
  - Notebooks and tutorials
    - E.g., `helpers/notebooks/hcache_simple.tutorial.ipynb`

## Write the Blog Text
- The format of the file should follow:
  ```markdown
  # Introduction
  ## What Is ...?
  ## When To Use ...?
  ## When NOT To Use ...?
  # How It Works
  # Real-World Scenarios
  ## Scenario 1: ...
  ## Scenario 2: ...
  # Advanced Features
  ## ...
  # Comparison with Alternatives
  # References
  ## Add references to the files in the repo
  ```

- E.g., for `hcache_simple.py`
  ```markdown
  # Introduction
  ## What Is `hcache_simple`?
  ## The Three Cache Layers
  ## When To Use `hcache_simple`
  ## When NOT To Use `hcache_simple`
  # How It Works
  # Real-World Scenarios
  ## Scenario 1: Caching LLM Calls
  ## Scenario 2: Binary Data Caching with Pickle
  ## Scenario 3: Per-Function Cache Organization
  # Advanced Features
  ## Performance Monitoring
  ## Source-Change Detection
  ## Global Caching Controls
  ## Mock Cache for Testing
  # Comparison with Alternatives
  # References
  ```

## Reference GitHub Files
- When referring to files in the repo follow
  `.claude/skills/blog.rules.md` `## References to GitHub Files`

## Add Visuals
- Add visuals to a blog following `.claude/skills/blog.rules.md` `# Visuals`
  - `## Add Visuals to Blog Posts`: suggestions
  - `## Types of Visuals`: types of visuals (such as mermaid, graphviz, tikz,
    images, website screenshots)

## Write File
- The file should be called like
  `website/docs/blog/posts/draft.in_<INT>_mins.helpers_<TOOL>.md`
  where `<INT>` is how long it will take to read the blog (e.g., 5 mins, 15 mins,
  30 mins) which is a function of the complexity

## Format
- At the end, format the text with
  ```bash
  > website/format_blog.sh <BLOG_FILE>
  ```

# Verification
- [ ] Confirm the file name matches
      `website/docs/blog/posts/draft.in_<INT>_mins.helpers_<TOOL>.md`
- [ ] Confirm the blog follows the section structure in
      `## Write the Blog Text`
- [ ] Confirm `website/format_blog.sh` ran without errors
