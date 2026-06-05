#!/bin/bash -xe

dir_names="amp/helpers_root/dev_scripts_helpers/cleanup_scripts helpers_root/dev_scripts_helpers/cleanup_scripts dev_scripts_helpers/cleanup_scripts"

amp/helpers_root/dev_scripts_helpers/system_tools/replace_text.py \
    --old "dataflow_orange.pipelines.C3.C3a_pipeline_tmp.C3a_DagBuilder_tmp" \
    --new "dataflow_lemonade.pipelines.C3.C3a_pipeline.C3a_DagBuilder" \
    --exclude_dirs "$dir_names"

amp/helpers_root/dev_scripts_helpers/system_tools/replace_text.py \
    --old "dataflow_orange.pipelines.C8.C8a_pipeline_tmp.C8a_DagBuilder_tmp" \
    --new "dataflow_lemonade.pipelines.C8.C8a_pipeline.C8a_DagBuilder" \
    --exclude_dirs "$dir_names"

amp/helpers_root/dev_scripts_helpers/system_tools/replace_text.py \
    --old "dataflow_orange.pipelines.C8.C8b_pipeline_tmp.C8b_DagBuilder_tmp" \
    --new "dataflow_lemonade.pipelines.C8.C8b_pipeline.C8b_DagBuilder" \
    --exclude_dirs "$dir_names"

amp/helpers_root/dev_scripts_helpers/system_tools/replace_text.py \
    --old "dataflow_orange.system.C3" \
    --new "dataflow_lemonade.system.C3" \
    --exclude_dirs "$dir_names"

amp/helpers_root/dev_scripts_helpers/system_tools/replace_text.py \
    --old "dataflow_orange.system.C8" \
    --new "dataflow_lemonade.system.C8" \
    --exclude_dirs "$dir_names"