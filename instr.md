In linters2/lint_cc.py --rule "dassert" --files .claude/skills/coding.rules.md
--dry_run

11:45:55 - INFO  hdbg.py init_logger:1078                               Saving log to file '/Users/saggese/src/umd_classes1/helpers_root/linters2/lint_cc.py.log'
11:45:55 - INFO  hdbg.py init_logger:1086                               > cmd='linters2/lint_cc.py --rule dassert --files .claude/skills/coding.rules.md --dry_run'
11:45:55 - INFO  lint_cc.py _main:368               Processing 1 file(s)
Processing files:   0%|                                                                                                                                                                   | 0/1 [00:00<?, ?it/s]
Traceback (most recent call last):
  File "/Users/saggese/src/umd_classes1/helpers_root/linters2/lint_cc.py", line 415, in <module>
    ret = _main(_parse())
          ^^^^^^^^^^^^^^^
  File "/Users/saggese/src/umd_classes1/helpers_root/linters2/lint_cc.py", line 382, in _main
    rule_content = _extract_rule(args.rule)
                   ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/saggese/src/umd_classes1/helpers_root/linters2/lint_cc.py", line 269, in _extract_rule
    return hmarsele.extract_rule_from_file(rule_spec)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/saggese/src/umd_classes1/helpers_root/helpers/hmarkdown_select.py", line 598, in extract_rule_from_file
    matched_spec = _parse_rigrule_output(file_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/saggese/src/umd_classes1/helpers_root/helpers/hmarkdown_select.py", line 555, in _parse_rigrule_output
    hdbg.dassert_ne(result.returncode, 0,
  File "/Users/saggese/src/umd_classes1/helpers_root/helpers/hdbg.py", line 185, in dassert_ne
    _dfatal(txt, msg, *args, only_warning=only_warning)
  File "/Users/saggese/src/umd_classes1/helpers_root/helpers/hdbg.py", line 142, in _dfatal
    dfatal(dfatal_txt)
  File "/Users/saggese/src/umd_classes1/helpers_root/helpers/hdbg.py", line 71, in dfatal
    raise assertion_type(ret)
AssertionError:
################################################################################
* Failed assertion *
'0'
!=
'0'
rigrule command failed for keyword 'dassert':
################################################################################


while the command works

> rigrule dassert
.claude/skills/testing.rules.md:657:## Do Not Use `hdbg.dassert` to Test Assertions
.claude/skills/coding.rules.md:180:## Use `dassert` instead of if ... raise
.claude/skills/coding.rules.md:199:## Use `dassert` instead of `assert`
.claude/skills/coding.rules.md:213:## Use Specialized `dassert_*`
.claude/skills/coding.rules.md:268:## Add Message to `dassert`
.claude/skills/coding.rules.md:327:## Use `raise` Instead of `dassert(False, ...)`

Print the output of rigrule dassert using hsystem.system_to_string 
when that code path is activated

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- When implementing notebooks follow the instructions in
  - `.claude/skills/notebook.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
