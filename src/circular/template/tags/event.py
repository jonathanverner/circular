"""
    Provides the :class:`Event` class for handling template constructs
    like

    ```
        <input type='submit' tpl-click='method(c)' />
    ```

    which fire a specified method when the element emits an event.
"""
try:
    from ..tpl import _compile, register_plugin
    from ..expression import parse
except:
    from circular.template.tpl import _compile, register_plugin
    from circular.template.expression import parse

from circular.utils.logger import Logger
logger = Logger(__name__)

from .tag import TagPlugin


class Event(TagPlugin):
    """
        General Event plugin providing callback services
        on dom-events fired by the elements on which the
        plugin is declared.
    """
    EVENT = ''

    def __init__(self, tpl_element, expression=None):
        super().__init__(tpl_element)
        self.element = None
        self.handler = None
        if isinstance(tpl_element, Event):
            self.handler = tpl_element.handler.clone()
            self.child = tpl_element.child.clone()
            self.EVENT = tpl_element.EVENT
        else:
            self.handler, _ = parse(expression)
            if not self.handler.is_function_call():
                raise Exception(self.EVENT+" Handler needs to be a function call: "+str(expression))
            self.child = _compile(tpl_element)
        self.child.bind('change', self._subtree_change_handler)

    def bind_event(self):
        if isinstance(self.element, list):
            for elt in self.element:
                elt.bind(self.EVENT, self._event_handler)
        else:
            self.element.bind(self.EVENT, self._event_handler)

    def unbind_event(self):
        if isinstance(self.element, list):
            for elt in self.element:
                elt.unbind(self.EVENT, self._event_handler)
        else:
            self.element.unbind(self.EVENT, self._event_handler)

    def bind_ctx(self, ctx):
        super().bind_ctx(ctx)
        self.element = self.child.bind_ctx(ctx)
        self.bind_event()
        self.handler.bind_ctx(ctx)
        return self.element

    def update(self):
        if self._dirty_subtree:
            self._dirty_subtree = False
            self.unbind_event()
            self.element = self.child.update()
            self.bind_event()

    def _event_handler(self, event):
        # py-lint: disable=bare-except; a tag plugin should not throw!
        logger.log("Handling " + self.EVENT)
        try:
            self.handler.call(event=event)
        except Exception as ex:
            logger.exception(ex)

    def __repr__(self):
        ret = "<" + self.EVENT + " " + str(self.handler) + ">"


class Click(Event):
    EVENT = 'click'

register_plugin(Click)
