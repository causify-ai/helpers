This document organizes all functions in `helpers/hpandas.py` into logical
categories based on their functionality.

The header of level 1 is the file that the code needs to go in
- E.g.,. hpandas_dassert.py means that all the code needs to go in helpers/hpandas_dassert.py

The code of each function needs to be copied exactly

The functions need to be in the order requested

The header of level 3 means that all the functions in that chunk
need to separated by a 

```
# #############################################################################
# Index/Axis Validation & Assertions
# #############################################################################
```

- hpandas.py should have the following format

from helpers.hpandas_dassert import *  # isort:skip  # noqa: F401,F403 # pylint: disable=unused-import,unused-wildcard-import,wildcard-import
from helpers.hpandas_conversion import *  # isort:skip  # noqa: F401,F403 # pylint: disable=unused-import,unused-wildcard-import,wildcard-import

# hpandas_dassert.py

### Index/Axis Validation & Assertions

- `_get_index()` - Extract the index from a Pandas object (Index, DataFrame, or Series)
- `dassert_index_is_datetime()` - Assert that the index contains datetime values
- `dassert_unique_index()` - Assert that the index has unique values
- `dassert_increasing_index()` - Assert that the index is monotonically increasing
- `dassert_strictly_increasing_index()` - Assert that the index is strictly increasing (unique + increasing)
- `dassert_monotonic_index()` - Assert that the index is monotonic (strictly increasing or decreasing)
- `dassert_time_indexed_df()` - Validate that DataFrame is time-indexed and well-formed
- `dassert_indices_equal()` - Assert that two DataFrames have equal indices
- `dassert_columns_equal()` - Assert that two DataFrames have equal columns
- `dassert_axes_equal()` - Assert that two DataFrames have equal indices and columns

- `dassert_series_type_is()` - Assert that a Series has a specific data type
- `dassert_series_type_in()` - Assert that a Series data type is one of the specified types
- `dassert_valid_remap()` - Assert that remapping rows/columns is valid
- `dassert_approx_eq()` - Assert approximate equality of values with tolerance
- `dassert_is_days()` - Assert that a Timedelta is an integer number of days

# hpandas_conversion.py

### DataFrame/Series Conversion

- `to_series()` - Convert a single-column DataFrame to a Series
- `as_series()` - Convert a single-column DataFrame to a Series or no-op if already a Series

### Infer type

- `infer_column_types()` - Determine the predominant data type in a column
- `infer_column_types_df()` - Identify predominant data type for each column in a DataFrame
- `convert_to_type()` - Convert a Series to a specified data type
- `convert_col_to_int()` - Convert a column to integer type
- `cast_series_to_type()` - Convert a Pandas Series to a given type
- `convert_df()` - Convert each DataFrame column to its predominant type

# hpandas_transform.py

### Resampling & Time Series Operations

- `resample_index()` - Resample a DatetimeIndex to a specified frequency
- `resample_df()` - Resample DataFrame by placing NaN in missing locations
- `reindex_on_unix_epoch()` - Transform Unix epoch column into a datetime index
- `find_gaps_in_dataframes()` - Find data present in one DataFrame but missing in another
- `find_gaps_in_time_series()` - Find missing points in a time series over a specified interval

### DataFrame Transformation

- `apply_index_mode()` - Process DataFrames according to index mode (assert_equal, intersect, leave_unchanged)
- `apply_columns_mode()` - Process DataFrames according to column mode (assert_equal, intersect, leave_unchanged)
- `trim_df()` - Trim DataFrame to a specified time interval

- `str_to_df()` - Convert a string representation of a DataFrame into a Pandas DataFrame
- `_assemble_df_rows()` - Organize DataFrame values into a column-row structure

### Column Operations

- `check_and_filter_matching_columns()` - Check and filter columns based on required columns
- `_resolve_column_names()` - Resolve column names and perform sanity checks

### Merge

- `merge_dfs()` - Wrapper around pd.merge with threshold validation
- `get_df_from_iterator()` - Concatenate all DataFrames in an iterator into one DataFrame

### Filter

- `subset_df()` - Remove N rows from input data and shuffle the remaining ones
- `filter_df()` - Filter DataFrame by column value

# hpandas_compare.py

- `compare_dataframe_rows()` - Compare contents of rows with same indices
- `compare_nans_in_dataframes()` - Compare DataFrames in terms of NaN equality
- `compare_dfs()` - Compare two DataFrames with various modes (diff, pct_change)

# hpandas_clean.py

- `drop_duplicates()` - Wrapper around pandas.drop_duplicates() with additional options
- `dropna()` - Wrapper around pandas.dropna() with reporting and inf handling
- `drop_axis_with_all_nans()` - Remove columns and rows containing only NaNs
- `drop_duplicated()` - Drop duplicates considering index and ignoring NaNs
- `remove_outliers()` - Remove outliers based on quantile thresholds

# hpandas_display.py

- `df_to_str()` - Print DataFrame to string with comprehensive formatting options
- `_df_to_str()` - Internal helper for df_to_str()
- `_display()` - Display DataFrame in a notebook at a given log level
- `get_df_signature()` - Compute a simple signature of a DataFrame for testing
- `convert_df_to_json_string()` - Convert DataFrame to pretty-printed JSON string
- `list_to_str()` - Convert a list of values into a formatted string representation

# hpandas_io.py

- `read_csv_to_df()` - Read a CSV file into a DataFrame
- `read_parquet_to_df()` - Read a Parquet file into a DataFrame
- `to_gsheet()` - Save a DataFrame to a Google Sheet

# hpandas_multiindex.py

- `add_multiindex_col()` - Add a column to a multi-index DataFrame
- `multiindex_df_info()` - Report information about a multi-index DataFrame
- `subset_multiindex_df()` - Filter multi-index DataFrame by timestamp index and column levels
- `compare_multiindex_dfs()` - Subset and compare two multi-index DataFrames

# hpandas_stats.py

- `compute_duration_df()` - Compute statistics about time indices for a dictionary of DataFrames

- `compute_weighted_sum()` - Compute weighted sums of DataFrames using weights

- `remap_obj()` - Substitute each value of an object with another value from a dictionary
- `get_random_df()` - Generate DataFrame with random data and datetime index
- `heatmap_df()` - Colorize a DataFrame with a heatmap based on numeric values
- `to_perc()` - Report percentage of True values for a list/Series
- `add_end_download_timestamp()` - Add a column with the current timestamp to a DataFrame

# hpandas_check_summary.py

- CheckSummary
