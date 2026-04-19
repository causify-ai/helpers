---
description: Write a tutorial for the slides
---

Act as a senior academic researcher in Data Science, Machine Learning, Artificial
Intelligence, and Computer Science.

The target audience is data scientists and ML practitioners

# Step 1
- Read the passed file $FILE

# Step 2
- Come up with 2 or 3 Python library that can be used to implement in Python
  some of the concepts and analysis explained in the slides
- Ignore general purpose libraries (such as pandas, numpy), but focus on specific
  ones that are relevant and specific of the content in $FILE
- Annotate at the beginning of $FILE the related packages
  ```
  // Packages:
  // - CausalNex
  //   - Python library for causal modeling (cause–effect, not just correlation)
  //   - Learns causal graphs, supports inference & interventions
  //   - Used for decision-making, risk analysis, and explainable AI
  ```

# Step 3
- Add a high level description of the tutorial at the beginning of $FILE
  ```
  // Tutorial Outline
  // - Load data and explore conditional dependencies
  // - Run PC/GES algorithms comparing outputs
  // - Validate with refutation tests (placebo, random treatment)
  // - Incorporate domain constraints (forbidden/required edges, temporal ordering)
  // - Handle latent confounders with FCI
  // - Visualize and compare algorithm results
  ```

# Step 3
- Suggest steps for the tutorial that can help the understanding of the content
  in each slide
- Add comments in the $FILE describing what can be done with the packages from
  step 2 to 
  - Use bullet points like
    ```
    // Tutorial:
    // - Use `CausalNex` to build domain knowledge graphs and define constraints
    // - Enforce temporal ordering by restricting edges between time layers
    // - Mark forbidden/required edges in algorithm parameters
    // - Compare discovery with vs. without constraints to measure impact
    ```
- Follow the rules in `helpers_root/.claude/skills/notebook.script.create/SKILL.md`
