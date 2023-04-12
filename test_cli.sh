#!/bin/bash

# First and only argument is path to the index file
set -e
INDEX_PATH=$1

# Test subcommand "latest"
cat packageIndex.txt | cut -d " " -f 1 | sort | uniq | while IFS=$'\n' read name; do
    real_answer=$(grep "^$name" $INDEX_PATH | cut -d " " -f 2 | sed "s/://" | sort -n | tail -1)
    resolver_answer=$(python3 resolver/ -I $INDEX_PATH latest $name)
    if [ $real_answer -ne $resolver_answer ]
    then
        echo "Answer for $name package is wrong: expected $real_answer, got $resolver_answer";
        exit 1
    fi
done

echo "Subcommand latest works fine for entries from $INDEX_PATH."
