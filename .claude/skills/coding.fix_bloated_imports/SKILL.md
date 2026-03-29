---
description: Fix Python imports of large packages needed only for few functions in a module
---

- I will pass you one of more files $FILES and one or more packages $PACKAGES that
  are usually large to import (e.g., `ipython`, `pandas`) and are needed only in
  few functions in the files

- In the files $FILES you will use a conditional import for type checking and lazy imports
  for $PACKAGES
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

- You want to use forward imports only for the types in the package to remove and
  not for the including 
  - **Bad**
    ```python
    "Tuple[Union[ipywidgets.FloatSlider, ipywidgets.IntSlider], ipywidgets.HBox]"
    ```
  - **Good**
    ```python
    Tuple[Union["ipywidgets.FloatSlider", "ipywidgets.IntSlider"], "ipywidgets.HBox"]
    ```

- If you see that most of the functions in $FILES require the passed package
  $PACKAGES, you might suggest to not do this transform
