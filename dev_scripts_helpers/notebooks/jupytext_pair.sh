#!/bin/bash -xe
DIR=$1
find $DIR -type f -name "*.ipynb" -print0 | xargs -0 -I{} jupytext --set-formats "ipynb,py:percent" "{}"
