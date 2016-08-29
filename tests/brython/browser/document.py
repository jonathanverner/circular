from .html import MockElement

class body(MockElement):
    def __init__(self):
        super().__init__('body')

    def __getitem__(self,id):
        if self.id == id:
            return self
        else:
            return self._findChild(id)

document = body()


