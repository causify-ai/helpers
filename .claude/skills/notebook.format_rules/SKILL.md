---
description: Conventions for Jupyter notebooks
---

- You are an expert Python developer

- I will pass you a Python file paired with Jupyter notebook with jupytext using
  a `py:percent` format

# Use Python Style

- For all the Python code you must follow the rules from
  @.claude/skills/coding.format_rules/SKILL.md

# Format of First Cell

- The first cell of a notebook contains basic initialization that is the same for
  all notebooks

  ```python
  %load_ext autoreload
  %autoreload 2

  # System libraries.
  import logging

  # Third party libraries.
  import numpy as np
  import pandas as pd
  import seaborn as sns
  import matplotlib.pyplot as plt
  ```

# Format of Second Cell
- The second cell contains imports specific of the notebook
  ```python
  import msml610_utils as ut
  import Lesson94_Information_Theory_utils as utils
  ```

# Format of Third Cell
- For a Jupyter notebook always use the following idiom for logging
  ```python
  import logging
  # Local utility.
  import utils

  _LOG = logging.getLogger(__name__)
  utils.init_logger(_LOG)
  ```

- In the local utility `*_utils.py` there should be a function like
  ```
  import helpers.hnotebook as hnotebo

  def init_logger(notebook_log: logging.Logger) -> None:
      hnotebo.config_notebook()
      hdbg.init_logger(verbosity=logging.INFO, use_exec_path=False)
      # Init notebook logging.
      hnotebo.set_logger_to_print(notebook_log)
      # Init utils logging.
      global _LOG
      _LOG = hnotebo.set_logger_to_print(_LOG)
      # Init module logging.
      causalml_logger: logging.Logger = logging.getLogger("causalml")
      hnotebo.set_logger_to_print(causalml_logger)
  ```

# Each Code Cell has a Single Purpose

- Each cell should do one logical thing only
  - Good examples:
    -	Import libraries
    -	Load data
    -	Clean data
    -	Plot data
    -	Train model
    -	Evaluate model
  - Bad example:
    - One giant cell that loads data, cleans it, trains a model, and plots results.

- If a cell does more than one step, split it

# Format of a Code Cell

- Each cell has only one concept / group of statements and a comment on the
  result
- Keep cells short
- Each cell has:
  - A comment explaining what we want to do
  - A group of commands
  - A statement to show the result (e.g., `print()`, `display()`)
  - A comment about the outcome
  ```
  # Comment explaining what we are trying to do.
  operation

  print results
  # Comment on the result.
  ```

- Example:
  ```python
  # Test with broken coin.
  biased_coin = [1.0, 0.0]
  print(f"Biased coin (100-0) entropy: {utils.calculate_entropy(biased_coin):.4f} bits")
  # If heads occurs 100% of the time → no uncertainty, $H = 0$ bit.
  ```

- Each cell should:
  - Focus on building objects, explaining with comments what is done
  - Remove the redundant `import` statements if needed from the generated cells
  - Print the object to help the user understand what is done
    ```
    pprint.pprint(summary_chain)
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
