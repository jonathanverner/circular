from unittest.mock import patch

import tests.brython.browser

from src.circular.utils.events import EventMixin

from src.circular.template.context import Context
from src.circular.template.tag import Template, TplNode, TagPlugin, TextPlugin, GenericTagPlugin, InterpolatedAttrPlugin, For, PrefixLookupDict
from src.circular.template.expobserver import ExpObserver
from src.circular.template.expression import ET_INTERPOLATED_STRING, parse


class MockAttr:
    def __init__(self,name,val=None):
        self.name = name
        self.value = val

    def clone(self):
        return MockAttr(self.name,self.value)

    def __repr__(self):
        return "<MockAttr("+self.name+","+self.value+")>"

class attrlist(list):
    def __getattr__(self, name):
        for a in self:
            if a.name == name:
                return a.value
        return super().__getattribute__(name)

class MockElement:
    def __init__(self,tag_name):
        self.tag_name = tag_name
        self.attributes = attrlist([])
        self.children = []
        self.elt = MockDomElt(self)
        self.nodeName = tag_name
        self.parent = None
        self.text = ''

    def clone(self):
        ret = MockElement(self.tag_name)
        for attr in self.attributes:
            ret.attributes.append(attr.clone())
        for ch in self.children:
            ret <= ch.clone()
        ret.text = self.text
        return ret

    def clear(self):
        self.elt.clear()
        self.children = []

    def _indexAttr(self,name):
        pos=0
        for attr in self.attributes:
            if attr.name == name:
                return pos
            pos+=1
        return -1

    def removeAttribute(self,name):
        pos=self._indexAttr(name)
        if pos > -1:
            del self.attributes[pos]

    def setAttribute(self,name,value):
        pos=self._indexAttr(name)
        if pos > -1:
            self.attributes[pos].value=value
        else:
            self.attributes.append(MockAttr(name,value))

    def insertBefore(self,domnode,before):
        pos = self.children.index(before)
        self.elt.insertBefore(domnode.elt,self.children[pos].elt)
        self.children.insert(pos,domnode)

    def replaceChild(self,replace_with,replace_what):
        pos = self.children.index(replace_what)
        self.elt.replaceChild(replace_with.elt,replace_what.elt)
        self.children[pos]=replace_with

    def __setattr__(self, name, value):
        if name in ['tag_name','attributes','children','elt','nodeName','parent','text']:
            return super().__setattr__(name,value)
        else:
            for attr in self.attributes:
                if attr.name == name:
                    attr.value = value
                    return
            self.attributes.append(MockAttr(name,value))

    def __delattr__(self, key):
        pos = -1
        for attr in self.attributes:
            pos += 1
            if attr.name == key:
                break
        if pos > -1:
            del self.attributes[pos]
        else:
            raise KeyError()

    def __le__(self, other):
        if isinstance(other,list):
            for o in other:
                self.children.append(o)
                self.elt.appendChild(o)
        else:
            self.children.append(other)
            self.elt.appendChild(other.elt)

class Comment(MockElement):
    def __init__(self, text):
        super().__init__('comment')
        self.text = text

class MockDomElt:
    def __init__(self,node,parent=None):
        self.parent = parent
        self.children = []
        self.node=node

    def clear(self):
        for ch in self.children:
            ch.parent = None
        self.children = []

    def appendChild(self,ch):
        self.children.append(ch)
        ch.parent = self

    def replaceChild(self,replace_with,replace_what):
        pos = self.children.index(replace_what)
        repl = self.children[pos]
        repl.parent = None
        self.children[pos] = replace_with
        replace_with.parent = self

    def insertBefore(self,ch,reference):
        pos = self.children.index(ch)
        self.children.insert(pos,ch)
        ch.parent = self
        self.children.insert(pos,ch)

class InterpolatedStr(EventMixin):
    def __init__(self,string):
        super().__init__()
        self.observer = ExpObserver(string,expression_type=ET_INTERPOLATED_STRING)
        self.observer.bind('change',self._change_handler)

    def bind_ctx(self,ctx):
        self.observer.context = ctx

    @property
    def src(self):
        return self.observer._exp_src

    @property
    def context(self):
        return self.observer.context

    @context.setter
    def context(self,ct):
        self.observer.context = ct

    @property
    def value(self):
        return self.observer.value

    def _change_handler(self,event):
        old,new  = event.data.get('old',""), event.data.get('new',"")
        self.emit('change',{'old':old,'value':new})

    def __repr__(self):
        return "InterpolatedStr("+self.src.replace("\n","\\n")+") = "+self._val


def test_incomplete():
    ctx = Context()
    s = InterpolatedStr("Ahoj {{ name }} {{ surname }}!")
    assert s.value == "Ahoj  !"

    ctx.name = "Jonathan"
    s.bind_ctx(ctx)
    assert s.value == "Ahoj Jonathan !"

    ctx.surname = "Verner"
    assert s.value == "Ahoj Jonathan Verner!"

def test_prefix_lookup():
    a = PrefixLookupDict(['ahoj','AhojJak'])
    a.set_prefix('tpl-')
    assert 'tpl-ahoj' in a
    assert 'TPL-AHOJ' in a
    assert 'tpl-Ahoj-Jak' in a

def test_register_plugins():
    class TestPlugin(TagPlugin):
        def __init__(self,tpl_element,model):
            pass
    TplNode.register_plugin(TestPlugin)
    TplNode.set_prefix('tpl-')
    assert 'tpl-Test-Plugin' in TplNode.PLUGINS
    meta = TplNode.PLUGINS['tpl-TestPlugin']
    assert 'model' in meta['args']
    assert meta['args']['model'] == 'model'
    assert 'tpl-TestPlugin' in TplNode.PLUGINS
    del TplNode.PLUGINS['tpl-TestPlugin']

def test_text_plugin():
    text_elem = MockElement('#text')
    text_elem.text = "Hello {{ name }}"
    tp = TextPlugin(text_elem)
    c = Context({})
    elem = tp.bind_ctx(c)
    assert elem.text == "Hello "
    c.name = "Jonathan"
    assert tp._dirty_self is True
    assert tp.update() is None
    assert tp._dirty_self is False
    assert elem.text == "Hello Jonathan"

    tp2 = tp.clone()
    c2 = Context({'name':'Ansa'})
    elem2 = tp2.bind_ctx(c2)
    assert elem2.text == "Hello Ansa"
    assert elem.text == "Hello Jonathan"
    assert tp._dirty_self is False

    text_elem = MockElement('#text')
    text_elem.text = "Hello"
    tp = TplNode(text_elem)
    c = Context({})
    elem = tp.bind_ctx(c)
    assert elem.text == "Hello"
    c.name = "Jonathan"
    assert tp.update() is None
    assert elem.text == "Hello"


@patch('tests.brython.browser.html.COMMENT',Comment)
def test_generic_plugin():
    text_elem = MockElement('#text')
    text_elem.text = "{{ name }}"
    t2_elem = MockElement('#text')
    t2_elem.text = "ahoj"
    div_elem = MockElement('div')
    div_elem <= text_elem
    div_elem <= t2_elem

    plug = GenericTagPlugin(div_elem)
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    text_elem = elem.children[0]
    com_elem = elem.children[1]
    t2_elem = elem.children[2]
    assert com_elem.tag_name == 'comment'
    assert text_elem.text == ""
    assert t2_elem.text == "ahoj"
    assert plug._dirty_self is False
    assert plug._dirty_subtree is False
    ctx.name = "Jonathan"
    assert plug._dirty_self is False
    assert plug._dirty_subtree is True
    assert plug.update() is None
    assert text_elem.text == "Jonathan"

@patch('tests.brython.browser.html.COMMENT',Comment)
def test_interpolated_attr_plugin():
    text_elem = MockElement('#text')
    text_elem.text = "{{ name }}"
    t2_elem = MockElement('#text')
    t2_elem.text = "ahoj"
    div_elem = MockElement('div')
    div_elem <= text_elem
    div_elem <= t2_elem

    plug = InterpolatedAttrPlugin(div_elem,"id","test")
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    assert elem.attributes.id == "test"

    plug = InterpolatedAttrPlugin(div_elem,"id","{{ id }}")
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    text_elem = elem.children[0]
    com_elem = elem.children[1]
    t2_elem = elem.children[2]
    assert elem.attributes.id == ""
    assert com_elem.tag_name == 'comment'
    assert text_elem.text == ""
    assert t2_elem.text == "ahoj"
    assert plug._dirty_self is False
    assert plug._dirty_subtree is False
    ctx.id = "test_id"
    assert plug._dirty_self is True
    assert plug._dirty_subtree is False
    assert plug.update() is None
    assert elem.attributes.id == "test_id"
    ctx.name = "Jonathan"
    assert plug._dirty_self is False
    assert plug._dirty_subtree is True
    assert plug.update() is None
    assert text_elem.text == "Jonathan"
    assert plug._dirty_subtree is False


    div_elem.attributes.append(MockAttr('id','{{ id }}'))
    plug = TplNode(div_elem)
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    assert elem.attributes.id == ""
    ctx.id = "test_id"
    assert plug.update() is None
    assert elem.attributes.id == "test_id"


def filter_comments(lst):
    return [ e for e in lst if e.tag_name != 'comment' ]

@patch('tests.brython.browser.html.COMMENT',Comment)
def test_for_plugin():
    div_elem = MockElement('div')
    div_elem.attributes.append(MockAttr('style','{{ c["css"] }}'))
    text_elem = MockElement('#text')
    text_elem.text = "{{ c['name'] }}"
    div_elem <= text_elem

    plug = For(div_elem,loop_spec="c in colours")
    ctx = Context({})
    elems=plug.bind_ctx(ctx)
    assert filter_comments(elems) == []
    ctx.colours = [{'name':'Red','css':'red'},{'name':'Blue','css':'blue'}]
    assert plug._dirty_self is True
    elems = plug.update()
    nocomment = filter_comments(elems)
    assert len(nocomment) == 2
    assert hasattr(nocomment[0].attributes,'style')
    assert nocomment[0].attributes.style == "red"
    assert nocomment[0].children[0].text == "Red"
    assert nocomment[1].attributes.style == "blue"
    assert nocomment[1].children[0].text == "Blue"
    ctx.colours[0]['name'] = 'Reddish'
    assert plug._dirty_self is False
    assert plug._dirty_subtree is True
    assert plug.update() is None
    assert filter_comments(nocomment[0].children)[0].text == "Reddish"

    # Test nested loops
    doc = MockElement('div')
    div_elem = MockElement('div')
    div_elem.attributes.append(MockAttr('for','c in colours'))
    div_elem.attributes.append(MockAttr('style','{{ c["css"] }}'))
    ch_elem = MockElement('span')
    ch_elem.attributes.append(MockAttr('for','name in c["names"]'))
    t_elem = MockElement('#text')
    t_elem.text = "{{ name }}"
    ch_elem <= t_elem
    div_elem <= ch_elem
    doc <= div_elem
    plug = TplNode(doc)
    ctx = Context()
    ctx.colours = [{'names':['Red','Reddish'],'css':'red'},{'names':['Blue'],'css':'blue'}]
    nocomment_children = filter_comments(plug.bind_ctx(ctx).children)
    assert len(nocomment_children) == 2
    assert len(filter_comments(nocomment_children[0].children)) == 2






