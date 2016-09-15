from bs4 import BeautifulSoup, Tag


def dom_from_html(html):
    """
        Creates a DOM structure from :param:`html`
    """

    soup = BeautifulSoup(html, "html.parser")
    return soup.contents[0]

def le(self, other):
    self.append(other)
Tag.__le__ = le




class doc(BeautifulSoup):

    def __init__(self):
        super().__init__("<html><body></body></html>", "parser.html")

    def __getitem__(self, selector):
        return self.select(selector)

    def __le__(self, other):
        self.append(other)




