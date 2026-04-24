#!/bin/bash
if [[ $1 == "wrap" ]]; then
    cmd='vimdiff -c "windo set wrap"'
else
    cmd='vimdiff'
fi;
cmd="$cmd linters2/test/outcomes/Test_add_class_frame.test9/tmp.final.actual.txt linters2/test/outcomes/Test_add_class_frame.test9/tmp.final.expected.txt"
eval $cmd