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
