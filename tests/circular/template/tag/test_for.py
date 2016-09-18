from tests.brython.browser.html import MockElement, MockAttr

from src.circular.platform.bs4 import Tag, dom_from_html, NodeType
from src.circular.template.context import Context
from src.circular.template.tags import For
from src.circular.template.tpl import _compile


def filter_comments(lst):
    return [e for e in lst if e.type != NodeType.COMMENT]


def test_for_plugin():
    div_elem = dom_from_html("""
        <div style="{{c['css']}}">{{ c['name'] }}</div>
    """)

    plug = For(div_elem, loop_spec="c in colours")
    ctx = Context({})
    elems = plug.bind_ctx(ctx)
    assert filter_comments(elems) == []
    ctx.colours = [{'name': 'Red', 'css': 'red'}, {'name': 'Blue', 'css': 'blue'}]
    assert plug._dirty_self is True
    elems = plug.update()
    nocomment = filter_comments(elems)
    assert len(nocomment) == 2
    assert 'style' in nocomment[0].attrs
    assert nocomment[0]['style'] == "red"
    assert nocomment[0].contents[0].string == "Red"
    assert nocomment[1]['style'] == "blue"
    assert nocomment[1].contents[0].string == "Blue"
    ctx.colours[0]['name'] = 'Reddish'
    assert plug._dirty_self is False
    assert plug._dirty_subtree is True
    assert plug.update() is None
    assert filter_comments(nocomment[0].contents)[0].string == "Reddish"


def test_nested_for():
    # Test nested loops
    html = """
        <div>
          <div for='c in colours' style='{{ c["css"] }}'>
            <span for='name in c["names"]' id='id-{{name}}'>{{ name }}{{parent_attr}}</span>
          </div>
        </div>
    """.replace('\n', '')
    doc = dom_from_html(html)
    plug = _compile(doc)
    ctx = Context()
    ctx.parent_attr = "Test"
    ctx.colours = [{'names': ['Red', 'Reddish'], 'css': 'red'}, {'names': ['Blue'], 'css': 'blue'}]
    doc = plug.bind_ctx(ctx)
    nocomment_children = filter_comments(doc.children)
    assert len(nocomment_children) == 2
    assert len(filter_comments(nocomment_children[0].children)) == 2
    red_elem = doc._findChild('id-Red')
    assert red_elem.children[0].text == 'RedTest'

