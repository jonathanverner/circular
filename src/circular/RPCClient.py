import json
from browser import websocket
from .utils.async import Promise, async, Return
from .utils.logger import Logger

logger = Logger(__name__)

class SocketFactory:
    SOCKETS = {}

    @classmethod
    def get_socket(cls, url, new = False):
        if url not in cls.SOCKETS:
            cls.SOCKETS[url] = websocket.WebSocket(url)
            cls.SOCKETS[url].bind('close',cls.close_handler(url))
        return cls.SOCKETS[url]

    @classmethod
    def close_handler(cls,url):
        def handler(evt):
            del cls.SOCKETS[url]
        return handler

class RPCClientFactory:
    CLIENTS = {}
    DEFAULT_URL = 'ws://localhost:8080/'

    @classmethod
    def _hash(cls,url,service_name):
        return url+':'+service_name

    @classmethod
    def get_client(cls, service_name, url = None):
        if url is None:
            url = RPCClientFactory.DEFAULT_URL
        h=cls._hash(url,service_name)
        if h not in cls.CLIENTS:
            cls.CLIENTS[h] = RPCClient(url,service_name)
        elif cls.CLIENTS[h].status > RPCClient.STATUS_READY:
            del cls.CLIENTS[h]
            cls.CLIENTS[h] = RPCClient(url,service_name)
        client = cls.CLIENTS[h]
        ret = Promise()
        if client.status < RPCClient.STATUS_READY:
            def __onr(svc):
                ret._finish(svc)
            client.bind('__on_ready__',__onr)
        else:
            ret._finish(client)
        return ret

class RPCClient:
    _NEXT_CALL_ID = 0
    _NEXT_CLIENT_ID = 0

    STATUS_OPENING_SOCKET = 0
    STATUS_SOCKET_OPEN = 1
    STATUS_QUERYING_SERVICE = 2
    STATUS_READY = 3
    STATUS_CLOSED_SOCKET = 4
    STATUS_ERROR = 5

    @classmethod
    def new_client_id(cls):
        ret = cls._NEXT_CLIENT_ID
        cls._NEXT_CLIENT_ID += 1
        return ret

    @classmethod
    def new_call_id(cls):
        ret = cls._NEXT_CALL_ID
        cls._NEXT_CALL_ID +=1
        return ret

    def _generate_method(self,method_name,svc_name=None):
        if svc_name is None:
            svc_name = self._service_name
        logger.debug("Generating method ",method_name, " of ", svc_name)

        def remote_call(*args,**kwargs):
            logger.debug("Calling ",method_name, "self:",self,"*args:",args, "**kwargs",kwargs)

            if not self.status == RPCClient.STATUS_READY:
                if (not self.status == RPCClient.STATUS_QUERYING_SERVICE) or (not svc_name == '__system__'):
                    logger.debug("STATUS:", self.status, "SVC:", svc_name)
                    raise Exception("Service not in operation:", self.status)

            ret = Promise()
            data = {
                'service':svc_name,
                'method':method_name,
                'args':args,
                'kwargs':kwargs,
                'call_id':RPCClient.new_call_id(),
                'client_id':self._client_id
            }
            self._calls_in_progress[data['call_id']] = ret
            logger.debug("Sending data:",json.dumps(data))
            self._socket.send(json.dumps(data))
            return ret
        setattr(self,method_name,remote_call)
        return remote_call

    def __init__(self, url, service_name):
        logger.debug("Calling RPCClient init")
        self._url = url
        self._socket = SocketFactory.get_socket(url)
        self._service_name = service_name
        self._calls_in_progress = {}
        self._event_handlers = {}
        self._method_promise = None
        self._client_id = RPCClient.new_client_id()
        self._generate_method('list_services',svc_name='__system__')
        self._generate_method('query_service',svc_name='__system__')
        self._socket.bind("message", self._on_message)
        self._socket.bind("close",self._on_close)
        if self._socket.readyState == self._socket.OPEN:
            self._status = RPCClient.STATUS_SOCKET_OPEN
            self._on_open()
        elif self._socket.readyState == self._socket.CLOSED or self._socket.readyState == self._socket.CLOSING:
            self._status = RPCClient.STATUS_CLOSED_SOCKET
        else:
            self._status = RPCClient.STATUS_OPENING_SOCKET
            self._socket.bind("open",self._on_open)


    @property
    def status(self):
        return self._status

    @property
    def methods(self):
        if self.status == RPCClient.STATUS_READY:
            return list(self._methods.items())
        else:
            return []

    def ready_promise(self):
        logger.debug("!!! READY PROMISE NOT IMPLEMENTED !!!")
        raise Exception("NOT IMPLEMENTED")
        return None
        rt = Promise()
        if self._status < RPCClient.STATUS_READY:
            def __onr(svc):
                rt._finish(svc)
            self.bind('__on_ready__',__onr)
        else:
            rt._finish(self)
        return rt

    @async
    def _on_open(self,evt=None):
        logger.debug("Web Socket Open, querying service", self._service_name, "STATUS:",self.status)
        self._status = RPCClient.STATUS_QUERYING_SERVICE
        logger.debug("Transitioning to status:",self.status)
        self._methods = yield self.query_service(self._service_name)
        logger.debug("Loading methods",self._methods)
        for m in self._methods.keys():
            self._generate_method(m)
        self._status = RPCClient.STATUS_READY
        handlers = self._event_handlers.get('__on_ready__',[])
        for handler in handlers:
            handler(self)


    def _on_close(self,evt):
        self._methods = []
        self._status = RPCClient.STATUS_CLOSED_SOCKET
        self.__init__(self._url,self._service_name)

    def _on_message(self,evt):
        msg = ngcore.dict_to_obj(json.loads(evt.data))
        if msg.client_id is not None:
            if not msg.client_id == self._client_id:
                return
        else:
            if not msg.service == self._service_name or not msg.service == '__system__':
                return
        logger.debug("Processing message:", msg)
        if msg.type == 'event':
            handlers = self._event_handlers.get(msg.event,[])
            for handler in handlers:
                handler(msg.data)
        elif msg.type == 'return':
            result_promise = self._calls_in_progress[msg.call_id]
            del self._calls_in_progress[msg.call_id]
            logger.debug("Result:", msg.result)
            logger.debug("Finishing call:", result_promise)
            result_promise._finish(msg.result)
        elif msg.type == 'exception':
            result_promise = self._calls_in_progress[msg.call_id]
            del self._calls_in_progress[msg.call_id]
            logger.debug("Finishing call (exception)", result_promise)
            result_promise._finish(msg.exception,status=Promise.STATUS_ERROR)

    def bind(self,event,handler):
        if event in self._event_handlers:
            self._event_handlers[event].append(handler)
        else:
            self._event_handlers[event] = [handler]

    def unbind(self,event,handler):
        if event in self._event_handlers:
            self._event_handlers[event].remove(handler)
