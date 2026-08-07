#!/bin/bash -xe

find .claude -name "*.md" -type f | xargs -n 1 lint_text.py --action capitalize_header -i
#find .claude -name "*.md" -type f | xargs -n 1 lint_text.py -i
