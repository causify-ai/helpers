#!/bin/bash -e
# """
# Find all the empty files that can be deleted.
# """

source helpers.sh

# TODO(ai_gp): We should get to the point where there are only files non-empty
# besides `__init__.py`.
cmd='find . -path ./.git -prune -o -type f -empty -not -name "__init__.py" -print'
execute "$cmd"
