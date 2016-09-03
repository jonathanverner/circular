from browser import ajax

from circular.utils.async import Promise, async

class HTTPException(Exception):

    def __init__(self, request):
        super(HTTPException, self).__init__()
        self.req = request


class HTTPRequest(Promise):
    """
        A promise representing the result of a HTTPRequest.
    """
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
        if super(HTTPRequest, self).start():
            self._req.open(self._method, self._url, True)
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

@async
def wget_urls(urls):
    """
        A simple example demonstrating the @async decorator in practice.
    """
    results = ''
    for url in urls:
        result = yield HTTPRequest(url, throw_on_error=False)
        if result:
            results = results + result.text
    yield Return(results)
