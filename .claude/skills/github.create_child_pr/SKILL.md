---
description: Create instructions to build a children PR
---

- You are in a <SRC> Git branch
  - E.g., `HelpersTask1273_Get_Mac_tests_to_pass`

- Find which one is the next branch available
  - E.g., 
  ```
  > i git_branch_next_name
  12:01:47 - INFO  hgit.py _get_branch_next_name_via_github_api:124       Found highest number '3' in all branches, next is '4'
  branch_next_name='HelpersTask1273_Get_Mac_tests_to_pass_4'
  ```

- Create a file `pr_merge.txt` with the instructions to:
  - Create a <DST> branch `HelpersTask1273_Get_Mac_tests_to_pass_4`
  - Copy the files needed to merge PR2 from `github_PR_plan.md` from the current
    branch to the target branch
  - Create a file `pr_commit_msg.txt` with the description of what the PR does
  - Create a file `pr_pytest.sh` with the tests to run to check the behavior of the PR
  - Make sure there are comments for each phase and that each command is correct


```
SRC_BRANCH=HelpersTask1273_Get_Mac_tests_to_pass
TARGET_BRANCH=HelpersTask1273_Get_Mac_tests_to_pass_4

git checkout master
git pull
git checkout -b $TARGET_BRANCH

cat > pr_commit_msg.txt << 'EOF'
Unit Test Infrastructure: Purification, Introspection, Numpy, and Base Updates

- Adds new test purification module (hunit_test_purification.py)
- Updates test infrastructure with new utility functions
- Improves introspection module for better test support
- Fixes numpy test compatibility issues
- Updates base unit test module for macOS compatibility
- All changes are related to test utilities and infrastructure improvements
- Well-isolated changes to testing subsystem
EOF

cat > pr_pytest.sh << 'EOF'
pytest \
    helpers/test/test_hunit_test_purification.py \
    helpers/test/test_hintrospection.py \
    helpers/test/test_hnumpy.py \
    helpers/test/test_hunit_test.py \
    -v
EOF

chmod +x pr_pytest.sh

FILES="helpers/hunit_test_purification.py helpers/test/test_hunit_test_purification.py helpers/test/test_hintrospection.py helpers/test/test_hnumpy.py helpers/test/test_hunit_test.py"

git checkout $SRC_BRANCH -- $FILES && git add $FILES

git commit -am pr_commit_msg.txt

i gh_create_pr --no-draft

pr_pytest.sh
```
