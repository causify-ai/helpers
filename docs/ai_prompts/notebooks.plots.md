## Use pandas and seaborn
- When writing new code:
  - Use pandas library instead of numpy
  - Prefer to use Seaborn package instead of matplotlib

- The goal is to make the code shorter and more readable

## Add all information on plot
- When creating a plot
  - Do not use the statement `print` after the plot
  - Add results and information directly to the plot

## Theoretical vs empirical data
- When plotting data with theoretical (e.g., the underlying distribution) vs
  empirical (e.g., the data coming from sampling)
  - Theoretical data should have lighter and transparent colors and dotted lines
  - Empirical data should have darker colors and be solid lines

-> plot
## Plotting graphs
- When a plot changes, it should not change the values on the y-axis and x-axis
- The xlim and ylim of the graphs should be fixed until the graph is too big
  to fit in which case it should change so that the xlim or ylim doubles or
  it's reduced in half, so that the xlim / ylim can be stable

