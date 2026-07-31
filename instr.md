Run the skill /coding.todoai_gp on each of the TODO, one at the time

./dev_scripts_helpers/documentation/transform_pandoc_ast_to_typst.py:673:    # TODO(ai_gp): Factor out this as a parser option in the library.
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2111:    # TODO(ai_gp): Move more boilerplate code to helper.
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2184:        # TODO(ai_gp): Also freeze output checking the presence of strings
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2203:        # TODO(ai_gp): Also freeze output checking the presence of strings
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2357:        # TODO(ai_gp): Also freeze output checking the presence of strings
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2383:        # TODO(ai_gp): Also freeze output checking the presence of strings
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2414:        # TODO(ai_gp): Also freeze output checking the presence of strings
./dev_scripts_helpers/documentation/test/test_notes_to_pdf.py:2444:        # TODO(ai_gp): Also freeze output checking the presence of strings
./dev_scripts_helpers/documentation/summarize_md.py:688:        # TODO(ai_gp): Use dassert_lte
./helpers/hsystem.py:83:# TODO(ai_gp): Use "" instead of None.
./helpers/lib_tasks/lib_tasks_git.py:695:# TODO(ai_gp): @all Move to hgit.
./helpers/lib_tasks/lib_tasks_git.py:719:    # TODO(ai_gp): Use system_to_lines, if possible.
./helpers/hmarkdown_coloring.py:227:# TODO(ai_gp): Use re.VERBOSE and comments this expression
./helpers/lib_tasks/test/test_lib_tasks_find.py:73:    # TODO(ai_gp): Rename the tests to test1, test2, ...
./helpers/test/test_hunit_test_purification.py:66:    # TODO(ai_gp): Factor out more code in an helper function
./helpers/test/test_hunit_test_purification.py:278:    # TODO(ai_gp): Factor out more code.
./helpers/test/test_hunit_test_purification.py:629:        # TODO(ai_gp): Assign super_module_root and then pass it. Do the same
./helpers/test/test_hunit_test_purification.py:1240:        # TODO(ai_gp): Move the umock.patch to the helper function to simplify
./helpers/test/test_hmarkdown_coloring.py:605:# TODO(ai_gp): Factor out a helper. Use expected string and assert_equal
./helpers/test/test_hmarkdown_coloring.py:615:    # TODO(ai_gp): Rename test1, ...

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
  - Wait for the user to confirm
