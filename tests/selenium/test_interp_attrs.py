from tests.utils import wait_for_script, selenium_setup_helper


def setup_function(func):
    selenium_setup_helper(func)


def script_class():
    """
        <span id='spanid' class='{{ " ".join(classes) }}'>
        </span>
    """
    from browser import document as doc, html
    from circular.template import Template, Context, set_prefix

    set_prefix('tpl-')
    tpl = Template(doc['test'])
    ctx = Context()
    tpl.bind_ctx(ctx)
    ctx.classes = ['red', 'green', 'blue']
    tpl.update()


def test_class(selenium):
    wait_for_script(selenium)
    span = selenium.find_element_by_id('spanid')
    assert span.get_attribute('class') == 'red green blue'


