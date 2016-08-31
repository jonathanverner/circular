"""
    Provides the base class ``TagPlugin`` for template plugins
"""
try:
    from ...utils.events import EventMixin
except:
    from circular.utils.events import EventMixin


class TagPlugin(EventMixin):
    """
        Plugins extending this class can set the `PRIORITY` class attribute to a non-zero
        number. The higher the number, the earlier they will be initialized. For example
        the `For` plugin sets the priority to 1000 (very high) because it wants to be
        initialized before the other plugins,e.g. if the template is
        ```
        <li tpl-for='c in colours' style='{{ c.css }}'>
        ```
        then the `tpl-for` plugin needs to be initialized before the plugin handling
        the interpolation on the style attribute because the context `c` is created
        by the tpl-for plugin. In general the order of initialization is as follows:

          1. plugins determined by attributes, ordered according to their PRIORITY
          2. the plugin handling interpolated attributes
          3. the plugin corresponding to the tag name

        Plugins extending this class can set the `NAME` class attribute. If set, it
        will be used to determine if the plugin applies to a given element. If it is
        not set, the class name will be used instead. For example the following
        plugin definition

        ```
        class My(TagPlugin):
            NAME='Foo'
            ...

        ```

        would apply to template elements of the form `<foo ...>` or `<div foo="..." ...>`.
    """

    def __init__(self, tpl_element):
        """
            @tpl_element is either a DOMNode or an instance of TagPlugin.
            In the second case, the TagPlugin should be cloned.
        """
        super().__init__()
        if isinstance(tpl_element, TagPlugin):
            self._orig_clone = tpl_element._orig_clone.clone()
        else:
            self._orig_clone = tpl_element.clone()
        self._dirty_self = True
        self._dirty_subtree = True
        self._bound = False
        self._ctx = None

    def bind_ctx(self, ctx):
        """ Binds a context to the node and returns a DOMNode
            representing the bound subtree.
        """
        self._ctx = ctx
        self._dirty_self = False
        self._dirty_subtree = False
        self._bound = True

    def update(self):
        """
            Updates the node with pending changes. If the changes result in
            a new element, returns it. Otherwise returns None.
        """
        if self._bound and (self._dirty_self or self._dirty_subtree):
            self._dirty_self = False
            self._dirty_subtree = False

    def clone(self):
        """
            Clones the plugin.
        """
        return self.__class__(self)

    def _self_change_chandler(self, event):
        if self._dirty_self:
            return
        self._dirty_self = True
        self.emit('change', event)

    def _subtree_change_handler(self, event):
        if self._dirty_subtree:
            return
        else:
            self._dirty_subtree = True
        if not self._dirty_self:
            self.emit('change', event)
