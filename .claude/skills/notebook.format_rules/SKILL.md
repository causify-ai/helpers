---
description: Format Jupyter notebooks according to conventions including jupytext, cell structure, and widget patterns
---

- You are an expert Python developer.

- I will pass you a Python file paired with Jupyter notebook with jupytext using
  a `py:percent` format
  - E.g., `msml610/tutorials/Lesson94-Information_Theory.py`

# Use Python Style

- For all the Python code you must follow the rules from
  @.claude/skills/coding.format_rules/SKILL.md

# Format of a Jupyter Notebook

- Each notebook has the following format

- The first cell of a notebook is:

  ```python
  %load_ext autoreload
  %autoreload 2

  import logging

  import numpy as np
  import pandas as pd
  import seaborn as sns
  import matplotlib.pyplot as plt

  ut.config_notebook()

  # Initialize logger.
  logging.basicConfig(level=logging.INFO)
  _LOG = logging.getLogger(__name__)
  ```

- The second cell is like:

  ```python
  import msml610_utils as ut
  import Lesson94_Information_Theory_utils as utils
  ```

# Do Not Use Emoji or Non-Ascii Characters

- Do not use emoji or non-ascii characters, but only ascii ones
- You can use Latex notation for formulas, like $...$ even if they are not
  rendered

# Do not allow page separators

- In Jupyter markdown cells remove separators like
  ```verbatim
  ---
  ```

# Title for the Comment Box

- When using `add_fitted_text_box()` set the title
  ```python
  ax.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
  ```

# Notebook Pairing to Python File and Utility File

- Each notebook is paired with Jupytext to a Python file and has a corresponding
  `*_utils.py` file containing the code corresponding to that notebook
  - E.g., for the Jupyter notebook
    `msml610/tutorials/Lesson94-Information_Theory.ipynb` is paired with
    Jupytext to the file `msml610/tutorials/Lesson94-Information_Theory.py` and
    the corresponding `*_utils.py` file is
    `./msml610/tutorials/Lesson94_Information_Theory_utils.py`
- Given the notebook, find and print the corresponding paired file and the
  `*_utils.py` file

# Remove HTML Links in Cells

- Remove HTML Links in Markdown cells like:
  ```markdown
  <a name='github-api-tutorial'></a>
  <a name='1.-install-dependencies'></a>
  <a name='setup'></a>
  ```

# Remove Cells to Install Jupyterlab-vim

- Remove Markdown cells containing installation of Jupyterlab-vim extension
  ```markdown
  !sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet jupyterlab-vim)"
  !jupyter labextension enable
  ```

# Replace Cells Installing Packages with Installing in the Docker Container
- Packages should be installed through Docker and `requirements.txt` not in
  the notebook
  ```markdown
  !sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet PyGithub)"
  ```

# Remove Cells Dealing with Secrets and Tokens

- Remove all cells that assign tokens like:
  ```
  os.environ["GITHUB_ACCESS_TOKEN"] = ""
  ```
- Enforce that all the secrets are passed as read-only from environment variables

# Format of Code Cells calling Utils Functions

- For code cells containing complex code
  - Add comments explaining the code
  - Avoid trivial comments, but focus on commenting the high level workings of
    the code, e.g., a comment every 2-3 lines of code.
  - Add a period at the end of each comment.

- E.g.,
  ```
  # Create an agent that can use tools and follow a system prompt defining its behavior.
  contract_agent = langchain.agents.create_agent(
      model=llm,
      tools=[ut.utc_now],
      # The system prompt instructs the agent to call the utc_now tool when time is requested
      # and to include the exact tool call inside a fenced Python block in the final response.
      system_prompt=(
          "When time is requested, call utc_now. "
          "In your final answer, include a fenced python block with the exact tool call used."
      ),
  )

  # Invoke the agent with a human message asking for the current UTC time,
  # which should trigger the agent to use the provided utc_now tool.
  contract_out = contract_agent.invoke(
      {
          "messages": [
              langchain_core.messages.HumanMessage(content="What is the current UTC time? Use your tool.")
          ]
      }
  )

  # Extract and print the content of the last message returned by the agent,
  # which should contain the final response including the tool call.
  print(getattr(contract_out["messages"][-1], "content", ""))
  ```

# Break Cells with Too Much Code

- If a cell has too much code, break it into multiple cells
- Each cell should:
  - Focus on building objects, explaining with comments what is done
  - Remove the redundant `import` statements if needed from the generated cells
  - Print the object to help the user understand what is done
    ```
    pprint.pprint(summary_chain)
    ```
