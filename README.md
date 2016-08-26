# Circular

Circular is a Python web-framework somewhat similar to [AngularJS 1](https://angularjs.org/). It is built upon the 
[Brython](http://www.brython.info/) python-to-js compiler.

# Using Circular

Currently, the code is not yet ready for use. If you are adventurous, you can look
at `web_src/index.html`. There are several steps you need to do:

## Include Brython

First install [Brython](http://www.brython.info) (note that currently Brython
version 2.6 is needed) and then put the following in the `<head>` section of your html:

```html
    <script type="text/javascript" src="https://cdn.rawgit.com/brython-dev/brython/3.2.6/www/src/brython_dist.js">
    </script>
    <script>
        var onLoadHandler = function() {
            brython({'debug':1});
        };
    </script>
```

and then

```html
    <body onload="onLoadHandler()">
```

to load initialize it and run the python scripts (shown later).

## Include the circular library

Next add the following into your `head` section

```html
<link rel="pythonpath" href="lib" hreflang="py" />
```

replacing `lib` with the url of the place where the `circular` directory with the library
is located.

## Write a template

For example, you could include the following in your body

```html
    <div id='test'>
        Hello {{ name }}, how are you? Which is your favourite colour?
        <ul>
            <li tpl-for='c in colours' class='{{ c["css"] }}'> c["name"] </li>
        </ul
    </div>

```

## Initialize the library & parse the template

Put a Python script tag into your head (eventually, you would put it into
a separate file, but for simplicity we include it in the head)

```html
<script type="text/python">

</script>
```
and put the following python code inside:

```python
from browser import document as doc

from circular.template import Template, Context

Template.set_prefix('tpl-')             # Sets the prefix used to identify template tags (e.g. tpl-for)
tpl = Template(doc['test_tpl'])         # Parses the template contained in the <div id='test'> dom element
ctx = Context()                         # Creates a new context (placeholder for data which can be used in the template)
tpl.bind_ctx(ctx)                       # Binds the context to the template (this populates the template with the data)
                                        # Initially the context does not contain any data so the rendered template will
                                        # not contain much.
ctx.name='Jonathan'                     # Set the name and colours variables
ctx.colours = [{"css":'red',"name":"Red"},{"css":'green',"name":"Green"},{"css":'blue',"name":'Blue'}]

                                        # After a while (approx. 100 msecs) the template should automatically update
                                        # with the new values
</script>
```

When you load the page it will take some time to initialize (load Brython),
and import the circular library. Eventually it should result in a page which looks
something like

```html
    <div id='test'>
        Hello Jonathan, how are you? Which is your favourite colour?
        <ul>
          <li class='red'>Red</li>
          <li class='green'>Green</li>
          <li class='blue'>Blue</li>
        </ul>
    </div>
```




# Hacking

## Source code

To get the source do:

```shell
$ git clone https://github.com/jonathanverner/circular.git
$ cd circular
$ git submodule init
$ git submodule update
```

(the last two steps pull in the Brython dependency)

The sources for the library are in the src/circular subfolder. Eventually I intend to provide p
more documentation. Currently just use the source (and the tests in tests/circular directory).

For development purposes there is a webpage which contains a python console and a test template
where you can experiment with the library and your changes to it. This webpage is located in
web_src. The page uses some stylesheets which are compiled from [Sass](http://sass-lang.com/) 
sources and icons from the [Material Design Icons](http://materialdesignicons.com).

[Fabric](http://www.fabfile.org/) is used to automate building the stylesheets and copying them 
to the right place (`www/css`, `www/fonts`). You can install fabric either using `pip`
(e.g. `pip install fabric`) or your package manager (e.g. `sudo apt-get install fabric`).
Then compiling and copying the stylesheets is just a matter of

```shell
$ fab web.deploy
```

Note that some python libraries are used to compile the sass source. 
To install them use 

```shell
$ fab test.mkenv
```

to build a virtual-env with the necessary packages and then **modify**
management/web/sass.sh to point to the right directory (sorry, I know
this is ugly, but I didn't have the time to change it yet and it works
for me :-))

To serve the test page, just run

```shell
$ fab web.serve
```

(which really is just a shortcut for `python -m SimpleHTTPServer`) and point
your browser to `http://localhost:8000`.

## Issues

The project uses the [Issue tracker](https://gitlab.com/Verner/circular/issues) at [GitLab](https://gitlab.com).

## Testing

Tests are based on the [pytest](http://docs.pytest.org/) testing framework for Python
and are run using

```shell
$ fab test.all
```

(or `fab test.single:template/test_tag.py` for a single test file; this drops you into a
pdb shell in case of failure)
