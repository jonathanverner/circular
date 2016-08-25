from fabric.api import task,lcd,local

from management.venv import venv
from management.settings import settings

@task
def build():
    venv(['sphinx-build','-b','html', '-D','latex_paper_size=a4', 'docs','www/docs'])
        
@task
def coverage():
    venv(['sphinx-build','-b','coverage', '-D','latex_paper_size=a4', 'docs','www/docs/coverage'])
    
@task
def clean():
    local('rm -rf www/docs')
    local('mkdir www/docs')
    
