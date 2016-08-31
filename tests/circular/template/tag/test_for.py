from tests.brython.browser.html import MockElement, MockAttr

from src.circular.template.context import Context
from src.circular.template.tags import For
from src.circular.template.tpl import _compile

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
    ch_elem = MockElement('span',id='id-{{name}}')
    ch_elem.attributes.append(MockAttr('for','name in c["names"]'))
    t_elem = MockElement('#text')
    t_elem.text = "{{ name }}{{parent_attr}}"
    ch_elem <= t_elem
    div_elem <= ch_elem
    doc <= div_elem
    plug = _compile(doc)
    ctx = Context()
    ctx.parent_attr = "Test"
    ctx.colours = [{'names':['Red','Reddish'],'css':'red'},{'names':['Blue'],'css':'blue'}]
    doc = plug.bind_ctx(ctx)
    nocomment_children = filter_comments(doc.children)
    assert len(nocomment_children) == 2
    assert len(filter_comments(nocomment_children[0].children)) == 2
    red_elem = doc._findChild('id-Red')
    assert red_elem.children[0].text == 'RedTest'

