"""
    Provides the :class:`GenericTag` plugin class which corresponds
    to a normal non-plugin based template node. The plugin
    calls :function:`_compile` on the child elements and attaches them as
    child template nodes to itself.
"""

from browser import html

from circular.utils.logger import Logger
logger = Logger(__name__)

try:
    from ..tpl import _compile
except:
    from circular.template.tpl import _compile

from .tag import TagPlugin


class GenericTagPlugin(TagPlugin):
    """
        The :class:`GenericTag` plugin class corresponds
        to a normal non-plugin based template node. The plugin
        calls :function:`_compile` on the child elements and
        attaches them as child template nodes to itself.
    """

    def _fence(self, node):
        # FIXME: Make it return a proper comment node in both testing and production
        # pylint: disable=bare-except; this is invalid code which needs to be changed anyway
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
            for child in self.children:
                elems = child.update()
                if elems is not None:
                    self.replace(child, elems)
            self._dirty_subtree = False

    def bind_ctx(self, ctx):
        super().bind_ctx(ctx)
        self.element = self.element.clone()
        self.element.clear()
        for child in self.children:
            rendered_elems = child.bind_ctx(ctx)
            if not isinstance(rendered_elems, list):
                rendered_elems = [rendered_elems]
            self.child_elements[child] = rendered_elems + [self._fence(child)]
            # pylint: disable=pointless-statement; pylint does not know about the special usage of <= in Brython
            self.element <= self.child_elements[child]
        return self.element

    def replace(self, child, elems):
        """
            Replace the dom-nodes generated by the given child template node :parameter:`child` with
            the elements :param:`elems` (used when updating the child)
        """
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
