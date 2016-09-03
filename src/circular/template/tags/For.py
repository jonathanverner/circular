"""
    Provides the For template plugin for looping constructs.
"""
import re


try:
    from ..tpl import _compile, register_plugin
    from ..expression import parse
    from ..context import Context
    from ...utils.logger import Logger
except:
    from circular.template.tpl import _compile, register_plugin
    from circular.template.expression import parse
    from circular.template.context import Context
    from circular.utils.logger import Logger

logger = Logger(__name__)


from .tag import TagPlugin


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
    SPEC_RE = re.compile(r'^\s*(?P<loop_var>[^ ]*)\s*in\s*(?P<sequence_exp>.*)$', re.IGNORECASE)
    COND_RE = re.compile(r'\s*if\s(?P<condition>.*)$', re.IGNORECASE)
    PRIORITY = 100  # The for plugin should be processed before all the others except for
                    # the template plugin

    def __init__(self, tpl_element, loop_spec=None):
        super().__init__(tpl_element)
        if isinstance(tpl_element, For):
            # pylint: disable=protected-access; we are cloning self, we can access protected variables
            self._var = tpl_element._var
            self._cond = tpl_element._cond
            self._exp = tpl_element._exp.clone()
            self.children = []
            self.child_template = tpl_element.child_template.clone()
        else:
            match = For.SPEC_RE.match(loop_spec)
            if match is None:
                raise Exception("Invalid loop specification: " + loop_spec)
            match = match.groupdict()
            self._var = match['loop_var']
            sequence_exp = match['sequence_exp']
            self._exp, pos = parse(sequence_exp, trailing_garbage_ok=True)
            match = For.COND_RE.match(sequence_exp[pos:])
            if match:
                self._cond, _ = parse(match['condition'])
            else:
                self._cond = None
            self.children = []
            self.child_template = _compile(tpl_element)
        self._exp.bind('change', self._self_change_chandler)

    def _clear(self):
        for (child, _elem) in self.children:
            child.unbind()
        self.children = []

    def bind_ctx(self, ctx):
        super().bind_ctx(ctx)
        self._clear()
        self._exp.bind_ctx(self._ctx)
        try:
            lst = self._exp.eval()
        # pylint: disable=broad-except; the For plugin must not choke on exceptions from user expressions and
        #                               these can potentially be arbitrary
        except Exception as exc:
            logger.exception(exc)
            logger.warn("Exception", exc, "when computing list", self._exp, "with context", self._ctx)
            lst = []
        ret = []
        for item in lst:
            item_ctx = Context({self._var: item}, base=self._ctx)
            try:
                if self._cond is None or self._cond.evalctx(item_ctx):
                    clone = self.child_template.clone()
                    elem = clone.bind_ctx(item_ctx)
                    clone.bind('change', self._subtree_change_handler)
                    ret.append(elem)
                    self.children.append((clone, elem))
            # pylint: disable=broad-except; the For plugin must not choke on exceptions from user conditions; these
            #                               can be arbitrary
            except Exception as exc:
                logger.exception(exc)
                logger.warn("Exception", exc, "when evaluating condition", self._cond, "with context", item_ctx)
        return ret

    def update(self):
        if self._dirty_self and self._bound:
            return self.bind_ctx(self._ctx)
        elif self._dirty_subtree:
            self._dirty_subtree = False
            ret = []
            have_new = False
            for (child, elem) in self.children:
                new_elem = child.update()
                if new_elem is not None:
                    ret.append(new_elem)
                    have_new = True
                else:
                    ret.append(elem)
            if have_new:
                return ret

    def __repr__(self):
        ret = "<For " + self._var + " in " + str(self._exp)
        if self._cond is not None:
            ret += " if " + self._cond
        ret += ">"
        return ret

register_plugin(For)
