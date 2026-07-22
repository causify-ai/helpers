---
description: Create a set of ideas for Jupyter notebooks to explore ideas and concepts
model: opus
---

# Goal

- Given some technical material provided from the user, come up with
  5 ideas of interactive Jupyter notebooks that teaches the concepts
  in the materials using
  - Visualization
  - Interaction
  - Exploration

- When possible suggest and use "famous" examples, data, experiments, and
  problems related to the provided material

- The output is a file `notebook_ideas.<tag>.md` markdown file that
  describe the ideas

# Template
- For each ideas use a template like
  ```
  ## 1. <Title>

  ### Goal
  Students gain intuitive understanding of ... by building and
  analyzing ... and exploring the relationship between ...

  ### Learning Objectives
  - Understand ...
  - Visualize ...

  ### Core Concepts
  - ...

  ### Key Packages
  - **package**: ...

  (Do not cite the standard packages like pandas, scipy, numpy, matplotlib)

  ### Learning Activities
  - Build ...
  - Generate ...
  - Test ...
  - Explore ...
  - Measure ...
  - Interactive ...
  ```

## Example

- For a query like "Explain propositional logic":
  ```
  ## 1. Interactive Logic Explorer

  ### Goal
  - Students will:
    - Gain intuitive understanding of propositional logic by building and analyzing
      logical formulas, truth tables, and inference rules
    - Explore the relationship between syntax, semantics, and computation.

  ### Learning Objectives
  - Construct propositional formulas and evaluate truth values
  - Enumerate all models and check entailment
  - Understand SAT solving and computational complexity
  - Visualize how expressiveness and tractability trade off

  ### Core Concepts
  - Propositional logic syntax (operators: ¬, ∧, ∨, ⟹, ⟺)
  - Semantics via truth tables and model interpretation
  - Inference rules (Modus Ponens, Modus Tollens, Resolution)
  - Model checking algorithm (sound and complete)
  - Satisfiability and NP-completeness

  ### Key Packages
  - **sympy** — symbolic logic, propositional formula manipulation
  - **python-sat** — SAT solver backends

  ### Learning Activities
  - Build formulas interactively: `(Rain ∧ Cold) ∨ Sunny`
  - Generate and display truth tables for arbitrary formulas
  - Test entailment between two formulas: does KB ⊨ α?
  - Explore inference rules (modus ponens, resolution)
  - Measure SAT solver complexity as # variables increases
  - Interactive "Wumpus World" knowledge base reasoning
  ```

# Conventions
- When writing markdown text follow
  - `.claude/skills/markdown.rules.md`: Markdown formatting rules
  - `.claude/skills/text.rules.md`: Bullet point conventions

# Lint
- After generating the file `notebook_ideas.<tag>.md`
  ```
  > lint_txt.py -i `notebook_ideas.<tag>.md`
  ```
