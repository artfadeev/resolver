#!/bin/bash -e

echo "Running python tests:";
python3 -m tests;

echo "Runing shell tests:";
index_path=$1;
if [ -z $index_path ];
then
    echo "Error: index_path not provided!";
    exit 1;
fi;

bash ./scripts/test_cli.sh $index_path;

echo "All tests are successfull!"
