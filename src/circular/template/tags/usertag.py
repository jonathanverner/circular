from circular.template.tpl import _compile, register_plugin, TagPlugin
from circular.template.expression import parse
from circular.template.context import Context


class UserTag(TagPlugin):
    """
        The :class:`UserTag` plugin allows users to easily define new html tags
        by subclassing it and reimplementing the relevant methods.
    """
    TEMPLATE = ""
    _compiled_tpl = None

    def _clone_args(self, tag):
        pass

    def _process_args(self, arguments):
        pass

    def __init__(self, tpl_element, **kwargs):
        """
            Descendant classes should override this to specify
            (via argument names) which attributes from the dom-element
            the plugin uses. However, the actual implementation should
            just be a single line:
            ```
                super().__init__(tpl_element,...)
            ```
            calling the base constructor which does all the work
            (initializing the arguments). Any processing that needs to
            be done at compile time should be put into the post_init
            method.
        """
        super().__init__(tpl_element, **kwargs)
        if self._compiled_tpl is None:
            self._compiled_tpl = _compile(self.TEMPLATE)
        self.tpl = self._compiled_tpl.clone()
        if isinstance(tpl_element, UserTag):
            self._clone_args(tpl_element)
            self.post_clone(tpl_element)
        else:
            self._process_args(kwargs)
            self.post_init()

    def post_clone(self, original):
        """
            This method is called by the clone of :param:`original`
            after it is done initializing itself. The default
            implementation just calls the :method:`post_init` method.
        """
        self.post_init()

    def post_init(self):
        """
            This method is called by the constructor after it is
            done initializing itself (e.g. compiling the template,
            initializing & compiling the args, etc.)
        """
        pass

    def pre_bind(self, ctx):
        """
            This method is called just before the template is bound to a
            context. The context is passed as :param:`ctx`.
        """
        pass

    def post_bind(self, elements):
        """
            This method is called after the template is bound to
            a context. The context is available as the :attribute:`_ctx`
            attribute on `self`. The bound DOM-element which corresponds passed as :param:`ctx`
        """
        return elements

    def bind_ctx(self, ctx):
        self.pre_bind(ctx)
        super().bind_ctx(ctx)
        elements = self.tpl.bind_ctx(ctx)
        self.post_bind(elements)

    def clone(self):
        return self

    def update(self):
        pass

