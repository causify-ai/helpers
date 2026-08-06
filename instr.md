1) Add an option lint_text.py to override the logic that infers the extension
   from the file

2) Add support for "smd" files and a transform smd_format

The format
- removes white spaces before \n
- removes the : after a single @tag@ before a new line

  E.g.,
  @Problem@:

  ->

  @Problem@

- Capitalize the first letter after a : 
  - _Explicit assumptions_: instead

  ->

  - _Explicit assumptions_: Instead

@Definition@: **models** -> 
@Definition@: **Models** -> 

- Make sure there is exactly one empty line between blocks
  starting with at least 3 : and other chunk of code

::: columns
:::: {.column width=40%}

- @Procedure@
  1. Compute single KDE for all chains
  2. Rank plot to check results
     - Histograms should look uniform, exploring different (and all)
       posterior regions
  3. Plot single KDE with all statistics

::::
:::: {.column width=60%}

![](msml610/lectures_source/figures/L07.1.Coin_example_numerical_solution_2.png)

::::
:::
