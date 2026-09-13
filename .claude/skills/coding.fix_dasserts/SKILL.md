---
description: Fix dassert in Python code
model: haiku
---

- I will pass you one or more files `<FILES>`

- Use the proper dasserts following instructions in
  `.claude/skills/coding.rules.md` in section
  ```markdown
  ## Use Specialized `dassert_*`
  ```

# Verification
- [ ] Confirm generic `assert` and `hdbg.dassert()` calls are replaced with the
      most specific `hdbg.dassert_*` function
- [ ] Confirm each `dassert_*` call has a clear message
