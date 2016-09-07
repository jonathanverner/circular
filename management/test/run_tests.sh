#!/bin/bash
set -ev
python -m SimpleHTTPServer 7000 &

PYTHONPATH='./src/:./tests/brython/' python -m pytest -rw --driver PhantomJS --ignore=./tests/selenium/webroot/ --ignore=./tests/results/tests tests
