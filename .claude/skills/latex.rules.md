This file contains rules and conventions for writing LaTeX formulas.

# Mathematical Symbols and Notation

## Symbol Conventions

- Include LaTeX formulas in `$$ $$` instead of `\[` and `\]`
- `$\Pr(...)$` for probability, instead of `P(...)`
- `$\EE[...]$` for expectation (mean), instead of `\mathbb{E}` or `E`
- `$\VV[...]$` for variance, instead of `\mathbb{V}`
- `$\mathcal{X}$` for sets or spaces (use calligraphic)
- `\vx`, `\vy` for vectors
- `\mA` for matrices
- `|` instead of `\mid` 
- Do not use `\left[`, `\left(`, `\right]`, `\right)` unless necessary

# Formula Formatting

## Multi-line Layout

- Format the LaTeX code on multiple lines to be easy to read
  - **Bad**
    $$\hat{ATE} = \frac{1}{N}\sum(({Y_{i}-Y_{jm}(i)})T_{i} + ({Y_{jm}(i)-Y_{i}})(1-T_{i}))$$
  - **Good**
    $$
    \hat{ATE}
    = \frac{1}{N}\sum (
      ( {Y_{i} - Y_{jm}(i)} )T_{i} +
      ( {Y_{jm}(i) - Y_{i}} )( 1 - T_{i} )
    )
    $$

# Converting Mathematical Formulas

## Conversion Guidelines

- Convert mathematical formulas to LaTeX without changing their meaning
  and formatting so that they are easily readable
  - **Bad**
    ```
    P(M | D) ∝ P(D | M) P(M)
    ```
  - **Good**
    ```
    $$
    P(M \mid D) \propto P(D \mid M)\, P(M)
    $$
    ```

  - **Bad**
    ```
    a* = argmax_a E_{M~P(M|D)}[Goal | do(a), M]
    ```
  - **Good**
    ```
    $$
    a^* = \arg\max_a
      \mathbb{E}_{M \sim P(M \mid D)}\left[
        \text{Goal} \mid do(a), M
      \right]
    $$
    ```
