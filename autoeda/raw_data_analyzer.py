#!/usr/bin/env python

"""
Raw Data Analyzer for AutoEDA Agent.

Analyzes raw data files (CSV, JSON, Parquet, Excel) and generates schema.json files
for use with the schema parser module.

Import as:

import raw_data_analyzer as rdanal
"""

import argparse
import dataclasses
import json
import logging
import pathlib
import warnings
from typing import Any, Dict, List, Optional

import pandas as pd

import helpers.hio as hio

# Configure logging.
logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


# #############################################################################
# ColumnAnalysis
# #############################################################################


@dataclasses.dataclass
class ColumnAnalysis:
    """
    Represent analysis results for a single column.
    """

    name: str
    data_type: str
    nullable: bool
    null_count: int
    unique_count: int
    sample_values: List[Any]
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    pattern: Optional[str] = None
    format_hint: Optional[str] = None


# #############################################################################
# DataAnalysisResult
# #############################################################################


@dataclasses.dataclass
class DataAnalysisResult:
    """
    Represent the complete data analysis result.
    """

    file_path: str
    total_rows: int
    total_columns: int
    columns: List[ColumnAnalysis]
    suggested_schema: Dict[str, Any]
    analysis_metadata: Dict[str, Any]
    error_message: Optional[str] = None


# #############################################################################
# RawDataAnalyzer
# #############################################################################


class RawDataAnalyzer:
    """
    Analyze raw data files and generate schema definitions.

    Supported formats:
    - CSV files
    - JSON files
    - Parquet files
    - Excel files
    """

    def __init__(
        self,
        *,
        sample_size: int = 10000,
        max_unique_values: int = 100,
        datetime_formats: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the raw data analyzer.

        :param sample_size: maximum number of rows to sample for
            analysis
        :param max_unique_values: maximum unique values to consider for
            enum types
        :param datetime_formats: list of datetime formats to try for
            detection
        """
        self.sample_size = sample_size
        self.max_unique_values = max_unique_values
        self.datetime_threshold = 0.8  # 80% success rate for datetime detection
        self.datetime_formats = datetime_formats or [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y%m%d",
        ]
        self.supported_formats = [".csv", ".json", ".parquet", ".xlsx", ".xls"]

    def analyze_file(self, file_path: str) -> DataAnalysisResult:
        """
        Analyze a data file and generate schema information.

        :param file_path: path to the data file to analyze
        :return: analysis results with suggested schema
        """
        try:
            path = pathlib.Path(file_path)
            if not path.exists():
                error_msg = f"Data file not found: {file_path}"
                return self._create_error_result(file_path, error_msg)
            if not self._is_supported_format(path.suffix):
                error_msg = f"Unsupported file format: {path.suffix}"
                return self._create_error_result(file_path, error_msg)
            # Load data based on file format.
            df = self._load_data(file_path)
            # Sample data if it's too large.
            if len(df) > self.sample_size:
                _LOG.info(
                    "Sampling %d rows from %d total rows",
                    self.sample_size,
                    len(df),
                )
                df = df.sample(n=self.sample_size, random_state=42)
            # Analyze each column.
            columns_analysis = self._analyze_columns(df)
            # Generate suggested schema.
            suggested_schema = self._generate_schema(columns_analysis, df)
            # Create analysis metadata.
            analysis_metadata = self._create_analysis_metadata(file_path, df)
            _LOG.info(
                "Successfully analyzed %d columns from %s",
                len(columns_analysis),
                file_path,
            )
            return DataAnalysisResult(
                file_path=file_path,
                total_rows=len(df),
                total_columns=len(df.columns),
                columns=columns_analysis,
                suggested_schema=suggested_schema,
                analysis_metadata=analysis_metadata,
            )
        except (IOError, ValueError, pd.errors.ParserError) as e:
            _LOG.error("Error analyzing file %s: %s", file_path, e)
            error_msg = f"Failed to analyze file: {str(e)}"
            return self._create_error_result(file_path, error_msg)

    def save_schema(
        self,
        analysis_result: DataAnalysisResult,
        output_path: str,
        *,
        include_analysis_metadata: bool = True,
    ) -> None:
        """
        Save the generated schema to a JSON file.

        :param analysis_result: analysis result containing the schema
        :param output_path: path where to save the schema.json file
        :param include_analysis_metadata: whether to include analysis
            metadata
        """
        try:
            schema_data = analysis_result.suggested_schema.copy()

            if include_analysis_metadata:
                schema_data["_analysis_metadata"] = (
                    analysis_result.analysis_metadata
                )

            # Ensure output directory exists.
            output_dir = pathlib.Path(output_path).parent
            hio.create_dir(str(output_dir), incremental=True)

            # Save schema to file.
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(schema_data, f, indent=2, default=str)

            _LOG.info("Schema saved to %s", output_path)

        except Exception as e:
            _LOG.error("Error saving schema to %s: %s", output_path, e)
            raise

    def _load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load data from file based on format.

        :param file_path: path to the data file
        :return: loaded DataFrame
        """
        path = pathlib.Path(file_path)
        file_extension = path.suffix.lower()
        if file_extension == ".csv":
            # Try different encodings and separators.
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                for sep in [",", ";", "\t"]:
                    try:
                        df = pd.read_csv(
                            file_path,
                            encoding=encoding,
                            sep=sep,
                            nrows=self.sample_size,
                        )
                        # Good indicator of correct separator.
                        if len(df.columns) > 1:
                            _LOG.debug(
                                "Successfully loaded CSV with encoding=%s, sep='%s'",
                                encoding,
                                sep,
                            )
                            return df
                    except (ValueError, TypeError, pd.errors.ParserError):
                        continue
            # Fallback to default pandas behavior.
            return pd.read_csv(file_path, nrows=self.sample_size)
        if file_extension == ".json":
            return pd.read_json(file_path, lines=True, nrows=self.sample_size)
        if file_extension == ".parquet":
            return pd.read_parquet(file_path)
        if file_extension in [".xlsx", ".xls"]:
            return pd.read_excel(file_path, nrows=self.sample_size)
        raise ValueError(f"Unsupported file format: {file_extension}")

    def _analyze_columns(self, df: pd.DataFrame) -> List[ColumnAnalysis]:
        """
        Analyze each column in the DataFrame.

        :param df: DataFrame to analyze
        :return: list of column analysis results
        """
        columns_analysis = []
        for col_name in df.columns:
            col_data = df[col_name]
            analysis = self._analyze_single_column(col_name, col_data)
            columns_analysis.append(analysis)
        return columns_analysis

    def _analyze_single_column(
        self,
        col_name: str,
        col_data: pd.Series,
    ) -> ColumnAnalysis:
        """
        Analyze a single column.

        :param col_name: name of the column
        :param col_data: column data as pandas Series
        :return: column analysis result
        """
        # Basic statistics.
        null_count = col_data.isnull().sum()
        unique_count = col_data.nunique()
        nullable = null_count > 0

        # Sample non-null values.
        non_null_data = col_data.dropna()
        sample_values = (
            non_null_data.head(5).tolist() if len(non_null_data) > 0 else []
        )

        # Infer data type.
        data_type, format_hint = self._infer_data_type(non_null_data)

        # Calculate statistics for numeric columns.
        min_value = None
        max_value = None
        mean_value = None
        std_value = None

        if data_type in ["integer", "float"] and len(non_null_data) > 0:
            try:
                numeric_data = pd.to_numeric(non_null_data, errors="coerce")
                min_value = float(numeric_data.min())
                max_value = float(numeric_data.max())
                mean_value = float(numeric_data.mean())
                std_value = float(numeric_data.std())
            except (ValueError, TypeError):
                pass

        # Detect patterns for string columns.
        pattern = None
        if data_type == "string" and len(non_null_data) > 0:
            pattern = self._detect_pattern(non_null_data)

        return ColumnAnalysis(
            name=col_name,
            data_type=data_type,
            nullable=nullable,
            null_count=int(null_count),
            unique_count=int(unique_count),
            sample_values=sample_values,
            min_value=min_value,
            max_value=max_value,
            mean_value=mean_value,
            std_value=std_value,
            pattern=pattern,
            format_hint=format_hint,
        )

    def _infer_data_type(self, data: pd.Series) -> tuple[str, Optional[str]]:
        """
        Infer the data type of a column.

        :param data: column data (non-null values)
        :return: tuple of (data_type, format_hint)
        """
        result_type = "string"
        format_hint = None
        if len(data) == 0:
            return result_type, format_hint
        # Check for boolean.
        if data.dtype == bool or set(data.astype(str).str.lower()) <= {
            "true",
            "false",
            "t",
            "f",
            "yes",
            "no",
            "y",
            "n",
            "1",
            "0",
        }:
            result_type = "boolean"
        # Check for integer.
        elif data.dtype in ["int64", "int32", "int16", "int8"]:
            result_type = "integer"
        # Check for float.
        elif data.dtype in ["float64", "float32"]:
            result_type = "float"
        else:
            # Try to convert to numeric.
            try:
                numeric_data = pd.to_numeric(data, errors="coerce")
                if not numeric_data.isnull().all():
                    # Check if all values are integers.
                    if (
                        numeric_data.fillna(0)
                        .apply(lambda x: x.is_integer())
                        .all()
                    ):
                        result_type = "integer"
                    else:
                        result_type = "float"
                else:
                    # Check for datetime.
                    datetime_type, datetime_format = self._check_datetime(data)
                    if datetime_type:
                        result_type = datetime_type
                        format_hint = datetime_format
            except (ValueError, TypeError):
                # Check for datetime as fallback.
                datetime_type, datetime_format = self._check_datetime(data)
                if datetime_type:
                    result_type = datetime_type
                    format_hint = datetime_format
        return result_type, format_hint

    def _check_datetime(
        self, data: pd.Series
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Check if data represents datetime values with improved detection.

        :param data: column data to check
        :return: tuple of (datetime_type, format_hint)
        """
        # Skip if data looks purely numeric.
        try:
            pd.to_numeric(data.head(10), errors="raise")
            return None, None
        except (ValueError, TypeError):
            pass
        # Sample a subset for testing.
        sample_data = data.head(min(100, len(data)))
        # Try specific datetime formats first.
        for fmt in self.datetime_formats:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    parsed = pd.to_datetime(
                        sample_data, format=fmt, errors="coerce"
                    )
                # Check success rate.
                success_rate = 1 - parsed.isnull().sum() / len(sample_data)
                if success_rate >= self.datetime_threshold:
                    # Determine if it's date or datetime.
                    non_null_parsed = parsed.dropna()
                    if len(non_null_parsed) > 0:
                        # Check if all times are midnight (date-only).
                        if all(
                            t.time() == non_null_parsed.iloc[0].time()
                            for t in non_null_parsed.head(10)
                        ):
                            return "date", fmt
                        return "datetime", fmt
            except (ValueError, TypeError, AttributeError):
                continue
        # Try pandas automatic parsing as last resort.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed = pd.to_datetime(
                    sample_data, errors="coerce", infer_datetime_format=True
                )
            success_rate = 1 - parsed.isnull().sum() / len(sample_data)
            if success_rate >= self.datetime_threshold:
                return "datetime", "auto"
        except (ValueError, TypeError, AttributeError):
            pass
        return None, None

    def _detect_pattern(self, data: pd.Series) -> Optional[str]:
        """
        Detect common patterns in string data.

        :param data: string column data
        :return: detected pattern or None
        """
        str_data = data.astype(str)
        # Check for common patterns.
        patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^[\+]?[1-9]?[0-9]{7,15}$",
            "url": r"^https?://[^\s/$.?#].[^\s]*$",
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "ip_address": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        }
        for pattern_name, pattern_regex in patterns.items():
            if str_data.str.match(pattern_regex, case=False).mean() > 0.8:
                return pattern_name
        return None

    def _generate_schema(
        self,
        columns_analysis: List[ColumnAnalysis],
        df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Generate JSON Schema from column analysis.

        :param columns_analysis: list of analyzed columns
        :param df: original DataFrame
        :return: JSON Schema dictionary
        """
        properties = {}
        required_fields = []

        for col in columns_analysis:
            col_schema = {
                "type": self._map_to_json_schema_type(col.data_type),
                "description": f"Column '{col.name}' with {col.unique_count} unique values",
            }

            # Add format hint if available.
            if col.format_hint and col.format_hint != "auto":
                col_schema["format"] = col.format_hint

            # Add constraints for numeric fields.
            if col.data_type in ["integer", "float"]:
                if col.min_value is not None:
                    col_schema["minimum"] = col.min_value
                if col.max_value is not None:
                    col_schema["maximum"] = col.max_value

            # Add enum for low-cardinality categorical fields.
            if (
                col.data_type == "string"
                and col.unique_count <= self.max_unique_values
                and col.unique_count > 1
            ):
                unique_values = df[col.name].dropna().unique().tolist()
                col_schema["enum"] = unique_values[:50]  # Limit enum size.

            # Add pattern if detected.
            if col.pattern:
                col_schema["pattern"] = col.pattern

            properties[col.name] = col_schema

            # Mark as required if no null values.
            if not col.nullable:
                required_fields.append(col.name)

        schema = {
            "type": "object",
            "title": "Generated Schema",
            "description": f"Auto-generated schema for data with {len(columns_analysis)} columns",
            "properties": properties,
        }

        if required_fields:
            schema["required"] = required_fields

        return schema

    def _map_to_json_schema_type(self, data_type: str) -> str:
        """
        Map internal data types to JSON Schema types.

        :param data_type: internal data type
        :return: JSON Schema type
        """
        type_mapping = {
            "integer": "integer",
            "float": "number",
            "boolean": "boolean",
            "string": "string",
            "datetime": "string",
            "date": "string",
            "object": "object",
            "array": "array",
        }
        return type_mapping.get(data_type, "string")

    def _create_analysis_metadata(
        self,
        file_path: str,
        df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Create metadata about the analysis process.

        :param file_path: path to analyzed file
        :param df: analyzed DataFrame
        :return: analysis metadata
        """
        return {
            "analysis_timestamp": pd.Timestamp.now().isoformat(),
            "analyzer_version": "1.0.0",
            "source_file": file_path,
            "sample_size": min(len(df), self.sample_size),
            "total_rows_analyzed": len(df),
            "total_columns_analyzed": len(df.columns),
            "file_size_bytes": pathlib.Path(file_path).stat().st_size,
            "analysis_settings": {
                "max_unique_values": self.max_unique_values,
                "datetime_formats": self.datetime_formats,
            },
        }

    def _is_supported_format(self, file_extension: str) -> bool:
        """
        Check if file format is supported.

        :param file_extension: file extension to check
        :return: whether the format is supported
        """
        return file_extension.lower() in self.supported_formats

    def _create_error_result(
        self,
        file_path: str,
        error_message: str,
    ) -> DataAnalysisResult:
        """
        Create a DataAnalysisResult with error information.

        :param file_path: path to the file that caused the error
        :param error_message: error message to include
        :return: DataAnalysisResult object with error details
        """
        return DataAnalysisResult(
            file_path=file_path,
            total_rows=0,
            total_columns=0,
            columns=[],
            suggested_schema={},
            analysis_metadata={},
            error_message=error_message,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze raw data files and generate schema information."
    )
    parser.add_argument("file", type=str, help="Path to the data file to analyze")
    args = parser.parse_args()
    analyzer = RawDataAnalyzer()
    result = analyzer.analyze_file(args.file)
    if result.error_message:
        _LOG.error("Error: %s", result.error_message)
    else:
        _LOG.info("File: %s", result.file_path)
        _LOG.info("Total rows: %d", result.total_rows)
        _LOG.info("Total columns: %d", result.total_columns)
        _LOG.info("Columns:")
        for col in result.columns:
            _LOG.info(
                "  - %s: %s, nullable=%s", col.name, col.data_type, col.nullable
            )
        _LOG.info("Suggested schema: %s", result.suggested_schema)
        _LOG.info("Metadata: %s", result.analysis_metadata)
        # Save suggested schema to JSON file.
        schema_path = args.file + ".schema.json"
        try:
            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(result.suggested_schema, f, indent=2)
            _LOG.info("Saved schema to %s", schema_path)
        except (IOError, TypeError, ValueError) as e:
            _LOG.error("Failed to save schema to %s: %s", schema_path, e)


if __name__ == "__main__":
    main()
