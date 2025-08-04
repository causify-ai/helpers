"""
Import as:

import dev_scripts_helpers.documentation.AgenticEDA.file_validator as dshdafva
"""

import os
import typing

import pandas as pd


# #############################################################################
# FileValidator
# #############################################################################


class FileValidator:
    """
    Validates input files and data integrity.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_file_path(self, file_path: str, root_dir: str) -> bool:
        """
        Validate if file path exists and is readable.

        Args:
            file_path: Path to the file to validate.
            root_dir: Root directory to resolve relative paths (default: current working directory).

        Returns
            bool: True if the file path is valid, False otherwise.
        """
        if not file_path or pd.isna(file_path):
            return False
        if root_dir is None:
            root_dir = os.getcwd()
        if os.path.isabs(file_path):
            absolute_path = file_path
        else:
            absolute_path = os.path.join(root_dir, file_path)
        # Normalize the path to avoid issues with different path formats
        absolute_path = os.path.normpath(absolute_path)
        # Check if the file exists and is readable
        if not os.path.exists(absolute_path):
            self.errors.append(
                f"File does not exist: {absolute_path} (original: {file_path})"
            )
            return False
        if not os.access(absolute_path, os.R_OK):
            self.errors.append(f"File is not readable: {absolute_path}")
            return False
        return True

    def validate_required_columns(
        self, df: pd.DataFrame, required_cols: typing.List[str]
    ) -> bool:
        """
        Validate that all required columns are present.

        Args:
            df: DataFrame to validate.
            required_cols: List of required column names.

        Returns
            bool: True if all required columns are present, False otherwise.
        """

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.errors.append(f"Missing required columns: {missing_cols}")
            return False
        return True

    def check_data_completeness(
        self, df: pd.DataFrame, required_cols: typing.List[str]
    ) -> pd.DataFrame:
        """
        Check if all required data is present for each row.

        Args:
            df: DataFrame to check.
            required_cols: List of required column names.

        Returns
            pd.DataFrame: DataFrame with validation status and messages.
        """

        df["_validation_status"] = "valid"
        df["_validation_errors"] = ""
        # Iterate through each row and check for missing values in required columns
        for idx, row in df.iterrows():
            errors = []
            for col in required_cols:
                if pd.isna(row[col]) or str(row[col]).strip() == "":
                    errors.append(f"Missing {col}")
            # Mark the row as invalid if there are any errors
            if errors:
                df.at[idx, "_validation_status"] = "invalid"
                df.at[idx, "_validation_errors"] = "; ".join(errors)
                self.warnings.append(f"Row {idx + 1}: {'; '.join(errors)}")
        return df
