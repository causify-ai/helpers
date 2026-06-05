# Sync all the ipynb.
ls -1 *.ipynb | xargs -n 1 jupytext --sync
