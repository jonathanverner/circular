from unittest.mock import patch

from tests.brython.browser.html import MockAttr, MockDomElt, MockElement
from tests.brython.browser import document

from src.circular.utils.events import EventMixin

from src.circular.template.context import Context
from src.circular.template import Template, register_plugin, set_prefix
from src.circular.template.tpl import PrefixLookupDict, PLUGINS, _compile
from src.circular.template.tags import TagPlugin, TextPlugin, GenericTagPlugin, InterpolatedAttrsPlugin, For
from src.circular.template.interpolatedstr import InterpolatedStr
from src.circular.template.expression import parse



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
    a = PrefixLookupDict(['ahoj','AhojJak','test_auto'])
    a.set_prefix('tpl-')
    assert 'tpl-ahoj' in a
    assert 'TPL-AHOJ' in a
    assert 'tpl-Ahoj-Jak' in a
    assert 'test-auto' in a
    assert 'test_Auto' in a
    assert 'TestAuto' in a

def test_register_plugins():
    class TestPlugin(TagPlugin):
        def __init__(self,tpl_element,model):
            pass
    register_plugin(TestPlugin)
    set_prefix('tpl-')
    assert 'tpl-Test-Plugin' in PLUGINS
    meta = PLUGINS['tpl-TestPlugin']
    assert 'model' in meta['args']
    assert meta['args']['model'] == 'model'
    assert 'tpl-TestPlugin' in PLUGINS
    del PLUGINS['tpl-TestPlugin']

