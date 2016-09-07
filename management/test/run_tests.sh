#!/bin/bash
set -ev
python -m SimpleHTTPServer 7000 2>/dev/null >/dev/null &

PYTHONPATH='./src/:./tests/brython/' python -m pytest -rw --driver PhantomJS --ignore=./tests/selenium/webroot/ --ignore=./tests/results/tests tests
