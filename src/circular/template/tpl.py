"""
    This module provides the Template class for creating data-bound
    templates.
"""
from browser import timer

try:
    from ..utils.events import EventMixin
except:
    from circular.utils.events import EventMixin


class PrefixLookupDict(dict):
    """
        Helper class for looking up data allowing a single data item
        to have variant keys. The implementation works by first
        converting the key to a canonical form and only then doing
        the lookup. The canonical form is derived as follows:

          -- strip any prefix (set via the :func: ``set_prefix`` method)
          -- remove any '-' and '_'
          -- convert the key to upper case
    """

    def __init__(self, init=None):
        super().__init__()
        self._prefix = ''
        if isinstance(init, list):
            for item in init:
                self[item] = item
        elif isinstance(init, dict):
            for (key, val) in init.items():
                self[key] = val

    def _canonical(self, key):
        canonical_key = key.upper().replace('-', '').replace('_', '')
        if canonical_key.startswith(self._prefix):
            return canonical_key[len(self._prefix):]
        else:
            return canonical_key

    def remove(self, key):
        try:
            del self[key]
        except KeyError:
            pass

    def set_prefix(self, prefix):
        self._prefix = prefix.upper().replace('-', '').replace('_', '')

    def update(self, other):
        for (key, val) in other.items():
            self[key] = val

    def __delitem__(self, key):
        return super().__delitem__(self._canonical(key))

    def __getitem__(self, key):
        return super().__getitem__(self._canonical(key))

    def __setitem__(self, key, value):
        return super().__setitem__(self._canonical(key), value)

    def __contains__(self, key):
        return super().__contains__(self._canonical(key))

PLUGINS = PrefixLookupDict()


def _build_kwargs(element, plugin):
    """
        Helper function which removes all attributes of element
        which are consumed by the plugin as parameters. It
        returns them (with their values) as a dict.
    """
    lookup_table = PrefixLookupDict(plugin['args'])
    kwargs = {}
    for attr in element.attributes:
        if attr.name in lookup_table:
            kwargs[lookup_table[attr.name]] = attr.value
            element.removeAttribute(attr.name)
    return kwargs


def _compile(tpl_element):
    """
        A function used internally by the Template class and plugins
        to recursively parse a dom-tree into a template. The argument
        is a tpl_element. It returns an instance of the ``TagPlugin``
        class representing the root of the template at ``tpl_element``.

        The function works as follows:

            1. If the element is a text node, initialize the ``TextPlugin``
            (which handles ``{{ name }}`` type constructs)

            2. Otherwise, if this is the first time the element is
            seen, build a list of all attribute plugins which need to be applied
            and save it to the element as a private attribute ``_plugins``

            3. Next order the attribute plugins by priority and initialize
            the first one (it is expected, that the plugin will recursively
            call _compile on the element thus allowing the other plugins to
            be initialized)

            4. Next handle attributes with interpolated values (e.g. ``id="{{ dom_id }}``)
            via the ``InterpolatedAttrsPlugin``

            5. Finally, initialize the ``GenericTag`` plugin which takes care
            of calling the ``_compile`` function recursively on the child elements.
            (Note that plugins may choose to ignore the children (or do something else with them)
            by not calling the _compile function)

    """
    if tpl_element.nodeName == '#text':
        # Interpolated text node plugin
        return TextPlugin(tpl_element)

    if not hasattr(tpl_element, '_plugins'):
        # This is the first pass over tpl_element,
        # we need to find out what the plugins are
        # and remove their params from the element
        # and save them for later
        plugin_metas = []
        for attr in tpl_element.attributes:
            if attr.name in PLUGINS:
                plugin_metas.append((attr.value, PLUGINS[attr.name]))
                tpl_element.removeAttribute(attr.name)

        # Order the plugins by priority
        plugin_metas.sort(key=lambda x: x[1]['priority'])
        plugins = []
        for (arg, plugin) in plugin_metas:
            plugins.append((plugin, [arg], _build_kwargs(tpl_element, plugin)))

        if tpl_element.nodeName in PLUGINS:
            tplug = PLUGINS[tpl_element.nodeName]
            plugins.append(tplug, [], _build_kwargs(tpl_element, tplug))

        setattr(tpl_element, '_plugins', plugins)

    plugins = getattr(tpl_element, '_plugins')

    # Now we initialize the first plugin, if any
    if len(plugins) > 0:
        plug_meta, args, kwargs = plugins.pop()
        return plug_meta['class'](tpl_element, *args, **kwargs)

    # If there are any attributes left, we initialize the
    # InterpolatedAttrsPlugin
    if len(tpl_element.attributes) > 0:
        return InterpolatedAttrsPlugin(tpl_element)

    # Finally, since no other plugin is found, return the GenericTag plugin
    return GenericTagPlugin(tpl_element)


def register_plugin(plugin_class):
    plugin_name = getattr(plugin_class, 'NAME', None) or plugin_class.__name__
    meta = {
        'class': plugin_class,
        'args': PrefixLookupDict(list(plugin_class.__init__.__code__.co_varnames)),
        'name': plugin_name,
        'priority': getattr(plugin_class, 'PRIORITY', 0)
    }
    meta['args'].remove('self')
    meta['args'].remove('tpl_element')
    PLUGINS[plugin_name] = meta


def set_prefix(prefix):
    """
        Sets the prefix which should be prepended to tag names. E.g. if the prefix is set to `tpl-`
        then the `for` plugin must be written as `tpl-for`:

        ```

            <li tpl-for="[1,2,3]" ...>...</li>

        ```
    """
    PLUGINS.set_prefix(prefix)


class Template(EventMixin):
    """
        The template class is the basic class used for data-binding functionality.
        Its constructor takes a :class:`DOMNode` element (e.g. ``doc['element_id']``) and
        parses it and its children into an internal structure. One can than
        use the :func:`Template.bind_ctx` instance method to bind the template to
        a context (an instence of the :class:`Context` class) containing
        the data. Once the data-binding is setup in this way any change to the context
        will trigger an update of the document tree.

        .. note::

           For performance reasons, the updates are only processed once every 100 msecs.

        Assuming we have a template::

        ```

            <div id='app'>
                Greetings from the {{ country }}
            </div>
        ```
        We could write::

        ```
            from browser import document as doc
            from circular.template import Template, Context

            ctx = Context()
            ctx.country = 'Czech republic'
            tpl = Template(doc['app'])
            tpl.bind_ctx(ctx)              # The page shows "Greetings from the Czech republic"

            ctx.country = 'United Kingdom' # After a 100 msecs the page shows "Greetings from the United Kingdom"
        ```
    """

    def __init__(self, elem):
        super().__init__()
        self.root = _compile(elem)
        self.elem = elem
        self.update_timer = None

    def bind_ctx(self, ctx):
        elem = self.root.bind_ctx(ctx)
        self.elem.parent.replaceChild(elem, self.elem)
        self.elem = elem
        self.root.bind('change', self._start_timer)

    def _start_timer(self, _event):
        if self.update_timer is None:
            self.update_timer = timer.set_interval(self.update, 50)

    def update(self):
        """ FIXME: We need handle the case when the root node
                   returns a new element(s) on update
        """
        elems = self.root.update()
        if self.update_timer is not None:
            timer.clear_interval(self.update_timer)
        self.update_timer = None
from .tags import *
