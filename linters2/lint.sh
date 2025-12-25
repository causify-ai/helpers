#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <argument>"
  exit 1
fi

DIR=$1

find $DIR -name "*.py" -o -name "*.ipynb" | grep -v ipynb_checkpoints | sort | tee tmp

pre-commit run --files $(cat tmp)
helpers_root/linters2/normalize_import.py $(cat tmp)
helpers_root/linters2/add_class_frames.py $(cat tmp)
