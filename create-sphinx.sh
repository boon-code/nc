#!/bin/bash

cd $(dirname $0)
mkdir -p ./sphinx/build/html
touch ./sphinx/build/html/.nojekyll
make --directory=sphinx/ html
tar cz --directory=./sphinx/build/html/ . > documentation.tgz

