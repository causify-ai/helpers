# Pair all the ipynb.
ls -1 *.ipynb | xargs -n 1 jupytext --set-formats ipynb,py:percent
