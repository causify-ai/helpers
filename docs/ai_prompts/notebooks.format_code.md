You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

## Modify only the Python file
- You will modify the Python file
- If there is no Python file, but only the ipynb you will run a command to pair
  the notebook and the Python file
  ```bash
  > uvx jupytext --set-formats ipynb,py:percent  <ipynb file>
  ```

## Use Python style
- For all the code follow the rules from `docs/ai_prompts/coding.format_code.md`

## Use pandas and seaborn
- When writing new code:
  - Use pandas library instead of numpy
  - Prefer to use Seaborn package instead of matplotlib

- The goal is to make the code shorter and more readable

## Add code to a library / utilities
- Find the library / utility file that correspond to a notebook
  - E.g., 
    ```
    Lesson94-Information_Theory.ipynb
    ->
    utils_Lesson94-Information_Theory.ipynb
    ```
- Implement the code
  - Saving the functions and the bulk of the code in the utils_ files
  - Having only the caller code in Jupyter notebook
- Reuse code already existing in the `utils_*.py` file and in the `helpers`
  directory

## Add code to the right place in the library
- The library / utility file should have a structure that follows the flow of the
  notebook
- Add the functions in the part of the utility file that corresponds to the
  Jupyter notebook

## Do not use emoji or non-ascii characters
- Do not use emoji or non-ascii characters, but only ascii ones
- You can use Latex notation for formulas, like $...$ even if they are not
  rendered

## Add all information on the graph
- When creating an interactive graph
  - Do not use the statement `print` after the graph
  - Add notations directly on the graph

## Format of each Jupyter cell
- Each cell has only one concept / group of statements and a comment on the
  result
- Each cell has
  - a comment explaining what we want to do
  - a group of commands
  - a statement to show the result (e.g., `print()`, `display()`)
  - a comment about the outcome
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

## Each Jupyter cell should have only one example
- Cells that contain more than one concept / example should be split so that each
  cell has only one example

- Example1

  - Bad: this cell has 3 examples and should be split in 3 cells, as below
    ```python
    # Test with fair coin.
    fair_coin = [0.5, 0.5]
    print(f"Fair coin entropy: {utils.calculate_entropy(fair_coin):.4f} bits")

    # Test with biased coin.
    biased_coin = [0.9, 0.1]
    print(f"Biased coin (90-10) entropy: {utils.calculate_entropy(biased_coin):.4f} bits")

    # Test with certain outcome.
    certain = [1.0, 0.0]
    print(f"Certain outcome entropy: {utils.calculate_entropy(certain):.4f} bits")
    ```

  - Good: each cell has one example
    ```python
    # Test with fair coin.
    # Two equally likely outcomes → maximum uncertainty, $H = 1$ bit
    fair_coin = [0.5, 0.5]
    print(f"Fair coin entropy: {utils.calculate_entropy(fair_coin):.4f} bits")
    ```

    ```
    # Test with biased coin.
    # If heads occurs 90% of the time → less uncertainty, $H < 1$ bit
    biased_coin = [0.9, 0.1]
    print(f"Biased coin (90-10) entropy: {utils.calculate_entropy(biased_coin):.4f} bits")
    ```

    ```
    # Test with certain outcome.
    # Certain results have no entropy, $H = 0$ bit.
    certain = [1.0, 0.0]
    print(f"Certain outcome entropy: {utils.calculate_entropy(certain):.4f} bits")
    ```

- Example2

  - Bad
  ```
  # Use the weather-activity example.
  print("Example: Weather and Activity Correlation")
  print("=" * 50)
  utils.visualize_information_decomposition(joint_prob)

  # Calculate and display mutual information.
  mi = utils.calculate_mutual_information(joint_prob)
  print(f"\nMutual Information I(Weather; Activity) = {mi:.4f} bits")
  print(f"This means knowing the weather reduces uncertainty about activity by {mi:.4f} bits")
  ```

  - Good: two different cells
    ```
    # Use the weather-activity example.
    print("Example: Weather and Activity Correlation")
    print("=" * 50)
    utils.visualize_information_decomposition(joint_prob)
    ```

    ```
    # Calculate and display mutual information.
    mi = utils.calculate_mutual_information(joint_prob)
    print(f"\nMutual Information I(Weather; Activity) = {mi:.4f} bits")
    print(f"This means knowing the weather reduces uncertainty about activity by {mi:.4f} bits")
    ```

## Interactive widgets
- Add the controls first with both sliders and a cell to enter the values
  - Clearly identify the meaning of each slider
  - E.g., "n = the number of sample points used", "rho = the correlation between the two random variables"

- Use a single row of 3 or 4 graphs (not in a 2 by 2 grid)
  - E.g., joint distribution, entropy metrics, sampled realizations, explanation
  - One graph should be "Comments" containing an explanation of what's happening
    in the remaining graphs, based on the values
  - Add information in each graph as a legend
- Do not print any information as `print()` statement, but write all the
  information in the "Comments" graph

- You can use `plot_joint_entropy_interactive()` in
  `msml610/tutorials/utils_Lesson94_Information_Theory.py` as a reference

## Final step
- After you have modified the Python file you will run a command to pair the
  notebook and the Python file

  ```
  > uvx jupytext --sync <python file>
  ```
