"""
E.g., ```

# Find all the dependency of a module from itself
> i find_dependency --module-name "amp.dataflow.model" --mode "find_lev2_deps" --ignore-helpers --only-module dataflow
amp/dataflow/model/stats_computer.py:16 dataflow.core
amp/dataflow/model/model_plotter.py:4   dataflow.model
```

:param module_name: the module path to analyze (e.g., `amp.dataflow.model`)
:param mode:
    - `print_deps`: print the result of grepping for imports
    - `find_deps`: find all the dependencies
    - `find_lev1_deps`, `find_lev2_deps`: find all the dependencies
:param only_module: keep only imports containing a certain module (e.g., `dataflow`)
:param ignore_standard_libs: ignore the Python standard libs (e.g., `os`, `...`)
:param ignore_helpers: ignore the `helper` lib
:param remove_dups: remove the duplicated imports
"""
