# Task: Add RawDescriptionHelpFormatter to all ArgumentParser instances

## Scope
- Update **all Python files** in the codebase that instantiate `argparse.ArgumentParser()`
- Includes: `dev_scripts_helpers/`, helpers modules, tests, everywhere

## Purpose
- `RawDescriptionHelpFormatter` preserves multi-line docstring formatting in help text
- Enables cleaner, more readable help output with preserved indentation and line breaks

## What to Change

### Before
```python
parser = argparse.ArgumentParser(
    description=__doc__,
)
```

### After
```python
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=__doc__,
)
```

## Details
- Add `formatter_class=argparse.RawDescriptionHelpFormatter` to **all** existing `ArgumentParser()` calls
- Apply to new parser instances going forward
- If parser already has a different `formatter_class`, replace it with `RawDescriptionHelpFormatter`
- Handle subparsers the same way (if they have `add_parser()` calls)

## Definition of Done
- Grep: `grep -r "ArgumentParser(" --include="*.py" | grep -v "formatter_class=argparse.RawDescriptionHelpFormatter"` returns no matches with `ArgumentParser(` on same line as instantiation
- All Python files checked and updated

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`
