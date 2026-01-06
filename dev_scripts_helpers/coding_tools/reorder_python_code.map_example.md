<!-- toc -->

- [Hpandas_Dassert.Py](#hpandas_dassertpy)
  * [Index/Axis Validation & Assertions](#indexaxis-validation--assertions)
- [Hpandas_Conversion.Py](#hpandas_conversionpy)
  * [Dataframe/Series Conversion](#dataframeseries-conversion)
  * [Infer Type](#infer-type)
- [Hpandas_Transform.Py](#hpandas_transformpy)
  * [Resampling & Time Series Operations](#resampling--time-series-operations)
  * [Dataframe Transformation](#dataframe-transformation)
  * [Column Operations](#column-operations)
  * [Merge](#merge)
  * [Filter](#filter)
- [Hpandas_Compare.Py](#hpandas_comparepy)
- [Hpandas_Clean.Py](#hpandas_cleanpy)
- [Hpandas_Display.Py](#hpandas_displaypy)
- [Hpandas_Io.Py](#hpandas_iopy)
- [Hpandas_Multiindex.Py](#hpandas_multiindexpy)
- [Hpandas_Stats.Py](#hpandas_statspy)
- [Hpandas_Check_Summary.Py](#hpandas_check_summarypy)

<!-- tocstop -->

# hpandas_Dassert.Py

## Index/Axis Validation & Assertions

- \_get_index()
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

# Hpandas_Conversion.Py

## Dataframe/Series Conversion

- to_series()
- as_series()

## Infer Type

- Infer_column_types()
- Infer_column_types_df()
- Convert_to_type()
- Convert_col_to_int()
- Cast_series_to_type()
- Convert_df()

# Hpandas_Transform.Py

## Resampling & Time Series Operations

- Resample_index()
- Resample_df()
- Reindex_on_unix_epoch()
- Find_gaps_in_dataframes()
- Find_gaps_in_time_series()

## Dataframe Transformation

- Apply_index_mode()
- Apply_columns_mode()
- Trim_df()

- Str_to_df()
- \_assemble_df_rows()

## Column Operations

- Check_and_filter_matching_columns()
- \_resolve_column_names()

## Merge

- Merge_dfs()
- Get_df_from_iterator()

## Filter

- Subset_df()
- Filter_df()

# Hpandas_Compare.Py

- Compare_dataframe_rows()
- Compare_nans_in_dataframes()
- Compare_dfs()

# Hpandas_Clean.Py

- Drop_duplicates()
- Dropna()
- Drop_axis_with_all_nans()
- Drop_duplicated()
- Remove_outliers()

# Hpandas_Display.Py

- Df_to_str()
- \_df_to_str()
- \_display()
- Get_df_signature()
- Convert_df_to_json_string()
- List_to_str()

# Hpandas_Io.Py

- Read_csv_to_df()
- Read_parquet_to_df()
- To_gsheet()

# Hpandas_Multiindex.Py

- Add_multiindex_col()
- Multiindex_df_info()
- Subset_multiindex_df()
- Compare_multiindex_dfs()

# Hpandas_Stats.Py

- Compute_duration_df()

- Compute_weighted_sum()

- Remap_obj()
- Get_random_df()
- Heatmap_df()
- To_perc()
- Add_end_download_timestamp()

# Hpandas_Check_Summary.Py

- CheckSummary
