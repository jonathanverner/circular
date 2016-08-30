import re

try:
    from ..tpl import TplNode
    from ..expression import parse
    from ..expobserver import ExpObserver
    from ..context import Context
except:
    from circular.template.tpl import TplNode
    from circular.template.expression import parse
    from circular.template.expobserver import ExpObserver
    from circular.template.context import Context


from .tag import TagPlugin

from circular.utils.logger import Logger
logger = Logger(__name__)

class For(TagPlugin):
    """
        The template plugin `For` is used to generate a list of DOM elements.
        When a dom-element has the `for` attribute set it should be of the form
        ```
            var in list
        ```
        or
        ```
            var in list if condition
        ```
        where `var` is a variable name, `list` is an expression evaluating to
        a list and `condition` is a boolean expression which can contain the
        variable `var`. When a template element with a `for` attribute is
        bound to a context, the `list` expression is evaluated and filtered
        to a list which contains only elements satisfying the optional `condition`.
        Then for each element in this final list a new DOM-element is created
        and bound to the context containing a single variable `var` with the
        element as its value. For example, given the context
        ```
           ctx.l = [1,2,3,4]
        ```
        the template element
        ```
           <li for="num in l"> {{ num }} </li>
        ```
        when bound to the context would create the following four elements:
        ```
            <li>1</li>
            <li>2</li>
            <li>3</li>
            <li>4</li>
        ```
    """
    SPEC_RE = re.compile('^\s*(?P<loop_var>[^ ]*)\s*in\s*(?P<sequence_exp>.*)$',re.IGNORECASE)
    COND_RE = re.compile('\s*if\s(?P<condition>.*)$',re.IGNORECASE)
    PRIORITY = 1000 # The for plugin should be processed before all the others

    def __init__(self,tpl_element,loop_spec=None):
        super().__init__(tpl_element)
        if isinstance(tpl_element,For):
            self._var = tpl_element._var
            self._cond = tpl_element._cond
            self._exp = tpl_element._exp.clone()
            self.children = []
            self.child_template = tpl_element.child_template.clone()
        else:
            m=For.SPEC_RE.match(loop_spec)
            if m is None:
                raise Exception("Invalid loop specification: "+loop_spec)
            m = m.groupdict()
            self._var = m['loop_var']
            sequence_exp = m['sequence_exp']
            self._exp,pos = parse(sequence_exp,trailing_garbage_ok=True)
            m = For.COND_RE.match(sequence_exp[pos:])
            if m:
                self._cond = parse(m['condition'])
            else:
                self._cond = None
            self.children = []
            self.child_template = TplNode(tpl_element)
        self._exp.bind('exp_change',self._self_change_chandler)

    def _clear(self):
        for (ch,elem) in self.children:
            ch.unbind()
        self.children = []

    def bind_ctx(self, ctx):
        self._ctx = ctx
        self._clear()
        self._exp.watch(self._ctx)
        try:
            lst = self._exp.evaluate(self._ctx)
        except Exception as ex:
            logger.exception(ex)
            logger.warn("Exception",ex,"when computing list",self._exp,"with context",self._ctx)
            lst = []
            self._ex=ex
        ret = []
        for item in lst:
            c=Context({self._var:item})
            try:
                if self._cond is None or self._cond.evaluate(c):
                    clone = self.child_template.clone()
                    elem = clone.bind_ctx(c)
                    clone.bind('change',self._subtree_change_handler)
                    ret.append(elem)
                    self.children.append((clone,elem))
            except Exception as ex:
                logger.exception(ex)
                logger.warn("Exception",ex,"when evaluating condition",self._cond,"with context",c)
                self._ex=ex
        super().bind_ctx(ctx)
        return ret

    def update(self):
        if self._dirty_self and self._bound:
            return self.bind_ctx(self._ctx)
        elif self._dirty_subtree:
            self._dirty_subtree = False
            ret = []
            have_new = False
            for (ch,elem) in self.children:
                new_elem = ch.update()
                if new_elem is not None:
                    ret.append(new_elem)
                    have_new = True
                else:
                    ret.append(elem)
            if have_new:
                return ret
    def __repr__(self):
        ret= "<For:"+self._var+" in "+str(self._exp)
        if self._cond is not None:
            ret += " if "+self._cond
        ret += ">"
        return ret
TplNode.register_plugin(For)
