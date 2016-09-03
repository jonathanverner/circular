"""
    A module providing the :class:`Promise` and :function:`async` decorator
    which can be make async operations look like sync. Typical usecase is
    as follows. Assume we have a method ``query_server`` which asynchronously
    queries a server. So, instead of returning the results, it returns an
    instance of the :class:`Promise` class. Normally one would call
    the :method:`then` method of this instance providing it with a call back
    to be called when the promise is "resolved", i.e. when the query has
    finished and results are ready. This, however, typically leads to something
    called the "callback" hell. The :function:`async` decorator can get
    around this by a clever use of the ``yield`` statement. So, instead of
    writing:

    ```
        def process_results(results):
            do_some_stuff(results)

        def send_query():
            promise = query_server()
            promise.then(process_results)
    ```

    one can write it in a more straightforward way:

    ```
        @async
        def process_query():
            results = yield query_server()
            do_some_stuff(results)
    ```

    eliminating the need to introduce the ``process_results`` callback.
"""

from .events import EventMixin, Event
from .decorator import decorator, func_name

from .logger import Logger
logger = Logger(__name__) # pylint: disable=invalid-name




class PromiseException(Exception):

    def __init__(self, message):
        super(PromiseException, self).__init__(message)


class Promise(EventMixin):
    """
        A base class representing the future result of an async action.
        Implementations should override the :method:`start` method
        which should start the asynchronous operation. The class will
        typically register a handler to be run when the operation finishes.
        This handler then needs to call the base :methdo:`_finish` method
        providing it with the :parameter:`result` parameter and
        :parameter:`status` (which should either be ``Promise.STATUS_FINISHED``
        in case the operation finished successfully or ``Promise.STATUS_ERROR``
        if an error happened).
    """
    STATUS_NEW = 0
    STATUS_INPROGRESS = 1
    STATUS_FINISHED = 2
    STATUS_ERROR = 3

    def __init__(self, start_immediately=True, throw_on_error=True):
        super(Promise, self).__init__()
        self.throw_on_error = throw_on_error
        self._status = Promise.STATUS_NEW
        self._success_handler = None
        self._error_handler = None
        self._result = None
        if start_immediately:
            self.start()

    def then(self, success_handler, error_handler=None):
        """
            Register a success callback (:param:`success_handler`) and, optionally,
            an error callback (:param:`error_handler`). The success callback will
            be called once the operation finishes with the result of the operation
            passed as the only parameter to the callback. If the operation was
            already finished, then the handler is called immediately.
        """
        self._success_handler = success_handler
        self._error_handler = error_handler
        if self.status == Promise.STATUS_FINISHED and self._error_handler:
            self._success_handler(self.result)
        elif self.status == Promise.STATUS_ERROR and self._error_handler:
            self._error_handler(self.result)

    def start(self):
        """
            Override this method and start the actuall asynchronous operation here.

            Note that the method should always first call the base :method:`start`
            and only proceed if it returns True. (The method does some book-keeping).
        """
        if self._status == Promise.STATUS_NEW:
            self._status = Promise.STATUS_INPROGRESS
            return True
        else:
            return False

    @property
    def result(self):
        """
            Returns the result of the operation if it is finished. If it is not
            finished, throws an exception.
        """
        if self._status == Promise.STATUS_FINISHED or self._status == Promise.STATUS_ERROR:
            return self._result
        else:
            raise PromiseException("Not finished")

    @property
    def status(self):
        return self._status

    def _finish(self, result, status=2):
        """
            Descendants should call this method once the operation is finished
            with the results.
        """
        self._result = result
        self._status = status
        if self._status == Promise.STATUS_FINISHED:
            if self._success_handler:
                logger.debug("Calling success handler with results:", self.result)
                self._success_handler(self.result)
            self.emit('success', self.result)
            self.unbind()
        elif self._status == Promise.STATUS_ERROR:
            if self._error_handler:
                logger.debug("Calling error handler with error:", self.result)
                self._error_handler(self.result)
            self.emit('error', self.result)
            self.unbind()


class Return:
    def __init__(self, val):
        self.val = val


def get_continuation(generator, result, throw_on_error=False):
    """
        A helper function which creates a success callback (run)
        and an error callback (err) for implementing the async decorator.
    """
    def run(val):
        # pylint: disable=bare-except
        try:
            promise = generator.send(val)
            if isinstance(promise, Return):
                result._finish(promise.val)
            else:
                succ, err = get_continuation(
                    generator, result, throw_on_error=promise.throw_on_error)
                promise.then(succ, err)
        except StopIteration:
            result._finish(None)
        except Exception as ex:
            result._finish(ex, status=Promise.STATUS_ERROR)

    def error(ex):
        # pylint: disable=bare-except
        try:
            if throw_on_error:
                promise = generator.throw(ex)
            else:
                promise = generator.send(None)
            if isinstance(promise, Return):
                result._finish(promise.val)
            else:
                succ, err = get_continuation(generator, result, throw_on_error=promise.throw_on_error)
                promise.then(succ, err)
        except StopIteration:
            result._finish(None)
        except Exception as internal_ex:
            result._finish(internal_ex, status=Promise.STATUS_ERROR)

    return run, error


@decorator
def async(func):
    """
        An async decorator which allows a function to "yield" promises dealing with them
        as thought they were synchronous operations, e.g.

        @async
        def print_google()
            html = yield wget("www.google.com")
            print(html)

        would download the www.google.com website and then print its html. The magic
        is that the ``wget`` function returns a promise, but the @async generator
        converts this promise into an actual value which is sent back to the function
        so that when ``print`` is called it has the results ready.
    """

    def run(*args, **kwargs):
        generator = func(*args, **kwargs)
        promise = next(generator)
        result = Promise()
        if isinstance(promise, Return):
            result._finish(promise.val)
        else:
            succ, err = get_continuation(generator, result)
            promise.then(succ, err)
        return result

    run.__interruptible = True

    return run


@decorator
def async_init(init):
    """
        A decorator for asynchronous constructors.
    """
    def new_init(self, *args, **kwargs):
        logger.debug("Calling decorated init for ", self.__class__.__name__)
        logger.debug("INIT PROMISE FOR", self.__class__.__name__, ":", self._init_promise)
        self._init_promise = async(init)(self, *args, **kwargs)
    return new_init


def defer(promise, func, *args, **kwargs):
    """
        The function :function:`defer` calls the A function which calls the
        :param:`func` function with :param:`*args` and :param:`**kwargs` after
        the promis :param:`promise` is finished.
    """
    ret = Promise()

    def on_success(event):
        logger.info("Calling deferred method ", func_name(func), " object is initialized.")
        logger.info("Args:", args)
        logger.info("Kwargs:", kwargs)
        ret._finish(func(*args, **kwargs))

    def on_error(event):
        # pylint: disable=line-too-long
        logger.error("Unable to call deferred method ", func_name(func), ", object failed to initialize properly.")
        logger.error("Event:", event)
        ret._finish(event.data, status=Promise.STATUS_ERROR)
    if ret.status == Promise.STATUS_FINISHED:
        on_success(Event('success', None, ret._result))
    elif ret.status == Promise.STATUS_ERROR:
        on_error(Event('error', None, ret._result))
    else:
        promise.bind('success', on_success)
        promise.bind('error', on_error)
    return ret


@decorator
def _generate_guard(func):
    def guard(self, *args, **kwargs):
        if self._init_promise.status == Promise.STATUS_FINISHED:
            return func(self, *args, **kwargs)
        else:
            if hasattr(func, '__interruptible'):
                logger.info("Defering method ", func_name(func), " until object is initialized.")
                logger.debug("Waiting for promise:", self._init_promise)
                return defer(self._init_promise, func, self, *args, **kwargs)
            else:
                logger.error("Calling method on Uninitialized object")
                raise PromiseException("Calling method on Unitialized object")
    return guard


def async_class(cls):
    """
        A decorator for classes having an asynchronous constructor.
        Care must be given that all method invocations must be deferred until
        the constructor has finished. This is done by the :function:`_generate_guard`
        function which is called on each class method.
    """
    for member in dir(cls):
        if not member[0:2] == '__':
            meth = getattr(cls, member)
            if hasattr(meth, '__call__'):
                setattr(cls, member, _generate_guard(meth))
    return cls
