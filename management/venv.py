from fabric.api import local

def venv(args,prefix="./"):
    nargs=[]
    for a in args:
        if ' ' in a:
            nargs.append("'"+a+"'")
        else:
            nargs.append(a)
    cmd = ' '.join(args)
    local('bash -lic "source '+prefix+'virtual_env/bin/activate && '+cmd+'"')
