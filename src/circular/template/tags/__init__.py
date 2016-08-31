"""
    Provides the abstract TagPlugin base class and some predefined plugins:

      - ``TextPlugin`` (for taking care of interpolated text (e.g. ``{{ name }} {{ surname }}``))
      - ``InterpolatedAttrsPlugin`` (for taking care of interpolated attribute elements (e.g. ``<span class='{{ css_classes }}'>``))
      - ``GenericTagPlugin`` (for taking care of normal html tags)
      - ``For`` plugin (looping construct)
      - ``Model`` plugin (bi-directional databinding for input elements)
      - ``Click`` plugin (for binding context-methods to the click event)

"""
from .tag import TagPlugin
from .textplugin import TextPlugin
from .generictag import GenericTagPlugin
from .interpolatedattrs import InterpolatedAttrsPlugin
from .For import For
from .model import Model
from .event import Click
