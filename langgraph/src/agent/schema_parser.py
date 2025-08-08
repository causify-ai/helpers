#!/usr/bin/env python

"""
Schema Parser Module for AutoEDA Agent.

A standalone module to parse JSON/YAML schema files and extract column information
for automated exploratory data analysis.

Import as:

import schema_parser as schpar
"""

import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

import helpers.hdbg as hdbg
import helpers.hio as hio

# Configure logging.
logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """
    Represent information about a single column.
    """
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    nullable: bool = True
    default: Any = None
    constraints: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """
        Initialize default values for optional fields.
        """
        if self.constraints is None:
            self.constraints = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ParsedSchema:
    """
    Represent the complete parsed schema result.
    """
    columns: List[ColumnInfo]
    raw_schema: Dict[str, Any]
    schema_type: str
    total_columns: int
    required_columns: int
    optional_columns: int
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Calculate derived fields from columns.
        """
        self.total_columns = len(self.columns)
        self.required_columns = sum(1 for col in self.columns if col.required)
        self.optional_columns = self.total_columns - self.required_columns


class SchemaParser:
    """
    Parse various schema formats and extract column information.
    
    Supported formats:
    - JSON Schema
    - Custom column definitions
    - YAML schema files
    - Generic key-value structures
    """

    def __init__(
        self,
        *,
        include_metadata: bool = True,
        output_format: str = "detailed",
    ) -> None:
        """
        Initialize the schema parser.
        
        :param include_metadata: whether to include metadata in parsed results
        :param output_format: output format, either "detailed" or "simple"
        """
        hdbg.dassert_in(output_format, ["detailed", "simple"])
        self.include_metadata = include_metadata
        self.output_format = output_format
        self.supported_formats = ["json", "yaml", "yml"]

    def parse_file(self, file_path: str) -> ParsedSchema:
        """
        Parse schema from a file.
        
        :param file_path: path to the schema file
        :return: parsed schema object with results
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                error_msg = f"Schema file not found: {file_path}"
                return self._create_error_result(error_msg)
            
            if not self._is_supported_format(path.suffix):
                error_msg = f"Unsupported file format: {path.suffix}"
                return self._create_error_result(error_msg)
            
            # Read file content.
            content = hio.from_file(str(path))
            
            return self.parse_content(content, str(path))
            
        except Exception as e:
            _LOG.error("Error parsing file %s: %s", file_path, e)
            error_msg = f"Failed to parse file: {str(e)}"
            return self._create_error_result(error_msg)

    def parse_content(
        self,
        content: str,
        *,
        source: str = "content",
    ) -> ParsedSchema:
        """
        Parse schema from string content.
        
        :param content: schema content as string
        :param source: source identifier for logging
        :return: parsed schema object with results
        """
        try:
            schema_data = self._parse_schema_content(content)
            schema_type = self._detect_schema_type(schema_data)
            columns = self._extract_columns(schema_data, schema_type)
            
            _LOG.info(
                "Successfully parsed %d columns from %s",
                len(columns),
                source,
            )
            
            return ParsedSchema(
                columns=columns,
                raw_schema=schema_data,
                schema_type=schema_type,
                total_columns=len(columns),
                required_columns=0,  # Will be calculated in __post_init__.
                optional_columns=0,  # Will be calculated in __post_init__.
            )
            
        except Exception as e:
            _LOG.error("Error parsing content from %s: %s", source, e)
            error_msg = f"Failed to parse content: {str(e)}"
            return self._create_error_result(error_msg)

    def to_dict(self, parsed_schema: ParsedSchema) -> Dict[str, Any]:
        """
        Convert ParsedSchema to dictionary format.
        
        :param parsed_schema: parsed schema object to convert
        :return: dictionary representation of the schema
        """
        return {
            "columns": [
                {
                    "name": col.name,
                    "data_type": col.data_type,
                    "required": col.required,
                    "description": col.description,
                    "nullable": col.nullable,
                    "default": col.default,
                    "constraints": col.constraints,
                    "metadata": col.metadata if self.include_metadata else {},
                }
                for col in parsed_schema.columns
            ],
            "schema_info": {
                "schema_type": parsed_schema.schema_type,
                "total_columns": parsed_schema.total_columns,
                "required_columns": parsed_schema.required_columns,
                "optional_columns": parsed_schema.optional_columns,
            },
            "raw_schema": parsed_schema.raw_schema,
            "error_message": parsed_schema.error_message,
        }

    def to_dataframe_schema(self, parsed_schema: ParsedSchema) -> Dict[str, str]:
        """
        Convert to simple column_name: data_type mapping for pandas.
        
        :param parsed_schema: parsed schema object to convert
        :return: simple mapping of column names to data types
        """
        return {col.name: col.data_type for col in parsed_schema.columns}

    def _parse_schema_content(self, content: str) -> Dict[str, Any]:
        """
        Parse content as JSON or YAML.
        
        :param content: raw content string to parse
        :return: parsed data as dictionary
        """
        content = content.strip()
        
        # Try JSON first.
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try YAML.
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid JSON/YAML format: {e}")

    def _detect_schema_type(self, schema_data: Dict[str, Any]) -> str:
        """
        Detect the type of schema format.
        
        :param schema_data: parsed schema data
        :return: detected schema type
        """
        if "properties" in schema_data and "type" in schema_data:
            return "json_schema"
        elif "columns" in schema_data:
            return "custom_columns"
        elif "fields" in schema_data:
            return "fields_format"
        elif any(
            isinstance(v, dict) and ("type" in v or "dataType" in v)
            for v in schema_data.values()
        ):
            return "generic_properties"
        else:
            return "unknown"

    def _extract_columns(
        self,
        schema_data: Dict[str, Any],
        schema_type: str,
    ) -> List[ColumnInfo]:
        """
        Extract column information based on schema type.
        
        :param schema_data: parsed schema data
        :param schema_type: detected schema type
        :return: list of column information objects
        """
        extractors = {
            "json_schema": self._extract_from_json_schema,
            "custom_columns": self._extract_from_custom_format,
            "fields_format": self._extract_from_fields_format,
            "generic_properties": self._extract_from_generic_format,
            "unknown": self._extract_from_unknown_format,
        }
        
        extractor = extractors.get(schema_type, self._extract_from_unknown_format)
        return extractor(schema_data)

    def _extract_from_json_schema(
        self,
        schema_data: Dict[str, Any],
    ) -> List[ColumnInfo]:
        """
        Extract columns from JSON Schema format.
        
        :param schema_data: JSON schema data
        :return: list of column information objects
        """
        columns = []
        properties = schema_data.get("properties", {})
        required_fields = set(schema_data.get("required", []))
        
        for column_name, column_info in properties.items():
            constraints = {}
            metadata = {}
            
            # Extract constraints.
            for key in [
                "minimum",
                "maximum",
                "minLength",
                "maxLength",
                "pattern",
                "enum",
            ]:
                if key in column_info:
                    constraints[key] = column_info[key]
            
            # Extract metadata if enabled.
            if self.include_metadata:
                excluded_keys = [
                    "type",
                    "description",
                    "minimum",
                    "maximum",
                    "minLength",
                    "maxLength",
                    "pattern",
                    "enum",
                ]
                metadata = {
                    k: v
                    for k, v in column_info.items()
                    if k not in excluded_keys
                }
            
            column = ColumnInfo(
                name=column_name,
                data_type=self._map_json_schema_type(
                    column_info.get("type", "string")
                ),
                required=column_name in required_fields,
                description=column_info.get("description", ""),
                nullable=not (column_name in required_fields),
                default=column_info.get("default"),
                constraints=constraints,
                metadata=metadata,
            )
            
            columns.append(column)
        
        return columns

    def _extract_from_custom_format(
        self,
        schema_data: Dict[str, Any],
    ) -> List[ColumnInfo]:
        """
        Extract columns from custom columns format.
        
        :param schema_data: custom format schema data
        :return: list of column information objects
        """
        columns = []
        columns_data = schema_data.get("columns", [])
        
        for column_info in columns_data:
            if not isinstance(column_info, dict):
                continue
            
            constraints = column_info.get("constraints", {})
            metadata = {}
            
            if self.include_metadata:
                excluded_keys = [
                    "name",
                    "type",
                    "required",
                    "description",
                    "nullable",
                    "default",
                    "constraints",
                ]
                metadata = {
                    k: v
                    for k, v in column_info.items()
                    if k not in excluded_keys
                }
            
            column = ColumnInfo(
                name=column_info.get("name", ""),
                data_type=self._normalize_data_type(
                    column_info.get("type", "string")
                ),
                required=column_info.get("required", False),
                description=column_info.get("description", ""),
                nullable=column_info.get("nullable", True),
                default=column_info.get("default"),
                constraints=constraints,
                metadata=metadata,
            )
            
            columns.append(column)
        
        return columns

    def _extract_from_fields_format(
        self,
        schema_data: Dict[str, Any],
    ) -> List[ColumnInfo]:
        """
        Extract columns from fields format.
        
        :param schema_data: fields format schema data
        :return: list of column information objects
        """
        columns = []
        fields_data = schema_data.get("fields", [])
        
        for field_info in fields_data:
            if not isinstance(field_info, dict):
                continue
            
            constraints = field_info.get("constraints", {})
            metadata = {}
            
            if self.include_metadata:
                excluded_keys = [
                    "name",
                    "type",
                    "optional",
                    "description",
                    "constraints",
                ]
                metadata = {
                    k: v
                    for k, v in field_info.items()
                    if k not in excluded_keys
                }
            
            column = ColumnInfo(
                name=field_info.get("name", ""),
                data_type=self._normalize_data_type(
                    field_info.get("type", "string")
                ),
                required=not field_info.get("optional", True),
                description=field_info.get("description", ""),
                nullable=field_info.get("optional", True),
                constraints=constraints,
                metadata=metadata,
            )
            
            columns.append(column)
        
        return columns

    def _extract_from_generic_format(
        self,
        schema_data: Dict[str, Any],
    ) -> List[ColumnInfo]:
        """
        Extract columns from generic format.
        
        :param schema_data: generic format schema data
        :return: list of column information objects
        """
        columns = []
        
        for key, value in schema_data.items():
            if not isinstance(value, dict):
                continue
            
            if "type" not in value and "dataType" not in value:
                continue
            
            metadata = {}
            if self.include_metadata:
                excluded_keys = [
                    "type",
                    "dataType",
                    "required",
                    "description",
                    "nullable",
                ]
                metadata = {
                    k: v for k, v in value.items() if k not in excluded_keys
                }
            
            column = ColumnInfo(
                name=key,
                data_type=self._normalize_data_type(
                    value.get("type", value.get("dataType", "string"))
                ),
                required=value.get("required", False),
                description=value.get("description", ""),
                nullable=value.get("nullable", True),
                metadata=metadata,
            )
            
            columns.append(column)
        
        return columns

    def _extract_from_unknown_format(
        self,
        schema_data: Dict[str, Any],
    ) -> List[ColumnInfo]:
        """
        Extract columns from unknown format by making best guesses.
        
        :param schema_data: unknown format schema data
        :return: list of column information objects
        """
        columns = []
        
        # Try to extract any key-value pairs as potential columns.
        for key, value in schema_data.items():
            if isinstance(value, str):
                # Assume string values are data types.
                column = ColumnInfo(
                    name=key,
                    data_type=self._normalize_data_type(value),
                    description="Inferred from key-value pair",
                )
                columns.append(column)
        
        return columns

    def _map_json_schema_type(self, json_type: str) -> str:
        """
        Map JSON Schema types to standard data types.
        
        :param json_type: JSON schema type string
        :return: normalized data type
        """
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "number": "float",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
            "null": "null",
        }
        return type_mapping.get(json_type.lower(), "string")

    def _normalize_data_type(self, data_type: str) -> str:
        """
        Normalize various data type representations.
        
        :param data_type: raw data type string
        :return: normalized data type
        """
        if not isinstance(data_type, str):
            return "string"
        
        data_type = data_type.lower().strip()
        
        type_mapping = {
            # String types.
            "str": "string",
            "text": "string",
            "varchar": "string",
            "char": "string",
            "nvarchar": "string",
            # Integer types.
            "int": "integer",
            "int32": "integer",
            "int64": "integer",
            "bigint": "integer",
            "smallint": "integer",
            # Float types.
            "float": "float",
            "float32": "float",
            "float64": "float",
            "double": "float",
            "decimal": "float",
            "numeric": "float",
            "real": "float",
            # Boolean types.
            "bool": "boolean",
            "bit": "boolean",
            # Date/Time types.
            "datetime": "datetime",
            "datetime64": "datetime",
            "timestamp": "datetime",
            "date": "date",
            "time": "time",
            # Other types.
            "json": "object",
            "jsonb": "object",
            "uuid": "string",
            "blob": "binary",
            "binary": "binary",
        }
        
        return type_mapping.get(data_type, data_type)

    def _is_supported_format(self, file_extension: str) -> bool:
        """
        Check if file format is supported.
        
        :param file_extension: file extension to check
        :return: whether the format is supported
        """
        return file_extension.lower().lstrip(".") in self.supported_formats

    def _create_error_result(self, error_message: str) -> ParsedSchema:
        """
        Create a ParsedSchema with error information.
        
        :param error_message: error message to include
        :return: ParsedSchema object with error details
        """
        return ParsedSchema(
            columns=[],
            raw_schema={},
            schema_type="error",
            total_columns=0,
            required_columns=0,
            optional_columns=0,
            error_message=error_message,
        )


# #############################################################################
# Convenience functions.
# #############################################################################


def parse_schema_file(
    file_path: str,
    *,
    include_metadata: bool = True,
) -> ParsedSchema:
    """
    Parse a schema file using default settings.
    
    :param file_path: path to schema file
    :param include_metadata: whether to include metadata
    :return: parsed schema object
    """
    parser = SchemaParser(include_metadata=include_metadata)
    return parser.parse_file(file_path)


def parse_schema_content(
    content: str,
    *,
    include_metadata: bool = True,
) -> ParsedSchema:
    """
    Parse schema content using default settings.
    
    :param content: schema content as string
    :param include_metadata: whether to include metadata
    :return: parsed schema object
    """
    parser = SchemaParser(include_metadata=include_metadata)
    return parser.parse_content(content)


def main():
    parser = argparse.ArgumentParser(description="Parse a schema file and log the results.")
    parser.add_argument("schema_file", type=str, help="Path to the schema file (JSON)")
    args = parser.parse_args()

    # Read schema content from file
    try:
        with open(args.schema_file, "r") as f:
            schema_content = f.read()
    except Exception as e:
        _LOG.error("Failed to read schema file %s: %s", args.schema_file, e)
        return

    result = parse_schema_content(schema_content)
    if result.error_message:
        _LOG.error("Error: %s", result.error_message)
    else:
        _LOG.info("Successfully parsed %d columns", result.total_columns)
        _LOG.info("Required columns: %d", result.required_columns)
        _LOG.info("Optional columns: %d", result.optional_columns)
        _LOG.info("Schema type: %s", result.schema_type)
        _LOG.info("Columns:")
        for col in result.columns:
            _LOG.info("  - %s: %s (required: %s)", col.name, col.data_type, col.required)

if __name__ == "__main__":
    main()