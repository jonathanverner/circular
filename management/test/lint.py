from fabric.api import task
from management.venv import venv
from management.settings import settings
import subprocess, os

conf = settings(__package__,strip_leading=1)

@task
def lint(report=False):
    args = ['PYTHONPATH=./src/:./tests/brython/ pylint']
    if not report:
        args.append('--reports=n')
    args.append('circular')
    venv(args)
