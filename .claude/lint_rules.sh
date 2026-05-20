#!/bin/bash -xe

find .claude -name "*.md" -type f | xargs -n 1 lint_txt.py --action capitalize_header -i
