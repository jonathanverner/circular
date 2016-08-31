from tests.brython.browser.html import MockElement
from tests.brython.browser import document

from src.circular.template.context import Context
from src.circular.template.tpl import Template

def test_model_plugin():
    div_elem = MockElement('div',id='test')
    text_elem = MockElement('#text',id='text')
    text_elem.text = "{{ c['name'] }}"
    div_elem <= text_elem
    input_elem = MockElement('input',model='c["name"]',id='input')
    div_elem <= input_elem
    document <= div_elem
    tpl = Template(document['test'])
    ctx = Context({})
    ctx.c = {'name':''}
    elem=tpl.bind_ctx(ctx)
    text_elem = document['text']
    input_elem = document['input']
    assert text_elem.text == ''
    input_elem.setAttribute('value','Jonathan')
    assert text_elem.text == 'Jonathan'
    assert ctx.c['name'] == 'Jonathan'
    assert input_elem.value == 'Jonathan'
    input_elem.value = 'Test'
    assert text_elem.text == 'Jonathan'
    assert ctx.c['name'] == 'Jonathan'
    ctx.c['name'] = 'Test2'
    assert input_elem.value == 'Test2'
    assert text_elem.text == 'Test2'

