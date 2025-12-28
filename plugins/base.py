"""
Plugin Base Classes and Interfaces
Defines the contract all plugins must follow.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum

from core.event import KernelEvent


logger = logging.getLogger(__name__)


class PluginCapability(Enum):
    """Plugin capabilities flags."""
    ANALYZE_EVENTS = "analyze_events"
    PROVIDE_UI_PANEL = "provide_ui_panel"
    EMIT_ALERTS = "emit_alerts"
    ANNOTATE_EVENTS = "annotate_events"


@dataclass
class PluginMetadata:
    """Plugin metadata for discovery and version checking."""
    name: str
    version: str
    author: str
    description: str
    min_engine_version: str = "1.0"
    capabilities: set[PluginCapability] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = set()


@dataclass
class PluginContext:
    """
    Restricted context object passed to plugins.
    Provides safe access to core functionality without direct core access.
    """
    
    def register_annotation(self, event_id: str, text: str) -> None:
        """Register an annotation for an event."""
        raise NotImplementedError
    
    def emit_warning(self, text: str) -> None:
        """Emit a non-disruptive warning to the UI."""
        raise NotImplementedError
    
    def add_panel(self, widget: Any) -> None:
        """Register a UI panel (PySide6 QWidget)."""
        raise NotImplementedError
    
    def get_event_by_id(self, event_id: str) -> Optional[KernelEvent]:
        """Retrieve an event by ID."""
        raise NotImplementedError


class KernelPlugin(ABC):
    """
    Base class for all kernel log plugins.
    
    Plugins observe kernel events, analyze them, and optionally extend the UI.
    They must NEVER block the event stream or modify kernel state.
    """
    
    def __init__(self):
        self.metadata = self._get_metadata()
        self.context: Optional[PluginContext] = None
        self.logger = logging.getLogger(self.metadata.name)
    
    @abstractmethod
    def _get_metadata(self) -> PluginMetadata:
        """
        Return plugin metadata.
        Subclasses MUST implement this.
        """
        raise NotImplementedError
    
    async def on_load(self, context: PluginContext) -> bool:
        """
        Called when plugin is loaded into the system.
        
        Args:
            context: Restricted plugin context
        
        Returns:
            True if load successful, False to abort
        """
        self.context = context
        self.logger.info(f"{self.metadata.name} loaded")
        return True
    
    async def on_event(self, event: KernelEvent) -> None:
        """
        Process a kernel event.
        
        MUST NOT block. Can optionally annotate, emit warnings, etc.
        Exceptions are caught and logged automatically.
        
        Args:
            event: The kernel event to process
        """
        pass
    
    async def on_unload(self) -> None:
        """
        Called when plugin is unloaded.
        Perform cleanup here.
        """
        self.logger.info(f"{self.metadata.name} unloaded")
    
    def _safe_execute(self, func, *args, **kwargs) -> Optional[Any]:
        """
        Execute a function safely with exception handling.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Plugin execution error: {e}")
            return None
