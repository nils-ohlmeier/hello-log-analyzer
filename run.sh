#!/bin/bash

aws s3 cp --recursive s3://telemetry-published-v2/loop/Firefox/ .

rm -r OTHER

find release beta aurora nightly -name "*.lzma" -exec lzma -d {} \;

./splitter.py release beta aurora nightly

./aggregator.py release beta aurora nightly

mkdir OUTPUT
cp report.json OUTPUT
