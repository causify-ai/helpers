Change cell3_interactive_sample_generator in
.claude/templates/interactive_notebook.template.ipynb to follow the idiom like
cell1_plot_true_target_function in
msml610/tutorials/L05_statistical_learning/L05_02_02_overfitting.ipynb

The code in .claude/templates/interactive_notebook.template.ipynb and its
_utils.py library should be a template

- Use the special widgets
- Use multiple plots aligned horizontally, that react to changes to the widgets
- Add a comment bar using yellow background

If needed, update the rules in .claude/skills/interactive_notebook.rules.md

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`
