---
description: Propose and add visuals for the slides
model: haiku
---

# Goal
- Given a markdown file with slides or slides from the user, propose visuals
  (e.g., diagrams, pictures, tables)

# Workflow

## Read Related Rules
- Read the file or the provided text
- Read `.claude/skills/slides.rules.md` for the slides conventions and rules
- Read `.claude/skills/visuals.rules.md` to understand the rules for the visuals

## Propose a Visual for Each Slide
- If a slide doesn't contain a visual element, consider what can be used to
  illustrate the concepts visually
- E.g., from `## Types of Illustrations` in `.claude/skills/visuals.rules.md`
  - Table
  - Mermaid graph
  - Graphviz diagram
  - TikZ diagram
  - Images
  - Website screenshots

## Output example

```
Slide 1: "A Map of Machine Learning"
- Current: Has mermaid mindmap ✓
- Assessment: Excellent visual already present. Keep as-is.

Slide 2: "Machine Learning Paradigms"
- Proposed: Comparison table showing Paradigm name, Question asked, and Key characteristic
  - Format: Use styled-table for consistency
  - Shows supervised vs unsupervised vs RL vs active learning side-by-side
  - Helps learners see the contrasts quickly

Slide 3: "Machine Learning Theory"
- Current: Text-only explanation of 4 theoretical foundations
- Proposed: Graphviz diagram showing theoretical frameworks
  - Show how VC theory, Bias-variance decomposition, MDL, and Bayesian approach relate
  - Color by category: theoretical foundations
  - Add connections showing dependencies/relationships

Slide 4: "Machine Learning Models"
- Current: Text-only list of model variants
- Proposed: Taxonomy diagram (Graphviz or TikZ)
  - Organize models by key distinctions: parametric vs non-parametric, linear vs non-linear
  - Show example models in each category
  - Helps learners understand the model space structure

Slide 5: "Machine Learning Techniques"
- Current: Text-only list of pipeline stages
- Proposed: ML Pipeline flowchart (Graphviz)
  - Show the stages: Input Processing → Model Building → Performance Evaluation → Diagnostic → Regularization → Aggregation
  - Color stages by function (data preparation, model, evaluation, improvement)
  - Include key techniques under each stage
  - This is the most impactful addition for learning

Slide 6: "Some machine Learning Adages"
- Current: Collection of quotes with attributions
- Assessment: Text-based content is appropriate here. No visual needed.

│ Slide │            Change             │     Type      │  Impact   │
---------------------------------------------------------------------
│ 1     │ Keep existing                 │ -             │ ✓ Good    │
│ 2     │ Add paradigm comparison table │ Table         │ High      │
│ 3     │ Add theory framework diagram  │ Graphviz      │ Medium    │
│ 4     │ Add model taxonomy diagram    │ Graphviz/TikZ │ High      │
│ 5     │ Add ML pipeline flowchart     │ Graphviz      │ Very High │
│ 6     │ Keep as-is                    │ -             │ ✓ Good    │
```

## Save the Plan
- Save the plan to a file `plan.slides.add_visuals.md`

## Ask User to Confirm
- Make numbered list of proposed changes for the user
- Once user confirms changes, perform the changes

## Constraints
- Maintain the structure of the text and keep the content of the existing text
