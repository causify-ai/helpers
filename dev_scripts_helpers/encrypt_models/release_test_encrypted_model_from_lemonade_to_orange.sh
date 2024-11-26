#!/bin/bash -xe
# 1) Set common vars.
export SRC_DIR=$HOME/src_vc/lemonade1
export DST_DIR=$HOME/src/orange1

# 2) Ecrypt `core_lem`. Disable `--test` option because there is no model under `core_lem`,
# only helper functions.
export MODEL_DIR=core_lem
cd $SRC_DIR
amp/helpers_root/dev_scripts_helpers/encrypt_models/encrypt_model.py \
    --input_dir $MODEL_DIR \
    --output_dir encrypted_core_lem \
    --release_dir $DST_DIR/$MODEL_DIR \
    -v DEBUG \
    2>&1 | tee encrypt_model.log

# # 3) Encrypt `dataflow_lemonade/pipelines`.
# Use C9 because it depends on `core_lem` meaning that we test `dataflow_lemonade/pipelines`
# and `core_lem` encryption at the same time.
export MODEL_DIR=dataflow_lemonade
export MODEL_NAME=C9
cd $SRC_DIR
amp/helpers_root/dev_scripts_helpers/encrypt_models/encrypt_model.py \
    --input_dir $MODEL_DIR/pipelines \
    --output_dir $MODEL_DIR/encrypted_pipelines \
    --release_dir $DST_DIR/$MODEL_DIR/pipelines \
    --model_dag_builder "${MODEL_NAME}a_DagBuilder" \
    --model_dag_builder_file ${MODEL_NAME}/${MODEL_NAME}a_pipeline.py \
    --test \
    -v DEBUG \
    2>&1 | tee encrypt_model.log

