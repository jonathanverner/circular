def decorator(dec):
    def augmented_decorator(f):
        decorated = dec(f)
        if hasattr(f,'_undecorated'):
            decorated._undecorated = f._undecorated
        else:
            decorated._undecorated = f
        if hasattr(f,'__expose_to_remote'):
            decorated.__expose_to_remote = f.__expose_to_remote
        for attr in dir(f):
            if not attr == '_undecorated' and not attr.startswith('__'):
                setattr(decorated,attr,getattr(f,attr))
        return decorated
    return augmented_decorator

def func_name(dec):
    if hasattr(dec,'_undecorated'):
        return dec._undecorated.__name__
    else:
        return dec.__name__
