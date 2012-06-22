#!/bin/bash

cd $(dirname $0)
cd sphinx
mkdir -p ./build/html
touch ./build/html/.nojekyll
make html
