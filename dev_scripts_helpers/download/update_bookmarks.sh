# 1. Update CSV with latest Raindrop bookmarks
if [[ 0 == 1 ]]; then
update_bookmarks_from_raindrop.py \
  --target local_csv \
  --local_csv /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
  --action download_raindrop_data --action combine_data
fi;

# 2. Show situation of CSV vs iCloud Drive (and notes1/bookmarks) — safe, no writes
if [[ 1 == 1 ]]; then
process_bookmarks.py \
  -i /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
  --dest_type obsidian --dry_run
fi;

# 3. Populate both destinations (same command, drop --dry_run)
if [[ 1 == 1 ]]; then
process_bookmarks.py \
  -i /Users/saggese/src/notes1/bookmarks/update_gsheet_links_from_raindrop.combined_data.csv \
  --dest_type obsidian --limit 10   # default limit=10; raise or use --limit 0 for backfill-only
fi;
