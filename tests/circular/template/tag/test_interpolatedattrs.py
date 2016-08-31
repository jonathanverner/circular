from tests.brython.browser.html import MockElement, MockAttr

from src.circular.template.context import Context
from src.circular.template.tags import InterpolatedAttrsPlugin
from src.circular.template.tpl import _compile

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
    plug = _compile(div_elem)
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    assert elem.attributes.id == ""
    ctx.id = "test_id"
    assert plug.update() is None
    assert elem.attributes.id == "test_id"

    div_elem.attributes.extend([MockAttr('id','{{ id }}'),MockAttr('style','{{ css }}'),MockAttr('name','???')])
    plug = _compile(div_elem)
    ctx = Context({})
    elem = plug.bind_ctx(ctx)
    assert elem.attributes.id == ""
    assert elem.attributes.style == ""
    assert elem.attributes.name == "???"
    ctx.css = "border:1px;"
    assert plug.update() is None
    assert elem.attributes.style == "border:1px;"
