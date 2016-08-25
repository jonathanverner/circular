from fabric.api import task, local
from management.venv import venv
import pip

@task
def install(package):
    venv(['pip','install',package])

@task
def list():
    venv(['pip','list'])

@task
def freeze():
    venv(['pip','freeze','> requirements.txt'])

@task
def uninstall(package):
    venv(['pip','uninstall',package])

@task
def mkenv():
    local("virtualenv -p /usr/bin/python3.4 virtual_env")
    venv(['pip','install','-r','requirements.txt'])

