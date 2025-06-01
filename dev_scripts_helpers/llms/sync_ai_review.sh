#!/bin/bash -xe
HELPERS_ROOT_DIR=$(find . -name "helpers_root" -type d | grep -v git) || true
if [[ -z $HELPERS_ROOT_DIR ]]; then
    HELPERS_ROOT_DIR="."
fi;
echo HELPERS_ROOT_DIR=$HELPERS_ROOT_DIR

ls $HELPERS_ROOT_DIR

\cp -rf /Users/saggese/src/helpers1/helpers/hgit.py $HELPERS_ROOT_DIR/helpers

ls $HELPERS_ROOT_DIR/dev_scripts_helpers/llms
\cp -rf /Users/saggese/src/helpers1/dev_scripts_helpers/llms/{ai_review.py,llm_prompts.py,llm_transform.py,inject_todos.py} $HELPERS_ROOT_DIR/dev_scripts_helpers/llms

ls $HELPERS_ROOT_DIR/helpers
\cp -rf /Users/saggese/src/helpers1/helpers/hmarkdown.py $HELPERS_ROOT_DIR/helpers

ls $HELPERS_ROOT_DIR/docs/code_guidelines
\cp -rf /Users/saggese/src/helpers1/docs/code_guidelines/*guidelines* $HELPERS_ROOT_DIR/docs/code_guidelines
