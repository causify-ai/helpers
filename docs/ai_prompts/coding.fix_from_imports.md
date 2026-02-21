- Replace any Python statement like `from X import Y` with the form `import X`
  and then replace the uses of `Y` with `X.Y`

- The only ones that can stay as `from X import Y` are
  ```
  from typing import Optional
  from IPython.display import display
  ```
