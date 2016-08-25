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
            
            <div id='app'>
                Greetings from the {{ country }}
            </div>
            
        We could write::
        
            from browser import document as doc
            from circular.template import Template, Context
            
            ctx = Context()
            ctx.country = 'Czech republic'
            tpl = Template(doc['app'])
            tpl.bind_ctx(ctx)              # The page shows "Greetings from the Czech republic"
            
            ctx.country = 'United Kingdom' # After a 100 msecs the page shows "Greetings from the United Kingdom"
    """
    @classmethod
    def set_prefix(cls,prefix):
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
        k = key.upper().replace('-','')
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
        self._prefix = prefix.upper().replace('-','')

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
            'name': plugin_name
        }
        meta['args'].remove('self')
        meta['args'].remove('tpl_element')
        cls.PLUGINS[plugin_name]=meta

    def __hash__(self):
        return self._hash

    def __init__(self,tpl_element):
        super().__init__()
        self._hash = TplNode._HASH_SEQ
        TplNode._HASH_SEQ += 1

        self.plugin = None           # The template plugin associated with the node

        # Initialize the plugins
        args = [tpl_element]
        kwargs = {}

        if isinstance(tpl_element,TplNode):
            self.plugin = tpl_element.plugin.clone()
            self.plugin.bind('change',self,'change')
            return

        if tpl_element.nodeName == '#text':
            # Interpolated text node plugin
            self.plugin = TextPlugin(*args,**kwargs)
        else:
            if tpl_element.nodeName in self.PLUGINS:
                # Get list of attributes which are consumed by tag-plugin
                tag_params = PrefixLookupDict(self.PLUGINS[tpl_element.nodeName]['args'])
            else:
                tag_params = []
            for attr in tpl_element.attributes:
                if attr.name in tag_params:
                    # Skip attributes consumed by tag-plugin
                    continue
                if attr.name in self.PLUGINS:
                    # If attribute corresponds to a plugin, initialize it
                    meta = self.PLUGINS[attr.name]
                    ld = PrefixLookupDict(meta['args'])
                    tpl_element.removeAttribute(attr.name)
                    for pattr in tpl_element.attributes:
                        if pattr.name in ld:
                            kwargs[ld[pattr.name]]=pattr.value
                            tpl_element.removeAttribute(pattr.name)
                    args.append(attr.value)
                    self.plugin = meta['class'](*args,**kwargs)
                    self.plugin.bind('change',self,'change')
                    return
                else:
                    # Initialize the interpolated attribute plugin
                    kwargs['name'] = attr.name
                    kwargs['value'] = attr.value
                    tpl_element.removeAttribute(attr.name)
                    self.plugin = InterpolatedAttrPlugin(*args,**kwargs)
                    self.plugin.bind('change',self,'change')
                    return

            # No more attributes to process, initialize the tag-plugin, if present
            if tpl_element.nodeName in self.PLUGINS:
                for attr in tpl_element.attributes:
                    kwargs[tag_params[attr.name]]=attr.value
                    tpl_element.removeAttribute(attr.name)
                self.plugin = self.PLUGINS[tpl_element.nodeName]['class'](*args,**kwargs)
            else:
                self.plugin = GenericTagPlugin(*args,**kwargs)
        self.plugin.bind('change',self,'change')

    def clone(self):
        return TplNode(self)

    def bind_ctx(self,ctx):
        return self.plugin.bind_ctx(ctx)

    def update(self):
        return self.plugin.update()

class TagPlugin(EventMixin):
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
            return html.SPAN(str(node))
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

class InterpolatedAttrPlugin(TagPlugin):
    def __init__(self,tpl_element,name=None,value=None):
        super().__init__(tpl_element)
        self.element = None
        if isinstance(tpl_element,InterpolatedAttrPlugin):
            self.name = tpl_element.name
            if tpl_element.observer is not None:
                self.observer = tpl_element.observer.clone()
                self.observer.bind('change',self._self_change_chandler)
            else:
                self.observer = None
            self.child = tpl_element.child.clone()
        else:
            self.name = name
            self.observer = None
            self.element = None
            if '{{' in value:
                self.observer = ExpObserver(value,ET_INTERPOLATED_STRING)
                self.observer.bind('change',self._self_change_chandler)
            else:
                self.value = value
            self.child = TplNode(tpl_element)
        self.child.bind('change',self._subtree_change_handler)

    def bind_ctx(self, ctx):
        self.element = self.child.bind_ctx(ctx)
        if self.observer:
            self.observer.context = ctx
            self.element.setAttribute(self.name,self.observer.value)
        else:
            self.element.setAttribute(self.name,self.value)
        super().bind_ctx(ctx)
        return self.element

    def update(self):
        if self._dirty_self and self._bound:
            self.element.setAttribute(self.name,self.observer.value)
            self._dirty_self = False
        if self._dirty_subtree:
            self._dirty_subtree = False
            return self.child.update()

    def __repr__(self):
        if self.observer is not None:
            return "<Attr: "+self.name +"='"+self.value+"' ("+self.observer._exp_src+")>"
        else:
            return "<Attr: "+self.name +"='"+self.value+"' >"

class For(TagPlugin):
    SPEC_RE = re.compile('^\s*(?P<loop_var>[^ ]*)\s*in\s*(?P<sequence_exp>.*)$',re.IGNORECASE)
    COND_RE = re.compile('\s*if\s(?P<condition>.*)$',re.IGNORECASE)

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
                #raise ex
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
TplNode.register_plugin(For)
