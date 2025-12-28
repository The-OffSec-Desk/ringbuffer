"""
Plugin system module
Provides plugin management, base classes, and example implementations.
"""

from plugins.base import KernelPlugin, PluginMetadata, PluginContext, PluginCapability
from plugins.manager import PluginManager

__all__ = [
    'KernelPlugin',
    'PluginMetadata',
    'PluginContext',
    'PluginCapability',
    'PluginManager',
]
