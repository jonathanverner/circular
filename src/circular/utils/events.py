"""
    The events module provides event dispatching services. The main class
    is the :class:`EventMixin` class which adds the :method:`bind` and
    :method:`emit` methods to the class. The :method:`bind` method registers event
    handlers for different events which are triggered by the :method:`emit`
    method.
"""

def generate_forward_handler(obj, forward_event):
    def handler(event):
        obj.emit(forward_event, event, _forwarded=True)
    return handler


class Event:
    """
        Event class encapsulating user data (:attribute:`data`)
        and event specific info (targets, whether it is handled,
        event id...)
    """
    _lastid = 0

    def __init__(self, name, target, data=None):
        self.targets = [target]
        self.names = [name]
        self.data = data
        self.handled = False
        self.eventid = Event._lastid
        Event._lastid += 1
        if Event._lastid > 2**31:
            Event._lastid = 0

    def retarget(self, tgt):
        self.targets.append(tgt)

    def rename(self, name):
        self.names.append(name)

    @property
    def name(self):
        return self.names[-1]

    @property
    def target(self):
        return self.targets[-1]

    def __repr__(self):
        # pylint: disable=line-too-long
        return "<Event "+repr(self.names)+" target:"+repr(self.targets)+"; data:"+repr(self.data)+">"


def add_event_mixin(obj):
    """Apply mixins to a class instance after creation"""
    # pylint: disable=protected-access
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (EventMixin, base_cls), {})
    obj._event_handlers = {}


class EventMixin:
    """
        A Mixin class which adds methods to an object to make it possible
        for it to emit events and for others to bind to its emitted events
    """

    def __init__(self):
        self._event_handlers = {}
        self._forwarding_from_objects = []

    def bind(self, event, handler, forward_event=None):
        """
           Registers an event handler for event. If :param:`forward_event` is provided
           and handler is an object, registers a handler which emits the
           event :param:`forward_event` on object :param:`handler` whenever the current object
           emits the event :param:`event`.
        """
        # pylint: disable=protected-access
        if forward_event is not None and isinstance(handler, EventMixin):
            generated_handler = generate_forward_handler(handler, forward_event)
            handler._forwarding_from_objects.append((self, generated_handler, event))
            handler = generated_handler

        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def stop_forwarding(self, only_event=None, only_obj=None):
        """
           Stops forwarding events which satisfy the following:

           1. If :param:`only_event` is ``None`` the rule is satisfied. Otherwise the event
           satisfies the rule if it is equal to :param:`only_event`.

           2. If :param:`only_obj` is ``None`` the rule is satisfied. Otherwise the event
           satisfies the rule if it originates from object :param:`only_obj`.
        """
        retain = []
        for (obj, handler, event) in self._forwarding_from_objects:
            if (only_event is None or event == only_event) and (
                    only_obj is None or obj == only_obj):
                obj.unbind(event, handler)
            else:
                retain.append((obj, handler, event))
        self._forwarding_from_objects = retain

    def unbind(self, event=None, handler=None):
        """
           Unregisters event handlers.

           If @event is None, unregisters ALL handlers for all events.

           If @event is provided and not an EventMixin but @handler is None,
           unregisters all handlers for event @event.

           Otherwise unregisters only the specified @handler from the event @event.
        """
        if event is None:
            self._event_handlers = {}
            for (obj, handler, event) in self._forwarding_from_objects:
                obj.unbind(event, handler)
            self._forwarding_from_objects = []
        else:
            handlers = self._event_handlers.get(event, [])
            if handler is None:
                handlers.clear()
            else:
                handlers.remove(handler)

    def emit(self, event, event_data=None, _forwarded=False):
        """
            Emits an envent on the object, calling all event handlers. Each
            event handler will be passed an object of type Event whose
            @data attribute will contain @event_data and @targets and @names@
            attribute will be a list of objects on which the event was called
            starting from the first one and going up along the forwarding chain
            (if forward handlers were registered).

            NOTE: _forwarded should NOT be set by the users. If is used
            internally by forward handlers to indicate that this is a
            forwarded event.
        """
        if _forwarded and isinstance(event_data, Event):
            event_data.retarget(self)
            event_data.rename(event)
        else:
            event_data = Event(event, self, event_data)
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            handler(event_data)
