"""
    Provides string interpolation on text dom-nodes, e.g. converts

    ```
        <div>
                Hello {{ name }} {{ surname}}!
        </div>
    ```

    assuming the context variable ``name`` is set to ``"John""``
    and ``surname`` to ``"Smith"`` into

    ```
        <div>
                Hello John Smith
        </div>
    ```
"""
try:
    from ..interpolatedstr import InterpolatedStr
except:
    from circular.template.interpolatedstr import InterpolatedStr

from .tag import TagPlugin


class TextPlugin(TagPlugin):
    """
        Provides string interpolation on text dom-nodes.
    """

    def __init__(self, tpl_element):
        super().__init__(tpl_element)
        self.interpolated_str = None
        if isinstance(tpl_element, TextPlugin):
            if tpl_element.interpolated_str is not None:
                self.interpolated_str = tpl_element.interpolated_str.clone()
                self.interpolated_str.bind('change', self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        else:
            if '{{' in tpl_element.string:
                self.interpolated_str = InterpolatedStr(tpl_element.string)
                self.interpolated_str.bind('change', self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        self.element = self._orig_clone

    def bind_ctx(self, ctx):
        self.element = self._orig_clone.clone()
        if self.interpolated_str is not None:
            super().bind_ctx(ctx)
            self.interpolated_str.bind_ctx(ctx)
            self.element.string = self.interpolated_str.value
            self._dirty_self = False
            self._dirty_subtree = False
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            self.element.string = self.interpolated_str.value
            self._dirty_self = False

    def __repr__(self):
        # pylint: disable=protected-access; (we abuse the fact that we know interpolated_str a bit; in principle, this should
        #                                    be fixed, but since __repr__ is not to be used in user-facing code, it should be
        #                                    fine for the moment)
        if self.interpolated_str is not None:
            return "<Text '"+self.interpolated_str._src.replace("\n", "\\n")+"' => '"+self.element.string.replace("\n", "\\n")+"'>"
        else:
            return "<Text '" + self.element.string.replace("\n", "\\n") + "'>"
