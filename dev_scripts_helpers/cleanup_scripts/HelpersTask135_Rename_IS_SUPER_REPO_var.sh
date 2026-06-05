#!/bin/bash -xe

# We need to execlude the file that we are running this script on,
# otherwise it will be replaced with the new values.
find . -type f \( -name "*.py" -o -name "*.sh" \) -not -name "HelpersTask135_Rename_IS_SUPER_REPO_var.sh" -exec perl -i -pe '
s/(\$|\w+_)IS_SUPER_REPO/$1USE_HELPERS_AS_NESTED_MODULE/g;
s/(\$|\w+_)is_super_repo/$1use_helpers_as_nested_module/g;
s/\bIS_SUPER_REPO\b/USE_HELPERS_AS_NESTED_MODULE/g;
s/\bis_super_repo\b/use_helpers_as_nested_module/gi;
s/CSFY_IS_SUPER_REPO/CSFY_USE_HELPERS_AS_NESTED_MODULE/g;
' {} \;
