# hpandas_dassert.py

## Index/Axis Validation & Assertions

- _get_index()
- dassert_index_is_datetime()
- dassert_unique_index()
- dassert_increasing_index()
- dassert_strictly_increasing_index()
- dassert_monotonic_index()
- dassert_time_indexed_df()
- dassert_indices_equal()
- dassert_columns_equal()
- dassert_axes_equal()

- dassert_series_type_is()
- dassert_series_type_in()
- dassert_valid_remap()
- dassert_approx_eq()
- dassert_is_days()

# hpandas_conversion.py

## DataFrame/Series Conversion

- to_series()
- as_series()

## Infer type

- infer_column_types()
- infer_column_types_df()
- convert_to_type()
- convert_col_to_int()
- cast_series_to_type()
- convert_df()

# hpandas_transform.py

## Resampling & Time Series Operations

- resample_index()
- resample_df()
- reindex_on_unix_epoch()
- find_gaps_in_dataframes()
- find_gaps_in_time_series()

## DataFrame Transformation

- apply_index_mode()
- apply_columns_mode()
- trim_df()

- str_to_df()
- _assemble_df_rows()

## Column Operations

- check_and_filter_matching_columns()
- _resolve_column_names()

## Merge

- merge_dfs()
- get_df_from_iterator()

## Filter

- subset_df()
- filter_df()

# hpandas_compare.py

- compare_dataframe_rows()
- compare_nans_in_dataframes()
- compare_dfs()

# hpandas_clean.py

- drop_duplicates()
- dropna()
- drop_axis_with_all_nans()
- drop_duplicated()
- remove_outliers()

# hpandas_display.py

- df_to_str()
- _df_to_str()
- _display()
- get_df_signature()
- convert_df_to_json_string()
- list_to_str()

# hpandas_io.py

- read_csv_to_df()
- read_parquet_to_df()
- to_gsheet()

# hpandas_multiindex.py

- add_multiindex_col()
- multiindex_df_info()
- subset_multiindex_df()
- compare_multiindex_dfs()

# hpandas_stats.py

- compute_duration_df()

- compute_weighted_sum()

- remap_obj()
- get_random_df()
- heatmap_df()
- to_perc()
- add_end_download_timestamp()

# hpandas_check_summary.py

- CheckSummary
