# Python Code Coverage with `pytest` and the `coverage` Module

## Overview
- Code coverage is a metric used to measure how much of your source code is
  exercised during test execution
- In Python, combining `pytest` (a testing framework) with the `coverage` module
  allows you to assess and improve the quality of your tests

## Tools Required
- **pytest**: A framework for writing and running Python tests.
- **coverage.py**: A tool to measure code coverage of Python programs.

- Install both using pip:
  ```bash
  > pip install pytest coverage pytest-cov
  ```

## Basic Workflow

- Assume you have a `test_math.py` containing unit tests:
  ```python
  from my_module import add

  def test_add():
      assert add(2, 3) == 5
  ```

- Run tests with coverage and collects coverage data:
  ```bash
  > pytest --cov=test_math.py
  ```
  or
  ```bash
  > coverage run -m pytest
  ```
- The options for `pytest coverage` are:
	```
	coverage reporting with distributed testing support:
		--cov=[SOURCE]        Path or package name to measure during execution (multi-
													allowed). Use --cov= to not do any source filtering and
													record everything.
		--cov-reset           Reset cov sources accumulated in options so far.
		--cov-report=TYPE     Type of report to generate: term, term-missing,
													annotate, html, xml, json, lcov (multi-allowed). term,
													term-missing may be followed by ":skip-covered".
													annotate, html, xml, json and lcov may be followed by
													":DEST" where DEST specifies the output location. Use
													--cov-report= to not generate any output.
		--cov-config=PATH     Config file for coverage. Default: .coveragerc
		--no-cov-on-fail      Do not report coverage if test run fails. Default: False
		--no-cov              Disable coverage report completely (useful for
													debuggers). Default: False
		--cov-fail-under=MIN  Fail if the total coverage is less than MIN.
		--cov-append          Do not delete coverage but append to current. Default:
													False
		--cov-branch          Enable branch coverage.
		--cov-precision=COV_PRECISION
													Override the reporting precision.
		--cov-context=CONTEXT
													Dynamic contexts to use. "test" for now.
	```

- After running the tests, display a coverage summary in the terminal:
  ```bash
  > coverage report

  Name           Stmts   Miss  Cover
  ------------------------------
  my_module.py      10      2    80%
  ```

- To view a detailed coverage report in your browser:
  ```bash
  > coverage html
  ```
- This generates an htmlcov directory containing an index.html file you can open
  in a browser

	```
	> coverage --help
	Coverage.py, version 7.8.0 with C extension
	Measure, collect, and report on code coverage in Python programs.

	usage: coverage <command> [options] [args]

	Commands:
			annotate    Annotate source files with execution information.
			combine     Combine a number of data files.
			debug       Display information about the internals of coverage.py
			erase       Erase previously collected coverage data.
			help        Get help on using coverage.py.
			html        Create an HTML report.
			json        Create a JSON report of coverage results.
			lcov        Create an LCOV report of coverage results.
			report      Report coverage stats on modules.
			run         Run a Python program and measure code execution.
			xml         Create an XML report of coverage results.

	Use "coverage help <command>" for detailed help on any command.
	Full documentation is at https://coverage.readthedocs.io/en/7.8.0
	```

## Use examples

- You want to measure the coverage of the codebase from a given unit tests
	```
	> pytest helpers/test/test_hmarkdown*.py --cov 2>&1 | tee log.txt
	...
	collected 117 items

	helpers/test/test_hmarkdown.py::Test_header_list_to_vim_cfile1::test_get_header_list1 (0.00 s) PASSED [  0%]
	helpers/test/test_hmarkdown.py::Test_header_list_to_markdown1::test_mode_headers1 (0.00 s) PASSED [  1%]
	helpers/test/test_hmarkdown.py::Test_header_list_to_markdown1::test_mode_list1 (0.00 s) PASSED [  2%]
	helpers/test/test_hmarkdown.py::Test_replace_fenced_blocks_with_tags1::test1 (0.00 s) PASSED [  3%]
	...

	================================ tests coverage ================================
	_______________ coverage: platform linux, python 3.12.3-final-0 ________________

	Name                                     Stmts   Miss Branch BrPart  Cover
	--------------------------------------------------------------------------
	__init__.py                                  0      0      0      0   100%
	conftest.py                                 79     38     18      7    49%
	helpers/__init__.py                          0      0      0      0   100%
	helpers/hcoverage.py                        69     53     14      0    19%
	helpers/hdbg.py                            394    267    136     23    29%
	helpers/hdocker.py                         564    510    102      0     8%
	helpers/henv.py                            216     92     46      4    50%
	helpers/hgit.py                            573    491    130      0    12%
	helpers/hintrospection.py                  125    102     48      0    13%
	helpers/hio.py                             345    244    118     12    25%
	...
	helpers/test/test_hmarkdown_bullets.py     132      0      2      0   100%
	--------------------------------------------------------------------------
	TOTAL                                     6956   3824   1700    168    41%
	```

- Generate the coverage for only certain target code (e.g.,
	`helpers/hmarkdown*.py`)
	```bash
	> coverage report --include=helpers/hmarkdown*.py
	Name                                 Stmts   Miss Branch BrPart  Cover
	----------------------------------------------------------------------
	helpers/hmarkdown.py                     9      0      0      0   100%
	helpers/hmarkdown_bullets.py            91     24     42      5    68%
	helpers/hmarkdown_coloring.py           60     19     16      2    62%
	helpers/hmarkdown_comments.py           28     12     10      4    53%
	helpers/hmarkdown_fenced_blocks.py      55      0     14      0   100%
	helpers/hmarkdown_filtering.py          53     43      6      0    17%
	helpers/hmarkdown_formatting.py        101     34     18      1    69%
	helpers/hmarkdown_headers.py           226      6     88      7    96%
	helpers/hmarkdown_rules.py             101     19     42      3    80%
	helpers/hmarkdown_slides.py             52      2     16      4    91%
	----------------------------------------------------------------------
	TOTAL                                  776    159    252     26    78%
	```

- 
