---
description: Find and merge redundant or highly overlapping research ideas
model: haiku
---

# Goal
- Find research ideas in `research/ideas/*.md` that are redundant or highly
  overlapping, and merge them on user confirmation

# Workflow

## Step 1: Read the Existing Ideas
- Read `research/ideas/README.md`
- Read the template `research/ideas/template.research_idea.md`
- Read the research ideas under `research/ideas/*.md`

## Step 2: Find Redundant Ideas
- Find the ideas that are redundant or highly overlapping
- Propose which files could be merged, and into which target file

## Step 3: Wait for the User
- Wait for the user to confirm the merge plan before changing any file

## Step 4: Merge the Ideas
- Merge the confirmed ideas into one file using the template
  `research/ideas/template.research_idea.md`
- Keep the file with the more complete specs (higher `Complete Specs`) as the
  target, and fold unique content from the other file(s) into it
- Delete the file(s) that were merged away

# Conventions
- Follow `.claude/skills/research_idea.rules.md`

# Constraints
- Never merge or delete files without explicit user confirmation of the plan
- Do not drop information: if two ideas differ, keep the union of their
  content, not just one side

# Examples
- See `.claude/skills/research_idea.rules.md` `# Examples` for a fully
  formatted research idea

# Verification
- [ ] Merge plan was confirmed by the user before any file was changed
- [ ] The merged file follows `research/ideas/template.research_idea.md`
- [ ] No unique content from the merged-away file(s) was lost
- [ ] The merged-away file(s) were deleted
