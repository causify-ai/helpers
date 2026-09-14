#!/bin/bash -xe
git ls-files | grep -E '\.log|tmp\.' | grep -v '/outcomes/' | grep -v build.version | grep -v docker_build
