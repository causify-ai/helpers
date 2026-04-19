This document contains conventions and rules to create agentic skills.

# Topic

- All skills should refer to a specific "topic"

- You can find the topics running a command like
  ```
  > find .claude/skills -name "*.md" | sed 's|.claude/skills/||; s|\..*||' | sort | uniq
  ```

## Example of topics

bash
blog
book
coding
coding_qa
cxo_slides
demo
docker
git
github
graphviz
gws
markdown
notebook
paper
readme
skill
slides
testing
text
tikz
tutorials
X_in_60_min

## Rules file

- Each topic might have a "rules" file, in the format `<topic>.rules.md` that
  contains all the convention for that specific topic

## Do not allow non-existing files
- All references in the skills should be to existing files
- If there is a non-existing reference try to find it
