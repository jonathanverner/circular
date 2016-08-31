from tests.brython.browser.html import MockElement

from src.circular.template.context import Context
from src.circular.template.tags import GenericTagPlugin


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
