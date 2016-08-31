"""
    The template submodule provides data-binding utilities.
"""
from .context import Context
from .tpl import Template, register_plugin, set_prefix
from .tags.tag import TagPlugin
