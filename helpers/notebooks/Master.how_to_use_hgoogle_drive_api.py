# %% [markdown]
# CONTENTS:
# - [hgoogle_file_api.py](#hgoogle_file_api.py)
#   - [Get Credentials for your drive](#get-credentials-for-your-drive)
#   - [Get Tab/Sheet id of a particular google sheet](#get-tab/sheet-id-of-a-particular-google-sheet)
#   - [Freeze Rows](#freeze-rows)
#   - [Change the height of certin rows](#change-the-height-of-certin-rows)
#   - [Read some nice data](#read-some-nice-data)
#   - [Write this nice data](#write-this-nice-data)

# %% [markdown]
# <a name='hgoogle_file_api.py'></a>
# # hgoogle_file_api.py

# %%
#!sudo /bin/bash -c "(source /venv/bin/activate; pip install --upgrade google-api-python-client)"
# !sudo /bin/bash -c "(source /venv/bin/activate; pip install --upgrade pip install oauth2client)"
#!sudo /bin/bash -c "(source /venv/bin/activate; pip install --upgrade gspread)"

# %%
import importlib
import helpers.hgoogle_drive_api as hgodrapi

importlib.reload(hgodrapi)

# %% [markdown]
# <a name='get-credentials-for-your-drive'></a>
# ## Get Credentials for your drive

# %%
google_creds = hgodrapi.get_credentials()
print(google_creds)

# %%
service = hgodrapi.get_sheets_service(credentials=google_creds)
print(service)

# %% [markdown]
# <a name='get-tab/sheet-id-of-a-particular-google-sheet'></a>
# ## Get Tab/Sheet id of a particular google sheet

# %%
sheet_name = "cleaned_profiles_1"
url = "https://docs.google.com/spreadsheets/d/1VRJQZ4kSoqAeOr9MkWcYbIcArNRyglTREaMg1WlZHGA/edit?gid=1687996260#gid=1687996260"
sheet_id = "1VRJQZ4kSoqAeOr9MkWcYbIcArNRyglTREaMg1WlZHGA"
credentials = google_creds

# %% [markdown]
# <a name='freeze-rows'></a>
# ## Freeze Rows

# %%
row_indices = [0, 1, 2]
hgodrapi.freeze_rows(
    sheet_id=sheet_id,  
    row_indices=row_indices,
    sheet_name = sheet_name,
    credentials=credentials
)

# %% [markdown]
# <a name='change-the-height-of-certin-rows'></a>
# ## Change the height of certin rows

# %%
hgodrapi.set_row_height(sheet_id=sheet_id,height= 20, start_index = 0, end_index =2, sheet_name = sheet_name,credentials=google_creds)

# %% [markdown]
# <a name='read-some-nice-data'></a>
# ## Read some nice data

# %%
nice_data = hgodrapi.read_google_file(url, sheet_name, credentials=google_creds)

# %%
nice_data.head()

# %%
nice_data.shape

# %% [markdown]
# <a name='write-this-nice-data'></a>
# ## Write this nice data

# %%
hgodrapi.write_to_google_sheet(nice_data, url, "testing_tab", credentials=google_creds)


