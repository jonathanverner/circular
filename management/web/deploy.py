import os, sys

from fabric.api import task
from management.shell import cpR, stream

from management.settings import settings
conf = settings(__package__,strip_leading=1)


from .stylesheets import buildcss

#def compile_js(src,dst=None):
    #if dst is not None:
        ##stream("browserify "+src,program=True).pipe("babel --presets es2015").save(dst)
        ##stream("browserify -t babelify --presets es2015 "+src,program=True).save(dst)
        #stream("browserify "+src,program=True).save(dst)
    #else:
        ##return stream("browserify "+src,program=True).pipe("babel --presets es2015")
        ##return stream("browserify -t babelify --presets es2015 "+src,program=True)
        #return stream("browserify "+src,program=True)



import jinja2
from jinja2.filters import environmentfilter
jinja_env=jinja2.Environment(extensions=['jinja2.ext.autoescape'])
jinja_env.loader=jinja2.FileSystemLoader(["."])
def render_tpl(tpl,context,dst):
    stream(jinja_env.get_template(tpl).render(context)).save(dst)


@task
def copy_assets():
    assets = conf.assets
    for asset in assets.values():
        cpR(asset['source'],asset['target'],pattern=asset['pattern'],create_parents=True)


@task
def deploy():
    buildcss()
    copy_assets()
    
@task
def serve():
    import SimpleHTTPServer
    import SocketServer
    
    os.chdir('www')

    PORT = 8000

    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

    httpd = SocketServer.TCPServer(("", PORT), Handler)

    print "serving at port", PORT
    httpd.serve_forever()
