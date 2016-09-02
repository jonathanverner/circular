.. _installing:

*******************
Installing Circular
*******************

=====================================================
Prerequisites: `Brython <http://www.brython.info>`_
=====================================================

First you will need to install Brython.

Option 1: Use a CDN hosted version of Brython
---------------------------------------------

This is the most straightforward. You just have to include the following snippet
in the head section of your ``index.html``:

.. code-block:: html

    <script type="text/javascript" src="https://cdn.rawgit.com/brython-dev/brython/3.2.7/www/src/brython_dist.js">
    </script>
    <script>
        var onLoadHandler = function() {
            brython({'debug':1});
        };
    </script>

and then call the function `onLoadHandler` when the page is loaded:

.. code-block:: html

    <body onload="onLoadHandler()">


Option 2: Install a local version of Brython
--------------------------------------------

Clone the `brython repo <https://github.com/brython-dev/brython.git>`_ from github:

.. code-block:: shell

    $ git clone https://github.com/brython-dev/brython.git


Then put a link to the `brython` directory to the place you serve your files from
and put the following in the `<head>` section of your html:

.. code-block:: html

    <script type="text/javascript" src="/brython/www/src/brython_dist.js">
    </script>
    <script>
        var onLoadHandler = function() {
            brython({'debug':1});
        };
    </script>


and

.. code-block:: html

    <body onload="onLoadHandler()">


to load initialize it and run the python scripts (shown later).

=====================================
Installing the the circular library
=====================================

Clone the `circular repo <https://gitlab.com/Verner/circular.git>`_ from `gitlab <https://gitlab.com>`_:

.. code-block:: shell

    $ git clone https://gitlab.com/Verner/circular.git


link the ``circular`` directory into a ``lib`` subdirectory of your web server root.
Then add the following into the head section of your `index.html`:

.. code-block:: html

    <link rel="pythonpath" href="lib" hreflang="py" />