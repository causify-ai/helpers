---
name: coding.fix_from_imports
description: Replace "from X import Y" style imports with "import X" and update usages throughout a file
---

- Replace any Python statement like `from X import Y` with the form `import X`
  and then replace the uses of `Y` with `X.Y`

- For aliased imports `from X import Y as Z`, convert to `import X` and replace
  all uses of `Z` with `X.Y`

- For nested module imports `from X.Y import Z`, convert to `import X.Y` and
  replace all uses of `Z` with `X.Y.Z`

- The only ones that can stay as `from X import Y` are:
  ```
  from __future__ import annotations
  from typing import Any, Dict, List, Optional, Tuple, Union, ...  (any typing name)
  from IPython.display import display
  ```
