import pandas as pd
import gspread_pandas
from IPython.display import display

import helpers.hdbg as hdbg
import helpers.hprint as hprint



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
    #print(df.shape)
    col_name = "merge_status"
    hdbg.dassert_in(col_name, df.columns)
    df_stats = df.groupby(col_name)[col_name].count()
    #print(df_stats)
    # vals = {}
    # for yamm_status_tmp in yamm_status:
    #     vals[yamm_status] = df_stats.get(yamm_status_tmp, 0)
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
    "linkedin_url",
    "job_title",
    "company_name",
    "company_domain",
    "city",
]


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
    spread = gspread_pandas.Spread(gsheet_url)
    df = spread.sheet_to_df(sheet=gsheet_name, index=None)
    cols_map = {
        "linkedinProfileUrl": "linkedin_url",
        "firstName": "first_name",
        "lastName": "last_name",
        "email": "email",
        "jobTitle": "job_title",
        "jobLocation": "city",
        "company": "company_name",
    }
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
