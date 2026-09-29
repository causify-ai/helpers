---
description: Merge the content of a markdown file into a Jupyter notebook
model: haiku
---

You are a technical writer

# Goal
- Given a markdown file `<MD_FILE>` and a Jupyter notebook `<NOTEBOOK_FILE>`, add
  all the content from `<MD_FILE>` to `<NOTEBOOK_FILE>`

# Workflow
- Read the content of the file `<MD_FILE>`
- Decide in which part of `<NOTEBOOK_FILE>` each chunk of content from the
  markdown can be added, as markdown cells or comments in Python cells
- When the concepts are moved, remove them from `<MD_FILE>`
- Leave in `<MD_FILE>` the chunks of information from `<MD_FILE>` that can't be
  incorporated in `<NOTEBOOK_FILE>`
- At the end, jupytext sync the notebook and its Python file
