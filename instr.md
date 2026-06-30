
### [x] Are the test running end-to-end or only capturing the script
Yes

### [x] Move code to lib_
Move all the code from ./dev_scripts_helpers/documentation/notes_to_pdf.py that
is not under the banner CLI to
./dev_scripts_helpers/documentation/lib_notes_to_pdf.py

### [ ] Unit test lib_
dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py

### Add more unit tests
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py

### Add tests for 
> notes_to_pdf.py --input=msml610/lectures_source/Lesson13.1-Explainability.txt --output=msml610/lectures/Lesson13.1-Explainability.pdf --type=slides --toc_type=navigation --debug_on_error --skip_action=cleanup_before --skip_action=cleanup_after --slides_engine typst --no_fail_on_warnings

1) Make the flow by default to run a single pandoc instead of two phases.

in other words, --skip_pandoc_ast_transform should become
--use_pandoc_ast_transform

2) When calling pandoc, if it's --slides_engine typst

add a step when calling pandoc

pandoc two_blocks.md \
    --from=markdown \
    --to=typst \
    --filter=./dev_scripts_helpers/documentation/convert_pandoc_divved_fence.py

- Make sure that the divved fence code in markdown

```
::: columns
:::: {.column width=55%}
## Block A

This is the first block.

- Point A
- Point B
- Point C
::::

:::: {.column width=45%}
## Block 2

This is the second block.

- Point X
- Point Y
- Point Z
::::
:::
```

## Rename 
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py

./dev_scripts_helpers/documentation/test/test_notes_to_pdf_py.py

## How to understand code coverage of executables

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
