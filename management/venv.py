from fabric.api import local

def venv(args):
    nargs=[]
    for a in args:
        if ' ' in a:
            nargs.append("'"+a+"'")
        else:
            nargs.append(a)
    cmd = ' '.join(args)
    local('bash -lic "source virtual_env/bin/activate && '+cmd+'"')