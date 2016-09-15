from tests.utils import wait_for_script, selenium_setup_helper


def setup_function(func):
    selenium_setup_helper(func)


def script_example():
    """
        Ahoj {{ name }}.
    """
    import asyncio

    from browser import document as doc, html, timer
    from circular.template import Template, Context, set_prefix

    fut = asyncio.Future()
    ctx = Context()

    def set_result():
        fut.set_result("Jonathan.")

    ctx.name = fut
    tpl = Template(doc['test'])
    tpl.bind_ctx(ctx)
    timer.set_timeout(set_result, 10)


def test_example(selenium):
    element = wait_for_script(selenium)
    assert element.text == "Ahoj Jonathan"


