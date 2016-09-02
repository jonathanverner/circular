"""
    Module providing observables to the template machinery. The main
    method is the :func: ``observe`` method which can be used to observe
    user-defined objects and get notifications about changes to the
    objects. One typically uses it as follows:

    ```
         def change_handler(ev):
             print("Object changed")
             if 'value' in ev.data:
               print("New value:",value)

         a = ListProxy([1,2,3])
         obs = observe(a)
         obs.bind('change',change_handler)
         obs.append("10")
    ```

    Where the last line will result in a call to the change_handler.

    WARNING: Only user-defined classes may be observed, not plain lists, dicts, etc.
    The module provides simple wrappers around ``dict`` (:class:`DictProxy`) and ``list`` 
    (:class:`ListProxy`) which can be observed.

"""
from circular.utils.events import EventMixin


def extend_instance(obj, cls):
    """
        Apply mixins to a class instance after creation
        (thanks http://stackoverflow.com/questions/8544983/dynamically-mixin-a-base-class-to-an-instance-in-python)
    """

    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type("Observable" + base_cls_name, (cls, base_cls), {})
    obj._orig_class = base_cls


class ObjMixin(object):
    """
        A mixin for observing general objects. Modifies
        the various methods which could change the object
        to emit an change event before calling the original method.
    """

    def _create_observer(self):
        if not hasattr(self, '_obs____'):
            self._obs____ = EventMixin()

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            change_event = {
                'observed_obj': self,
                'type': '__setattr__',
                'key': name,
                'value': value,
            }
            self._orig_class.__setattr__(self, name, value)
            # super().__setattr__(name,value)
            self._obs____.emit('change', change_event)
        else:
            # self._orig_class.__setattr__(self,name,value)
            super().__setattr__(name, value)

    def __delattr__(self, name):
        if not name.startswith('_'):
            change_event = {
                'observed_obj': self,
                'type': '__delattr__',
                'key': name
            }
            if hasattr(self, name):
                change_event['old'] = getattr(self, name)
            self._orig_class.__delattr__(self, name)
            # super().__delattr__(name)
            self._obs____.emit('change', change_event)
        else:
            super().__delattr__(name)


class ArrayMixin(object):
    """
        A mixin for observing an list/dict style classes. Modifies
        the various methods which could change the object
        to emit an change event before calling the original method.
    """

    def _create_observer(self):
        if not hasattr(self, '_obs____'):
            self._obs____ = EventMixin()

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            change_event = {
                'observed_obj': self,
                'type': '__setattr__',
                'key': name,
                'value': value
            }
            if hasattr(self, name):
                change_event['old'] = getattr(self, name)
            self._orig_class.__setattr__(self, name, value)
            # super().__setattr__(name,value)
            self._obs____.emit('change', change_event)
        else:
            super().__setattr__(name, value)

    def __setitem__(self, key, value):
        change_event = {
            'observed_obj': self,
            'type': '__setitem__',
            'key': key,
            'value': value
        }
        try:
            change_event['old'] = self[key]
        except:
            pass
        self._orig_class.__setitem__(self, key, value)
        # super().__setitem__(key,value)
        self._obs____.emit('change', change_event)

    def __delitem__(self, key):
        change_event = {
            'observed_obj': self,
            'type': '__delitem__',
            'key': key,
        }
        try:
            change_event['old'] = self[key]
        except:
            pass
        self._orig_class.__delitem__(self, key)
        # super().__delitem__(key)
        self._obs____.emit('change', change_event)

    def append(self, item):
        change_event = {
            'observed_obj': self,
            'type': 'append',
            'index': len(self) - 1,
            'value': item
        }
        self._orig_class.append(self, item)
        # super().append(item)
        self._obs____.emit('change', change_event)

    def insert(self, index, item):
        change_event = {
            'observed_obj': self,
            'type': 'insert',
            'index': index - 1,
            'value': item
        }
        self._orig_class.insert(self, index, item)
        # super().insert(index,item)
        self._obs____.emit('change', change_event)

    def remove(self, item):
        change_event = {
            'observed_obj': self,
            'type': 'remove',
            'value': item
        }
        self._orig_class.remove(self, item)
        # super().remove(item)
        self._obs____.emit('change', change_event)

    def clear(self):
        change_event = {
            'observed_obj': self,
            'type': 'clear',
            'value': []
        }
        self._orig_class.clear(self)
        # super().clear()
        self._obs____.emit('change', change_event)

    def extend(self, lst):
        change_event = {
            'observed_obj': self,
            'type': 'extend',
            'value': lst
        }
        self._orig_class.extend(self, lst)
        # super().extend(lst)
        self._obs____.emit('change', change_event)

    def update(self, dct, **kwargs):
        change_event = {
            'observed_obj': self,
            'type': 'extend',
            'value': dct,
            'additional_value': kwargs
        }
        self._orig_class.update(self, dct)
        # super().update(dct)
        self._obs____.emit('change', change_event)

    def pop(self, *args):
        if len(args) > 0:
            index = args[0]
        else:
            index = len(self) - 1
        change_event = {
            'observed_obj': self,
            'type': '__delitem__',
            'key': index,
        }
        change_event['old'] = self._orig_class.pop(self, *args)
        # change_event['old']=super().pop(*args)
        self._obs____.emit('change', change_event)
        return change_event['old']

    def sort(self, *args, **kwargs):
        self._orig_class.sort(self, *args, **kwargs)
        # super().sort(*args,**kwargs)
        self._obs____.emit('change', {'type': 'sort'})

    def reverse(self, *args, **kwargs):
        self._orig_class.reverse(self, *args, **kwargs)
        # super().reverse(*args,**kwargs)
        self._obs____.emit('change', {'type': 'reverse'})


class ListProxy(list):
    """
        A wrapper around list objects for making them observable
    """

    def __init__(self, lst):
        this = []
        for item in lst:
            if isinstance(item, list):
                this.append(ListProxy(item))
            elif isinstance(item, dict):
                this.append(DictProxy(item))
            else:
                this.append(item)
        super().__init__(this)


class DictProxy(dict):
    """
        A wrapper around dict objects for making them observable
    """

    def __init__(self, dct):
        this = {}
        for key, val in dct.items():
            if isinstance(val, list):
                this[key] = ListProxy(val)
            elif isinstance(val, dict):
                this[key] = DictProxy(val)
            else:
                this[key] = val
        super().__init__(this)


def observe(obj, observer=None, ignore_errors=False):
    """
        Returns an observer object monitoring changes to ``obj``.

        One can specify any instance of EventMixin as the ``observer``
        parameter. In this case any change events will be emitted
        (forwarded) by the provided observer.

        If ``ignore_errors`` is False, the method may throw, e.g. if
        the user tries to observe a built in type. Otherwise it will
        just return None in case of error.

        WARNING: Only instances of user-defined classes can be
        observed. If you need to observe a ``list`` or a ``dict``
        wrap them in a ``ListProxy`` or ``DictProxy``. Or, alternatively,
        consider using the Context class which automatically and
        recursively wraps any ``list`` and ``Dict`` variables which
        are assigned to it.
    """
    if not hasattr(obj, '_obs____'):
        if type(obj) in [str, int, dict, list, tuple, set, type(None), bool]:
            if not ignore_errors:
                raise Exception("Cannot observe primitive types:")
            else:
                return None
        try:
            if hasattr(obj, '__setitem__'):
                extend_instance(obj, ArrayMixin)
            else:
                extend_instance(obj, ObjMixin)
            obj._create_observer()
        except Exception as exc:
            if not ignore_errors:
                raise Exception("Cannot observe (is obj a primitive type?):"+str(exc))
            else:
                return None
    if observer is not None:
        obj._obs____.bind('change', observer, 'change')
    return obj._obs____
