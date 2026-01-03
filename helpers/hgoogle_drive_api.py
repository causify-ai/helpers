"""
Use cases for this module are at:
helpers/notebooks/Master_how_to_use_hgoogle_drive_api.ipynb

Import as:

import helpers.hgoogle_drive_api as hgodrapi
"""

import logging
import os.path
import re
from datetime import datetime
from typing import List, Optional

# This package need to be manually installed until it is added to the
# container.
# Run the following line in a notebook:
# ```
# > !sudo /bin/bash -c "(source /venv/bin/activate; pip install --upgrade google-api-python-client)"
# ```
# Or run the following part in python:
# ```
# import subprocess
# install_code = subprocess.call(
#   'sudo /bin/bash -c "(source /venv/bin/activate; pip install --upgrade google-api-python-client)"',
#   shell=True,
# )
# ```

# Try to import optional Google API dependencies.
try:
    # Authentication for Google API to produce credentials.
    import google.oauth2.service_account as goasea

    # Google API client for service objects (e.g., Drive, Sheets, etc.)
    import googleapiclient.discovery as godisc

    # Built on top of Google API to simplify interactions with Google Sheets.
    import gspread

    _GOOGLE_API_AVAILABLE = True
except ImportError:
    # If Google API packages are not installed, set placeholders.
    _GOOGLE_API_AVAILABLE = False

import pandas as pd

import helpers.hdbg as hdbg
import helpers.henv as henv
import helpers.hpandas as hpandas

_LOG = logging.getLogger(__name__)


def install_needed_modules(
    *, use_sudo: bool = True, venv_path: Optional[str] = None
) -> None:
    """
    Install needed modules for Google Drive API.

    :param use_sudo: whether to use sudo to install the module
    :param venv_path: path to the virtual environment
        E.g., /Users/saggese/src/venv/client_venv.helpers
    """
    henv.install_module_if_not_present(
        "google",
        package_name="google-auth",
        use_sudo=use_sudo,
        use_activate=True,
        venv_path=venv_path,
    )
    henv.install_module_if_not_present(
        "googleapiclient",
        package_name="google-api-python-client",
        use_sudo=use_sudo,
        use_activate=True,
        venv_path=venv_path,
    )
    henv.install_module_if_not_present(
        "gspread",
        package_name="gspread",
        use_sudo=use_sudo,
        use_activate=True,
        venv_path=venv_path,
    )
    # Reload the currently imported modules to make sure any freshly installed dependencies are loaded.
    import importlib
    import sys

    # Reload this module (hgoogle_drive_api) if already imported
    this_module_name = __name__
    if this_module_name in sys.modules:
        importlib.reload(sys.modules[this_module_name])


# #############################################################################
# Credentials
# #############################################################################


def get_credentials(
    *,
    service_key_path: Optional[str] = None,
) -> "goasea.Credentials":
    """
    Get credentials for Google API with service account key.

    :param service_key_path: service account key file path.
    :return: Google credentials.
    """
    # service_key_path = "/home/.config/gspread_pandas/google_secret.json"
    if not service_key_path:
        service_key_path = os.path.join(
            os.path.expanduser("~"),
            ".config",
            "gspread_pandas",
            "google_secret.json",
        )
    service_key_path = os.path.join(os.path.dirname(__file__), service_key_path)
    # Download service.json from Google API, then save it as
    # /home/.config/gspread_pandas/google_secret.json
    # Instructions: https://gspread-pandas.readthedocs.io/en/latest/getting_started.html#client-credentials"
    hdbg.dassert_file_exists(
        service_key_path,
        "Failed to read service key file: %s",
        service_key_path,
    )
    # Scopes required for making API calls.
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    creds = goasea.Credentials.from_service_account_file(
        service_key_path, scopes=scopes
    )
    return creds


# #############################################################################
# Google Sheets API
# #############################################################################


# TODO(gp): Extend this to work with v3, v4, etc.
# TODO(ai_gp): Make it private if it's not called by anybody else.
def get_sheets_service(credentials: "goasea.Credentials") -> "godisc.Resource":
    """
    Get Google Sheets service with provided credentials.

    :param credentials: Google credentials object.
    :return: Google Sheets service instance.
    """
    # Ensure credentials are provided.
    hdbg.dassert(credentials, "The 'credentials' parameter must be provided")
    # Build the Sheets service.
    sheets_service = godisc.build(
        "sheets", "v4", credentials=credentials, cache_discovery=False
    )
    return sheets_service


# TODO(ai_gp): Make it private if it's not called by anybody else.
def get_gsheet_id(
    credentials: "goasea.Credentials",
    sheet_id: str,
    *,
    tab_name: Optional[str] = None,
) -> str:
    """
    Get the sheet ID from the sheet name in a Google Sheets document.

    :param credentials: Google credentials object.
    :param sheet_id: ID of the Google Sheet document.
    :param tab_name: Name of the sheet (tab) in the Google Sheets
        document.
    :return: Sheet ID of the sheet with the given name or the first
        sheet if the name is not provided.
    """
    sheets_service = get_sheets_service(credentials)
    sheet_metadata = (
        sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    )
    sheets = sheet_metadata.get("sheets", [])
    if tab_name:
        for sheet in sheets:
            properties = sheet.get("properties", {})
            if properties.get("title") == tab_name:
                return properties.get("sheetId")
        raise ValueError(f"Sheet with name '{tab_name}' not found.")
    # Return the ID of the first sheet if no sheet name is provided.
    first_sheet_id = sheets[0].get("properties", {}).get("sheetId")
    return first_sheet_id


# TODO(ai_gp): -> get_gsheet_name
# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def get_tab_name_from_url(
    credentials: "goasea.Credentials",
    url: str,
) -> str:
    """
    Get the name of a Google Sheet from its URL.

    E.g., https://docs.google.com/spreadsheets/d/1GnnmtGTrHDwMP77VylEK0bSF_RLUV5BWf1iGmxuBQpI
    -> pitchbook.Outreach_AI_companies

    :param credentials: Google credentials object.
    :param url: URL of the Google Sheets file.
    :return: Name of the Google Sheet (spreadsheet title).
    """
    # TODO(ai): Should we use the Sheets API instead?
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(url)
    tab_name = spreadsheet.title
    _LOG.debug("Retrieved sheet name: '%s'", tab_name)
    return tab_name


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def get_tabs_from_gsheet(
    credentials: "goasea.Credentials",
    url: str,
) -> List[str]:
    """
    Get all the tabs (worksheets) from a Google Sheet.

    :param credentials: Google credentials object.
    :param url: URL of the Google Sheet.
    :return: List of tab names.
    """
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(url)
    return [sheet.title for sheet in spreadsheet.worksheets()]


# #############################################################################


def _extract_file_id_from_url(url: str) -> str:
    """
    Extract the file ID from a Google Docs/Sheets/Drive URL.

    E.g.,
    https://docs.google.com/spreadsheets/d/FILE_ID/...
    https://docs.google.com/document/d/FILE_ID/...
    https://drive.google.com/file/d/FILE_ID/...

    :param url: URL of the Google Docs/Sheets/Drive file.
    :return: File ID extracted from the URL.
    """
    # Handle URLs like:
    # https://docs.google.com/spreadsheets/d/FILE_ID/...
    # https://docs.google.com/document/d/FILE_ID/...
    # https://drive.google.com/file/d/FILE_ID/...
    pattern = r"/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)
    hdbg.dassert(match, "Invalid URL format: %s", url)
    file_id = match.group(1)
    _LOG.debug("Extracted file ID: '%s' from URL: '%s'", file_id, url)
    return file_id


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def get_gsheet_tab_url(
    credentials: "goasea.Credentials",
    url: str,
    tab_name: str,
) -> str:
    """
    Generate the full URL for a specific tab in a Google Sheet.

    E.g.,
    - Input URL: https://docs.google.com/spreadsheets/d/1NLY7dTmkXmllYfewDH53z-uSRpC9-zBTTmAOB_O30DI
    - Tab name: Sheet3
    - Output: https://docs.google.com/spreadsheets/d/1NLY7dTmkXmllYfewDH53z-uSRpC9-zBTTmAOB_O30DI/edit?gid=229426446#gid=229426446

    :param credentials: Google credentials object.
    :param url: URL of the Google Sheets file.
    :param tab_name: Name of the tab to generate the URL for.
    :return: Full URL with the gid parameter for the specified tab.
    """
    hdbg.dassert(tab_name, "tab_name parameter must be provided")
    # Extract the spreadsheet ID from the URL.
    sheet_id = _extract_file_id_from_url(url)
    _LOG.debug("Extracted sheet_id: '%s' from URL: '%s'", sheet_id, url)
    # Get the gid for the specified tab.
    gid = get_gsheet_id(credentials, sheet_id, tab_name=tab_name)
    _LOG.debug("Retrieved gid: '%s' for tab: '%s'", gid, tab_name)
    # Construct the full URL with the gid parameter.
    full_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?gid={gid}#gid={gid}"
    _LOG.debug("Generated full URL: '%s'", full_url)
    return full_url


# TODO(ai_gp): Make it private if it's not called by anybody else.
def freeze_rows_in_gsheet(
    credentials: "goasea.Credentials",
    sheet_id: str,
    num_rows_to_freeze: int,
    *,
    tab_name: Optional[str] = None,
    bold: bool = True,
) -> None:
    """
    Freeze specified rows in the given sheet.

    :param credentials: Google credentials object.
    :param sheet_id: ID of the Google Sheet (spreadsheet ID).
    :param num_rows_to_freeze: Number of rows to freeze (starting from row 0).
    :param tab_name: Name of the sheet (tab) to freeze rows in.
        Defaults to the first tab if not provided.
    :param bold: If True, make the frozen rows bold.
    """
    hdbg.dassert_lt(0, num_rows_to_freeze)
    tab_id = get_gsheet_id(credentials, sheet_id=sheet_id, tab_name=tab_name)
    sheets_service = get_sheets_service(credentials)
    # Build the batch update request.
    requests = []
    # Add freeze rows request.
    requests.append(
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": tab_id,
                    "gridProperties": {"frozenRowCount": num_rows_to_freeze},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        }
    )
    # Add bold formatting request if requested.
    if bold:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 0,
                        "endRowIndex": num_rows_to_freeze,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True,
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.bold",
                }
            }
        )
        _LOG.debug(
            "Adding bold formatting to %s frozen rows", num_rows_to_freeze
        )
    # Execute the batch update.
    freeze_request = {"requests": requests}
    response = (
        sheets_service.spreadsheets()
        .batchUpdate(spreadsheetId=sheet_id, body=freeze_request)
        .execute()
    )
    _LOG.debug("response: %s", response)


# TODO(ai_gp): Make it private if it's not called by anybody else.
def set_row_height_in_gsheet(
    credentials: "goasea.Credentials",
    sheet_id: str,
    height: int,
    *,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    tab_name: Optional[str] = None,
) -> None:
    """
    Set the height for rows in the given Google sheet.

    :param credentials: Google credentials object.
    :param sheet_id: ID of the Google Sheet (spreadsheet ID).
    :param height: Height of the rows in pixels.
    :param start_index: Starting index of the rows (zero-based). If
        None, applies to all rows.
    :param end_index: Ending index of the rows (zero-based). If None,
        applies to all rows.
    :param tab_name: Name of the sheet (tab) to set row height in.
        Defaults to the first tab if not provided.
    """
    tab_id = get_gsheet_id(credentials, sheet_id=sheet_id, tab_name=tab_name)
    sheets_service = get_sheets_service(credentials)
    if start_index is None and end_index is None:
        sheet_metadata = (
            sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        )
        sheet_properties = next(
            sheet
            for sheet in sheet_metadata.get("sheets", [])
            if sheet.get("properties", {}).get("sheetId") == tab_id
        ).get("properties", {})
        grid_properties = sheet_properties.get("gridProperties", {})
        start_index, end_index = 0, grid_properties.get("rowCount", 1000)
    elif start_index is None:
        start_index = 0
    elif end_index is None:
        sheet_metadata = (
            sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        )
        sheet_properties = next(
            sheet
            for sheet in sheet_metadata.get("sheets", [])
            if sheet.get("properties", {}).get("sheetId") == tab_id
        ).get("properties", {})
        grid_properties = sheet_properties.get("gridProperties", {})
        end_index = grid_properties.get("rowCount", 1000)
    elif start_index >= end_index:
        raise ValueError(
            f"Invalid params: start_index ({start_index}) must be less than end_index ({end_index})."
        )
    # Create request.
    set_row_height_request = {
        "requests": [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": tab_id,
                        "dimension": "ROWS",
                        "startIndex": start_index,
                        "endIndex": end_index,
                    },
                    "properties": {"pixelSize": height},
                    "fields": "pixelSize",
                }
            }
        ]
    }
    # Get response.
    response = (
        sheets_service.spreadsheets()
        .batchUpdate(spreadsheetId=sheet_id, body=set_row_height_request)
        .execute()
    )
    _LOG.debug("response: %s", response)


# TODO(ai_gp): Make it private if it's not called by anybody else.
def set_text_wrapping_clip_in_gsheet(
    credentials: "goasea.Credentials",
    sheet_id: str,
    *,
    tab_name: Optional[str] = None,
) -> None:
    """
    Set text wrapping to "CLIP" for all columns in the given Google sheet.

    :param credentials: Google credentials object.
    :param sheet_id: ID of the Google Sheet (spreadsheet ID).
    :param tab_name: Name of the sheet (tab) to set text wrapping in.
        Defaults to the first tab if not provided.
    """
    tab_id = get_gsheet_id(credentials, sheet_id=sheet_id, tab_name=tab_name)
    sheets_service = get_sheets_service(credentials)
    # Get sheet metadata to determine the range.
    sheet_metadata = (
        sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    )
    sheet_properties = next(
        sheet
        for sheet in sheet_metadata.get("sheets", [])
        if sheet.get("properties", {}).get("sheetId") == tab_id
    ).get("properties", {})
    grid_properties = sheet_properties.get("gridProperties", {})
    row_count = grid_properties.get("rowCount", 1000)
    col_count = grid_properties.get("columnCount", 26)
    _LOG.debug(
        "Setting text wrapping to CLIP for sheet with %s rows and %s columns",
        row_count,
        col_count,
    )
    # Create request to set text wrapping to CLIP.
    set_wrapping_request = {
        "requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": tab_id,
                        "startRowIndex": 0,
                        "endRowIndex": row_count,
                        "startColumnIndex": 0,
                        "endColumnIndex": col_count,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "wrapStrategy": "CLIP",
                        }
                    },
                    "fields": "userEnteredFormat.wrapStrategy",
                }
            }
        ]
    }
    # Execute the batch update.
    response = (
        sheets_service.spreadsheets()
        .batchUpdate(spreadsheetId=sheet_id, body=set_wrapping_request)
        .execute()
    )
    _LOG.debug("response: %s", response)


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def from_gsheet(
    credentials: "goasea.Credentials",
    url: str,
    *,
    tab_name: Optional[str] = None,
) -> pd.DataFrame:
    """
    Read data from a Google Sheet.

    :param credentials: Google credentials object.
    :param url: URL of the Google Sheets file.
    :param tab_name: Name of the tab to read (default: first sheet if
        not specified).
    :return: pandas DataFrame with the sheet data.
    """
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(url)
    if tab_name is None:
        # Read the first sheet.
        worksheet = spreadsheet.get_worksheet(0)
    else:
        # Read the specified sheet.
        worksheet = spreadsheet.worksheet(tab_name)
    data = worksheet.get_all_records()
    hdbg.dassert(data, "The sheet '%s' is empty", tab_name)
    df = pd.DataFrame(data)
    _LOG.debug("Data fetched")
    return df


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def to_gsheet(
    credentials: "goasea.Credentials",
    df: pd.DataFrame,
    url: str,
    *,
    tab_name: Optional[str] = "new_data",
    freeze_rows: bool = False,
    set_text_wrapping_clip: bool = False,
) -> None:
    """
    Write data to a specified Google Sheet and tab.

    :param credentials: Google credentials object.
    :param df: Data to be written.
    :param url: URL of the Google Sheet.
    :param tab_name: Name of the tab where the data will be written.
    """
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(url)
    # Try to get existing worksheet or create new one.
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        _LOG.debug(
            "Tab '%s' not found, creating a new tab with that name",
            tab_name,
        )
        worksheet = spreadsheet.add_worksheet(
            title=tab_name, rows="100", cols="20"
        )
    #
    if freeze_rows:
        freeze_rows_in_gsheet(
            credentials,
            spreadsheet.id,
            num_rows_to_freeze=1,
            tab_name=tab_name,
        )
        #
        set_row_height_in_gsheet(
            credentials,
            spreadsheet.id,
            height=20,
            tab_name=tab_name,
        )
    # Clear and write data.
    worksheet.clear()
    # Replace NaN/inf values with empty strings for JSON compatibility.
    df_clean = df.fillna("").replace([float("inf"), float("-inf")], "")
    values = [df_clean.columns.values.tolist()] + df_clean.values.tolist()
    worksheet.update("A1", values)
    #
    if set_text_wrapping_clip:
        set_text_wrapping_clip_in_gsheet(
            credentials,
            spreadsheet.id,
            tab_name=tab_name,
        )
    _LOG.info("Data written to:\ntab '%s'\nGoogle Sheet '%s'", tab_name, url)
    _LOG.info("url=%s", get_gsheet_tab_url(credentials, url, tab_name))


# #############################################################################
# Google file API
# #############################################################################


# TODO(ai_gp): Make it private if it's not called by anybody else.
def get_gdrive_service(credentials: "goasea.Credentials") -> "godisc.Resource":
    """
    Get Google Drive service with provided credentials.

    :param credentials: Google credentials object.
    :return: Google Drive service instance.
    """
    # Ensure credentials are provided.
    hdbg.dassert(credentials, "The 'credentials' parameter must be provided")
    # Build the drive service.
    gdrive_service = godisc.build(
        "drive", "v3", credentials=credentials, cache_discovery=False
    )
    return gdrive_service


def _create_new_google_document(
    credentials: "goasea.Credentials",
    doc_name: str,
    doc_type: str,
) -> str:
    """
    Create a new Google document (Sheet or Doc).

    :param credentials: Google credentials object.
    :param doc_name: The name of the new Google document.
    :param doc_type: The type of the Google document ('sheets' or
        'docs').
    :return: doc_id. The ID of the created document in Google Drive.
    """
    if doc_type not in ["sheets", "docs"]:
        raise ValueError("Invalid doc_type. Must be 'sheets' or 'docs'.")
    # Build the service for the respective document type.
    service = godisc.build(
        doc_type,
        "v4" if doc_type == "sheets" else "v1",
        credentials=credentials,
        cache_discovery=False,
    )
    # Create the document with the specified name.
    document = {"properties": {"title": doc_name}}
    create_method = (
        service.spreadsheets().create
        if doc_type == "sheets"
        else service.documents().create
    )
    response = create_method(
        body=document,
        fields="spreadsheetId" if doc_type == "sheets" else "documentId",
    ).execute()
    # Extract the document ID.
    doc_id = response.get(
        "spreadsheetId" if doc_type == "sheets" else "documentId"
    )
    return doc_id


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def move_gfile_to_dir(
    credentials: "goasea.Credentials",
    gfile_id: str,
    folder_id: str,
) -> dict:
    """
    Move a Google file to a specified folder in Google Drive.

    :param credentials: Google credentials object.
    :param gfile_id: The ID of the Google file.
    :param folder_id: The ID of the folder.
    :return: The response from the API after moving the file.
    """
    # TODO(gp): -> get_gdrive_service
    service = godisc.build(
        "drive", "v3", credentials=credentials, cache_discovery=False
    )
    res = (
        service.files()
        .update(
            fileId=gfile_id,
            body={},
            addParents=folder_id,
            removeParents="root",
            supportsAllDrives=True,
        )
        .execute()
    )
    return res


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def share_google_file(
    credentials: "goasea.Credentials",
    gfile_id: str,
    user: str,
) -> None:
    """
    Share a Google file with a user.

    :param credentials: Google credentials object.
    :param gfile_id: The ID of the Google file.
    :param user: The email address of the user.
    """
    # Build the Google Drive service using the provided credentials.
    # TODO(gp): -> get_gdrive_service
    service = godisc.build(
        "drive", "v3", credentials=credentials, cache_discovery=False
    )
    # Create the permission.
    parameters = {"role": "reader", "type": "user", "emailAddress": user}
    new_permission = (
        service.permissions().create(fileId=gfile_id, body=parameters).execute()
    )
    _LOG.debug(
        "The new permission ID of the document is: '%s'",
        new_permission.get("id"),
    )
    _LOG.debug("The Google file is shared with '%s'", user)


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def create_empty_google_file(
    credentials: "goasea.Credentials",
    gfile_type: str,
    gfile_name: str,
    gdrive_folder_id: str,
    *,
    user: Optional[str] = None,
) -> str:
    """
    Create a new Google file (sheet or doc) and move it to a specified folder.

    :param credentials: Google credentials object for API access.
    :param gfile_type: the type of the Google file ('sheet' or 'doc').
    :param gfile_name: the name of the new Google file.
    :param gdrive_folder_id: the ID of the Google Drive folder.
    :param user: the email address of the user to share the Google file.
    :return: the ID of the created Google file, or None if an error
        occurred.
    """
    # Create the new Google file (either Sheet or Doc).
    if gfile_type == "sheet":
        gfile_id = _create_new_google_document(
            credentials,
            doc_name=gfile_name,
            doc_type="sheets",
        )
    elif gfile_type == "doc":
        gfile_id = _create_new_google_document(
            credentials,
            doc_name=gfile_name,
            doc_type="docs",
        )
    else:
        raise ValueError(f"Invalid gfile_type={gfile_type}")
    _LOG.debug("Created a new Google %s '%s'", gfile_type, gfile_name)
    # Move the Google file to the specified folder.
    if gdrive_folder_id:
        move_gfile_to_dir(credentials, gfile_id, gdrive_folder_id)
    # Share the Google file to the user and send an email.
    if user:
        share_google_file(credentials, gfile_id, user)
        _LOG.debug(
            "The new Google '%s': '%s' is shared with '%s'",
            gfile_type,
            gfile_name,
            user,
        )
    # Return the file ID.
    return gfile_id


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def create_or_overwrite_with_timestamp(
    credentials: "goasea.Credentials",
    file_name: str,
    folder_id: str,
    *,
    file_type: str = "sheets",
    overwrite: bool = False,
) -> str:
    """
    Create or overwrite a Google Sheet or Google Doc with a timestamp in a
    specific Google Drive folder.

    :param credentials: Google credentials object.
    :param file_name: Name for the file (timestamp will be added).
    :param folder_id: Google Drive folder ID where the file will be
        created or updated.
    :param file_type: Type of file to create ('sheets' or 'docs').
    :param overwrite: If True, overwrite an existing file. Otherwise,
        create a new file.
    :return: The ID of the created or overwritten file.
    """
    # Authenticate with Google APIs using the provided credentials.
    # TODO(gp): -> get_gdrive_service
    drive_service = godisc.build("drive", "v3", credentials=credentials)
    if file_type == "sheets":
        mime_type = "application/vnd.google-apps.spreadsheet"
    elif file_type == "docs":
        mime_type = "application/vnd.google-apps.document"
    else:
        raise ValueError("Invalid file_type. Must be 'sheets' or 'docs'.")
    query = (
        f"'{folder_id}' in parents and mimeType = '{mime_type}'"
        f" and name contains '{file_name}'"
    )
    response = (
        drive_service.files()
        .list(
            q=query,
            fields="files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        )
        .execute()
    )
    files = response.get("files", [])
    # Check if overwriting or creating new file.
    if files and overwrite:
        file_id = files[0]["id"]
        _LOG.debug("Overwriting existing file '%s'", files[0]["name"])
    else:
        # Create new file with timestamp.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_file_name = f"{file_name}_{timestamp}"
        file_metadata = {
            "name": new_file_name,
            "mimeType": mime_type,
            "parents": [folder_id],
        }
        file = (
            drive_service.files()
            .create(body=file_metadata, fields="id", supportsAllDrives=True)
            .execute()
        )
        file_id = file.get("id")
        _LOG.debug(
            "New file '%s' created successfully in folder '%s'",
            new_file_name,
            folder_id,
        )
    return file_id


# #############################################################################
# Google folder API
# #############################################################################


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def create_google_drive_folder(
    credentials: "goasea.Credentials",
    folder_name: str,
    parent_folder_id: str,
) -> str:
    """
    Create a new Google Drive folder inside the given folder.

    :param credentials: Google credentials object.
    :param folder_name: the name of the new Google Drive folder.
    :param parent_folder_id: the ID of the parent folder.
    :return: the ID of the created Google Drive folder.
    """
    # Build the Google Drive service using the provided credentials.
    # TODO(gp): -> get_gdrive_service
    service = godisc.build(
        "drive", "v3", credentials=credentials, cache_discovery=False
    )
    # Define the metadata for the new folder.
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id],
    }
    # Create the folder in Google Drive.
    folder = service.files().create(body=file_metadata, fields="id").execute()
    # Log and return the folder ID.
    _LOG.debug("Created a new Google Drive folder '%s'", folder_name)
    _LOG.debug("The new folder id is '%s'", folder.get("id"))
    return folder.get("id")


def _get_folders_in_gdrive(*, credentials: "goasea.Credentials") -> list:
    """
    Get a list of folders in Google Drive.

    :param credentials: Google credentials object.
    :return: A list of folders (each containing an ID and name).
    """
    # Build the Google Drive service using the provided credentials.
    # TODO(gp): -> get_gdrive_service
    service = godisc.build(
        "drive", "v3", credentials=credentials, cache_discovery=False
    )
    # Make the API request to list folders.
    response = (
        service.files()
        .list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces="drive",
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )
    # Return the list of folders (id and name).
    return response.get("files", [])


def get_folder_id_by_name(
    credentials: "goasea.Credentials",
    name: str,
) -> dict:
    """
    Get the folder id by the folder name.

    :param credentials: Google credentials object.
    :param name: The name of the folder.
    :return: Dictionary with folder id and name.
    """
    folders = _get_folders_in_gdrive(credentials=credentials)
    folder_list = []
    # Find all folders matching the name.
    for folder in folders:
        if folder.get("name") == name:
            folder_list.append(folder)
    if len(folder_list) == 1:
        _LOG.debug("Found folder: %s", folder_list[0])
    elif len(folder_list) > 1:
        for folder in folder_list:
            _LOG.debug(
                "Found folder: '%s', '%s'",
                folder.get("name"),
                folder.get("id"),
            )
        _LOG.debug(
            "Return the first found folder. '%s' '%s' ",
            folder_list[0].get("name"),
            folder_list[0].get("id"),
        )
        _LOG.debug(
            "if you want to use another '%s' folder, "
            "please change the folder id manually.",
            name,
        )
    else:
        raise ValueError(f"Can't find the folder '{name}'.")
    return folder_list[0]


def _get_folder_path_list(
    service: "godisc.Resource",
    file_id: str,
) -> List[str]:
    """
    Get the full folder path as a list of folder names.

    :param service: Google Drive service instance.
    :param file_id: The ID of the file.
    :return: List of folder names from root to immediate parent folder.
        Returns empty list if file is at root level.
    """
    # Get file metadata with parents.
    file_metadata = (
        service.files()
        .get(
            fileId=file_id,
            fields="parents",
            supportsAllDrives=True,
        )
        .execute()
    )
    parents = file_metadata.get("parents", [])
    # If no parents, file is at root level.
    if not parents:
        _LOG.debug("File is at root level")
        return []
    # Build the path by traversing up the folder hierarchy.
    path_list = []
    current_id = parents[0]  # Files typically have one parent in Google Drive.
    while current_id:
        folder_metadata = (
            service.files()
            .get(
                fileId=current_id,
                fields="name,parents",
                supportsAllDrives=True,
            )
            .execute()
        )
        folder_name = folder_metadata.get("name")
        path_list.insert(0, folder_name)
        parents = folder_metadata.get("parents", [])
        current_id = parents[0] if parents else None
    _LOG.debug("Folder path: %s", path_list)
    return path_list


# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
def get_google_path_from_url(
    credentials: "goasea.Credentials",
    url: str,
) -> List[str]:
    """
    Get the full folder path from a Google Docs/Sheets/Drive URL.

    E.g., https://docs.google.com/spreadsheets/d/1GnnmtGTrHDwMP77VylEK0bSF_RLUV5BWf1iGmxuBQpI
    -> ['My Drive', 'Folder1', 'Folder2']

    :param credentials: Google credentials object.
    :param url: URL of the Google Docs/Sheets/Drive file.
    :return: List of folder names from root to immediate parent folder.
        Returns empty list if file is at root level.
    """
    # Extract file ID from URL.
    file_id = _extract_file_id_from_url(url)
    # Get Google Drive service.
    service = get_gdrive_service(credentials)
    # Get folder path as list.
    path_list = _get_folder_path_list(service, file_id)
    _LOG.debug("Retrieved folder path for URL '%s': %s", url, path_list)
    return path_list


def print_info_about_google_url(
    credentials: "goasea.Credentials", url: str, tab_name: str = None
) -> None:
    print("url: '%s'" % url)
    print("file name: '%s'" % get_tab_name_from_url(credentials, url))
    print("tab names: '%s'" % get_tabs_from_gsheet(credentials, url))
    if tab_name is not None:
        print("full url: '%s'" % get_gsheet_tab_url(credentials, url, tab_name))
    print(
        "folder path: '%s'"
        % "/".join(get_google_path_from_url(credentials, url))
    )


# TODO(gp): Add clean up
# TODO(ai_gp): Pass the credentials: Optional["goasea.Credentials"] = None after the *
# TODO(gp): Make url mandatory and when url = "tmp" use the hardcored value.
# TODO(gp): -> save_df_to_gsheet
def save_df_to_tmp_gsheet(
    df: pd.DataFrame,
    *,
    url: str = "",
    tab_name: str = "",
    remove_empty_columns: bool = False,
    remove_stable_columns: bool = False,
    verbose: bool = True,
) -> None:
    """
    Save a DataFrame to a Google Sheet.

    :param df: The DataFrame to save.
    :param tab_name: The name of the tab to save the DataFrame to.
    """
    if remove_stable_columns:
        df = hpandas.remove_stable_columns(df, verbose=verbose)
    if remove_empty_columns:
        df = hpandas.remove_empty_columns(df, verbose=verbose)
    if url == "":
        url = "https://docs.google.com/spreadsheets/d/1NLY7dTmkXmllYfewDH53z-uSRpC9-zBTTmAOB_O30DI/edit?gid=0#gid=0"
    if tab_name == "":
        # Find the first tab name that is not empty.
        tab_names = get_tabs_from_gsheet(get_credentials(), url)
        for i in range(0, 100):
            tab_name = "Sheet" + str(i)
            if tab_name not in tab_names:
                break
        hdbg.dassert_ne(tab_name, "No empty tab name found")
    to_gsheet(
        get_credentials(),
        df,
        url,
        tab_name=tab_name,
        freeze_rows=True,
        set_text_wrapping_clip=True,
    )
