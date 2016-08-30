try:
    from ..utils.events import EventMixin
except:
    from circular.utils.events import EventMixin

from .expression import parse, parse_interpolated_str
from .context import Context

class InterpolatedStr(EventMixin):

    def __init__(self,string):
        super().__init__()
        if isinstance(string,InterpolatedStr):
            self._src = string._src
            self.asts = []
            for a in string.asts:
                self.asts.append(a.clone())
        else:
            self._src = string
            self.asts = parse_interpolated_str(string)

        for i in range(len(self.asts)):
            self.asts[i].bind('change',lambda ev:self._change_chandler(ev,i))

        self._dirty = True
        self._dirty_vals = True
        self._cached_vals = []
        self._cached_val = ""
        self.ctx = Context()
        self.evaluate()


    def bind_ctx(self,context):
        for a in self.asts:
            a.bind_ctx(context)
        self._dirty = True
        self._cached_val = ""

    def clone(self):
        return InterpolatedStr(self)

    def _change_chandler(self,event,ast_index):
        if not self._dirty_vals:
            if 'value' in event.data:
                self._cached_vals[ast_index] = event.data['value']
            else:
                self._dirty_vals = True
        if self._dirty:
            return
        self._dirty = True
        self.emit('change',{})

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
        self._cached_vals=[]
        for ast in self.asts:
            try:
                self._cached_vals.append(ast.eval())
            except:
                self._cached_vals.append("")
        self._cached_val = "".join(self._cached_vals)
        self._dirty = False



