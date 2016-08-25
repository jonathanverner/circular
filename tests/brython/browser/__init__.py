import sys
sys.modules['browser'] = __import__('tests.brython.browser')
from . import console, document, html, timer
sys.modules['browser'].html = html
sys.modules['browser'].console = console
sys.modules['browser'].document = document
sys.modules['browser'].timer = timer
