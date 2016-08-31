from tests.brython.browser.html import MockElement

from src.circular.template.context import Context
from src.circular.template.tags import TextPlugin
from src.circular.template.tpl import _compile


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
    tp = _compile(text_elem)
    c = Context({})
    elem = tp.bind_ctx(c)
    assert elem.text == "Hello"
    c.name = "Jonathan"
    assert tp.update() is None
    assert elem.text == "Hello"

