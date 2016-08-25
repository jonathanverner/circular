import os
import posixpath
import subprocess
import re

class stream(object):
    def __init__(self,data,program=False,cwd=None):
        if program:
            p = subprocess.Popen(data, stdout=subprocess.PIPE,stdin=subprocess.PIPE,shell=True,cwd=cwd)
            self.data = p.communicate("")[0]
        else:
            self.data = data

    def pipe(self,program,cwd=None,stdout=None):
        if callable(program):
            if cwd is not None:
                cd = os.getcwd()
                os.chdir(cwd)
                ret = stream(program(self.data))
                os.chdir(cd)
                return ret
        else:
            if stdout is None:
                stdout=subprocess.PIPE
            p = subprocess.Popen(program, stdout=stdout,stdin=subprocess.PIPE,shell=True,cwd=cwd)
            return stream(p.communicate(self.data)[0])

    def append(self,data):
        if isinstance(data,stream):
            self.data = self.data + data.data
        else:
            self.data = self.data + data

    def save(self,path,append=False):
        if append:
            out = open(path,'a')
        else:
            out = open(path,'w')
        out.write(self.data)

def cat(*args):
    data = ""
    for path in args:
        if type(path) == list:
            for p in path:
                if os.path.exists(p):
                    data = data + open(p,'r').read()
        elif os.path.exists(path):
            data = data + open(path,'r').read()
    return stream(data)


def ls(path, pattern, recursive=False):
    ret = []
    if not os.path.isdir(path):
        return [path]
    for node in os.listdir(path):
        try:
            if re.match(pattern,node):
                node_path = os.path.join(path,node)
                if os.path.isdir(node_path):
                    if recursive:
                        ret.extend(ls(os.path.join(node_path),pattern,recursive))
                else:
                    ret.append(node_path)
        except Exception, e:
            pass
    return ret


def cp(src,dst,create_parents=False,filters=[]):
    src_dir = os.path.dirname(src)
    if create_parents:
        mkdir_p(os.path.dirname(dst))
    s=stream(open(src).read())
    for f in filters:
        s = s.pipe(f,cwd=src_dir)
    s.save(dst)
    
def cpR(src,dst,pattern='.*',create_parents=False,filters=[]):
    for p in ls(src,pattern,True):
        if os.path.exists(p) and not os.path.isdir(p):
            dest_path = dst+'/'+p[len(src):]
            cp(p,dest_path,create_parents=create_parents,filters=filters)
    

def mkdir_p(path):
    dirs = path.split(os.sep)
    parent=''
    for d in dirs:
        path = parent+d
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise BaseException("Path component '"+parent+d+"' is a file")
        else:
            os.mkdir(path)
        parent = parent + d + posixpath.sep
