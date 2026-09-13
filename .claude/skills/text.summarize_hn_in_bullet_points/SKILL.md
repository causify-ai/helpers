---
description: Summarize a Hacker News discussion on a topic in bullet points
model: haiku
---

# Goal
- Summarize a Hacker News discussion for a given topic
- Follow the bullet point formatting rules in `.claude/skills/text.rules.md`

# Workflow

## Read the Input
- Given a pointer to a discussion on HackerNews in the form of a URL
  - E.g., `https://news.ycombinator.com/item?id=47743628`

## Summarize the Article
- Summarize the main article in 5 bullet points
  ```markdown
  # The peril of laziness lost
  - ...
  - ...
  ```

## Summarize the Comments
- Analyze the Hacker News comment section for the linked article

- From all comments, summarize the 5 most interesting ones based on the
  following criteria:
  - Thought-provoking or insightful
  - Presents a unique perspective or uncommon knowledge
  - Sparks discussion or debate
  - Technically informative or educational
  - Controversial but well-argued
  - Do not print the name of the commenter

- Avoid selecting comments that are:
  - Simple jokes or memes
  - Very short reactions
  - Repetitive or low-effort

## Write the Output
- Do not output any comment on screen
- Output the result in a file `hn.txt` without bold or other markdown formatting
- Run the command:
  ```bash
  > lint_text.py -i hn.txt
  ```
- Run the command:
  ```bash
  > cat hn.txt
  ```

# Verification
- [ ] Confirm `hn.txt` was created and contains no bold or markdown formatting
- [ ] Confirm `lint_text.py -i hn.txt` completed without errors
