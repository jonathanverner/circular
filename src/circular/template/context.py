from .observer import ListProxy, DictProxy

class Context(object):
    """ Class used for looking up identifiers when evaluating an expression. """
    def __init__(self, dct=None):
        if dct is None:
            self._dct = {}
        else:
            self._dct = dct
        self._saved = {}

    def reset(self,dct):
        keys = list(self._dct.keys())
        for k in keys:
            delattr(self,k)
        if isinstance(dct,dict):
            for k in dct.keys():
                setattr(self,k,dct[k])
        elif isinstance(dct,Context):
            for k in dct._dct.keys():
                setattr(self,k,getattr(dct,k))

    def __iter__(self):
        return iter(self._dct)

    def __getattr__(self,attr):
        if attr in self._dct:
            return self._dct[attr]
        else:
            super().__getattribute__(attr)

    def __setattr__(self,attr,val):
        if attr.startswith('_'):
            super().__setattr__(attr,val)
        else:
            if type(val) == list:
                self._dct[attr]=ListProxy(val)
            elif type(val) == dict:
                self._dct[attr]=DictProxy(val)
            else:
                self._dct[attr]=val

    def __delattr__(self,attr):
        if attr.startswith('_'):
            super().__delattr__(attr)
        else:
            del self._dct[attr]

    def __repr__(self):
        return repr(self._dct)

    def __str__(self):
        return str(self._dct)

    def _get(self, name):
        return self._dct[name]

    def _set(self,name,val):
        if type(val) == list:
            self._dct[name]=ListProxy(val)
        elif type(val) == dict:
            self._dct[name]=DictProxy(val)
        else:
            self._dct[name]=val

    def _clear(self):
        self._dct.clear()

    def _save(self, name):
        """ If the identifier @name is present, saves its value on
            the saved stack """
        if name not in self._dct:
            return
        if not name in self._saved:
            self._saved[name] = []
        self._saved[name].append(self._dct[name])

    def _restore(self,name):
        """ If the identifier @name is present in the saved stack
            restores its value to the last value on the saved stack."""
        if name in self._saved:
            self._dct[name] = self._saved[name].pop()
            if len(self._saved[name]) == 0:
                del self._saved[name]
