"""
    Module providing the :class:`TemplatePlugin` and
    :class:`IncludePlugin` classes.
"""

from browser.html import DIV

from circular.template.tpl import _compile, register_plugin
from circular.template.expression import parse
from circular.template.context import Context
from circular.utils.async import async, async_class, async_init
from circular.network.http import HTTPRequest

from .tag import TagPlugin


class TemplatePlugin(TagPlugin):
    """
        The template plugin allows defining templates which can be included
        in other places.

        ```
            <div tpl-template='avatar' class='avatar'>
                <a href='person.url'>{{ person.name}}</a>
            </div>
        ```

        Once the template is defined, one can use the :class:`Include`
        plugin to use the template:

        ```
            <tpl-include template='avatar' tpl-context='me' />
        ```

        which, assuming the context contains a variable ``me`` with
        the attribute ``url`` set to ``http://me.com`` and ``name``
        set to ``John`` expand into:

        ```
            <div class='avatar'>
                <a href='http://me.com'>Johh</a>
            </div>
        ```
    """
    NAME = 'Template'
    PRIORITY = 200  # The template plugin should be processed before all the others

    def __init__(self, tpl_element, name):
        super().__init__(tpl_element)
        self._template = _compile(tpl_element)
        self._name = name

    def bind(self, ctx):
        ctx.circular.TEMPLATE_CACHE[self._name] = self

    def instantiate(self, ctx):
        tpl_clone = self._template.clone()
        return tpl_clone

    def clone(self):
        return self

    def update(self):
        pass


class Include(TagPlugin):
    """
        The :class:`Include` plugin allows instantiating templates
        saved in the template cache. Assuming a template ``avatar`` was
        declared in the current context (e.g. via :class:`TemplatePlugin`)
        one can include it as follows:

        ```
            <include name='avatar'/>
        ```

        Also, one will typically want to provide a special context
        to the template. This can be done using the :class:`ContextPlugin`
        plugin as follows:

        ```
            <tpl-include name='avatar' tpl-context='me'/>
        ```

    """

    def __init__(self, tpl_element, name=None):
        super().__init__(tpl_element)
        if isinstance(tpl_element, Include):
            self._name = tpl_element._name
        else:
            self._name = name

    def bind_ctx(self, ctx):
        super().bind_ctx(ctx)
        self._tpl_instance = ctx.circular.TEMPLATE_CACHE[self._name].instantiate(ctx)
        return self._tpl_instance.bind_ctx(ctx)

    def update(self):
        return self._tpl_instance.update()
