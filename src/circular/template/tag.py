from browser import html, document, timer

from circular.utils.events import EventMixin

from .expobserver import ExpObserver
from .expression import ET_INTERPOLATED_STRING, parse
from .context import Context

from circular.utils.logger import Logger
logger = Logger(__name__)

import re

class Template:
    """
        The template class is the basic class used for data-binding functionality.
        Its constructor takes a :class:`DOMNode` element (e.g. ``doc['element_id']``) and
        parses it and its children into an internal structure. One can than 
        use the :func:`Template.bind_ctx` instance method to bind the template to 
        a context (an instence of the :class:`Context` class) containing
        the data. Once the data-binding is setup in this way any change to the context
        will trigger an update of the document tree. 
        
        .. note:: 
        
           For performance reasons, the updates are only processed once every 100 msecs. 
        
        Assuming we have a template::

        ```
            
            <div id='app'>
                Greetings from the {{ country }}
            </div>
        ```
        We could write::

        ```
            from browser import document as doc
            from circular.template import Template, Context
            
            ctx = Context()
            ctx.country = 'Czech republic'
            tpl = Template(doc['app'])
            tpl.bind_ctx(ctx)              # The page shows "Greetings from the Czech republic"
            
            ctx.country = 'United Kingdom' # After a 100 msecs the page shows "Greetings from the United Kingdom"
        ```
    """
    @classmethod
    def set_prefix(cls,prefix):
        """
            Sets the prefix which should be prepended to tag names. E.g. if the prefix is set to `tpl-`
            then the `for` plugin must be written as `tpl-for`:

            ```

                <li tpl-for="[1,2,3]" ...>...</li>

            ```

        """
        TplNode.set_prefix(prefix)

    def __init__(self,elem):
        self.root = TplNode(elem)
        self.elem = elem
        self.update_timer = None

    def bind_ctx(self,ctx):
        elem = self.root.bind_ctx(ctx)
        self.elem.parent.replaceChild(elem,self.elem)
        self.elem = elem
        self.root.bind('change',self._start_timer)

    def _start_timer(self,event):
        if self.update_timer is None:
            self.update_timer = timer.set_interval(self.update,100)

    def update(self):
        """ FIXME: We need handle the case when the root node
                   returns a new element(s) on update
        """
        elems = self.root.update()
        if self.update_timer is not None:
            timer.clear_interval(self.update_timer)
        self.update_timer = None

class PrefixLookupDict(dict):
    def __init__(self,init=None):
        super().__init__()
        self._prefix = ''
        if isinstance(init,list):
            for item in init:
                self[item] = item
        elif isinstance(init,dict):
            for (k,v) in init.items():
                self[k] = v

    def _canonical(self,key):
        k = key.upper().replace('-','').replace('_','')
        if k.startswith(self._prefix):
            return k[len(self._prefix):]
        else:
            return k

    def remove(self,key):
        try:
            del self[key]
        except:
            pass

    def set_prefix(self,prefix):
        self._prefix = prefix.upper().replace('-','').replace('_','')

    def update(self, other):
        for (k,v) in other.items():
            self[k] = v

    def __delitem__(self, key):
        return super().__delitem__(self._canonical(key))

    def __getitem__(self,key):
        return super().__getitem__(self._canonical(key))

    def __setitem__(self,key,value):
        return super().__setitem__(self._canonical(key),value)

    def __contains__(self,key):
        return super().__contains__(self._canonical(key))

class TplNode(EventMixin):
    PLUGINS = PrefixLookupDict()
    _HASH_SEQ=0

    @classmethod
    def set_prefix(cls,prefix):
        cls.PLUGINS.set_prefix(prefix)
        cls.PREFIX=prefix

    @classmethod
    def register_plugin(cls,plugin_class):
        plugin_name = getattr(plugin_class,'NAME',None) or plugin_class.__name__
        meta = {
            'class':plugin_class,
            'args':PrefixLookupDict(list(plugin_class.__init__.__code__.co_varnames)),
            'name': plugin_name,
            'priority':getattr(plugin_class,'PRIORITY',0)
        }
        meta['args'].remove('self')
        meta['args'].remove('tpl_element')
        cls.PLUGINS[plugin_name]=meta

    def __hash__(self):
        return self._hash

    @classmethod
    def _build_kwargs(cls,element,plugin):
        ld = PrefixLookupDict(plugin['args'])
        kwargs = {}
        for attr in element.attributes:
            if attr.name in ld:
                kwargs[ld[attr.name]]=attr.value
                element.removeAttribute(attr.name)
        return kwargs

    def __init__(self,tpl_element):
        super().__init__()
        self._hash = TplNode._HASH_SEQ
        TplNode._HASH_SEQ += 1

        self.plugin = None           # The template plugin associated with the node

        if isinstance(tpl_element,TplNode):
            self.plugin = tpl_element.plugin.clone()
            self.plugin.bind('change',self,'change')
            return

        if tpl_element.nodeName == '#text':
            # Interpolated text node plugin
            self.plugin = TextPlugin(tpl_element)
        else:
            if not hasattr(tpl_element,'_plugins'):
                # This is the first pass over tpl_element,
                # we need to find out what the plugins are
                # and remove their params from the element
                # and save them for later
                plugin_metas = []
                for attr in tpl_element.attributes:
                    if attr.name in self.PLUGINS:
                        plugin_metas.append((attr.value,self.PLUGINS[attr.name]))
                        tpl_element.removeAttribute(attr.name)

                # Order the plugins by priority
                plugin_metas.sort(key = lambda x:x[1]['priority'])
                plugins = []
                for (arg,p) in plugin_metas:
                    plugins.append((p,[arg],self._build_kwargs(tpl_element,p)))

                if tpl_element.nodeName in self.PLUGINS:
                    tplug = self.PLUGINS[tpl_element.nodeName]
                    plugins.append(tplug, [], self._build_kwargs(tpl_element,tplug))
                set_meta = True
                setattr(tpl_element,'_plugins',plugins)

            plugins = getattr(tpl_element,'_plugins')

            # Now we initialize the first plugin, if any
            if len(plugins) > 0:
                plug_meta,args,kwargs = plugins.pop()
                self.plugin = p['class'](tpl_element,*args,**kwargs)
                self.plugin.bind('change',self,'change')
                return

            # If there are any attributes left, we initialize the InterpolatedAttrsPlugin
            if len(tpl_element.attributes) > 0:
                self.plugin = InterpolatedAttrsPlugin(tpl_element)
                self.plugin.bind('change',self,'change')
                return

            self.plugin = GenericTagPlugin(tpl_element)
        self.plugin.bind('change',self,'change')

    def clone(self):
        return TplNode(self)

    def bind_ctx(self,ctx):
        return self.plugin.bind_ctx(ctx)

    def update(self):
        return self.plugin.update()

    def __repr__(self):
        return "<TplNode "+repr(self.plugin)+" >"

class TagPlugin(EventMixin):
    """
        Plugins extending this class can set the `PRIORITY` class attribute to a non-zero
        number. The higher the number, the earlier they will be initialized. For example
        the `For` plugin sets the priority to 1000 (very high) because it wants to be
        initialized before the other plugins,e.g. if the template is
        ```
        <li tpl-for='c in colours' style='{{ c.css }}'>
        ```
        then the `tpl-for` plugin needs to be initialized before the plugin handling
        the interpolation on the style attribute because the context `c` is created
        by the tpl-for plugin. In general the order of initialization is as follows:

          1. plugins determined by attributes, ordered according to their PRIORITY
          2. the plugin handling interpolated attributes
          3. the plugin corresponding to the tag name

        Plugins extending this class can set the `NAME` class attribute. If set, it
        will be used to determine if the plugin applies to a given element. If it is
        not set, the class name will be used instead. For example the following
        plugin definition

        ```
        class My(TagPlugin):
            NAME='Foo'
            ...

        ```

        would apply to template elements of the form `<foo ...>` or `<div foo="..." ...>`.
    """

    def __init__(self,tpl_element):
        """
            @tpl_element is either a DOMNode or an instance of TagPlugin.
            In the second case, the TagPlugin should be cloned.
        """
        super().__init__()
        if isinstance(tpl_element,TagPlugin):
            self._orig_clone = tpl_element._orig_clone.clone()
        else:
            self._orig_clone = tpl_element.clone()
        self._dirty_self = True
        self._dirty_subtree = True

    def bind_ctx(self,ctx):
        """ Binds a context to the node and returns a DOMNode
            representing the bound subtree.
        """
        self._dirty_self = False
        self._dirty_subtree = False
        self._bound = True

    def update(self):
        """
            Updates the node with pending changes. If the changes result in
            a new element, returns it. Otherwise returns None.
        """
        if self._bound and (self._dirty_self or self._dirty_subtree):
            self._dirty_self = False
            self._dirty_subtree = False

    def clone(self):
        """
            Clones the plugin.
        """
        return self.__class__(self)

    def _self_change_chandler(self,event):
        if self._dirty_self:
            return
        self._dirty_self = True
        self.emit('change',event)

    def _subtree_change_handler(self,event):
        if self._dirty_subtree:
            return
        else:
            self._dirty_subtree = True
        if not self._dirty_self:
            self.emit('change',event)

class TextPlugin(TagPlugin):
    def __init__(self, tpl_element):
        super().__init__(tpl_element)
        self.observer = None
        if isinstance(tpl_element,TextPlugin):
            if tpl_element.observer is not None:
                self.observer = tpl_element.observer.clone()
                self.observer.bind('change',self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        else:
            if '{{' in tpl_element.text:
                self.observer = ExpObserver(tpl_element.text,expression_type=ET_INTERPOLATED_STRING)
                self.observer.bind('change',self._self_change_chandler)
            else:
                self._dirty_self = False
                self._dirty_subtree = False
        self.element = self._orig_clone

    def bind_ctx(self,ctx):
        self.element = self._orig_clone.clone()
        if self.observer is not None:
            super().bind_ctx(ctx)
            self.observer.context = ctx
            self.element.text = self.observer.value
            self._dirty_self = False
            self._dirty_subtree = False
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            self.element.text = self.observer.value
            self._dirty_self = False

    def __repr__(self):
        if self.observer is not None:
            return "<TextPlugin '"+self.observer._exp_src.replace("\n","\\n")+"' => '"+self.element.text.replace("\n","\\n")+"'>"
        else:
            return "<TextPlugin '"+self.element.text.replace("\n","\\n")+"'>"

class GenericTagPlugin(TagPlugin):
    def _fence(self,node):
        try:
            return html.COMMENT(str(node))
        except:
            return html.SPAN()
            return document.__class__(document.createComment(str(node)))

    def __init__(self,tpl_element):
        super().__init__(tpl_element)
        self.children = []
        self.child_elements = {}
        if isinstance(tpl_element,GenericTagPlugin):
            self.element = tpl_element.element.clone()
            self.element.clear()
            for ch in tpl_element.children:
                node = ch.clone()
                node.bind('change',self._subtree_change_handler)
                self.children.append(node)
                self.child_elements[node] = [self._fence(node)]
        else:
            self.element = tpl_element.clone()
            self.element.clear()
            for ch in tpl_element.children:
                node = TplNode(ch)
                node.bind('change',self._subtree_change_handler)
                self.children.append(node)
                self.child_elements[node] = [self._fence(node)]

    def update(self):
        if self._dirty_subtree and self._bound:
            for ch in self.children:
                elems = ch.update()
                if elems is not None:
                    self.replace(ch,elems)
            self._dirty_subtree = False

    def bind_ctx(self, ctx):
        self.element = self.element.clone()
        self.element.clear()
        for ch in self.children:
            rendered_elems = ch.bind_ctx(ctx)
            if type(rendered_elems) is not list:
                rendered_elems = [rendered_elems]
            self.child_elements[ch] = rendered_elems+[self._fence(ch)]
            self.element <= self.child_elements[ch]
        super().bind_ctx(ctx)
        return self.element

    def replace(self,ch,elems):
        fence = self.child_elements[ch][-1]
        for old_el in self.child_elements[ch][:-1]:
            logger.debug("Deleting",old_el)
            old_el.__del__()
        if type(elems) == list:
            for el in elems:
                self.element.insertBefore(el,fence)
            self.child_elements[ch] = elems + [fence]
        else:
            self.element.insertBefore(elems,fence)
            self.child_elements[ch] = [elems,fence]

    def __repr__(self):
        return "<Generic: "+self.element.tagName+">"

class InterpolatedAttrsPlugin(TagPlugin):
    def __init__(self,tpl_element):
        super().__init__(tpl_element)
        self.element = None
        self.observers = {}
        self.names = []
        if isinstance(tpl_element,InterpolatedAttrsPlugin):
            for (name,obs) in tpl_element.observers.items():
                if isinstance(obs,ExpObserver):
                    o = obs.clone()
                    self.observers[name] = o
                    o.bind('change',self._self_change_chandler)
                else:
                    self.observers[name] = obs
            self.child = tpl_element.child.clone()
        else:
            for attr in tpl_element.attributes:
                if '{{' in attr.value:
                    obs = ExpObserver(attr.value,ET_INTERPOLATED_STRING)
                    obs.bind('change',self._self_change_chandler)
                else:
                    obs = attr.value
                self.observers[attr.name] = obs
                tpl_element.removeAttribute(attr.name)
            self.child = TplNode(tpl_element)
        self.child.bind('change',self._subtree_change_handler)

    def bind_ctx(self, ctx):
        self.element = self.child.bind_ctx(ctx)
        for (name,obs) in self.observers.items():
            if isinstance(obs,ExpObserver):
                obs.context = ctx
                self.element.setAttribute(name,obs.value)
            else:
                self.element.setAttribute(name,obs)
        super().bind_ctx(ctx)
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            for (name,obs) in self.observers.items():
                if isinstance(obs,ExpObserver):
                    self.element.setAttribute(name,obs.value)
                else:
                    self.element.setAttribute(name,obs)
            self._dirty_self = False
        if self._dirty_subtree:
            self._dirty_subtree = False
            return self.child.update()

    def __repr__(self):
        ret = "<Attr: ";
        attrs = []
        for (name,obs) in self.observers.items():
            if isinstance(obs,ExpObserver):
                attrs.append(name+"="+obs.value+"("+obs._exp_src+")")
            else:
                attrs.append(name+"="+obs)
        return "<Attrs: "+" ".join(attrs)+" >"


class For(TagPlugin):
    """
        The template plugin `For` is used to generate a list of DOM elements.
        When a dom-element has the `for` attribute set it should be of the form
        ```
            var in list
        ```
        or
        ```
            var in list if condition
        ```
        where `var` is a variable name, `list` is an expression evaluating to
        a list and `condition` is a boolean expression which can contain the
        variable `var`. When a template element with a `for` attribute is
        bound to a context, the `list` expression is evaluated and filtered
        to a list which contains only elements satisfying the optional `condition`.
        Then for each element in this final list a new DOM-element is created
        and bound to the context containing a single variable `var` with the
        element as its value. For example, given the context
        ```
           ctx.l = [1,2,3,4]
        ```
        the template element
        ```
           <li for="num in l"> {{ num }} </li>
        ```
        when bound to the context would create the following four elements:
        ```
            <li>1</li>
            <li>2</li>
            <li>3</li>
            <li>4</li>
        ```
    """
    SPEC_RE = re.compile('^\s*(?P<loop_var>[^ ]*)\s*in\s*(?P<sequence_exp>.*)$',re.IGNORECASE)
    COND_RE = re.compile('\s*if\s(?P<condition>.*)$',re.IGNORECASE)
    PRIORITY = 1000 # The for plugin should be processed before all the others

    def __init__(self,tpl_element,loop_spec=None):
        super().__init__(tpl_element)
        if isinstance(tpl_element,For):
            self._var = tpl_element._var
            self._cond = tpl_element._cond
            self._exp = tpl_element._exp.clone()
            self.children = []
            self.child_template = tpl_element.child_template.clone()
        else:
            m=For.SPEC_RE.match(loop_spec)
            if m is None:
                raise Exception("Invalid loop specification: "+loop_spec)
            m = m.groupdict()
            self._var = m['loop_var']
            sequence_exp = m['sequence_exp']
            self._exp,pos = parse(sequence_exp,trailing_garbage_ok=True)
            m = For.COND_RE.match(sequence_exp[pos:])
            if m:
                self._cond = parse(m['condition'])
            else:
                self._cond = None
            self.children = []
            self.child_template = TplNode(tpl_element)
        self._exp.bind('exp_change',self._self_change_chandler)

    def _clear(self):
        for (ch,elem) in self.children:
            ch.unbind()
        self.children = []

    def bind_ctx(self, ctx):
        self._ctx = ctx
        self._clear()
        self._exp.watch(self._ctx)
        try:
            lst = self._exp.evaluate(self._ctx)
        except Exception as ex:
            logger.exception(ex)
            logger.warn("Exception",ex,"when computing list",self._exp,"with context",self._ctx)
            lst = []
            self._ex=ex
        ret = []
        for item in lst:
            c=Context({self._var:item})
            try:
                if self._cond is None or self._cond.evaluate(c):
                    clone = self.child_template.clone()
                    elem = clone.bind_ctx(c)
                    clone.bind('change',self._subtree_change_handler)
                    ret.append(elem)
                    self.children.append((clone,elem))
            except Exception as ex:
                logger.exception(ex)
                logger.warn("Exception",ex,"when evaluating condition",self._cond,"with context",c)
                self._ex=ex
        super().bind_ctx(ctx)
        return ret

    def update(self):
        if self._dirty_self and self._bound:
            return self.bind_ctx(self._ctx)
        elif self._dirty_subtree:
            self._dirty_subtree = False
            ret = []
            have_new = False
            for (ch,elem) in self.children:
                new_elem = ch.update()
                if new_elem is not None:
                    ret.append(new_elem)
                    have_new = True
                else:
                    ret.append(elem)
            if have_new:
                return ret
    def __repr__(self):
        ret= "<For:"+self._var+" in "+str(self._exp)
        if self._cond is not None:
            ret += " if "+self._cond
        ret += ">"
        return ret
TplNode.register_plugin(For)

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


    def __init__(self, tpl_element,model=None,update_interval=None,update_event='input'):
        super().__init__(tpl_element)
        self._model_change_timer = None
        self._input_change_timer = None
        if isinstance(tpl_element,Model):
            self._update_event = tpl_element._update_event
            self._update_interval = tpl_element._update_interval
            self._model_observer = tpl_element.model.clone()
            self.child = tpl_element.child.clone()
        else:
            self._update_event = update_event
            if update_interval is not None:
                self._update_interval = int(update_interval)
            else:
                self._update_interval = None
            self._model_observer = ExpObserver(model)
            self.child = TplNode(tpl_element)
        if self._update_interval:
            self._model_observer.bind('change',self._defer_model_change)
        else:
            self._model_observer.bind('change',self._model_change)
        self.child.bind('change',self._subtree_change_handler)
        logger.debug("Initialized model plugin")

    def bind_ctx(self,ctx):
        self.element = self.child.bind_ctx(ctx)
        self._model_observer.context = ctx
        if self._update_interval:
            self.element.bind(self._update_event,self._defer_input_change)
        else:
            self.element.bind(self._update_event,self._input_change)
        super().bind_ctx(ctx)
        return self.element

    def _defer_model_change(self,event):
        if self._model_change_timer is None:
            self._model_change_timer = timer.set_interval(self._model_change,self._update_interval)

    def _defer_input_change(self,event):
        if self._input_change_timer is None:
            self._input_change_timer = timer.set_interval(self._input_change,self._update_interval)

    def _model_change(self,event=None):
        if self.element and self._model_observer.have_value() and self.element.value != self._model_observer.value:
            self.element.value = self._model_observer.value
            if self._model_change_timer:
                timer.clear_interval(self._model_change_timer)
                self._model_change_timer = None

    def _input_change(self,event=None):
        if self.element and (not self._model_observer.have_value() or self.element.value != self._model_observer.value):
            self._model_observer.evaluate_assignment(self.element.value)
            if self._input_change_timer:
                timer.clear_interval(self._input_change_timer)
                self._input_change_timer = None

    def __repr__(self):
        if self._model_observer.have_value():
            return "<ModelPlugin "+self._model_observer._exp_src+" ("+self._model_observer.value+")>"
        else:
            return "<ModelPlugin "+self._model_observer._exp_src+" (undefined)>"
TplNode.register_plugin(Model)