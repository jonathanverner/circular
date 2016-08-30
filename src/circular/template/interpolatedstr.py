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

        for ast in self.asts:
            ast.bind('change',self._change_chandler)

        self._dirty = True
        self._cached_val = ""
        self.ctx = Context()
        self.evaluate()


    def bind(self,context):
        for a in self.asts:
            a.bind(context)
        self._dirty = True
        self._cached_val = ""

    def clone(self):
        return InterpolatedStr(self)

    def _change_chandler(self,event):
        if self._dirty:
            return
        self._dirty = True
        self.emit('change',{})

    @property
    def value(self):
        if self._dirty:
            self.evaluate()
        return self._cached_val

    def evaluate(self):
        self._cached_val = ""
        for ast in self.asts:
            try:
                self._val += ast.eval()
            except:
                pass
        self._dirty = False



