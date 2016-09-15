from browser import document, window
from javascript import JSObject


def dom_from_html(html):
    """
        Creates a DOM structure from :param:`html`
    """
    div = window.document.createElement('div')
    div.innerHTML = html
    return div.children


class Tag:
    def __init__(self, element_or_html):
        if isinstance(element_or_html, str):
            element_or_html = dom_from_html(element_or_html)[0].elt
        self._elt = JSObject(element_or_html)
        if self._elt.nodeType == self._elt.ELEMENT_NODE:
            self.name = self._elt.tagName

    def get(self, key):
        return self._elt.getAttribute(key)

    @property
    def parent(self):
        if self._elt.parentElement is None:
            return Document()
        else:
            return Tag(self._elt.parentNode.elt)

    @property
    def parents(self):
        parent = self.parent
        while isinstance(parent, Tag):
            yield parent
            parent = parent.parent

    @property
    def next_sibling(self):
        return Tag(self._elt.nextSibling)

    @property
    def next_siblings(self):
        sib = self.next_sibling
        while sib is not None:
            yield sib
            sib = sib.next_sibling

    @property
    def previous_sibling(self):
        return Tag(self._elt.previousSibling)

    @property
    def previous_siblings(self):
        sib = self.previous_sibling
        while sib is not None:
            yield sib
            sib = sib.previous_sibling

    @property
    def next_element(self):
        return Tag(self._elt.nextElementSibling)

    @property
    def next_elements(self):
        sib = self.next_element
        while sib is not None:
            yield sib
            sib = sib.next_element

    @property
    def previous_element(self):
        return Tag(self._elt.previousElementSibling)

    @property
    def previous_elements(self):
        sib = self.previous_element
        while sib is not None:
            yield sib
            sib = sib.previous_element

    @property
    def contents(self):
        return [Tag(ch) for ch in self._elt.children]

    @property
    def children(self):
        return iter(self.contents())

    @property
    def descendants(self):
        for ch in self._elt.children:
            t = Tag(ch)
            yield t
            for d in t.descendants:
                yield d

    def append(self, tag_or_text):
        if isinstance(tag_or_text, str):
            self._elt.appendChild(dom_from_html(tag_or_text)[0].elt)
        else:
            self._elt.appendChild(tag_or_text._elt)

    def insert(self, pos, tag_or_text):
        if isinstance(tag_or_text, str):
            self._elt.insertBefore(dom_from_html(tag_or_text)[0].elt, self._elt.children[pos])
        else:
            self._elt.insertBefore(tag_or_text._elt, self._elt.children[pos])

    def __getitem__(self, key):
        ret = self._elt.getAttribute(key)
        if ret is None:
            raise KeyError(key)
        else:
            if key in ['class', 'rev', 'accept-charset', 'headers', 'accesskey']:
                ret = ret.split(' ')
                if len(ret) == 1:
                    ret = ret[0]
            return ret

    def __setitem__(self, key, value):
        if isinstance(value, list):
            value = ' '.join(list)
        self._elt.setAttribute(key, value)


def _test_attrs(tag, attrs):
    for (attr, val) in attrs.items():
        if not tag.get(attr) == val:
            return False
    return True


class Document:
    def __init__(self):
        pass

    def find_all(self, filter, attrs=None, limit=0, recursive=True, class_=None, **kwargs):
        ret = []
        count = 0
        attr_selector = ''
        if attrs is not None:
            kwargs.update(attrs)
        if class_ is not None:
            kwargs['class'] = class_
        if len(kwargs) > 0:
            for (attr, val) in kwargs.items():
                attr_selector += '['+attr+'='+str(val)+']'
        if isinstance(filter, list):
            filter = ','.join(filter)
        if isinstance(filter, str):
            ret = self[str+attr_selector]
            if limit > 0:
                ret = ret[:limit]
        elif callable(filter):
            for tag in self[attr_selector]:
                if filter(tag):
                    ret.append(tag)
                    count += 1
                if limit > 0 and count > limit:
                    break
        return ret

    def find(self, name, attrs=None, **kwargs):
        if attrs is not None:
            kwargs.update(attrs)
        attr_selector = ''
        if len(kwargs) > 0:
            for (attr, val) in kwargs.items():
                attr_selector += '['+attr+'='+str(val)+']'
        if isinstance(filter, list):
            filter = ','.join(filter)
        if isinstance(filter, str):
            ret = window.document.querySelector(str)
            if ret is None:
                return None
            else:
                return Tag(ret)
        elif callable(filter):
            for tag in self[attr_selector]:
                if filter(tag):
                    return tag
        return None

    @property
    def contents(self):
        return [Tag(ch.elt) for ch in window.document.children]

    @property
    def children(self):
        return iter(self.contents())

    @property
    def descendants(self):
        for ch in self._elt.children:
            t = Tag(ch)
            yield t
            for d in t.descendants:
                yield d

    def select(self, selector):
        return self[selector]

    def __getitem__(self, selector):
        return [Tag(l) for l in window.document.querySelectorAll(key)]

    def __getattr__(self, name):
        return self.find(name)



