---
description: Summarize the discussion on Hacker News on a topic
model: haiku
---

- Given a pointer to a discussion on HackerNews in the form of a URL
  - E.g., https://news.ycombinator.com/item?id=47743628

- All the output the text should be structured markdown bullet points following
  the rules in `.claude/skills/text.summarize_in_bullet_points/SKILL.md`

# Step 1: Summarize article
- Summarize the main article in 5 bullet points
  ```
  # The peril of laziness lost
  - ...
  - ...
  ```

# Step 2: Summarize comments
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

# Step 3:
- Do not output any comment on screen
- Output the result in a file `hn.txt` without bold or other markdown formatting,
  but also 
- Run `lint_txt.py -i hn.txt`
- Run `cat hn.txt`
