#!/bin/bash

DATA_ROOT=vim_bench
SETTING=$1
SOURCE_DATASET=$2
INPUT_IMAGE_PATH=$DATA_ROOT/$SOURCE_DATASET/source_image_path

run_zs_converter() {
    python bench_tool/converter.py --input-file $DATA_ROOT/$SOURCE_DATASET/vim_$SOURCE_DATASET.jsonl --input-image-path $INPUT_IMAGE_PATH --output-image-path $DATA_ROOT/$SOURCE_DATASET/VIM_$SOURCE_DATASET\_$SETTING --raw-image-path $DATA_ROOT/$SOURCE_DATASET/VIM_$SOURCE_DATASET\_$SETTING\_raw --bench-name $SOURCE_DATASET
}

run_os_converter() {
    SEQUNCE_NUM=$1
    ORIENTATION=$2
    python bench_tool/converter_sequence.py --input-file $DATA_ROOT/$SOURCE_DATASET/vim_$SOURCE_DATASET\_wcontextlines\_$SEQUNCE_NUM.jsonl --input-image-path $INPUT_IMAGE_PATH --output-image-path $DATA_ROOT/$SOURCE_DATASET/VIM_$SOURCE_DATASET\_$SETTING --raw-image-path $DATA_ROOT/$SOURCE_DATASET/VIM_$SOURCE_DATASET\_$SETTING\_raw --bench-name $SOURCE_DATASET --sequence-num $SEQUNCE_NUM --add-context $DATA_ROOT/$SOURCE_DATASET/vim_$SOURCE_DATASET.json --orientation $ORIENTATION
}

run_ps_converter() {
    python bench_tool/converter_sequence.py --input-file $DATA_ROOT/$SOURCE_DATASET/vim_$SOURCE_DATASET.jsonl --input-image-path $INPUT_IMAGE_PATH --output-image-path $DATA_ROOT/$SOURCE_DATASET/VIM_$SOURCE_DATASET\_$SETTING --raw-image-path $DATA_ROOT/$SOURCE_DATASET/VIM_$SOURCE_DATASET\_$SETTING\_raw --bench-name $SOURCE_DATASET
}

case $SETTING in
    "zs")
        run_zs_converter
        ;;
    "os")
        run_os_converter 2 horizontal
        ;;
    "ps")
        run_ps_converter
        ;;
    *)
        echo "Invalid setting: $SETTING"
        exit 1
        ;;
esac
