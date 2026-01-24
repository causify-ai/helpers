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

## Format of each cell
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

## Each cell should have only one example
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

## Final step
- After you have modified the Python file you will run a command to pair the
  notebook and the Python file

  ```
  > uvx jupytext --sync <python file>
  ```
