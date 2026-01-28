You are an expert Python developer.

I will pass you a Python file paired with Jupyter notebook with jupytext using a
py:percent format (e.g., msml610/tutorials/Lesson94-Information_Theory.py)

## Interactive widgets conventions
- Interactive widgets must always have:
  - The name of the variable (e.g., n, mu, nu)
  - A short explanation of what they are (e.g., number of samples, prob of
    success)
  - Value cell and "-" and "+" buttons

- Use code in `msml610_utils.py` like `_create_slider_widget()`,
  `build_widget_control()` to create the widgets

## Little-by-little interactive widgets
- We want to build intuition of complex concepts using Jupyter cells one at the
  time, layering concepts

- For instance to explain the Hoeffding Inequality, we can build the intuition
  over multiple cells
  - The first cell shows
    - Create a Bernoulli binomial X with a given prob of success mu and N the
      number of samples
    - There is a box for the random seed
      - The seed can be selected by hand and starts from 42
      - There is pushed to get an increased seed
    - The cell shows N samples from X

  - The second cell shows
    - mu and N are fixed from the previous cell
    - The PDF of N samples
    - The empirical mean of N samples, nu
    - The mean and the variance of the Bernoulli
    - Clicking on the seed new realizations are generated

  - The third cell shows
    - The distribution of the empirical mean nu when N_samples are generated
    - Plot the expected distribution given the law of large numbers and computing
      the sample std dev

- For little-by-little widgets is ok to keep code in simple functions in the
  notebook so that the user can see the internals of the code
- The complex functions (especially the ones plotting graphs and the widgets)
  should go in the `utils_*.py` files

## End-to-end interactive widgets
- After the intuition of a complex concept has been built little-by-little then

- When the user asks for an "end-to-end interactive widget", it means that there
  should be multiple graphs (like 3 or 4 on the same row)
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

## Interactive widgets conventions
- Interactive widgets must always have:
  - The name of the variable (e.g., n, mu, nu)
  - A short explanation of what they are (e.g., number of samples, prob of
    success)
  - Value cell and "-" and "+" buttons

- Use code in `msml610_utils.py` like `_create_slider_widget()`,
  `build_widget_control()` to create the widgets

