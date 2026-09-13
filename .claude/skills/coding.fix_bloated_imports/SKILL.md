---
description: Fix Python imports of large packages needed only for few functions in a module
model: haiku
---

- I will pass you one or more files `<FILES>` and one or more packages `<PACKAGES>` that
  are usually large to import (e.g., `ipython`, `pandas`) and are needed only in
  few functions in the files

- In the files `<FILES>` you will use a conditional import for type checking and lazy imports
  for `<PACKAGES>`
  - E.g., transform
    ```python
    def make_slider() -> "ipywidgets.IntSlider":
        import ipywidgets
        ...
    ```
    into
    ```python
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        import ipywidgets

    def make_slider() -> "ipywidgets.IntSlider":
        import ipywidgets
        ...
    ```

- Use forward references only for the types in the package to remove and
  not for the including
  - **Bad** (quotes the whole expression as one string)
    ```python
    "Tuple[Union[ipywidgets.FloatSlider, ipywidgets.IntSlider], ipywidgets.HBox]"
    ```
  - **Good** (quotes only the package types)
    ```python
    Tuple[Union["ipywidgets.FloatSlider", "ipywidgets.IntSlider"], "ipywidgets.HBox"]
    ```

- If you see that most of the functions in `<FILES>` require the passed package
  `<PACKAGES>`, you might suggest to not do this transform

# Verification
- [ ] Confirm `<PACKAGES>` is imported only under `TYPE_CHECKING` or inside the
      functions that use it
- [ ] Confirm forward references quote only the package types, not full
      expressions
