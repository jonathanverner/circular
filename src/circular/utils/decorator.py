"""
    Small utility functions to decorate decorators so that
    they save the undecorated function for later use.
"""
def decorator(dec):
    """
        Returns a new decorator which saves the undecorated
        method as :attribute:`_undecorated` of the decorated method.

        Also propagates the :attribute:`__expose_to_remote` upwards.
        (This attribute is used by the server side of the RPCClient)
    """
    def augmented_decorator(func):
        # pylint: disable=protected-access
        decorated = dec(func)
        if hasattr(func, '_undecorated'):
            decorated._undecorated = func._undecorated
        else:
            decorated._undecorated = func
        if hasattr(func, '__expose_to_remote'):
            decorated.__expose_to_remote = func.__expose_to_remote
        for attr in dir(func):
            if not attr == '_undecorated' and not attr.startswith('__'):
                setattr(decorated, attr, getattr(func, attr))
        return decorated
    return augmented_decorator


def func_name(dec):
    """
        Returns the original function name of a function decorated with
        a compliant decorator (e.g. one gotten from the :function:`decorator` function)
        decorated function.
    """
    # pylint: disable=protected-access
    if hasattr(dec, '_undecorated'):
        return dec._undecorated.__name__
    else:
        return dec.__name__
