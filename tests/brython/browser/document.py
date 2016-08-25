def createComment(comm):
    return Comment(comm)

class MockAttr:
    def __init__(self,name,val=None):
        self.name = name
        self.value = val

    def clone(self):
        return MockAttr(self.name,self.value)

    def __repr__(self):
        return "<MockAttr("+self.name+","+self.value+")>"

class attrlist(list):
    def __getattr__(self, name):
        for a in self:
            if a.name == name:
                return a.value
        return super().__getattribute__(name)

class MockElement:
    def __init__(self,tag_name):
        self.tag_name = tag_name
        self.attributes = attrlist([])
        self.children = []
        self.elt = MockDomElt()
        self.nodeName = tag_name
        self.parent = None
        self.text = ''

    def clone(self):
        ret = MockElement(self.tag_name)
        for attr in self.attributes:
            ret.attributes.append(attr.clone())
        for ch in self.children:
            ret <= ch.clone()
        ret.text = self.text
        return ret

    def clear(self):
        self.elt.clear()
        self.children = []

    def insertBefore(self,domnode,before):
        pos = self.children.index(before)
        self.elt.insertBefore(domnode.elt,self.children[pos].elt)
        self.children.insert(pos,domnode)

    def replaceChild(self,replace_with,replace_what):
        pos = self.children.index(replace_what)
        self.elt.replaceChild(replace_with.elt,replace_what.elt)
        self.children[pos]=replace_with

    def __setattr__(self, name, value):
        if name in ['tag_name','attributes','children','elt','nodeName','parent','text']:
            return super().__setattr__(name,value)
        else:
            for attr in self.attributes:
                if attr.name == name:
                    attr.value = value
                    return
            self.attributes.append(MockAttr(name,value))

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
        if isinstance(other,list):
            for o in other:
                self.children.append(o)
                self.elt.appendChild(o)
        else:
            self.children.append(other)
            self.elt.appendChild(other.elt)

class Comment(MockElement):
    def __init__(self, text):
        super().__init__('comment')
        self.text = text

class MockDomElt:
    def __init__(self,parent=None):
        self.parent = parent
        self.children = []

    def clear(self):
        for ch in self.children:
            ch.parent = None
        self.children = []

    def appendChild(self,ch):
        self.children.append(ch)
        ch.parent = self

    def replaceChild(self,replace_with,replace_what):
        pos = self.children.index(replace_what)
        repl = self.children[pos]
        repl.parent = None
        self.children[pos] = replace_with
        replace_with.parent = self

    def insertBefore(self,ch,reference):
        pos = self.children.index(ch)
        self.children.insert(pos,ch)
        ch.parent = self
        self.children.insert(pos,ch)

