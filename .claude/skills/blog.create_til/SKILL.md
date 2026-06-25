---
description: Write a "today I learned" blog
model: haiku
---

# Goal
Write a concise, engaging, and educational "Today I Learned" (TIL) blog post
about the topic / content from the user

## Structure
1. Title
2. What I Learned
3. Why It Matters
4. Example / Demonstration
5. Key Takeaways
6. References or Further Reading

- The post should:
  - Start with a short introduction explaining what I learned and why it
    caught my attention
  - Clearly explain the concept in simple language suitable for software
    engineers, tech enthusiasts, or curious readers
  - Include a practical example, code snippet, or real-world use case where
    appropriate
  - Highlight any surprising insights, common misconceptions, or lessons
    learned during the discovery process
  - End with key takeaways and actionable advice for readers who want to
    explore the topic further

## Use Front Matter and TLDR
- Add front matter as in `.claude/skills/blog.rules.md` `## Front Matter (YAML)`
- Add TL;DR as in `.claude/skills/blog.rules.md` `## TL;DR Section`

## Tone
- Conversational and reflective
- Technical but accessible
- Curious and educational

## Length
- Keep the post between 500–1000 words and focus on clarity, practical value, and
  genuine learning rather than exhaustive coverage

## Formatting Rules
- Follow the rules in:
  - `.claude/skills/blog.rules.md`
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Beautify
- Run a command to format the code for proper visualization
  ```
  > prettier --tab-width 4 <FILE> -w
  ```
