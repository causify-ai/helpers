#!/bin/bash -xe
render_images.py -i $1.typ
typst compile --root . $1.typ
open $1.pdf
