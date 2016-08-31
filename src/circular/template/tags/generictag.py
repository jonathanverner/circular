from browser import html

try:
    from ..tpl import _compile
except:
    from circular.template.tpl import _compile

from .tag import TagPlugin


from circular.utils.logger import Logger
logger = Logger(__name__)


class GenericTagPlugin(TagPlugin):
    def _fence(self,node):
        try:
            return html.COMMENT(str(node))
        except:
            return html.SPAN()

    def __init__(self,tpl_element):
        super().__init__(tpl_element)
        self.children = []
        self.child_elements = {}
        if isinstance(tpl_element,GenericTagPlugin):
            self.element = tpl_element.element.clone()
            self.element.clear()
            for ch in tpl_element.children:
                node = ch.clone()
                node.bind('change',self._subtree_change_handler)
                self.children.append(node)
                self.child_elements[node] = [self._fence(node)]
        else:
            self.element = tpl_element.clone()
            self.element.clear()
            for ch in tpl_element.children:
                node = _compile(ch)
                node.bind('change',self._subtree_change_handler)
                self.children.append(node)
                self.child_elements[node] = [self._fence(node)]

    def update(self):
        if self._dirty_subtree and self._bound:
            for ch in self.children:
                elems = ch.update()
                if elems is not None:
                    self.replace(ch,elems)
            self._dirty_subtree = False

    def bind_ctx(self, ctx):
        super().bind_ctx(ctx)
        self.element = self.element.clone()
        self.element.clear()
        for ch in self.children:
            rendered_elems = ch.bind_ctx(ctx)
            if type(rendered_elems) is not list:
                rendered_elems = [rendered_elems]
            self.child_elements[ch] = rendered_elems+[self._fence(ch)]
            self.element <= self.child_elements[ch]
        return self.element

    def replace(self,ch,elems):
        fence = self.child_elements[ch][-1]
        for old_el in self.child_elements[ch][:-1]:
            old_el.__del__()
        if type(elems) == list:
            for el in elems:
                self.element.insertBefore(el,fence)
            self.child_elements[ch] = elems + [fence]
        else:
            self.element.insertBefore(elems,fence)
            self.child_elements[ch] = [elems,fence]

    def __repr__(self):
        return "<Generic "+self.element.tagName+">"
