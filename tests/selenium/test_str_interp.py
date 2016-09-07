from tests.utils import wait_for_script, selenium_setup_helper


def setup_function(func):
    selenium_setup_helper(func)


def script_example():
    """
        Ahoj {{ name }} {{ surname }}!
    """
    from browser import document as doc, html
    from circular.template import Template, Context, set_prefix

    set_prefix('tpl-')
    tpl = Template(doc['test'])
    ctx = Context()
    tpl.bind_ctx(ctx)
    ctx.name = 'Jonathan'
    ctx.surname = 'Verner'
    tpl.update()


def test_example(selenium):
    element = wait_for_script(selenium)
    assert element.text == "Ahoj Jonathan Verner!"

