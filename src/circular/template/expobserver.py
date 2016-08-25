from circular.utils.events import EventMixin

from .expression import parse, ET_EXPRESSION, ET_INTERPOLATED_STRING, parse_interpolated_str
from .context import Context

class ExpObserver(EventMixin):

    def __init__(self,expression,expression_type=ET_EXPRESSION,clone=False):
        super().__init__()
        if clone:
            self._clone(expression)
        else:
            self._exp_src = expression
            self._exp_type = expression_type
            if expression_type == ET_EXPRESSION:
                self.asts = [parse(expression)]
            else:
                self.asts = parse_interpolated_str(expression)
        for ast in self.asts:
            ast.bind('exp_change',self._change_chandler)
        self.ctx = Context()
        self.evaluate()
        self._last_event_id = -1


    def watch(self,context):
        self.ctx = context
        for ast in self.asts:
            ast.watch(self.ctx)
        self.evaluate()
        self._last_event_id = -1

    def _clone(self,observer):
        self._exp_src = observer._exp_src
        self._exp_type = observer._exp_type
        self.asts = []
        for a in observer.asts:
            self.asts.append(a.clone())

    def clone(self):
        return ExpObserver(self,clone=True)

    @property
    def context(self):
        return self.ctx

    @context.setter
    def context(self,ctx):
        self.ctx = ctx
        for ast in self.asts:
            ast.watch(self.ctx)
        event_data = {
            'exp':self._exp_src,
            'observer':self,
        }
        if self._have_val:
            event_data['old']=self._val
        self.evaluate()
        if self._have_val:
            event_data['new']=self._val
        self.emit('change',event_data)

    def _change_chandler(self,event):
        if event.data['source_id'] == self._last_event_id:
            return
        else:
            self._last_event_id = event.data['source_id']
        event_data = {
            'exp':self._exp_src,
            'observer':self,
            'source_id':event.data['source_id']
        }
        if self._have_val:
            event_data['old']=self._val
        self.evaluate()
        if self._have_val:
            event_data['new'] = self._val
        self.emit('change',event_data)

    def have_value(self):
        return self._have_val

    @property
    def value(self):
        return self._val

    def evaluate(self):
        if self._exp_type == ET_EXPRESSION:
            try:
                self._val = self.asts[0].evaluate(self.ctx)
                self._have_val = True
            except:
                self._have_val = False
        else:
            self._val = ""
            for ast in self.asts:
                try:
                    self._val += ast.evaluate(self.ctx)
                except:
                    pass
            self._have_val = True



