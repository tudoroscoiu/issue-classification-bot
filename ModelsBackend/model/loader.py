"""Simple plugin loader"""

import importlib

class PluginLoader:
    """Plugin loader class"""

    @staticmethod
    def initialize(self) -> None:
        """Initialize plugin loader"""

def import_module(module_name: str) -> PluginLoader:
    return importlib.import_module(module_name) # type: ignore

def load_plugin(plugin_name: list[str]) -> None:
    """Load plugin"""
    for plugin in plugin_name:
        plugin_module = import_module(plugin)
        plugin_module.initialize()
