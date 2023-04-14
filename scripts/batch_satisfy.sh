#!/bin/bash -e
index_path=$1;
mode=$2;

output_file=$3;
if [ -z $output_file ];
then
    output_file="processed_${mode}_${index_path}";
fi;
echo "Outputting to file $output_file";

cat $index_path | sed "s/:.*//" | while IFS=$'\n' read name; do
    echo "=== Processing package $name ===";
    python3 -m resolver --mode $mode -I $index_path satisfy $name;
done > $output_file


