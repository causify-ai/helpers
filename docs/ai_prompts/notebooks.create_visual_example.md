I want to create an example of an interactive visualization in a Jupyter notebook
with ipywidget to understand the passed concept.

Execute all the steps, unless the user explicitly says to execute in steps
- In that case, execute one step at the time and ask the user if you can proceed
  with the second step

# Step 1)
- Given the problem
  - Find, print, and read the Python code paired to the notebook
    - E.g., `./msml610/tutorials/Lesson94-Information_Theory.py`
  - Find, print, and read the `utils_*.py` file
    - E.g., `./msml610/tutorials/utils_Lesson94_Information_Theory.py`
  - Find notes in the lecture notes
    - E.g., `msml610/lectures_source/Lesson94.Refresher_information_theory.txt`

- Make a proposal and explain in short bullet points what can be done and why
  should be done
- The goals are:
  - strong intuition
  - visual explanation
  - interactivity where user can change the important variables and see the results
    immediately

- Do not write any code

- Example
  ```
  ## Concept to explain
  - Build an interactive intuition building examples for joint entropy

  ## Concept
  - Create an interactive visualization where the user controls the joint
    probability distribution of two discrete random variables X and Y, and sees
    entropy values and visuals update live.

  ## What the user sees
  This lets people feel how joint entropy changes as:
  - variables become dependent / independent
  - mass concentrates or spreads
  - uncertainty shifts between marginals and joint

  Visuals (all update live)
  - Heatmap of the joint distribution P(X,Y)
  - Bar charts of marginals P(X) and P(Y)
  - Numbers updating live:
    - H(X)
    - H(Y)
    - H(X,Y)

  Controls
    - Sliders that control:
    - Correlation / dependence strength
    - Noise level
    - Distribution skew

  ## Setup

  Two binary random variables:

  - \( X \in \{0,1\} \)
  - \( Y \in \{0,1\} \)

  Use a single slider:

  - **dependence** \( \in [0, 1] \)

  ## How the Slider Works (Intuition)

  - **dependence = 1.0**
    - \( Y = X \) (perfect correlation)
    - Low joint entropy

  - **dependence = 0.0**
    - \( X \) and \( Y \) are independent
    - Maximum joint entropy

  - **In between**
    - Partial structure
    - Partial uncertainty

  ## Visual Intuition Payoff

  Users will see:

  - The joint distribution heatmap collapse onto the diagonal
  - Entropy values change smoothly as the slider moves
  - Joint entropy increase faster than marginal entropies
  ```

# Step 2)
- Propose an implementation in few bullet points
  - E.g., what are the functions, where are they stored
- Ask all clarifying questions if things are not clear

# Step 3)
- Follow the instructions in `docs/ai_prompts/notebooks.format_rules.md`
