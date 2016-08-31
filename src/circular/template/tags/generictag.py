"""
    Provides the ``GenericTag`` plugin class which corresponds
    to a normal non-plugin based template node. The plugin
    calls ``_compile`` on the child elements and attaches them as
    child template nodes to itself.
"""

from browser import html

from circular.utils.logger import Logger
logger = Logger(__name__) # pylint: disable=C0103

try:
    from ..tpl import _compile
except:
    from circular.template.tpl import _compile

from .tag import TagPlugin


class GenericTagPlugin(TagPlugin):

    def _fence(self, node):
        try:
            return html.COMMENT(str(node))
        except:
            return html.SPAN()

    def __init__(self, tpl_element):
        super().__init__(tpl_element)
        self.children = []
        self.child_elements = {}
        if isinstance(tpl_element, GenericTagPlugin):
            self.element = tpl_element.element.clone()
            self.element.clear()
            for child in tpl_element.children:
                node = child.clone()
                node.bind('change', self._subtree_change_handler)
                self.children.append(node)
                self.child_elements[node] = [self._fence(node)]
        else:
            self.element = tpl_element.clone()
            self.element.clear()
            for child in tpl_element.children:
                node = _compile(child)
                node.bind('change', self._subtree_change_handler)
                self.children.append(node)
                self.child_elements[node] = [self._fence(node)]

    def update(self):
        if self._dirty_subtree and self._bound:
            for ch in self.children:
                elems = ch.update()
                if elems is not None:
                    self.replace(ch, elems)
            self._dirty_subtree = False

    def bind_ctx(self, ctx):
        super().bind_ctx(ctx)
        self.element = self.element.clone()
        self.element.clear()
        for ch in self.children:
            rendered_elems = ch.bind_ctx(ctx)
            if not isinstance(rendered_elems, list):
                rendered_elems = [rendered_elems]
            self.child_elements[ch] = rendered_elems + [self._fence(ch)]
            self.element <= self.child_elements[ch]
        return self.element

    def replace(self, child, elems):
        fence = self.child_elements[child][-1]
        for old_el in self.child_elements[child][:-1]:
            old_el.__del__()
        if isinstance(elems, list):
            for elt in elems:
                self.element.insertBefore(elt, fence)
            self.child_elements[child] = elems + [fence]
        else:
            self.element.insertBefore(elems, fence)
            self.child_elements[child] = [elems, fence]

    def __repr__(self):
        return "<Generic " + self.element.tagName + ">"
