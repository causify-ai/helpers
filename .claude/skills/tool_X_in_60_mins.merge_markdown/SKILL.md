---
description: Merge the content of a markdown file into a Jupyter notebook
---

You are a technical writer.

Given a markdown file <MD_FILE> and a Jupyter notebook <NOTEBOOK_FILE>, you need
to read the content of the file <MD_FILE>

Your goal is to add all the content from <MD_FILE> to <NOTEBOOK_FILE>

Decide in which part of the <NOTEBOOK_FILE> each chunk of the content from the
markdown can be added as markdown cells or comments in Python cells
- When the concepts are moved, you can remove them from <MD_FILE>

Leave in <MD_FILE> the chunks of information from <MD_FILE> can't be incorporated
in <NOTEBOOK_FILE>

At end you need to jupytext sync the notebook and its Python file
