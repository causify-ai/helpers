# pip install pyan3==1.1.1
# brew install graphviz
#pyan3 $1/*.py --dot > callgraph.dot
pyan3 ck_marketing/plugins/hunterio/hunter_api.py --dot > callgraph.dot
dot -Tpng callgraph.dot -o callgraph.png

#pycg your_package_or_script.py -o cg.json
