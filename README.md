# Circular

Circular is a Python web-framework somewhat similar to (AngularJS 1)[https://angularjs.org/]. It is built upon the 
(Brython)[http://http://www.brython.info/] python-to-js compiler.

# Hacking

To get the source do:

```
$ git clone git@github.com:jonathanverner/circular.git
$ cd circular
$ git submodule init
$ git submodule update
```

(the last two steps pull in the Brython dependency)

The sources for the library are in the src/circular subfolder. Eventually I intend to provide p
more documentation. Currently just use the source (and the tests in tests/circular directory).

For development purposes there is a webpage which contains a python console and a test template
where you can experiment with the library and your changes to it. This webpage is located in
web_src. The page uses some stylesheets which are compiled from (Sass)[http://sass-lang.com/] 
sources and icons from the (Material Design Icons)[http://materialdesignicons.com].

(Fabric)[http://www.fabfile.org/] is used to automate building the stylesheets and copying them 
to the right place (`www/css`, `www/fonts`). You can install fabric either using `pip`
(e.g. `pip install fabric`) or your package manager (e.g. `sudo apt-get install fabric`).
Then compiling and copying the stylesheets is just a matter of

```
$ fab web.deploy
```

Note that some python libraries are used to compile the sass source. 
To install them use 

```
$ fab test.mkenv
```

to build a virtual-env with the necessary packages and then **modify**
management/web/sass.sh to point to the right directory (sorry, I know
this is ugly, but I didn't have the time to change it yet and it works
for me :-))

To serve the test page, just run

```
$ fab web.serve
```

(which really is just a shortcut for `python -m SimpleHTTPServer`) and point
your browser to `http://localhost:8000`.

# Testing

Tests are based on the (pytest)[http://docs.pytest.org/] testing framework for Python
and are run using

```
$ fab test.all
```

(or `fab test.single:template/test_tag.py` for a single test file; this drops you into a
pdb shell in case of failure)
