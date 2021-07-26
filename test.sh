#!/bin/sh

MISSING=""

if command -v python2 > /dev/null 2>&1; then
    for FILE in eg/*.dtr; do
        echo "python2 src/dieter.py $FILE"
        python2 src/dieter.py $FILE || exit 1
    done
else
    MISSING="${MISSING}2"
fi
if command -v python3 > /dev/null 2>&1; then
    for FILE in eg/*.dtr; do
        echo "python3 src/dieter.py $FILE"
        python3 src/dieter.py $FILE || exit 1
    done
else
    MISSING="${MISSING}3"
fi

if [ "x${MISSING}" = "x23" ]; then
    echo "Neither python2 nor python3 found on executable search path. Aborting."
    exit 1
fi
