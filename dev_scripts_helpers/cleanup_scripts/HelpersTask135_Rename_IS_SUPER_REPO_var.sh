#!/bin/bash -xe

find . -type f -exec perl -i -pe '
s/(\$|\w+_)IS_SUPER_REPO/$1USE_HELPERS_AS_NESTED_MODULE/g;
s/(\$|\w+_)is_super_repo/$1use_helpers_as_nested_module/g;
s/\bIS_SUPER_REPO\b/USE_HELPERS_AS_NESTED_MODULE/g;
s/\bis_super_repo\b/use_helpers_as_nested_module/gi;
s/CSFY_IS_SUPER_REPO/CSFY_USE_HELPERS_AS_NESTED_MODULE/g;
' {} \;
