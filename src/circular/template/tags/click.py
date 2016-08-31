try:
    from ..tpl import _compile, register_plugin
    from ..expression import parse
except:
    from circular.template.tpl import _compile, register_plugin
    from circular.template.expression import parse

from circular.utils.logger import Logger
logger = Logger(__name__)

from .tag import TagPlugin

class Click(TagPlugin):
    def __init__(self,tpl_element,expression=None):
        super().__init__(tpl_element)
        self.element = None
        self.handler = None
        if isinstance(tpl_element,Click):
            self.handler = tpl_element.handler.clone()
            self.child = tpl_element.child.clone()
        else:
            self.handler = parse(expression)
            if not self.handler.is_function_call():
                raise Exception("Click Handler needs to be a function call: "+str(expression))
            self.child = _compile(tpl_element)
        self.child.bind('change',self._subtree_change_handler)

    def bind_click(self):
        if type(self.element) == list:
            for el in self.element:
                el.bind('click',self._click_handler)
        else:
            self.element.bind('click',self._click_handler)

    def unbind_click(self):
        if type(self.element) == list:
            for elt in self.element:
                elt.unbind('click',self._click_handler)
        else:
            self.element.unbind('click',self._click_handler)


    def bind_ctx(self, ctx):
        self.element = self.child.bind_ctx(ctx)
        self.bind_click()
        self.handler.bind_ctx(ctx)
        super().bind_ctx(ctx)
        return self.element

    def update(self):
        if self._dirty_subtree:
            self._dirty_subtree = False
            self.unbind_click()
            self.element = self.child.update()
            self.bind_click()

    def _click_handler(self,event):
        logger.log("Handling click")
        try:
            self.handler.call(event=event)
        except Exception as ex:
            logger.exception(ex)

    def __repr__(self):
        ret = "<OnClick: "+str(self.handler)+">"
register_plugin(Click)