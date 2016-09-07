from fabric.api import task, local, lcd
from management.venv import venv
from management.settings import settings
import os

conf = settings(__package__, strip_leading=1)

@task
def all():
    cleanup()
    with lcd('tests/selenium/webroot'):
        local('python -m SimpleHTTPServer 7000 2>/dev/null >/dev/null &')
    venv(['PYTHONPATH=./src/:./tests/brython/ python',
          '-m pytest',
          '-rw',
          '--driver PhantomJS',
          '--html tests/results/results.html',
          '--cov=./src/circular',
          '--ignore=./tests/selenium/webroot/',
          '--ignore=./tests/results/',
          'tests'])
    cleanup()

@task
def server():
    cleanup()
    venv(['PYTHONPATH=./src/:./tests/brython/ python',
          '-m pytest',
          '-rw',
          '--html tests/results/results.html',
          '--cov=./src/circular',
          '--ignore=./tests/selenium/',
          '--ignore=./tests/results/',
          'tests'])
    cleanup()

@task
def single(test):
    cleanup()
    venv(['PYTHONPATH=./src/:./tests/brython/ python',
          '-m pytest',
          '--pdb',
          '--full-trace',
          '--maxfail=1',
          '--driver PhantomJS',
          '--ignore=./tests/selenium/webroot/',
          '--ignore=./tests/results/',
          os.path.join('tests/circular', test)])
    cleanup()

@task
def cleanup():
    local('rm -f ./tests/selenium/webroot/tests/*')
