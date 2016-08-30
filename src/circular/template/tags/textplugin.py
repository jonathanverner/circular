try:
    from ..interpolatedstr import InterpolatedStr
    from ..expression import ET_INTERPOLATED_STRING
except:
    from circular.template.interpolatedstr import InterpolatedStr

from .tag import TagPlugin

class TextPlugin(TagPlugin):
    def __init__(self, tpl_element):
        super().__init__(tpl_element)
        self.interpolated_str = None
        if isinstance(tpl_element,TextPlugin):
            if tpl_element.interpolated_str is not None:
                self.interpolated_str = tpl_element.interpolated_str.clone()
                self.interpolated_str.bind('change',self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        else:
            if '{{' in tpl_element.text:
                self.interpolated_str = InterpolatedStr(tpl_element.text)
                self.interpolated_str.bind('change',self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        self.element = self._orig_clone

    def bind_ctx(self,ctx):
        self.element = self._orig_clone.clone()
        if self.interpolated_str is not None:
            super().bind_ctx(ctx)
            self.interpolated_str.bind_ctx(ctx)
            self.element.text = self.interpolated_str.value
            self._dirty_self = False
            self._dirty_subtree = False
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            self.element.text = self.interpolated_str.value
            self._dirty_self = False

    def __repr__(self):
        if self.interpolated_str is not None:
            return "<TextPlugin '"+self.interpolated_str._exp_src.replace("\n","\\n")+"' => '"+self.element.text.replace("\n","\\n")+"'>"
        else:
            return "<TextPlugin '"+self.element.text.replace("\n","\\n")+"'>"