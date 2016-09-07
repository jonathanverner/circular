#!/bin/bash
set -ev
cd ./tests/selenium/webroot
python -m http.server 7000 &
cd ../../../

PYTHONPATH='./src/:./tests/brython/' python -m pytest -rw --driver PhantomJS --ignore=./tests/selenium/webroot/ --ignore=./tests/results/tests tests
