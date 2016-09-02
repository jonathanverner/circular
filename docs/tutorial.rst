.. _tutorial:

*******************
     Tutorial
*******************


Currently, the code is not yet ready for general use. If you are adventurous, you can look
at `web_src/index.html`. In the following we assume you have followed the
instructions in the :ref:`Installing <installing>` chapter. In this guide we will
build a very simple example without going into too much detail. A more thorough
example will be provided once the library becomes fit for general consumption.


Write a template
================

For example, you could include the following in your body

.. code-block:: jinja

    <div id='test'>
        Hello {{ name }}, how are you? Which is your favourite colour?
        <ul>
            <li tpl-for='c in colours' class='{{ c["css"] }}'> c["name"] </li>
        </ul
    </div>


Initialize the library & parse the template
===========================================

Put a Python script tag into your head (eventually, you would put it into
a separate file, but for simplicity we include it in the head)

.. code-block:: html

    <script type="text/python">

    </script>

and put the following python code inside:

.. code-block:: python

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


When you load the page it will take some time to initialize (load Brython),
and import the circular library. Eventually it should result in a page which looks
something like

.. code-block:: html

    <div id='test'>
        Hello Jonathan, how are you? Which is your favourite colour?
        <ul>
          <li class='red'>Red</li>
          <li class='green'>Green</li>
          <li class='blue'>Blue</li>
        </ul>
    </div>
