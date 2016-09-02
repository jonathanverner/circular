"""
    Provides the :class:`Model` plugin for two-way data binding between
    context and html input elements.
"""
from browser import timer

try:
    from ..expression import parse
    from ..tpl import _compile, register_plugin
except:
    from circular.template.expression import parse
    from circular.template.tpl import _compile, register_plugin

from .tag import TagPlugin

try:
    from ...utils.logger import Logger
except:
    from circular.utils.logger import Logger
logger = Logger(__name__)


class Model(TagPlugin):
    """
        The model plugin binds an input element value to a context variable (or a simple expression).
        For example the template:
        ```
            Hello {{ name }}
            <input model='name' type='textinput' />
        ```
        when bound to a context would update the value of the variable `name` in the context
        whenever a user typed (or pasted in) a new value on the input field. The plugin takes
        two optional parameters: `update_event` and `update_interval`. When `update_event` is
        set, the context is updated whenever the given event is fired on the input element.
        The default is to update whenever the event `input` is fired. When `update_interval`
        is set to number, the context is updated at most once per the given number of milliseconds.

        WARNING: The Model plugin must come before any plugin which creates more than one
        element (e.g. the `For` plugin).
    """
    def __init__(self, tpl_element, model=None, update_interval=None, update_event='input'):
        super().__init__(tpl_element)
        self._model_change_timer = None
        self._input_change_timer = None
        self.element = None
        self._ctx = None
        if isinstance(tpl_element, Model):
            self._update_event = tpl_element._update_event
            self._update_interval = tpl_element._update_interval
            self._model = tpl_element.model.clone()
            self.child = tpl_element.child.clone()
        else:
            self._update_event = update_event
            if update_interval is not None:
                self._update_interval = int(update_interval)
            else:
                self._update_interval = None
            self._model, _ = parse(model)
            self.child = _compile(tpl_element)
            assert self._model.is_assignable(), "The expression "+model+" does not support assignment"
        if self._update_interval:
            self._model.bind('change', self._defer_model_change)
        else:
            self._model.bind('change', self._model_change)
        self.child.bind('change', self._subtree_change_handler)

    def bind_ctx(self, ctx):
        self.element = self.child.bind_ctx(ctx)
        self._model.bind_ctx(ctx)
        self.element.value = self._model.value
        if self._update_interval:
            self.element.bind(self._update_event, self._defer_input_change)
        else:
            self.element.bind(self._update_event, self._input_change)
        super().bind_ctx(ctx)
        return self.element

    def _defer_model_change(self, _event):
        if self._model_change_timer is None:
            self._model_change_timer = timer.set_interval(
                self._model_change, self._update_interval)

    def _defer_input_change(self, _event):
        if self._input_change_timer is None:
            self._input_change_timer = timer.set_interval(
                self._input_change, self._update_interval)

    def _model_change(self, event=None):
        if self._model_change_timer:
            timer.clear_interval(self._model_change_timer)
            self._model_change_timer = None
        if self.element:
            if 'value' in event.data:
                new_val = event.data['value']
            else:
                new_val = self._model.value
            if not self.element.value == new_val:
                self.element.value = new_val

    def _input_change(self, _event=None):
        if self.element:
            if self._model.value != self.element.value:
                if self._input_change_timer:
                    timer.clear_interval(self._input_change_timer)
                    self._input_change_timer = None
                self._model.value = self.element.value

    def __repr__(self):
        return "<Model " + repr(self._model) + \
            " (" + str(self._model.value) + ")>"

register_plugin(Model)
