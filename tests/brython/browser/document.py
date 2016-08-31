from .html import MockElement, MockDomElt

class body(MockElement):
    def __init__(self):
        super().__init__('body')

    def __getitem__(self,id):
        if self.id == id:
            return self
        else:
            return self._findChild(id)

    def _reset(self):
        self.attributes.clear()
        self.children = []
        self.parent = None
        self.elt = MockDomElt(self)
        self.text = ''

document = body()


