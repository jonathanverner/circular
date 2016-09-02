from fabric.api import task
from management.venv import venv
from management.settings import settings
import subprocess, os

conf = settings(__package__,strip_leading=1)

@task
def all():
    cleanup()
    venv(['PYTHONPATH=./src/:./tests/brython/ python','-m', 'pytest', '-rw', '--cov=./src/circular', 'tests'])
    cleanup()

@task
def single(test):
    cleanup()
    venv(['PYTHONPATH=./src/:./tests/brython/ python','-m', 'pytest', '--pdb','--full-trace', '--maxfail=1',os.path.join('tests/circular',test)])
    cleanup()

@task
def cleanup():
    pass
