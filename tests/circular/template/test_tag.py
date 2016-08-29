from unittest.mock import patch

from tests.brython.browser.html import MockAttr, MockDomElt, MockElement
from tests.brython.browser import document
from src.circular.utils.events import EventMixin

from src.circular.template.context import Context
from src.circular.template.tag import Template, TplNode, TagPlugin, TextPlugin, GenericTagPlugin, InterpolatedAttrsPlugin, For, PrefixLookupDict
from src.circular.template.expobserver import ExpObserver
from src.circular.template.expression import ET_INTERPOLATED_STRING, parse



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
    assert com_elem.tagName == 'comment'
    assert text_elem.text == ""
    assert t2_elem.text == "ahoj"
    assert plug._dirty_self is False
    assert plug._dirty_subtree is False
    ctx.name = "Jonathan"
    assert plug._dirty_self is False
    assert plug._dirty_subtree is True
    assert plug.update() is None
    assert text_elem.text == "Jonathan"

def test_interpolated_attrs_plugin():
    text_elem = MockElement('#text')
    text_elem.text = "{{ name }}"
    t2_elem = MockElement('#text')
    t2_elem.text = "ahoj"
    div_elem = MockElement('div',id="test")
    div_elem <= text_elem
    div_elem <= t2_elem

    plug = InterpolatedAttrsPlugin(div_elem)
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    assert elem.attributes.id == "test"

    div_elem.setAttribute('id',"{{ id }}")
    plug = InterpolatedAttrsPlugin(div_elem)
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    text_elem = elem.children[0]
    com_elem = elem.children[1]
    t2_elem = elem.children[2]
    assert elem.attributes.id == ""
    assert com_elem.tagName == 'comment'
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

    div_elem.attributes.extend([MockAttr('id','{{ id }}'),MockAttr('style','{{ css }}'),MockAttr('name','???')])
    plug = TplNode(div_elem)
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    assert elem.attributes.id == ""
    assert elem.attributes.style == ""
    assert elem.attributes.name == "???"
    ctx.css = "border:1px;"
    assert plug.update() is None
    assert elem.attributes.style == "border:1px;"


def filter_comments(lst):
    return [ e for e in lst if e.tagName != 'comment' ]

def test_for_plugin():
    div_elem = MockElement('div',style='{{ c["css"] }}')
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

def test_nested_for():
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



