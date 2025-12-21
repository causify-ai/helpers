"""
Import as:

import helpers.hpandas as hpandas
"""

from typing import Any, Union

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hlogging as hlogging
import helpers.hprint as hprint

# Handle different versions of s3fs where core module may be at different
# locations.
try:
    import s3fs

    # Try to access s3fs.core to check if it exists
    if hasattr(s3fs, "core"):
        from s3fs.core import S3File, S3FileSystem
    else:
        # In newer versions, classes might be directly in s3fs module.
        try:
            from s3fs import S3File, S3FileSystem
        except ImportError:
            # Fallback to dynamic import
            S3File = getattr(s3fs, "S3File", None)
            S3FileSystem = getattr(s3fs, "S3FileSystem", None)
except ImportError:
    # If s3fs is not available, define dummy classes for type hints.
    s3fs = None

    class S3File:
        pass

    class S3FileSystem:
        pass


_LOG = hlogging.getLogger(__name__)


def read_csv_to_df(
    stream: Union[str, S3File, S3FileSystem],
    *args: Any,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Read a CSV file into a `pd.DataFrame`.
    """
    # Gets filename from stream if it is not already a string,
    # so it can be inspected for extension type.
    file_name = stream if isinstance(stream, str) else vars(stream)["path"]
    # Handle zipped files.
    if any(file_name.endswith(ext) for ext in (".gzip", ".gz", ".tgz")):
        hdbg.dassert_not_in("compression", kwargs)
        kwargs["compression"] = "gzip"
    elif file_name.endswith(".zip"):
        hdbg.dassert_not_in("compression", kwargs)
        kwargs["compression"] = "zip"
    # Read.
    _LOG.debug(hprint.to_str("args kwargs"))
    df = pd.read_csv(stream, *args, **kwargs)
    return df


def read_parquet_to_df(
    stream: Union[str, S3File, S3FileSystem],
    *args: Any,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Read a Parquet file into a `pd.DataFrame`.
    """
    # Read.
    _LOG.debug(hprint.to_str("args kwargs"))
    df = pd.read_parquet(stream, *args, **kwargs)
    return df


# #############################################################################


# TODO(Paul): Add unit tests.


def to_gsheet(
    df: pd.DataFrame,
    gsheet_name: str,
    gsheet_sheet_name: str,
    overwrite: bool,
) -> None:
    """
    Save a dataframe to a Google sheet.

    :param df: the dataframe to save to a Google sheet
    :param gsheet_name: the name of the Google sheet to save the df
        into; the Google sheet with this name must already exist on the
        Google Drive
    :param gsheet_sheet_name: the name of the sheet in the Google sheet
    :param overwrite: if True, the contents of the sheet are erased
        before saving the dataframe into it; if False, the dataframe is
        appended to the contents of the sheet
    """
    import gspread_pandas

    spread = gspread_pandas.Spread(
        gsheet_name, sheet=gsheet_sheet_name, create_sheet=True
    )
    if overwrite:
        spread.clear_sheet()
    else:
        sheet_contents = spread.sheet_to_df(index=None)
        combined_df = pd.concat([sheet_contents, df])
        df = combined_df.drop_duplicates()
    spread.df_to_sheet(df, index=False)
