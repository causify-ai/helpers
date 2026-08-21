---
description: Split a raw idea dump file into titled ideas and create idea files
model: sonnet
---

# Goal
- Given a file `<FILE>` containing research ideas in a very early, unstructured
  form (loose fragments, one-liners, mixed bullets), add a `## <Title>` header
  above each distinct idea, then, once the user approves, create one
  template-formatted research idea file per idea

# Workflow

## Step 1: Read the Inputs
- Read `<FILE>`
- Read the template `.claude/templates/research_idea.template.md`
- Read `.claude/skills/research_idea.rules.md` for file naming and directory
  conventions
- Read the file names under `research/ideas/*.md` to know which ideas already
  exist

## Step 2: Title and Group the Fragments
- Split `<FILE>` into distinct ideas
  - Merge fragments that clearly describe the same idea into one group; it is
    fine to reorder or combine fragments that belong together
  - Keep fragments that are already distinct ideas separate, even if short
- Add a `## <Title>` header directly above each idea's raw content
  - `<Title>` is a short noun phrase (3-8 words) that names the idea, in the
    same style as existing file names, e.g. `Hierarchical Training`,
    `Compression as Proxy for Understanding`
  - If a fragment already has a `##` header, keep or refine that title instead
    of adding a duplicate one
- Do not summarize, expand, or fabricate content; only add headers and move
  fragments next to the other fragments of the same idea
- Flag (do not silently drop) any fragment whose idea already exists as a file
  under `research/ideas/*.md`, so the user can decide whether to skip it
- Write the titled, grouped result back into `<FILE>`

## Step 3: Wait for the User
- Show the user the list of proposed titles and which fragments were grouped
  under each
- Wait for the user to review and approve `<FILE>` before creating any new
  idea file
- If the user requests different titles or groupings, apply the changes and
  present the file again

## Step 4: Create One Idea File per Approved Idea
- For each approved `## <Title>` section, create
  `research/ideas/draft.<Idea_Name>.md`, per `.claude/skills/research_idea.rules.md`
  `## Status Prefixes`
  - `<Idea_Name>` is `<Title>` in Title_Case_With_Underscores, matching
    existing file names (e.g. `Hierarchical Training` -> `Hierarchical_Training`)
- Seed the new file with the section's raw content as the seed for `Core Idea`
- Follow the template `.claude/templates/research_idea.template.md` and the
  workflow in `.claude/skills/research_idea.format/SKILL.md` to map the seeded
  content onto the template's sections
- Skip creating a file for any idea the user chose to skip in Step 3

## Step 5: Clean Up the Source File
- Ask the user whether to remove, from `<FILE>`, the sections that were split
  out into new idea files (or delete `<FILE>` if every section was split out)
- Only remove a section once its new idea file exists and the user confirms
  its content was fully captured

# Conventions
- Follow `.claude/skills/research_idea.rules.md`

# Constraints
- Do not create any new idea file before the user approves the titled,
  grouped `<FILE>` from Step 2
- Do not fabricate content when titling or grouping fragments in Step 2; only
  add headers and reorganize the existing raw text
- Do not remove content from `<FILE>` without user confirmation, per Step 5

# Examples
- `research/ideas/new_ideas.md`: a raw idea dump file, the typical `<FILE>`
  input for this skill
- See `.claude/skills/research_idea.rules.md` `# Examples` for a fully
  formatted research idea

# Verification
- [ ] Every fragment in `<FILE>` is grouped under a `## <Title>` header
- [ ] The user approved the titled, grouped `<FILE>` before any new idea file
      was created
- [ ] Each new idea file follows `.claude/templates/research_idea.template.md`
- [ ] Each new idea file is named `research/ideas/draft.<Idea_Name>.md` per
      `.claude/skills/research_idea.rules.md` `## Status Prefixes`
- [ ] No content from `<FILE>` was fabricated or lost while splitting
