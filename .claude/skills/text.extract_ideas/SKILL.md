---
description: Extract the most interesting ideas from the text
---

You are an expert reader and critical thinker.

When execute each step, print each step before it's executed

# Step 1: Read the given text

Analyze the text below and extract the most thought-provoking, surprising, and
intellectually interesting ideas.

Focus on:
- Ideas that challenge common assumptions or conventional wisdom
- Concepts that are counterintuitive, paradoxical, or unexpected
- Insights with deep implications (philosophical, scientific, social, or
  psychological)
- Particularly elegant, novel, or powerful ways of explaining something
- Any hidden patterns, connections, or underlying themes

# Step 2: Extract ideas

For each idea create bullet points using following
`@.claude/skills/markdown.rules.md` and
`@.claude/skills/text.rules.bullet_points.md`

1. Create an header 1 with a short summary
   ```
   # <id>. Creative Destruction as Generative Force
   ```
2. State the idea clearly and concisely
   ```
   **Idea**: ...
   ```
2. Explain why it is interesting, surprising, or important
   ```
   **Why it is interesting**: ...
   ```
3. (Optional) Add a short reflection or question that deepens the insight
   ```
   **Reflections**: ...
   ```

- E.g.,
  ```
  # 1. Pre-training as "Crappy Evolution"
  - **Idea**
    - ...
    - ...
  - **Why it's interesting**:
    - Pre-training LLMs on internet data creates a practical shortcut to
      biological evolution—encoding vast human knowledge into neural weights
    - Not true evolution (doesn't run on biology), but achieves similar
      bootstrapping in weeks instead of millions of years
    - Reframes AI development from "mimicking nature" to "using human cultural
      artifacts as evolutionary substitute"
    - Suggests evolution was finding an algorithm; pre-training is compressing
      knowledge
  - **Reflection**
    - If pre-training is evolution's shortcut, what breaks down in the analogy?
    - Is intelligence from knowledge compression equivalent to intelligence from
      algorithmic discovery?
  ```

Prioritize quality over quantity—select only the most compelling ideas.

# Step 3: Save the output
- Save the output in `<file>.ideas.md`
- Run `lint_txt.py -i` to format `<file>.ideas.md`
