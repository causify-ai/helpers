---
description: Extract the most interesting ideas from the text
model: opus
---

# Goal
- You are an expert reader and critical thinker
- Print each step before executing it

# Workflow

## Read the Given Text
- Analyze the text below and extract the most thought-provoking, surprising, and
  intellectually interesting ideas

- Focus on:
  - Ideas that challenge common assumptions or conventional wisdom
  - Concepts that are counterintuitive, paradoxical, or unexpected
  - Insights with deep implications (philosophical, scientific, social, or
    psychological)
  - Particularly elegant, novel, or powerful ways of explaining something
  - Any hidden patterns, connections, or underlying themes

## Extract Ideas
- For each idea create bullet points using following
  `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`

- Create an header 1 with a short summary
  ```markdown
  # <ID>. Creative Destruction as Generative Force
  ```
- State the idea clearly and concisely
  ```markdown
  **Idea**: ...
  ```
- Explain why it is interesting, surprising, or important
  ```markdown
  **Why it is interesting**: ...
  ```
- (Optional) Add a short reflection or question that deepens the insight
  ```markdown
  **Reflections**: ...
  ```

- E.g.,
  ```markdown
  # 1. Pre-training as "Crappy Evolution"
  - **Idea**
    - ...
    - ...
  - **Why it's interesting**:
    - Pre-training LLMs on internet data creates a practical shortcut to
      biological evolution: encoding vast human knowledge into neural weights
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

- Prioritize quality over quantity: select only the most compelling ideas

## Save the Output
- Save the output in `<FILE>.ideas.md`
- Run `lint_text.py -i` to format `<FILE>.ideas.md`

# Verification
- [ ] Confirm `<FILE>.ideas.md` was created
- [ ] Confirm `lint_text.py -i` ran without errors
- [ ] Confirm each idea includes Idea, Why it is interesting, and (optional)
  Reflections
