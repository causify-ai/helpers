import logging
import functools
import time
import pickle
import os

import pandas as pd
import gspread_pandas
from IPython.display import display

from tqdm.autonotebook import tqdm

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hgoogle_file_api as hgapi

from helpers_root.config_root.config.config_ import ValueTypeHint

_LOG = logging.getLogger(__name__)

# #############################################################################
# Google Sheets
# #############################################################################


GSPREAD_CACHE_FILENAME = "gspread_cache.pkl"

def cache_dict_to_disk(data: dict) -> None:
    _LOG.info("caching to disk: %s", data.keys())
    with open(GSPREAD_CACHE_FILENAME, 'wb') as file:
        pickle.dump(data, file)


def load_dict_from_cache() -> dict:
    if not os.path.exists(GSPREAD_CACHE_FILENAME):
        _LOG.info("No cache from disk")
        data = {}
        cache_dict_to_disk(data)
    with open(GSPREAD_CACHE_FILENAME, 'rb') as file:
        data = pickle.load(file)
    return data


if "_GSPREAD_CACHE" not in globals():
    # Load from disk.
    _GSPREAD_CACHE = load_dict_from_cache()


def reset_cache():
    global _GSPREAD_CACHE
    _GSPREAD_CACHE = {}


#@functools.lru_cache(maxsize=128)
def get_cached_sheet_to_df(url, sheet_name):
    global _GSPREAD_CACHE
    if not _GSPREAD_CACHE.keys():
        print("Cache is EMPTY!")
    key = "%s:%s" % (url, sheet_name)
    if key in _GSPREAD_CACHE:
        _LOG.debug("Cached data found for %s %s" % (url, sheet_name))
        return _GSPREAD_CACHE[key]
    _LOG.info("Reading data from %s %s" % (url, sheet_name))
    spread = gspread_pandas.Spread(url)
    df = spread.sheet_to_df(sheet=sheet_name, index=None)
    #
    _GSPREAD_CACHE[key] = df
    cache_dict_to_disk(_GSPREAD_CACHE)
    return df


def extract_dfs(spread, names, transform_func):
    dfs = []
    for name in names:
        print(name)
        df = spread.sheet_to_df(sheet=name, index=None)
        print(df.shape)
        df = transform_func(df)
        display(df.head(1))
        dfs.append(df)
    #
    df = pd.concat(dfs, axis=0)
    return df


csfy_schema = [
    "first_name",
    "last_name",
    "email",
    "email_verification",
    "linkedin_url",
    "job_title",
    "job_title_description",
    "company_name",
    "company_domain",
    "city",
]


def normalize_csfy_schema(df, cols_map):
    hdbg.dassert_is_subset(cols_map.keys(), df.columns)
    df = df[cols_map.keys()]
    df_out = df.rename(columns=cols_map, inplace=False)
    # Convert in CSFY schema.
    hdbg.dassert_is_subset(df_out.columns, csfy_schema)
    for col in csfy_schema:
        if col not in df_out.columns:
            df_out[col] = ""
    df_out = df_out[csfy_schema]
    return df_out


def get_VC_Tier_2_Partners_data(df):
    cols_map = {
        "email_first": "email",
        "First name": "first_name",
        "last_name": "last_name",
        "job_title": "job_title",
        "company_name": "company_name",
        "company_domain": "company_domain",
        "city": "city",
        "Merge status": "merge_status"
    }
    hdbg.dassert_is_subset(cols_map.keys(), df.columns)
    df = df[cols_map.keys()]
    df_out = df.rename(columns=cols_map, inplace=False)
    return df_out


def get_CausifyScraper_data(gsheet_url, gsheet_name):
    """
    Parse the data from the Google Sheet and convert it to the CSFY schema.

    E.g., Search4.FinTech_VC_in_US.SalesNavigator
    https://docs.google.com/spreadsheets/d/1Lbnyvbb28Cv-y0k-nrG1NSES9F6rxesGoHZV2LOJ6wA/
    """
    # TODO(gp): Use cached.
    spread = gspread_pandas.Spread(gsheet_url)
    df = spread.sheet_to_df(sheet=gsheet_name, index=None)
    #
    cols_map = {
        "linkedinProfileUrl": "linkedin_url",
        "firstName": "first_name",
        "lastName": "last_name",
        "email": "email",
        "jobTitle": "job_title",
        "jobLocation": "city",
        "company": "company_name",
        #"companyWebsite": "company_domain",
    }
    # hdbg.dassert_is_subset(cols_map.keys(), df.columns)
    # df = df[cols_map.keys()]
    # df_out = df.rename(columns=cols_map, inplace=False)
    # # Convert in CSFY schema.
    # hdbg.dassert_is_subset(df_out.columns, csfy_schema)
    # for col in csfy_schema:
    #     if col not in df_out.columns:
    #         df_out[col] = ""
    # df_out = df_out[csfy_schema]
    df_out = normalize_csfy_schema(df, cols_map)
    return df_out


# profileUrl	https://www.linkedin.com/sales/lead/ACwAAABGC0...
# fullName	Zhenya Loginov
# firstName	Zhenya
# lastName	Loginov
# companyName	Accel
# title	Partner
# companyId	17412
# companyUrl	https://www.linkedin.com/sales/company/17412
# regularCompanyUrl	https://www.linkedin.com/company/17412
# summary
# titleDescription	I invest and help European and Israeli founder...
# industry	Venture Capital and Private Equity Principals
# companyLocation	Palo Alto, California, United States
# location	Palo Alto, California, United States
# durationInRole	10 months in role
# durationInCompany	10 months in company
# pastExperienceCompanyName
# pastExperienceCompanyUrl
# pastExperienceCompanyTitle
# pastExperienceDate
# pastExperienceDuration
# connectionDegree	Out of Network
# profileImageUrl	https://media.licdn.com/dms/image/C5103AQHLVkA...
# sharedConnectionsCount	0
# name	Zhenya Loginov
# vmid	ACwAAABGC0cBTaYzMWKXyySFD4zZyoPI59OadWk
# linkedInProfileUrl	https://www.linkedin.com/in/ACwAAABGC0cBTaYzMW...
# isPremium	TRUE
# isOpenLink	FALSE
# query	https://www.linkedin.com/sales/search/people?q...
# timestamp	2024-07-11T18:03:01.973Z
# defaultProfileUrl	https://linkedin.com/in/zhenyaloginov
# hunter_extracted_email	zloginov@accel.com
# hunter_verification	valid
# dropcontact_mail	NaN
# all_emails	NaN


def extract_and_validate_email(df: pd.DataFrame) -> str:
    """
    Extract and validate the email from a transposed DataFrame.
    """
    # List of possible email sources
    import numpy as np
    email_fields = ['hunter_extracted_email', 'dropcontact_mail', 'all_emails']
    # Extract email values from the relevant fields
    email_values = df[email_fields]
    num_values = [
        set([str(v) for v in row if (str(v) != "" and str(v) != "nan")]) for
        _, row in email_values.iterrows()]
    #num_values
    num_values_out = []
    for val in num_values:
        if len(val) > 1:
            raise ValueError("Multiple emails found: %s" % val)
        elif len(val) == 1:
            val = list(val)[0]
        elif len(val) == 0:
            val = "nan"
        num_values_out.append(val)
    return num_values_out


def get_CausifyScraper_data_v2():
    """
    Parse the data from the Google Sheet and convert it to the CSFY schema.

    E.g.,
    Accel_search_export.gsheet
    https://docs.google.com/spreadsheets/d/1tgKVlDMVJJkPPyulTU1ibkBcGLKXeVjLTYN8jhQ9c3M/edit?gid=1151734371#gid=1151734371
    """
    # Accel_search_export.gsheet
    # Andreessen Horowitz (a16z)_search_export.gsheet
    # Benchmark Capital_search_export.gsheet
    # Bessemer Venture Partners_search_export.gsheet
    # General Catalyst_search_export.gsheet
    # Greylock Partners_search_export.gsheet
    # Index Ventures_search_export.gsheet
    # Insight Partners_search_export.gsheet
    # Kleiner Perkins_search_export.gsheet
    # Sequoia Capital_search_export.gsheet
    #
    # > find /Users/saggese/Library/CloudStorage/GoogleDrive-gp@kaizen-tech.io/Shared\ drives/Cold\ outreach/\!All_VC_lists -name "*search_export*" -print0 | sort -z  | xargs -0 -n 1 cat
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1tgKVlDMVJJkPPyulTU1ibkBcGLKXeVjLTYN8jhQ9c3M","resource_key":"","email":"gp@kaizen-tech.io"}
    # https://docs.google.com/spreadsheets/d/1tgKVlDMVJJkPPyulTU1ibkBcGLKXeVjLTYN8jhQ9c3M/edit?gid=1151734371#gid=1151734371
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1p7mKeeUuUS4a2OsHnTbWpe5Fscp8mvjocsWRL8ya6PA","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1Iz9ypwENHwSU-meGknkrH_q7Gbg-CK6pArMQcxNvF3s","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1y3bVUkC2qaZWFwkY9xvOcoUnqXEIDEC06mjUdiwXNNc","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1RQMhAOpiu8BTyiNUl9O6DrmovEYAFqPPyBhiPD9uEZA","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"197W6s8K4tOzSdoT11rk3huGTxlttzXxpkWruHHzyeDQ","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1xSYf8Hzg7vPmP_pSBe4NMkANX013FuTQR2SJgOr8AqU","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1Gf6dVplfK-ufHoGdY3RchlcapQY2Ig5gopM2YMOTuz4","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1EzsnB-a0cmiWpl2A9-McNrTR4D_jXJY9UB0byy8PuIA","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1Ric5JLQOwkj9m4iwZtSo46VzOI0XDEMdeJZBEO4fPQ8","resource_key":"","email":"gp@kaizen-tech.io"}
    # {"":"WARNING! DO NOT EDIT THIS FILE! ANY CHANGES MADE WILL BE LOST!","doc_id":"1rmImy9VByGf1cNKbYmUVh7ktojtRpXL4QLdvPLAB8C4","resource_key":"","email":"gp@kaizen-tech.io"}
    urls = """
1tgKVlDMVJJkPPyulTU1ibkBcGLKXeVjLTYN8jhQ9c3M
1p7mKeeUuUS4a2OsHnTbWpe5Fscp8mvjocsWRL8ya6PA
1Iz9ypwENHwSU-meGknkrH_q7Gbg-CK6pArMQcxNvF3s
1y3bVUkC2qaZWFwkY9xvOcoUnqXEIDEC06mjUdiwXNNc
1RQMhAOpiu8BTyiNUl9O6DrmovEYAFqPPyBhiPD9uEZA
197W6s8K4tOzSdoT11rk3huGTxlttzXxpkWruHHzyeDQ
1xSYf8Hzg7vPmP_pSBe4NMkANX013FuTQR2SJgOr8AqU
1Gf6dVplfK-ufHoGdY3RchlcapQY2Ig5gopM2YMOTuz4
1EzsnB-a0cmiWpl2A9-McNrTR4D_jXJY9UB0byy8PuIA
1Ric5JLQOwkj9m4iwZtSo46VzOI0XDEMdeJZBEO4fPQ8
1rmImy9VByGf1cNKbYmUVh7ktojtRpXL4QLdvPLAB8C4
"""
    urls = urls.split()
    urls = ["https://docs.google.com/spreadsheets/d/" + url for url in urls if url != ""]
    _LOG.debug("urls=\n%s", urls)
    dfs = []
    #urls = urls[:2]
    for url in tqdm(urls):
        #_LOG.debug("Reading %s", url)
        df = get_cached_sheet_to_df(url, "hunter_verification")
        display(df.head(1))
        dfs.append(df)
        #time.sleep(20)
    # Concat.
    _LOG.info("Done")
    df2 = pd.concat(dfs, axis=0)
    display(df2.head(2))
    #
    df2["email"] = extract_and_validate_email(df2)
    # Convert to CSFY schema.
    cols_map = {
        "linkedInProfileUrl": "linkedin_url",
        "firstName": "first_name",
        "lastName": "last_name",
        "email": "email",
        "hunter_verification": "email_verification",
        "title": "job_title",
        "titleDescription": "job_title_description",
        "companyName": "company_name",
        "companyLocation": "city",
    }
    df_out = normalize_csfy_schema(df2, cols_map)
    return df_out


# titleDescription

# ######

def dedup_df(df):
    num_rows = df.shape[0]
    # These are dups for sure.
    duplicated = df.duplicated(subset=["first_name", "last_name", "email"])
    if duplicated.sum() > 0:
        print("num_rows=%s" % df.shape[0])
        df = df.drop_duplicates(subset=["first_name", "last_name", "email"])
        print("num_rows (after dedup)=%s" % df.shape[0])
    # Check for same first / last name.
    duplicated = df.duplicated(subset=["first_name", "last_name"])
    if duplicated.sum() > 0:
        print("names duplicated=%s" % duplicated.sum())
    # Sort.
    df.sort_values(by=["first_name", "last_name"], inplace=True)
    return df


first_names_examples = {
    "Dr. Felix": "Felix",
    "David S.": "David",
    "Christian J.P.": "Christian",
    "Crystal J": "Crystal",
    "Gianpiero (JP)": "JP",
    "Heather A": "Heather",
    "Kristofer \"Kriffy\"": "Kriffy",
    "L. Antonio": "Antonio",
    "Lawrence \"Larry\"": "Larry",
    "Pierre-Jean \"PJ\"": "PJ",
    "R. Danae": "Danae",
    "Richard \"Dick\"": "Dick",
    "Richard (Dick)": "Dick",
    "Timothy P.": "Timothy",
    "Wenji (Tony)": "Tony",
    #
    "AJ": "AJ",
    "ALBERT": "Alberto",
    "AZ": "AZ",
    "joany": "Joany",
}




import re


def clean_first_name(text):
    # Regex to match titles like Dr., Mr., Ms., Mrs., Prof., etc., followed by a
    # first name.
    match = re.search(r'\b(?:Dr\.|Mr\.|Ms\.|Mrs\.|Prof\.|Rev\.)\s+(\w+)',
                      text)
    if match:
        # Return the captured first name.
        text = match.group(1)
    # Regex to match nicknames in parentheses or quotes or extract the first
    # word after a period.
    match = re.search(r'"([^"]+)"|\(([^\)]+)\)|\b(?:\w\.)\s*(\w+)', text)
    if match:
        text = match.group(1) or match.group(2) or match.group(3)
    return text


# I will give a list of "job titles" AT "company name" and you decide if that
# person is an investor, a customer for AI products. If you are sure report "NA"


def print_causify_df_stats(df):
    display(df.head(2))
    print("num_rows=%s" % df.shape[0])
    # These are dups for sure.
    df = df.drop_duplicates(subset=["first_name", "last_name", "email"])
    print("num_rows (after dedup)=%s" % df.shape[0])
    # Report stats.
    print("email_pct=%s" %
            hprint.perc((df["email"] != "").sum(), df.shape[0]))
    # Check for same first / last name.
    duplicated = df.duplicated(subset=["first_name", "last_name"])
    print("names duplicated=%s" % duplicated.sum())


def save_to_tmp(df):
    # Name of the new Google Sheet (this will be created)
    spread = gspread_pandas.Spread('display_tmp')
    # Write DataFrame to the Google Sheet (this creates the sheet if it doesn't exist)
    spread.df_to_sheet(df, index=False, sheet='Sheet1', start='A1',
                       replace=True)
    #
    #hgapi.set_row_height("display_tmp", 30)


# #############################################################################
# Yamm
# #############################################################################


# Total sent	726     100%
# BOUNCED	    20	    2.8%	Email not delivered (e.g., email account deactivate)
# EMAIL_OPENED	266	    36.6%	User opened email
# RESPONDED	    24	    3.4%	User responded
# EMAIL_CLICKED	31	    4.4%	User clicked one link
# EMAIL_SENT	385	    53.0%	Email sent but not opened
# UNSUBSCRIBED	0	    0.0%    Unsubscribed

# DELIVERED	    706	    97.2%	Email was actually delivered
#   = total_sent - bounced


def yamm_stats(df):
    col_name = "merge_status"
    hdbg.dassert_in(col_name, df.columns)
    df_stats = df.groupby(col_name)[col_name].count()
    vals = df_stats.to_dict()
    yamm_status = {
        "BOUNCED": "bounced",
        "EMAIL_OPENED": "opened",
        "RESPONDED": "responded",
        "EMAIL_CLICKED": "clicked",
        "EMAIL_SENT": "unopened",
        "UNSUBSCRIBED": "unsubscribed"
    }
    for k, v in yamm_status.items():
        vals[v] = int(vals.get(k, 0))
    #
    vals["total"] = df.shape[0]
    vals["delivered"] = vals["total"] - vals["bounced"]
    return vals


def yamm_stats_to_pct(vals):
    if isinstance(vals, pd.DataFrame):
        vals = yamm_stats(vals)
    print("Total emails sent: %s" % vals["total"])
    yamm_ordered = ("delivered bounced opened responded clicked "
                    "unopened unsubscribed").split()
    vals_pct = {}
    for k in yamm_ordered:
        hdbg.dassert_lte(vals[k], vals["total"])
        vals_pct[k] = vals[k] / vals["total"]
        vals_pct[k] = float("%.1f" % (vals_pct[k] * 100))
        print("%s: %.1f%%" % (k, vals_pct[k]))
    #return vals_pct


def merge_yamm_dfs(spread, names):
    dfs = []
    for name in names:
        print(name)
        df = spread.sheet_to_df(sheet=name, index=None)
        print(df.shape)
        dfs.append(df)
    #
    df = pd.concat(dfs, axis=0)
    return df


