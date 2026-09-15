#!/bin/bash -e
git ls-files --recurse-submodules | grep -E '\.log|tmp\.' | grep -v '/outcomes/' | grep -v build.version | grep -v docker_build | grep -v 'class_project/data605' | grep -v 'class_project/msml610'
