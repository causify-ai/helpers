#!/usr/bin/env python3
"""
Context Engineering Script
Reads function metadata from CSV/MD files and extracts lines and docstrings from actual code files.
"""

import argparse
import os
import sys
import pandas as pd
from typing import Set
import logging

import function_extractor as dshdfuex
import file_validator as dshdafva
import utils as dshdagut

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main function to handle command line arguments and process the input file.
    """
    parser = argparse.ArgumentParser(description='Generate context from function metadata')
    parser.add_argument('--in-file', required=True, help='Input file path')
    parser.add_argument('--out-file', required=True, help='Output file path')
    parser.add_argument('--file-type', choices=['csv', 'md'], default='csv', 
                       help='Input file type (csv or md)')
    args = parser.parse_args()    
    root_dir = os.getcwd()
    logger.info("Starting context generation...")    
    logger.info(f"Working from root directory: {root_dir}")
    # Read input file
    logger.info(f"Reading input file: {args.in_file}")
    df = dshdagut.read_input_file(args.in_file, args.file_type)
    valid_count = 0
    required_cols = ['Function Type', 'Script Path', 'Function Name']
    # Validate input DataFrame
    validator = dshdafva.FileValidator()    
    if not validator.validate_required_columns(df, required_cols):
        # Validate if columns exist
        logger.error("Validation failed: Missing required columns")
        for error in validator.errors:
            logger.error(error)
        sys.exit(1)

    # Validate completeness
    logger.info("Validating data completeness...")
    df['_validation_status'] = 'valid'
    df['_validation_message'] = ''    
    for idx, row in df.iterrows():
        for col in required_cols:
            if pd.isna(row[col]) or str(row[col]).strip() == '':
                df.at[idx, '_validation_status'] = 'invalid'
                msg = f"Missing value in '{col}'"
                df.at[idx, '_validation_message'] += msg + '; '
                logger.warning(f"Row {idx}: {msg}")

    # Validate file paths
    logger.info("Validating file paths...")
    for idx, row in df.iterrows():
        if df.at[idx, '_validation_status'] != 'valid':
            continue
        file_path = row['Script Path']
        if not validator.validate_file_path(file_path, root_dir):
            df.at[idx, '_validation_status'] = 'invalid'
            msg = f"Invalid file path: {file_path}"
            df.at[idx, '_validation_message'] += msg + '; '
            logger.warning(f"Row {idx}: {msg}")

    # Extract function information
    logger.info("Extracting function information...")
    extractor = dshdfuex.FunctionExtractor()
    # Add columns for extracted lines and docstring
    df['Lines'] = None
    df['Docstring'] = None
    for idx, row in df.iterrows():
        if df.at[idx, '_validation_status'] != 'valid':
            continue
        file_path = row['Script Path']
        function_name = row['Function Name']
        # Log the extraction attempt
        logger.info(f"Row {idx}: Extracting function '{function_name}' from '{file_path}'")
        lines, docstring = extractor.extract_function_info(file_path, function_name, root_dir)
        if lines and docstring is not None:
            # Update DataFrame with extracted information
            df.at[idx, 'Lines'] = lines
            df.at[idx, 'Docstring'] = docstring
            valid_count += 1
        else:
            df.at[idx, '_validation_status'] = 'extraction_failed'
            msg = f"Function '{function_name}' not found or docstring missing in '{file_path}'"
            df.at[idx, '_validation_message'] += msg + '; '
            logger.error(f"Row {idx}: {msg}")
    
    # Final Report
    total_rows = len(df)
    invalid_rows = len(df[df['_validation_status'] != 'valid'])
    failed_extractions = len(df[df['_validation_status'] == 'extraction_failed'])
    logger.info(f"Processing complete:")
    logger.info(f"  Total rows: {total_rows}")
    logger.info(f"  Successfully processed: {valid_count}")
    logger.info(f"  Invalid rows: {invalid_rows}")
    logger.info(f"  Extraction failures: {failed_extractions}")    
    # Log any file-wide warnings/errors
    if validator.warnings:
        logger.info("Warnings:")
        for warning in validator.warnings:
            logger.warning(warning)
    if extractor.errors:
        logger.info("Extraction errors:")
        for error in extractor.errors:
            logger.error(error)
    # Write output
    logger.info(f"Writing output to: {args.out_file}")
    dshdagut.write_output_file(df, args.out_file)
    logger.info("Context generation completed!")

if __name__ == "__main__":
    main()