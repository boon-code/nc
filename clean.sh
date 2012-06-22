#!/bin/bash

cd $(dirname $0)
rm -rf ./sphinx/build
find ./src/ -name "*.pyc" -exec rm "{}" ";"
find . -name "*~" -exec rm "{}" ";"
