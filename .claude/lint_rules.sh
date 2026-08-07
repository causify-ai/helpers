#!/bin/bash -xe

<<<<<<< HEAD
find .claude -name "*.md" -type f | xargs -n 1 lint_txt.py --clear_actions --action capitalize_header -i
#find .claude -name "*.md" -type f | xargs -n 1 lint_txt.py -i
=======
find .claude -name "*.md" -type f | xargs -n 1 lint_text.py --action capitalize_header -i
#find .claude -name "*.md" -type f | xargs -n 1 lint_text.py -i
>>>>>>> 57f91ae1 (UmdTask517_Get_regressions_to_pass_1 (#1341))
