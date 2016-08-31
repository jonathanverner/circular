from browser import ajax

from .logger import Logger
from .events import EventMixin, Event
from .decorator import decorator, func_name
logger = Logger(__name__)


class PromiseException(Exception):

    def __init__(self, message):
        super(PromiseException, self).__init__(message)


class Promise(EventMixin):
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
        self._success_handler = success_handler
        self._error_handler = error_handler
        if self.status == Promise.STATUS_FINISHED and self._error_handler:
            self._success_handler(self.result)
        elif self.status == Promise.STATUS_ERROR and self._error_handler:
            self._error_handler(self.result)

    def start(self):
        if self._status == Promise.STATUS_NEW:
            self._status = Promise.STATUS_INPROGRESS
            return True
        else:
            return False

    @property
    def result(self):
        if self._status == Promise.STATUS_FINISHED or self._status == Promise.STATUS_ERROR:
            return self._result
        else:
            raise PromiseException("Not finished")

    @property
    def status(self):
        return self._status

    def _finish(self, result, status=2):
        self._result = result
        self._status = status
        if self._status == Promise.STATUS_FINISHED:
            if self._success_handler:
                logger.debug("Calling success handler with results:",self.result)
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


class HTTPException(Exception):

    def __init__(self, request):
        super(HTTPException, self).__init__()
        self.req = request


class HTTPRequest(Promise):
    METHOD_POST = 'POST'
    METHOD_GET = 'GET'

    def __init__(self, url, method='GET', data=None, **kwargs):
        self._url = url
        self._req = ajax.ajax()
        self._req.bind("complete", self._complete_handler)
        self._data = data
        self._method = method
        super(HTTPRequest, self).__init__(**kwargs)

    def start(self):
        if super(HTTPRequest,self).start():
            self._req.open(self._method,self._url,True)
            self._req.set_header('content-type','application/x-www-form-urlencoded')
            if self._data is None:
                self._req.send()
            else:
                self._req.send(self._data)
            return True
        else:
            return False

    def _complete_handler(self, req):
        if req.status == 200 or req.status == 0:
            self._finish(req)
        else:
            self._finish(HTTPException(req), Promise.STATUS_ERROR)


def get_continuation(generator, result, throw_on_error=False):

    def run(val):
        try:
            async = generator.send(val)
            if isinstance(async, Return):
                result._finish(async.val)
            else:
                succ, err = get_continuation(
                    generator, result, throw_on_error=async.throw_on_error)
                async.then(succ, err)
        except StopIteration:
            result._finish(None)
        except Exception as ex:
            result._finish(ex, status=Promise.STATUS_ERROR)

    def error(ex):
        try:
            if throw_on_error:
                async = generator.throw(ex)
            else:
                async = generator.send(None)
            if isinstance(async, Return):
                result._finish(async.val)
            else:
                succ, err = get_continuation(
                    generator, result, throw_on_error=async.throw_on_error)
                async.then(succ, err)
        except StopIteration:
            result._finish(None)
        except Exception as ex:
            result._finish(ex, status=Promise.STATUS_ERROR)

    return run, error


@decorator
def async(f):

    def run(*args, **kwargs):
        generator = f(*args, **kwargs)
        async = next(generator)
        result = Promise()
        if isinstance(async, Return):
            result._finish(async.val)
        else:
            succ, err = get_continuation(generator, result)
            async.then(succ, err)
        return result

    run.__interruptible = True

    return run


@decorator
def async_init(init):
    def new_init(self, *args, **kwargs):
        logger.debug("Calling decorated init for ", self.__class__.__name__)
        logger.debug("INIT PROMISE FOR",self.__class__.__name__,":",self._init_promise)
        self._init_promise = async(init)(self, *args, **kwargs)
    return new_init


def defer(promise, f, *args, **kwargs):
    ret = Promise()

    def on_success(event):
        logger.info("Calling deferred method ",func_name(f)," object is initialized.")
        logger.info("Args:", args)
        logger.info("Kwargs:", kwargs)
        ret._finish(f(*args, **kwargs))

    def on_error(event):
        logger.error("Unable to call deferred method ",func_name(f),", object failed to initialize properly.")
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
def _generate_guard(f):
    def guard(self, *args, **kwargs):
        if self._init_promise.status == Promise.STATUS_FINISHED:
            return f(self, *args, **kwargs)
        else:
            if hasattr(f,'__interruptible'):
                logger.info("Defering method ",func_name(f)," until object is initialized.")
                logger.debug("Waiting for promise:", self._init_promise)
                return defer(self._init_promise, f, self, *args, **kwargs)
            else:
                logger.error("Calling method on Uninitialized object")
                raise PromiseException("Calling method on Unitialized object")
    return guard


def async_class(cls):
    for m in dir(cls):
        if not m[0:2] == '__':
            meth = getattr(cls, m)
            if hasattr(meth, '__call__'):
                setattr(cls, m, _generate_guard(meth))
    return cls


@async
def wget_urls(urls):
    results = ''
    for url in urls:
        result = yield HTTPRequest(url, throw_on_error=False)
        if result:
            results = results + result.text
    yield Return(results)


# run(wget_urls,["/media/teaching/alg110006/maze/maze.py","/media/teaching/alg110006/maze/css/style.css"])
