from src.circular.utils.events import EventMixin
from src.circular.template.context import Context


class MockAttr:
    def __init__(self, name, val=None):
        self.name = name
        self.value = val

    def clone(self):
        return MockAttr(self.name, self.value)

    def __repr__(self):
        return "<MockAttr("+self.name+","+self.value+")>"


class attrlist(list):
    def __getattr__(self, name):
        for a in self:
            if a.name == name:
                return a.value
        return super().__getattribute__(name)


class MockElement(EventMixin):
    _LAST_ID = 0

    def __init__(self, tagName, **kwargs):
        super().__init__()
        self.tagName = tagName
        self.attributes = attrlist([])
        self.children = []
        self.elt = MockDomElt(self)
        self.nodeName = tagName
        self.parent = None
        self._text = ''
        if self.tagName == 'input' or self.tagName == 'textarea':
            self.value = ''
        for (arg, value) in kwargs.items():
            self.setAttribute(arg, kwargs[arg])

    @property
    def text(self):
        ret = self._text
        for ch in self.children:
            ret += ch.text
        return ret

    @text.setter
    def text(self, val):
        self._text = val

    @property
    def id(self):
        try:
            return self.attributes[self._indexAttr('id')].value
        except:
            self.id = str(MockElement._LAST_ID)
            MockElement._LAST_ID += 1
            return str(MockElement._LAST_ID-1)

    @id.setter
    def set_id(self, value):
        self.attributes[self._indexAttr('id')].value = value

    def click(self):
        self.emit('click', {'type': 'click', 'target': self})

    def clone(self):
        ret = MockElement(self.tagName)
        for attr in self.attributes:
            ret.attributes.append(attr.clone())
        for ch in self.children:
            ret <= ch.clone()
        ret._text = self._text
        return ret

    def clear(self):
        self.elt.clear()
        self.children = []

    def _indexAttr(self, name):
        pos = 0
        for attr in self.attributes:
            if attr.name == name:
                return pos
            pos += 1
        return -1

    def removeAttribute(self, name):
        pos = self._indexAttr(name)
        if pos > -1:
            del self.attributes[pos]

    def setAttribute(self, name, value):
        if name == 'value':
            self.value = value
            self.emit('input', Context({'target': self}))
        else:
            pos = self._indexAttr(name)
            if pos > -1:
                self.attributes[pos].value = value
            else:
                self.attributes.append(MockAttr(name, value))

    def insertBefore(self, domnode, before):
        pos = self.children.index(before)
        self.elt.insertBefore(domnode.elt, self.children[pos].elt)
        self.children.insert(pos, domnode)

    def replaceChild(self, replace_with, replace_what):
        pos = self.children.index(replace_what)
        self.elt.replaceChild(replace_with.elt, replace_what.elt)
        self.children[pos] = replace_with
        replace_with.parent = self
        replace_what.parent = None

    def _findChild(self, id):
        for ch in self.children:
            if ch.id == id:
                return ch
            ret = ch._findChild(id)
            if ret is not None:
                return ret
        return None

    def __getattr__(self, attr):
        if attr == 'value':
            pos = self._indexAttr(attr)
            return self.attributes[pos].value
        return super().__getattribute__(attr)

    def __setattr__(self, name, value):
        if name in ['tagName', 'attributes', 'children', 'elt', 'nodeName', 'parent', 'text', 'value'] or name.startswith('_'):
            return super().__setattr__(name, value)
        else:
            for attr in self.attributes:
                if attr.name == name:
                    attr.value = value
                    return
            self.attributes.append(MockAttr(name, value))

    def __delattr__(self, key):
        pos = -1
        for attr in self.attributes:
            pos += 1
            if attr.name == key:
                break
        if pos > -1:
            del self.attributes[pos]
        else:
            raise KeyError()

    def __le__(self, other):
        if isinstance(other, list):
            for o in other:
                o.parent = self
                self.children.append(o)
                self.elt.appendChild(o)
        else:
            other.parent = self
            self.children.append(other)
            self.elt.appendChild(other.elt)

    def __repr__(self):
        ret = "<"+self.tagName
        if len(self.attributes) > 0:
            ret += " "+" ".join([a.name+"='"+str(a.value)+"'" for a in self.attributes])
        ret += ">"
        return ret


class MockDomElt:
    def __init__(self, node, parent=None):
        self.parent = parent
        self.children = []
        self.node = node

    def clear(self):
        for ch in self.children:
            ch.parent = None
        self.children = []

    def appendChild(self, ch):
        self.children.append(ch)
        ch.parent = self

    def replaceChild(self, replace_with, replace_what):
        pos = self.children.index(replace_what)
        repl = self.children[pos]
        repl.parent = None
        self.children[pos] = replace_with
        replace_with.parent = self

    def insertBefore(self, ch, reference):
        pos = self.children.index(ch)
        self.children.insert(pos, ch)
        ch.parent = self
        self.children.insert(pos, ch)


class COMMENT(MockElement):
    def __init__(self, text=None, **kwargs):
        super().__init__('comment', **kwargs)
        self._comment_text = text


class SPAN(MockElement):
    def __init__(self, **kwargs):
        super().__init__('span', **kwargs)
