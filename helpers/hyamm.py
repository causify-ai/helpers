yamm_status = "DELIVERED BOUNCED EMAIL_OPENED RESPONDED EMAIL_CLICKED EMAIL_SENT UNSUBSCRIBED".split()

def yamm_stats(df):
    #print(df.shape)
    df_stats = df.groupby("Merge status")["Merge status"].count()
    #print(df_stats)
    # vals = {}
    # for yamm_status_tmp in yamm_status:
    #     vals[yamm_status] = df_stats.get(yamm_status_tmp, 0)
    vals = df_stats.to_dict()
    for k in yamm_status:
        vals[k] = vals.get(k, 0)
    vals["EMAIL_SENT"] = df.shape[0]
    print(vals)