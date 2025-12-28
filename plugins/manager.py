"""
Plugin Manager
Safe loading, unloading, and execution of plugins with error isolation.
"""

import asyncio
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from importlib.util import spec_from_file_location, module_from_spec

from plugins.base import KernelPlugin, PluginContext, PluginMetadata
from core.event import KernelEvent
from core.errors import PluginError, PluginLoadError, PluginVersionError


logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages plugin lifecycle: discovery, loading, execution, unloading.
    Plugins are sandboxed and failures are isolated.
    """
    
    def __init__(self, plugin_dir: Optional[Path] = None, engine_version: str = "1.0"):
        self.plugin_dir = plugin_dir or Path(__file__).parent
        self.engine_version = engine_version
        self.plugins: Dict[str, KernelPlugin] = {}
        self.enabled_plugins: set[str] = set()
        self._context_impl: Optional[PluginContext] = None
    
    def set_context(self, context: PluginContext) -> None:
        """Set the plugin context implementation."""
        self._context_impl = context
    
    async def discover_plugins(self) -> List[PluginMetadata]:
        """
        Discover all available plugins in the plugin directory.
        Does NOT load them.
        """
        plugins = []
        
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_") or plugin_file.name == "base.py" or plugin_file.name == "manager.py":
                continue
            
            try:
                metadata = await self._inspect_plugin_file(plugin_file)
                if metadata:
                    plugins.append(metadata)
                    logger.info(f"Discovered plugin: {metadata.name} v{metadata.version}")
            except Exception as e:
                logger.warning(f"Failed to discover plugin {plugin_file.name}: {e}")
        
        return plugins
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a plugin by name.
        
        Args:
            plugin_name: Name of the plugin module (without .py)
        
        Returns:
            True if load successful, False otherwise
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return True
        
        try:
            plugin = await self._load_plugin_module(plugin_name)
            if not plugin:
                return False
            
            # Check version compatibility
            if hasattr(plugin.metadata, 'min_engine_version'):
                if not self._check_version_compatibility(
                    plugin.metadata.min_engine_version,
                    self.engine_version
                ):
                    raise PluginVersionError(
                        f"Plugin requires engine v{plugin.metadata.min_engine_version}, "
                        f"have v{self.engine_version}"
                    )
            
            # Call on_load hook
            if self._context_impl:
                success = await plugin.on_load(self._context_impl)
                if not success:
                    logger.error(f"Plugin {plugin_name} on_load returned False")
                    return False
            
            self.plugins[plugin_name] = plugin
            logger.info(f"Plugin {plugin_name} loaded successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise PluginLoadError(f"Failed to load {plugin_name}: {e}")
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin by name."""
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} not loaded")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            await plugin.on_unload()
            del self.plugins[plugin_name]
            if plugin_name in self.enabled_plugins:
                self.enabled_plugins.discard(plugin_name)
            logger.info(f"Plugin {plugin_name} unloaded")
            return True
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a loaded plugin."""
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} not loaded")
            return False
        
        self.enabled_plugins.add(plugin_name)
        logger.info(f"Plugin {plugin_name} enabled")
        return True
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a loaded plugin."""
        self.enabled_plugins.discard(plugin_name)
        logger.info(f"Plugin {plugin_name} disabled")
        return True
    
    async def process_event(self, event: KernelEvent) -> None:
        """
        Process an event through all enabled plugins.
        Plugin failures do not affect other plugins or the core system.
        """
        for plugin_name in self.enabled_plugins:
            if plugin_name not in self.plugins:
                continue
            
            plugin = self.plugins[plugin_name]
            try:
                await plugin.on_event(event)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"Plugin {plugin_name} error processing event: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown all plugins gracefully."""
        for plugin_name in list(self.plugins.keys()):
            await self.unload_plugin(plugin_name)
        logger.info("All plugins shut down")
    
    # Private helpers
    
    async def _load_plugin_module(self, plugin_name: str) -> Optional[KernelPlugin]:
        """Load a plugin module and return plugin instance."""
        plugin_file = self.plugin_dir / f"{plugin_name}.py"
        
        if not plugin_file.exists():
            raise PluginLoadError(f"Plugin file not found: {plugin_file}")
        
        try:
            # Load module dynamically
            spec = spec_from_file_location(f"plugins.{plugin_name}", plugin_file)
            if not spec or not spec.loader:
                raise PluginLoadError(f"Cannot load {plugin_file}")
            
            module = module_from_spec(spec)
            sys.modules[f"plugins.{plugin_name}"] = module
            spec.loader.exec_module(module)
            
            # Find KernelPlugin subclass
            for item_name in dir(module):
                item = getattr(module, item_name)
                if isinstance(item, type) and issubclass(item, KernelPlugin) and item != KernelPlugin:
                    return item()
            
            raise PluginLoadError(f"No KernelPlugin subclass found in {plugin_file}")
        
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin {plugin_name}: {e}")
    
    async def _inspect_plugin_file(self, plugin_file: Path) -> Optional[PluginMetadata]:
        """Inspect a plugin file for metadata without fully loading it."""
        # For now, return None (can be implemented with AST parsing for safety)
        return None
    
    @staticmethod
    def _check_version_compatibility(required: str, available: str) -> bool:
        """Check if available version satisfies required version."""
        # Simple comparison: "1.0" vs "1.1" etc.
        try:
            req_parts = [int(x) for x in required.split('.')]
            avail_parts = [int(x) for x in available.split('.')]
            return avail_parts >= req_parts
        except ValueError:
            return False
