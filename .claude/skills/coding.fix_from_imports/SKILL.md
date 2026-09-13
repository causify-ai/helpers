---
description: Replace `from X import Y` imports with `import X` and update usages in a file
model: haiku
---

- Replace any Python statement like `from X import Y` with the form `import X`
  and then replace the uses of `Y` with `X.Y`

- For aliased imports `from X import Y as Z`, convert to `import X` and replace
  all uses of `Z` with `X.Y`

- For nested module imports `from X.Y import Z`, convert to `import X.Y` and
  replace all uses of `Z` with `X.Y.Z`

- The only ones that can stay as `from X import Y` are:
  ```python
  from __future__ import annotations
  from typing import Any, Dict, List, Optional, Tuple, Union, ...  (any typing name)
  from IPython.display import display
  from pathlib import Path
  ```

- Do not use
  ```python
  # Re-export get_chat_model for backward compatibility.
  get_chat_model = langchain_API_utils.get_chat_model
  ```
  but replace all the callers

# Verification
- [ ] Confirm no remaining `from X import Y` statements outside the allowed
      exceptions
- [ ] Confirm every use of the imported name is updated to `X.Y` (or `X.Y.Z`
      for nested modules)
- [ ] Confirm no backward-compatibility re-export aliases remain
