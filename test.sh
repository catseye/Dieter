#!/bin/sh

for FILE in eg/*.dtr; do
    echo $FILE
    python2 src/dieter.py $FILE || exit 1
    python3 src/dieter.py $FILE || exit 1
done
