git status | \grep ipynb | \grep delete | awk '{print $2}' | sed 's/ipynb/py/' | xargs -n 1 jupytext --sync
