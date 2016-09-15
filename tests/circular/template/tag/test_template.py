from tests.brython.browser.html import MockElement
from tests.brython.browser import document

from src.circular.template import Context
from src.circular.template import Template


def setup_function(func):
    document._reset()


def test_template_plugin():
    test_elem = MockElement('div', id='test')
    tpl_elem = MockElement('div', template='my_template', id='tpl{{ id }}')
    text_elem = MockElement('#text')
    text_elem.text = "{{ name }}"
    tpl_elem <= text_elem

    incl = MockElement('include', name='my_template')

    test_elem <= tpl_elem
    test_elem <= incl

    document <= test_elem

    tpl = Template(document['test'])
    ctx = Context({})
    ctx.name = 'test'
    ctx.id = 10
    elem = tpl.bind_ctx(ctx)

    txt = document['tpl10']
    assert txt.text == 'test'
