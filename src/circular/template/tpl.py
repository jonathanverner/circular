from browser import timer

try:
    from ..utils.events import EventMixin
except:
    from circular.utils.events import EventMixin


class PrefixLookupDict(dict):

    def __init__(self, init=None):
        super().__init__()
        self._prefix = ''
        if isinstance(init, list):
            for item in init:
                self[item] = item
        elif isinstance(init, dict):
            for (k, v) in init.items():
                self[k] = v

    def _canonical(self, key):
        k = key.upper().replace('-', '').replace('_', '')
        if k.startswith(self._prefix):
            return k[len(self._prefix):]
        else:
            return k

    def remove(self, key):
        try:
            del self[key]
        except:
            pass

    def set_prefix(self, prefix):
        self._prefix = prefix.upper().replace('-', '').replace('_', '')

    def update(self, other):
        for (k, v) in other.items():
            self[k] = v

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
    ld = PrefixLookupDict(plugin['args'])
    kwargs = {}
    for attr in element.attributes:
        if attr.name in ld:
            kwargs[ld[attr.name]] = attr.value
            element.removeAttribute(attr.name)
    return kwargs


def _compile(tpl_element):
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
        for (arg, p) in plugin_metas:
            plugins.append((p, [arg], _build_kwargs(tpl_element, p)))

        if tpl_element.nodeName in PLUGINS:
            tplug = PLUGINS[tpl_element.nodeName]
            plugins.append(tplug, [], _build_kwargs(tpl_element, tplug))
        set_meta = True
        setattr(tpl_element, '_plugins', plugins)

    plugins = getattr(tpl_element, '_plugins')

    # Now we initialize the first plugin, if any
    if len(plugins) > 0:
        plug_meta, args, kwargs = plugins.pop()
        return p['class'](tpl_element, *args, **kwargs)

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


class Template:
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
        self.root = _compile(elem)
        self.elem = elem
        self.update_timer = None

    def bind_ctx(self, ctx):
        elem = self.root.bind_ctx(ctx)
        self.elem.parent.replaceChild(elem, self.elem)
        self.elem = elem
        self.root.bind('change', self._start_timer)

    def _start_timer(self, event):
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
