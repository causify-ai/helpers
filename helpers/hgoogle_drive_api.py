"""
Use cases for this module are at:
helpers/notebooks/Master_how_to_use_hgoogle_drive_api.ipynb

Import as:

import helpers.hgoogle_drive_api as hgodrapi
"""

import logging
import os.path
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


import google.oauth2.service_account as goasea
import googleapiclient.discovery as godisc
import gspread
import pandas as pd

import helpers.hdbg as hdbg

_LOG = logging.getLogger(__name__)


def get_credentials(
    *,
    service_key_path: Optional[str] = None,
) -> goasea.Credentials:
    """
    Get credentials for Google API with service account key.

    :param service_key_path: service account key file path.
    :return: Google credentials.
    """
    if not service_key_path:
        service_key_path = "/home/.config/gspread_pandas/google_secret.json"
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


def get_sheets_service(credentials: goasea.Credentials) -> godisc.Resource:
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


# TODO(ai_gp): -> get_gsheet_id()
def get_sheet_id(
    credentials: goasea.Credentials,
    sheet_id: str,
    *,
    sheet_name: Optional[str] = None,
) -> str:
    """
    Get the sheet ID from the sheet name in a Google Sheets document.

    :param credentials: Google credentials object.
    :param sheet_id: ID of the Google Sheet document.
    :param sheet_name: Name of the sheet (tab) in the Google Sheets
        document.
    :return: Sheet ID of the sheet with the given name or the first
        sheet if the name is not provided.
    """
    sheets_service = get_sheets_service(credentials)
    sheet_metadata = (
        sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    )
    sheets = sheet_metadata.get("sheets", [])
    if sheet_name:
        for sheet in sheets:
            properties = sheet.get("properties", {})
            if properties.get("title") == sheet_name:
                return properties.get("sheetId")
        raise ValueError(f"Sheet with name '{sheet_name}' not found.")
    # Return the ID of the first sheet if no sheet name is provided.
    first_sheet_id = sheets[0].get("properties", {}).get("sheetId")
    return first_sheet_id


# TODO(ai_gp): -> get_gsheet_name_from_url()
def get_sheet_name_from_url(
    credentials: goasea.Credentials,
    url: str,
) -> str:
    """
    Get the name of a Google Sheet from its URL.

    :param credentials: Google credentials object.
    :param url: URL of the Google Sheets file.
    :return: Name of the Google Sheet (spreadsheet title).
    """
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_url(url)
    sheet_name = spreadsheet.title
    _LOG.debug("Retrieved sheet name: '%s'", sheet_name)
    return sheet_name


def freeze_rows_in_gsheet(
    credentials: goasea.Credentials,
    sheet_id: str,
    num_rows_to_freeze: int,
    *,
    sheet_name: Optional[str] = None,
) -> None:
    """
    Freeze specified rows in the given sheet.

    :param credentials: Google credentials object.
    :param sheet_id: ID of the Google Sheet (spreadsheet ID).
    :param row_indices: Row indices to freeze (zero-based index).
    :param sheet_name: Name of the sheet (tab) to freeze rows in.
        Defaults to the first tab if not provided.
    """
    hdbg.dassert_lt(0, num_rows_to_freeze)
    tab_id = get_sheet_id(
        credentials, sheet_id=sheet_id, sheet_name=sheet_name
    )
    sheets_service = get_sheets_service(credentials)
    freeze_request = {
        "requests": [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": tab_id,
                        "gridProperties": {"frozenRowCount": num_rows_to_freeze},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            }
        ]
    }
    response = (
        sheets_service.spreadsheets()
        .batchUpdate(spreadsheetId=sheet_id, body=freeze_request)
        .execute()
    )
    _LOG.debug("response: %s", response)


def set_row_height_in_gsheet(
    credentials: goasea.Credentials,
    sheet_id: str,
    height: int,
    *,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    sheet_name: Optional[str] = None,
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
    :param sheet_name: Name of the sheet (tab) to set row height in.
        Defaults to the first tab if not provided.
    """
    tab_id = get_sheet_id(
        credentials, sheet_id=sheet_id, sheet_name=sheet_name
    )
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


# TODO(ai_gp): -> from_gsheet()
def read_google_sheet(
    credentials: goasea.Credentials,
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
        worksheet = spreadsheet.get_worksheet(0)
    else:
        worksheet = spreadsheet.worksheet(tab_name)
    data = worksheet.get_all_records()
    hdbg.dassert(data, "The sheet '%s' is empty", tab_name)
    df = pd.DataFrame(data)
    _LOG.debug("Data fetched")
    return df


# TODO(ai_gp): -> to_gsheet()
def write_to_google_sheet(
    credentials: goasea.Credentials,
    df: pd.DataFrame,
    url: str,
    *,
    tab_name: Optional[str] = "new_data",
    freeze_rows: bool = False,
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
            sheet_name=tab_name,
        )
        #
        set_row_height_in_gsheet(
            credentials,
            spreadsheet.id,
            height=20,
            sheet_name=tab_name,
        )
    # Clear and write data.
    worksheet.clear()
    values = [df.columns.values.tolist()] + df.values.tolist()
    worksheet.update("A1", values)
    _LOG.debug(
        "Data successfully written to the tab '%s' of the Google Sheet",
        tab_name,
    )


# #############################################################################
# Google file API
# #############################################################################


def get_gdrive_service(credentials: goasea.Credentials) -> godisc.Resource:
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
    credentials: goasea.Credentials,
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


def move_gfile_to_dir(
    credentials: goasea.Credentials,
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


def create_empty_google_file(
    credentials: goasea.Credentials,
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


def create_or_overwrite_with_timestamp(
    credentials: goasea.Credentials,
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


def create_google_drive_folder(
    credentials: goasea.Credentials,
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


def _get_folders_in_gdrive(*, credentials: goasea.Credentials) -> list:
    """
    Get a list of folders in Google Drive.

    :param credentials: Google credentials object.
    :return: A list of folders (each containing an ID and name).
    """
    # Build the Google Drive service using the provided credentials.
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
    credentials: goasea.Credentials,
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


def share_google_file(
    credentials: goasea.Credentials,
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

