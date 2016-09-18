import copy
import bs4 as _BS4

from circular.platform.common.bs4 import NodeType


def dom_from_html(html):
    """
        Creates a DOM structure from :param:`html`
    """

    soup = _BS4.BeautifulSoup(html, "html.parser")
    if len(soup.contents) > 0:
        for ch in soup.children:
            if ch.type != NodeType.TEXT:
                return ch


def le(self, other):
    self.append(other)
_BS4.Tag.__le__ = le


def tp(self):
    if isinstance(self, _BS4.element.Comment):
        return NodeType.COMMENT
    elif isinstance(self, _BS4.element.NavigableString):
        return NodeType.TEXT
    elif isinstance(self, _BS4.element.Tag):
        return NodeType.ELEMENT
_BS4.Tag.type = property(tp)
_BS4.NavigableString.type = property(tp)
_BS4.Comment.type = property(tp)


def bind(self, event, handler):
    pass
_BS4.Tag.bind = bind


def clone(self):
    return copy.copy(self)
_BS4.Tag.clone = clone
_BS4.NavigableString.clone = clone
_BS4.Comment.clone = clone


class Document(_BS4.BeautifulSoup):

    def __init__(self):
        super().__init__("<html><body></body></html>", "html.parser")

    def __getitem__(self, selector):
        return self.select(selector)

    def __le__(self, other):
        self.append(other)

Tag = _BS4.Tag
