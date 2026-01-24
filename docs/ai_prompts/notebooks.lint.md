You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

## Step 1.
- Given the input, you will create a Python file called with the same name of the
  file

- You will split cells so that each cell has only one example, and a comment on
  the result

- E.g., the following cell has 3 examples and should be split in 3 cells
  and have comments.

  ```
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

becomes

  ```
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

For all the code follow the rules from `docs/ai_prompts/coding.format_code.md`

## Step 2
- After you have modified the Python file you will run a command to pair the
  notebook and the Python file

  ```
  > uvx jupytext --sync <python file>
  ```
