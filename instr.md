Find all the tests that can't run because they have a dependency from a package
that is not available, e.g.,

ImportError while importing test module '/Users/saggese/src/umd_classes1/helpers_root/helpers/test/test_hasyncio.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../venv/client_venv.helpers/lib/python3.11/site-packages/_pytest/python.py:493: in importtestmodule
    mod = import_path(
../venv/client_venv.helpers/lib/python3.11/site-packages/_pytest/pathlib.py:582: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.11/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
../venv/client_venv.helpers/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:174: in exec_module
    exec(co, module.__dict__)
helpers_root/helpers/test/test_hasyncio.py:5: in <module>
    import helpers.hasyncio as hasynci
helpers_root/helpers/hasyncio.py:26: in <module>
    import async_solipsism  # type: ignore[import-not-found]
E   ModuleNotFoundError: No module named 'async_solipsism'
__________________________________________________________________________________________________ ERROR collecting helpers_root/helpers/test/test_haws.py __________________________________________________________________________________________________
ImportError while importing test module '/Users/saggese/src/umd_classes1/helpers_root/helpers/test/test_haws.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../venv/client_venv.helpers/lib/python3.11/site-packages/_pytest/python.py:493: in importtestmodule
    mod = import_path(
../venv/client_venv.helpers/lib/python3.11/site-packages/_pytest/pathlib.py:582: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.11/3.11.11/Frameworks/Python.framework/Versions/3.11/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1204: in _gcd_import
    ???
<frozen importlib._bootstrap>:1176: in _find_and_load
    ???
<frozen importlib._bootstrap>:1147: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:690: in _load_unlocked
    ???
../venv/client_venv.helpers/lib/python3.11/site-packages/_pytest/assertion/rewrite.py:174: in exec_module
    exec(co, module.__dict__)
helpers_root/helpers/test/test_haws.py:8: in <module>
    from moto import mock_aws
E   ModuleNotFoundError: No module named 'moto'


and mark them as pytest.mark.need_dev_container
