---
description: Summarize the discussion on Hacker News on a topic
model: haiku
---

For bullet point formatting rules, refer to `@.claude/skills/text.rules.bullet_points`

## Input

- Given a pointer to a discussion on HackerNews in the form of a URL
  - E.g., https://news.ycombinator.com/item?id=47743628

## Step 1: Summarize article

- Summarize the main article in 5 bullet points
  ```
  # The peril of laziness lost
  - ...
  - ...
  ```

## Step 2: Summarize comments

- Analyze the Hacker News comment section for the linked article.

- From all comments, summarize the 5 most interesting ones based on the following
  criteria:
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

## Step 3: Output

- Do not output any comment on screen
- Output the result in a file `hn.txt` without bold or other markdown formatting
- Run `lint_txt.py -i hn.txt`
- Run `cat hn.txt`
