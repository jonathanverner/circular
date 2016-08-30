try:
    from ..expobserver import ExpObserver
    from ..expression import ET_INTERPOLATED_STRING
except:
    from circular.template.expobserver import ExpObserver
    from circular.template.expression import ET_INTERPOLATED_STRING

from .tag import TagPlugin

class TextPlugin(TagPlugin):
    def __init__(self, tpl_element):
        super().__init__(tpl_element)
        self.observer = None
        if isinstance(tpl_element,TextPlugin):
            if tpl_element.observer is not None:
                self.observer = tpl_element.observer.clone()
                self.observer.bind('change',self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        else:
            if '{{' in tpl_element.text:
                self.observer = ExpObserver(tpl_element.text,expression_type=ET_INTERPOLATED_STRING)
                self.observer.bind('change',self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        self.element = self._orig_clone

    def bind_ctx(self,ctx):
        self.element = self._orig_clone.clone()
        if self.observer is not None:
            super().bind_ctx(ctx)
            self.observer.context = ctx
            self.element.text = self.observer.value
            self._dirty_self = False
            self._dirty_subtree = False
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            self.element.text = self.observer.value
            self._dirty_self = False

    def __repr__(self):
        if self.observer is not None:
            return "<TextPlugin '"+self.observer._exp_src.replace("\n","\\n")+"' => '"+self.element.text.replace("\n","\\n")+"'>"
        else:
            return "<TextPlugin '"+self.element.text.replace("\n","\\n")+"'>"