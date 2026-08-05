#!/bin/bash -xe

find .claude -name "*.md" -type f | xargs -n 1 lint_txt.py --clear_actions --action capitalize_header -i
#find .claude -name "*.md" -type f | xargs -n 1 lint_txt.py -i
