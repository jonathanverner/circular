try:
    from ..tpl import TplNode
    from ..interpolatedstr import InterpolatedStr
except:
    from circular.template.tpl import TplNode
    from circular.template.interpolatedstr import InterpolatedStr


from .tag import TagPlugin

class InterpolatedAttrsPlugin(TagPlugin):
    def __init__(self,tpl_element):
        super().__init__(tpl_element)
        self.element = None
        self.values = {}
        self.names = []
        if isinstance(tpl_element,InterpolatedAttrsPlugin):
            for (name,obs) in tpl_element.values.items():
                if isinstance(obs,InterpolatedStr):
                    obs = obs.clone()
                    obs.bind('change',self._self_change_chandler)
                self.values[name] = obs
            self.child = tpl_element.child.clone()
        else:
            for attr in tpl_element.attributes:
                if '{{' in attr.value:
                    obs = InterpolatedStr(attr.value)
                    obs.bind('change',self._self_change_chandler)
                else:
                    obs = attr.value
                self.values[attr.name] = obs
                tpl_element.removeAttribute(attr.name)
            self.child = TplNode(tpl_element)
        self.child.bind('change',self._subtree_change_handler)

    def bind_ctx(self, ctx):
        self.element = self.child.bind_ctx(ctx)
        for (name,obs) in self.values.items():
            if isinstance(obs,InterpolatedStr()):
                obs.bind(ctx)
                self.element.setAttribute(name,obs.value)
            else:
                self.element.setAttribute(name,obs)
        super().bind_ctx(ctx)
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            for (name,obs) in self.values.items():
                if isinstance(obs,InterpolatedStr):
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
        for (name,obs) in self.values.items():
            if isinstance(obs,InterpolatedStr):
                attrs.append(name+"="+obs.value+"("+obs._src+")")
            else:
                attrs.append(name+"="+obs)
        return "<Attrs: "+" ".join(attrs)+" >"