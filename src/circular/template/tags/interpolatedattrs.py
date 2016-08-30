try:
    from ..tpl import TplNode
    from ..expobserver import ExpObserver
    from ..expression import ET_INTERPOLATED_STRING
except:
    from circular.template.tpl import TplNode
    from circular.template.expobserver import ExpObserver
    from circular.template.expression import ET_INTERPOLATED_STRING

from .tag import TagPlugin

class InterpolatedAttrsPlugin(TagPlugin):
    def __init__(self,tpl_element):
        super().__init__(tpl_element)
        self.element = None
        self.observers = {}
        self.names = []
        if isinstance(tpl_element,InterpolatedAttrsPlugin):
            for (name,obs) in tpl_element.observers.items():
                if isinstance(obs,ExpObserver):
                    o = obs.clone()
                    self.observers[name] = o
                    o.bind('change',self._self_change_chandler)
                else:
                    self.observers[name] = obs
            self.child = tpl_element.child.clone()
        else:
            for attr in tpl_element.attributes:
                if '{{' in attr.value:
                    obs = ExpObserver(attr.value,ET_INTERPOLATED_STRING)
                    obs.bind('change',self._self_change_chandler)
                else:
                    obs = attr.value
                self.observers[attr.name] = obs
                tpl_element.removeAttribute(attr.name)
            self.child = TplNode(tpl_element)
        self.child.bind('change',self._subtree_change_handler)

    def bind_ctx(self, ctx):
        self.element = self.child.bind_ctx(ctx)
        for (name,obs) in self.observers.items():
            if isinstance(obs,ExpObserver):
                obs.context = ctx
                self.element.setAttribute(name,obs.value)
            else:
                self.element.setAttribute(name,obs)
        super().bind_ctx(ctx)
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            for (name,obs) in self.observers.items():
                if isinstance(obs,ExpObserver):
                    self.element.setAttribute(name,obs.value)
                else:
                    self.element.setAttribute(name,obs)
            self._dirty_self = False
        if self._dirty_subtree:
            self._dirty_subtree = False
            return self.child.update()

    def __repr__(self):
        ret = "<Attr: ";
        attrs = []
        for (name,obs) in self.observers.items():
            if isinstance(obs,ExpObserver):
                attrs.append(name+"="+obs.value+"("+obs._exp_src+")")
            else:
                attrs.append(name+"="+obs)
        return "<Attrs: "+" ".join(attrs)+" >"