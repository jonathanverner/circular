from tests.brython.browser.html import MockElement
from src.circular.platform.bs4 import Document, dom_from_html

from src.circular.template.context import Context
from src.circular.template.tpl import Template

document = Document()


class TestClick(object):

    def setup_method(self, method):
        self.called = False
        self.ctx = Context()
        document.clear()

    def test_basic(self):
        self.obj = None
        self.event = None

        def handler(x, event):
            self.obj = x
            self.event = event
            self.called = True

        elem = dom_from_html('<div id="test" click="handler(ch)"></div>')

        self.ctx.handler = handler
        self.ctx.ch = 10
        document <= elem
        tpl = Template(elem)
        tpl.bind_ctx(self.ctx)
        elem = document['test']
        assert self.called is False
        elem.click()
        assert self.obj == 10
        assert self.event.data['target'] is elem
        assert self.event.data['type'] == 'click'
