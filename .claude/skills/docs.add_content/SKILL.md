---
description: Add content to the docs without redundancy and report skipped parts
model: sonnet
---

# Goal

- The user passes, in this order:
  1. The content `<CONTENT>` to add: text, or a path to a file holding the text
  2. Optionally, the target `<TARGET>`: a file in `<DOCS_DIR>` (existing or new)
     or a header inside it
- Add the new information in `<CONTENT>` to the right files in `<DOCS_DIR>`
- Never duplicate what the docs already say
- Report every chunk that was redundant, did not fit, or conflicts with the docs

# Conventions

- Follow the rules in
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`
  - `<DOCS_DIR>/documentation_meta/all.writing_docs.how_to_guide.md`, in
    particular `### Convention for file names`, `### Format of each doc`, and
    `### Do not add redundancy`
  - `<DOCS_DIR>/documentation_meta/all.diataxis.explanation.md` to pick the doc type
    (`.tutorial.md`, `.how_to_guide.md`, `.reference.md`, `.explanation.md`)
- Match the style, tone, and header structure of the file being edited

# Workflow

## Resolve the docs dir

- Go to the root of the Git work tree
  ```bash
  > cd $(git rev-parse --show-toplevel)
  ```
- Set `<DOCS_DIR>`
  - If `helpers_root` is a submodule of this repo, use `helpers_root/docs`
    - Check with
      ```bash
      > git config --file .gitmodules --get-regexp 'submodule\..*\.path' | grep -w helpers_root
      ```
  - Otherwise use `docs`
    - This is the case when the repo is `helpers` itself
- Check that `<DOCS_DIR>` exists, otherwise STOP and tell the user

## Read the content

- If `<CONTENT>` is a path, read the file and never modify or delete it
- Split `<CONTENT>` into chunks, where each chunk states one idea, fact, rule, or
  procedure
  - Keep the examples attached to the chunk they illustrate
  - Drop pure filler (greetings, meta comments such as "add this to the docs")

## Survey the docs

- Read `<DOCS_DIR>/README.md` to learn the directory structure and file naming
- List the doc files
  ```bash
  > find <DOCS_DIR> -name "*.md" | sort
  ```
- For each chunk, search for its key terms, synonyms, tool names, and commands
  ```bash
  > rg -i "<TERM>" <DOCS_DIR> --glob "*.md"
  ```
- Read in full every file that matches, or whose name or headers match the topic
  of the chunk
  - Do not decide on redundancy from the file name or a grep hit alone

## Classify each chunk

- Assign exactly one class to each chunk
  - **Redundant**: a doc already says the same thing, even if the words differ
    - Report the file, the header, and the line of the existing statement
    - Add nothing
  - **Partially redundant**: a doc covers part of the chunk
    - Add only the missing part, in the file that holds the covered part
    - Report which part was already there
  - **Conflicts**: the chunk contradicts an existing statement
    - Do not edit and do not pick a winner
    - Report both statements with file and header, and ask the user which is right
  - **Does not fit**: no file in `<DOCS_DIR>` is the right home
    - Typical reasons
      - The chunk is code-level detail that belongs in a docstring or comment
      - The chunk is a rule for AI agents and belongs in `.claude/skills/*.rules.md`
        (see `.claude/skills/rules.add/SKILL.md`)
      - The chunk is a blog idea, a research idea, or a TODO
      - The chunk is a different doc type than every candidate file (e.g., a
        step-by-step procedure with only `.explanation.md` files on the topic)
      - The chunk is a summary of an external page (the docs link to the web, they
        do not summarize it)
      - The chunk is too vague or ephemeral to document (dates, versions, status)
    - Report the reason and the better home, if known
    - If the chunk is a coherent new topic with no home, propose a new file name
      `<DOCS_DIR>/<COMPONENT>/<AUDIENCE>.<TOPIC>.<DIATAXIS_TAG>.md`
      - Create the file only if `<TARGET>` names it
  - **New and fits**: no doc covers it and a file is the right home
    - Add it as described below

## Choose the placement

- If `<TARGET>` was passed, use it, but still apply the classes above
  - If `<TARGET>` is a poor home for a chunk, report the chunk as **Does not fit**
    instead of forcing it in
- Otherwise rank the candidate files by
  - Match of the topic with the file name and headers
  - Match of the Diataxis type of the chunk with the file tag
  - Directory (see the directory descriptions in `<DOCS_DIR>/README.md`)
- If one file is a clear winner, use it
- If two or more files are equally good, or the right header in the file is unclear,
  STOP and ask the user instead of guessing
- Pick the header
  - Put the chunk under the existing header it extends
  - Add a new header only when no header covers it, at the same level as its
    siblings and in the same order logic as the file (e.g., alphabetical or by
    workflow stage)

## Write the content

- Rewrite each chunk in the style of the target file
  - Use bullets, imperative mood, active voice, one idea per bullet
  - Reuse the terms the target file already uses for the same concept
  - Capitalize the headings
  - Wrap lines at the width used by the file
- Add a Good / Bad example only if the target file does that for similar rules
- Do not reorder, reword, or delete existing text in the file
- Do not edit the `## Last review` tag since it records a human review
- If the file has a `<!-- toc -->` block and a header was added, update the TOC
- Run the lint skill on each edited file, see `.claude/commands/lint.md`

## Report

- Never commit or stage the changes
- Report in bullets with these sections, omitting the empty ones
  - **Added**: chunk summary, file, header
  - **Partially redundant**: chunk summary, what was already covered and where,
    what was added
  - **Redundant**: chunk summary, file, header of the existing statement
  - **Conflicts**: chunk summary, both statements with file and header, question
    for the user
  - **Does not fit**: chunk summary, reason, suggested home or new file name
  - **Questions**: placement decisions left to the user
- Quote the shortest passage that proves a chunk is redundant or conflicts

# Constraints

- Never add a chunk that a doc already states
- Never create a new file unless the user named it in `<TARGET>`
- Never edit files outside `<DOCS_DIR>`, except the TOC and the lint fixes inside
  the edited files
- Never guess a target when several files fit equally well
- Never commit without user permission

# Examples

- **Bad** (adds a duplicate: the guide already says it)
  ```
  Added to docs/tools/git/all.git.how_to_guide.md:
  - Open several branches for one task when the work splits into chunks
  ```
- **Good** (reports the overlap and adds nothing)
  ```
  Redundant:
  - "Open several branches for one task when the work splits into chunks":
    already in `docs/tools/git/all.git.how_to_guide.md`,
    `#### Always work in a branch` ("It is ok to open multiple branches for a
    given task if needed")
  ```
- **Bad** (forces a code-level detail into a user guide)
  ```
  Added to docs/tools/git/all.git.how_to_guide.md:
  - `_parse_branch()` returns `None` when the name has no task number
  ```
- **Good** (reports it as not fitting)
  ```
  Does not fit:
  - "`_parse_branch()` returns `None` when the name has no task number": code
    detail, move it to the docstring of `_parse_branch()`
  ```

# Verification

- [ ] Confirm `<DOCS_DIR>` was resolved from the submodule check and not assumed
- [ ] Confirm every chunk of `<CONTENT>` appears in exactly one section of the
      report
- [ ] Confirm each **Redundant** claim cites a file and header that exist and say
      the same thing
- [ ] Confirm no added bullet repeats a statement elsewhere in `<DOCS_DIR>` (rerun
      the `rg` search on the key terms of each added bullet)
- [ ] Confirm each added chunk sits under a header that fits its topic and the
      Diataxis type of the file
- [ ] Confirm no existing text was changed or removed, with `git diff`
- [ ] Confirm the `## Last review` tag is unchanged
- [ ] Confirm the edited files follow `.claude/skills/markdown.rules.md` and
      `.claude/skills/text.rules.md`
- [ ] Confirm nothing was staged or committed
