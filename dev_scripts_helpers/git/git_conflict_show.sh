#!/bin/bash -e

# """
# Generate the files involved in a merge conflict for a single file.
#
# Not every conflict has all 3 stages (e.g., an add/add or delete/modify
# conflict is missing the base or one of the sides), so a missing stage is
# reported and skipped instead of aborting the script.
# """

source helpers.sh

check_num_args $# 1

show_stage() {
  # """
  # Extract one stage of a conflicted file into an output file.

  # :param stage: conflict stage number (1=base, 2=ours, 3=theirs)
  # :param file: path of the conflicted file
  # :param out_file: path to write the extracted content to
  # :return: 0 if the stage exists, 1 if it was missing (out_file is removed)
  # """
  stage=$1
  file=$2
  out_file=$3
  if git show ":$stage:$file" >$out_file 2>/dev/null; then
    return 0
  else
    echo "WARNING: stage $stage ('$out_file') not found for '$file': skipping"
    rm -f $out_file
    return 1
  fi;
}

FILE=$1
echo "# Processing $FILE"
BASE="$FILE.1_base"
show_stage 1 $FILE $BASE && HAS_BASE=1 || HAS_BASE=0
#
OUR="$FILE.2_our"
show_stage 2 $FILE $OUR && HAS_OUR=1 || HAS_OUR=0
#
THEIR="$FILE.3_their"
show_stage 3 $FILE $THEIR && HAS_THEIR=1 || HAS_THEIR=0
#
#ls $FILE.*
if [[ $HAS_THEIR == 1 && $HAS_OUR == 1 ]]; then
  echo "> vimdiff $THEIR $OUR"
fi;
if [[ $HAS_BASE == 1 && $HAS_OUR == 1 ]]; then
  echo "> vimdiff $BASE $OUR"
fi;
if [[ $HAS_BASE == 1 && $HAS_THEIR == 1 ]]; then
  echo "> vimdiff $BASE $THEIR"
fi;
