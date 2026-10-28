# Where to Add Material

- This document explains where to put new material about how we work with AI agents,
  so that each fact is written once

## Motivation

- New material can go in three places:
  - Blogs
  - How-to guides for humans
  - Skills
- The same fact often ends up in more than one place
  - E.g., the branch naming pattern, or the table of `auto_task` skills
- Problems caused by copies:
  - Copies drift: one is updated and the others go stale
  - An agent that reads a stale copy follows it
  - An author does not know where a new fact belongs
- Goal: a rule that tells an author where a fact goes, and keeps all the other
  places pointing to it

## Core Concepts

### The Three Places

- Each place has one audience and one job:

  | Place        | Audience      | Owns                                   | Never holds                         |
  | :----------- | :------------ | :------------------------------------- | :---------------------------------- |
  | Skill        | Agent         | How to do one step, conventions        | Why the flow exists, order of steps |
  | How-to guide | Human         | Order of steps, which skill, gates     | Step details, copies of skill text  |
  | Blog         | Public reader | Story, opinion, trade-offs, lessons    | Anything a reader must follow       |

- Where each place lives:
  - Skills: `.claude/skills/`
  - How-to guides: `docs/<DIR>/all.<topic>.how_to_guide.md`
  - Blogs: `website/docs/blog/posts/`
- A skill place has two kinds of files
  - `.claude/skills/<TOPIC>.<ACTION>/SKILL.md`: the steps of one task
  - `.claude/skills/<TOPIC>.rules.md`: the conventions shared by the skills of one
    topic
  - See `.claude/skills/skill.rules.md` for the authoring conventions
- Relation to Diataxis (see `docs/documentation_meta/all.diataxis.explanation.md`)
  - A how-to guide is a Diataxis how-to guide: goal oriented, for a human
  - A skill is an instruction for an agent: it is outside Diataxis
  - A blog is narrative: it is outside Diataxis

### One Home per Fact

- A fact is anything a reader could copy:
  - A naming pattern
  - A convention
  - The order of steps
  - A command and its options
  - A threshold, e.g., the maximum size of a PR
  - A decision
- Each fact has exactly one home
- Every other place links to the home and does not restate the fact

### Direction of Links

- Levels, from the most precise to the most narrative: skill, how-to guide, blog
- Write a fact at the lowest level that needs it
- Links go only from a higher level to a lower one
  - A blog links to a how-to guide
  - A how-to guide links to a skill or a rule file
- A skill or a how-to guide never depends on a blog

## How It Works

### Find the Home

- Ask these questions in order and stop at the first yes:
  1. Is it a convention shared by several skills of a topic, e.g., a naming
     pattern or a format?
     - Home: `.claude/skills/<TOPIC>.rules.md`
  2. Is it a procedure an agent runs for one task?
     - Home: `.claude/skills/<TOPIC>.<ACTION>/SKILL.md`
  3. Is it the order of steps, the choice of skill, or a point where a human must
     decide?
     - Home: a how-to guide in `docs/`
  4. Is it a story, an opinion, a trade-off, or a lesson learned?
     - Home: a blog post
     - Link to the how-to guide for anything the reader must follow
- If the answer to 1 to 3 is "both", split the fact
  - The what goes in the lower level
  - The when and why go in the level above, with a link

### Before Writing

- Search for an existing home before adding text
  - `rig --rule "<keyword>"` finds a convention in the rule files
  - `mdm skill list` and `mdm skill describe <name>` find a skill
  - `rig "<keyword>" docs/` finds a how-to guide
- If a home exists, extend it or link to it
- If no home exists, create the new text at the level chosen above
- Use `/docs.add_content` to add text to a how-to guide
  - It avoids redundancy and reports the parts it skipped
- Use `/text.merge_content_into` to move content into a blog
- Use `/rules.add` to add a convention to the rule files

### Fix an Existing Duplicate

- Keep the copy at the lowest level
- Replace each other copy with a link
  - Use `/text.merge_files` to move content without redundancy
- Check that no information was lost in the move
- Run `/skill.check_refs` when the change touches skill files

### Reference Files by Repo Path

- Write every file reference as the path from the repo root, not the bare file name
  - **Good**: `docs/documentation_meta/all.where_to_add_material.explanation.md`
  - **Bad**: `all.where_to_add_material.explanation.md`
- A path from the repo root works from any file and can be found with `rig`

### Examples

- Branch naming pattern of an issue
  - Home: `.claude/skills/auto_task.rules.md`
  - How-to guides and blogs link to it
- Order "criticize the plan, then execute", and the choice of execution mode
  - Home: `docs/tools/ai/all.auto_task.how_to_guide.md`
- Table of skills for the whole flow, from idea to merged PR
  - Belongs in: `docs/planning/all.plan_work.how_to_guide.md`
- What `/github.get_pr_to_pass_ci_tests` does
  - Home: `.claude/skills/github.get_pr_to_pass_ci_tests/SKILL.md`
  - A how-to guide only names the skill and says when to run it
- The size cap of a PR and the reason for it
  - How-to guide: states the number
  - Blog: tells what went wrong without a cap, and links to the number

## Design Rationale

- Do not repeat yourself
  - `docs/planning/all.plan_work.how_to_guide.md` already says to point to a doc
    and not copy it
- Agents read skills and rules, so they must be short, exact, and consistent
  - A contradiction between two copies makes the agent choose at random
- Humans need the order of steps and the judgment calls
  - Step details in a how-to guide go stale when the skill changes
- Blogs are dated and narrative, so they age fastest
  - Nothing that must stay correct depends on a blog
- One direction of links gives one place to update
  - It also avoids two docs that point to each other and drift apart

## Tradeoffs and Alternatives

### Current Approach

- One home per fact, links everywhere else
- Advantages:
  - No drift between copies
  - A change touches one file
  - A clear answer to "where do I add this?"
- Drawbacks:
  - A reader follows links to get the full picture
  - A blog is less self-contained
  - Authors need discipline to link and not copy

### Alternative: Self-Contained Copies

- Each place repeats what its reader needs
- Advantages:
  - Each reader gets the whole story in one file
- Drawbacks:
  - Every change must be made in up to three files
  - Copies drift, and nobody knows which one is right

### Alternative: Generate the Upper Levels

- Generate how-to guides and blogs from the skills
- Advantages:
  - No drift by construction
- Drawbacks:
  - Generated text loses the narrative and the judgment
  - Needs tooling that does not exist yet

## Related Docs

- `docs/documentation_meta/all.diataxis.explanation.md`: the four modes of
  documentation
- `docs/documentation_meta/all.writing_docs.how_to_guide.md`: conventions for
  writing docs
- `docs/planning/all.plan_work.how_to_guide.md`: how we plan and track project work
- `docs/tools/ai/all.ai_workflows.how_to_guide.md`: topics, skills, and rules
- `docs/tools/ai/all.auto_task.how_to_guide.md`: from task list to merged PR
- `.claude/skills/skill.rules.md`: conventions for writing skills
