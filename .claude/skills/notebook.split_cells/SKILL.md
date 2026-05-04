---
description: Split Jupyter notebook cells so each cell contains only one concept or example
---

# Each Jupyter Cell Should Have Only One Example

- Cells that contain more than one concept / example should be split so that
  each cell has only one example

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
    - First cell
      ```python
      # Test with fair coin.
      # Two equally likely outcomes → maximum uncertainty, $H = 1$ bit
      fair_coin = [0.5, 0.5]
      print(f"Fair coin entropy: {utils.calculate_entropy(fair_coin):.4f} bits")
      ```
    - Second cell
      ```python
      # Test with biased coin.
      # If heads occurs 90% of the time → less uncertainty, $H < 1$ bit
      biased_coin = [0.9, 0.1]
      print(f"Biased coin (90-10) entropy: {utils.calculate_entropy(biased_coin):.4f} bits")
      ```
    - Third cell
      ```python
      # Test with certain outcome.
      # Certain results have no entropy, $H = 0$ bit.
      certain = [1.0, 0.0]
      print(f"Certain outcome entropy: {utils.calculate_entropy(certain):.4f} bits")
      ```

- Example2
  - Bad
    ```python
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
    ```python
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

# Important

- Always follow the conventions and guidelines in `@.claude/skills/notebook.rules.md`
