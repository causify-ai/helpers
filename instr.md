Step 1
Add a --stats_file output for 

/Users/saggese/src/umd_classes1/helpers_root/dev_scripts_helpers/llms/llm_cli.py --input=bookmarks/2026-08-15.hn_49314902.Software_Engineering_fundamentals_matter_more.3.hn_url.txt --output=bookmarks/2026-08-15.hn_49314902.Software_Engineering_fundamentals_matter_more.4.hn_url.summary.md --pf=tmp.summarize_text_with_llm.prompt.txt --model=gpt-4o-mini --lint

to save the info like:
- model: ...
- number of chars in (approximate tokens) for input
- number of chars out (tokens)
- number of chars prompt (tokens)
- wallclock time to summarize
- cost

Step 2
In process_bookmarks.py read the stats for both summarization tasks
and add information about 
- wallclock time to download
and the information from the stats_file for both phases

- Save a new file associated to the output with the stats
