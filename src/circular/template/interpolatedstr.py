"""
    This module provides the :class:`InterpolatedStr` class which
    can be used to interpolate complex strings with multiple
    instances of ``{{ }}``-type circular expressions.
"""
try:
    from ..utils.events import EventMixin
except:
    from circular.utils.events import EventMixin

from .expression import parse_interpolated_str


class InterpolatedStr(EventMixin):
    """
        The :class:`InterpolatedStr` manages string interpolations.
        Use it as follows:

        ```
            from circular.template.context import Context
            from circular.template.interpolatedstr import InterpolatedStr

            c = context()
            istr = InterpolatedStr("Hello {{name}}, {{surname}}!")
            assert istr.value == "Hello , !"
            c.name = "John"
            assert istr.value == "Hello John, !"
            c.name = "Smith"
            assert istr.value == "Hello John, Smith!"
        ```

        The class tries to do some clever tricks to only evaluate the
        subexpressions which have changed due to a given context change.
        (e.g. c.name='Anne' would not affect the second expresssion in
        the above example).

    """

    def __init__(self, string):
        super().__init__()
        if isinstance(string, InterpolatedStr):
            # pylint: disable=protected-access; we are cloning ourselves, we have access to protected variables
            self._src = string._src
            self.asts = []
            for ast in string.asts:
                self.asts.append(ast.clone())
        else:
            self._src = string
            self.asts = parse_interpolated_str(string)

        for i in range(len(self.asts)):
            # FIXME: Wrong closure !!!
            self.asts[i].bind('change', lambda event: self._change_chandler(event, i))

        self._dirty = True
        self._dirty_vals = True
        self._cached_vals = []
        self._cached_val = ""
        self.evaluate()

    def bind_ctx(self, context):
        for ast in self.asts:
            ast.bind_ctx(context)
        self._dirty = True
        self._cached_val = ""

    def clone(self):
        return InterpolatedStr(self)

    def _change_chandler(self, event, ast_index):
        if not self._dirty_vals:
            if 'value' in event.data:
                self._cached_vals[ast_index] = event.data['value']
            else:
                self._dirty_vals = True
        if self._dirty:
            return
        self._dirty = True
        self.emit('change', {})

    @property
    def value(self):
        if self._dirty:
            if self._dirty_vals:
                self.evaluate()
            else:
                self._cached_val = "".join(self._cached_vals)
        return self._cached_val

    def evaluate(self):
        self._cached_val = ""
        self._cached_vals = []
        for ast in self.asts:
            try:
                self._cached_vals.append(ast.eval())
                # pylint: disable=bare-except; interpolated str must handle any exceptions when evaluating circular expressions
            except:
                self._cached_vals.append("")
        self._cached_val = "".join(self._cached_vals)
        self._dirty = False
