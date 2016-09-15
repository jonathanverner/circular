"""
    Module providing the :class:`TemplatePlugin` and
    :class:`IncludePlugin` classes.
"""

from circular.template.tpl import _compile, register_plugin
from circular.template.expression import parse
from circular.template.context import Context

from .tag import TagPlugin


class TemplateLoader:
    """
        The :class:`TemplateLoader` class takes care of storing and retrieving
        templates defined/requested by the user or other plugins.
    """
    TEMPLATES = {}

    @classmethod
    def store(cls, context, name, template):
        """
            Store the template :param:`template` under the key :param:`name`
            for the context :param:`context`. The template will be accessible
            from the given context and any of its children (i.e. those who have
            it (transitively) as their base).
        """
        if context not in cls.TEMPLATES:
            cls.TEMPLATES[context] = {}
        cls.TEMPLATES[context][name] = template

    @classmethod
    def load(cls, context, name):
        """
            Returns a template stored under the key :param:`name` for the
            context :param:`context` or one of its (transitive) bases. If
            there is no such template, raises an exception.
        """
        ctx_tpls = cls.TEMPLATES.get(context, {})
        if name in ctx_tpls:
            return ctx_tpls[name].clone()
        elif isinstance(context._base, Context):
            return cls.load(context._base, name)
        raise Exception("Template "+name+" not found")


class TemplatePlugin(TagPlugin):
    """
        The :class:`TemplatePlugin` plugin allows defining templates which can be included
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
                <a href='http://me.com'>John</a>
            </div>
        ```
    """
    NAME = 'Template'
    PRIORITY = 200  # The template plugin should be processed before all the others

    def __init__(self, tpl_element, name):
        super().__init__(tpl_element)
        self._template = _compile(tpl_element)
        self._name = name

    def bind_ctx(self, ctx):
        super().bind_ctx(ctx)
        TemplateLoader.store(ctx, self._name, self._template)

    def clone(self):
        return self

    def update(self):
        pass


class Include(TagPlugin):
    """
        The :class:`Include` plugin allows instantiating templates
        saved in the template cache. Assuming a template ``avatar`` was
        declared in the current (or some base) context
        (e.g. via :class:`TemplatePlugin`) one can include it as follows:

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
        self._tpl_instance = TemplateLoader.load(ctx, self._name)
        return self._tpl_instance.bind_ctx(ctx)

    def update(self):
        return self._tpl_instance.update()

register_plugin(Include)
register_plugin(TemplatePlugin)
