#!/bin/sh

for FILE in eg/*.dtr; do
    echo $FILE
    src/dieter.py $FILE || exit 1
done
