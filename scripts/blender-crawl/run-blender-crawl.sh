#!/bin/bash
directory=$1 

echo "Looking for .blend files in follwing directory: '$directory'" 
for file in $directory/*.blend; do
    if test -f "$file"; then
        echo "FOUND FILE!" $(basename ${file})
        blender $file --background --python test-py-file.py
    fi
done
echo "Blener-Crawl is done!"


# Usage!
# pass directory containing .blend files like example below:
# ./run-blender-crawl.sh /path/to/blends/