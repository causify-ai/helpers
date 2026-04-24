- This file contains conventions and rules for notebooks

# Python Code Style and Conventions

## Use Python Style

- For all the Python code you must follow the rules from
  `@.claude/skills/coding.rules.md`

# Notebook Structure and Initialization

## Format of First Cell

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

## Format of Second Cell

- The second cell contains imports specific of the notebook
  ```python
  import msml610_utils as ut
  import Lesson94_Information_Theory_utils as utils
  ```

## Format of Third Cell

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

## Notebook Pairing to Python File and Utility File

- Each notebook is paired with Jupytext to a Python file and has a corresponding
  `*_utils.py` file containing the code corresponding to that notebook
  - E.g., for the Jupyter notebook
    `msml610/tutorials/Lesson94-Information_Theory.ipynb` is paired with
    Jupytext to the file `msml610/tutorials/Lesson94-Information_Theory.py` and
    the corresponding `*_utils.py` file is
    `./msml610/tutorials/Lesson94_Information_Theory_utils.py`
- Given the notebook, find and print the corresponding paired file and the
  `*_utils.py` file

# Code Cell Organization and Content

## Each Code Cell has a Single Purpose

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

## Format of a Code Cell

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

## Format of Code Cells calling Utils Functions

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

# Text and Formatting Standards

## Do Not Use Emoji or Non-Ascii Characters

- Do not use emoji or non-ascii characters, but only ascii ones
- You can use Latex notation for formulas, like $...$ even if they are not
  rendered

## Do Not Allow Page Separators

- In Jupyter markdown cells remove separators like
  ```verbatim
  ---
  ```

## Remove HTML Links in Cells

- Remove HTML Links in Markdown cells like:
  ```markdown
  <a name='github-api-tutorial'></a>
  <a name='1.-install-dependencies'></a>
  <a name='setup'></a>
  ```

# Cell Cleanup and Security

## Remove Cells to Install Jupyterlab-vim

- Remove Markdown cells containing installation of Jupyterlab-vim extension
  ```markdown
  !sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet jupyterlab-vim)"
  !jupyter labextension enable
  ```

## Replace Cells Installing Packages with Installing in the Docker Container

- Packages should be installed through Docker and `requirements.txt` not in
  the notebook
  ```markdown
  !sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet PyGithub)"
  ```

## Remove Cells Dealing with Secrets and Tokens

- Remove all cells that assign tokens like:
  ```
  os.environ["GITHUB_ACCESS_TOKEN"] = ""
  ```
- Enforce that all the secrets are passed as read-only from environment variables

# Purpose

- Maintain synchronization between Jupyter notebook files (.ipynb) and their
  paired Python files (.py) using Jupytext
- Edit notebooks through their Python source files, ensuring consistency between
  formats

# When to Use

- User asks to modify a Jupyter notebook (.ipynb file)
- User asks to create a notebook from existing .ipynb file without a paired .py file
- User asks to add cells, modify cells, or change notebook structure

# When NOT to Use

- User is asking questions about notebook content
- User wants to work with a Python file directly (not a notebook)

# Workflow

## Step 1: Sync Before Editing

- Check if a paired Python file exists
  - If yes: Sync the files to ensure they are in sync
    ```bash
    > uvx jupytext --sync <path/to/notebook_name.py>
    ```
  - If no: Create the pairing in `py:percent` format
    ```bash
    > uvx jupytext --set-formats ipynb,py:percent <path/to/notebook_name.ipynb>
    ```

## Step 2: Edit Only the Python File

- Modify only the .py file, never the .ipynb file directly
- Follow all notebook formatting rules from `@.claude/skills/notebook.format/SKILL.md`
- Make changes to cell content, structure, and metadata through the .py file
- Use the NotebookEdit tool on the paired .py file if needed

## Step 3: Sync After Editing

- After completing all modifications to the .py file, sync to update the .ipynb file
  ```bash
  > uvx jupytext --sync <path/to/notebook_name.py>
  ```
- This propagates your changes to the Jupyter notebook format

# Example Workflow

- User request: "Add a new cell to my tutorial notebook"
  ```bash
  > uvx jupytext --sync notebooks/my_tutorial.py
  # (edit notebooks/my_tutorial.py using NotebookEdit tool)
  > uvx jupytext --sync notebooks/my_tutorial.py
  ```

- User request: "Create a Python file for this notebook"
  ```bash
  > uvx jupytext --set-formats ipynb,py:percent notebooks/my_tutorial.ipynb
  ```

# Key Points

- Always use `py:percent` format for jupytext pairing
- Sync before editing to catch any upstream changes
- Sync after editing to generate the updated .ipynb file
- Never edit .ipynb files directly when a .py file exists
- The NotebookEdit tool and Edit tool work on the .py file

# Use Pandas and Seaborn

- When writing new code:
  - Use `pandas` library instead of `numpy`
  - Prefer to use `Seaborn` package instead of `matplotlib`
- The goal is to make the code shorter and more readable

# Add All Information on Plot

- When creating a plot
  - Do not use the statement `print` after the plot
  - Add results and information directly to the plot using `ax.text`

# Theoretical vs Empirical Data

- When plotting data with theoretical (e.g., the mean of the underlying
  distribution) vs empirical (e.g., the sample mean of the data):
  - The theoretical data should have lighter and transparent colors and dotted
    lines
  - Empirical data should have darker colors and be solid lines

# Title for the Comment Box

- When using `add_fitted_text_box()` set the title
  ```python
  ax.set_title("Comments", fontsize=14, fontweight="bold", pad=20)
  ```
