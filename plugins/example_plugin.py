"""
Example Plugins for Kernel Event Processing
Demonstrates the plugin API and best practices.
"""

import asyncio
import re
from typing import Optional
from plugins.base import KernelPlugin, PluginMetadata, PluginContext, PluginCapability
from core.event import KernelEvent


class USBWatcherPlugin(KernelPlugin):
    """
    USB Device Watcher
    Detects and annotates USB device connection/disconnection events.
    """
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="USB Watcher",
            version="1.0",
            author="Kernel Log Team",
            description="Monitor and annotate USB device events",
            capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.ANNOTATE_EVENTS}
        )
    
    async def on_load(self, context: PluginContext) -> bool:
        self.context = context
        self.logger.info("USB Watcher initialized")
        return True
    
    async def on_event(self, event: KernelEvent) -> None:
        """Detect USB events and annotate them."""
        if not event.subsystem or 'usb' not in event.subsystem.lower():
            return
        
        message = event.message.lower()
        
        # Detect USB device connection
        if 'new' in message and 'device' in message:
            await self._annotate_event(event, "🔌 USB device connected")
        
        # Detect USB disconnection
        elif 'disconnect' in message or 'removed' in message:
            await self._annotate_event(event, "❌ USB device disconnected")
        
        # Detect USB errors
        elif 'error' in message or 'failed' in message:
            await self._annotate_event(event, "⚠️ USB error detected")
    
    async def _annotate_event(self, event: KernelEvent, annotation: str) -> None:
        """Helper to annotate an event."""
        if self.context:
            self.context.register_annotation(event.event_id, annotation)


class OOMDetectorPlugin(KernelPlugin):
    """
    Out-Of-Memory Detector
    Identifies kernel OOM killer events and memory pressure situations.
    """
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="OOM Detector",
            version="1.0",
            author="Kernel Log Team",
            description="Detect and analyze out-of-memory killer events",
            capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.EMIT_ALERTS}
        )
    
    async def on_load(self, context: PluginContext) -> bool:
        self.context = context
        self.oom_count = 0
        self.logger.info("OOM Detector initialized")
        return True
    
    async def on_event(self, event: KernelEvent) -> None:
        """Detect OOM events and emit warnings."""
        message = event.message.lower()
        
        # Detect OOM killer invocation
        if 'oom killer' in message or 'oom-kill' in message:
            self.oom_count += 1
            annotation = f"💀 OOM Kill #{self.oom_count}"
            
            if self.context:
                self.context.register_annotation(event.event_id, annotation)
                self.context.emit_warning(
                    f"Out-of-memory killer triggered (#{self.oom_count})"
                )
        
        # Detect memory pressure warnings
        elif 'memory' in message and ('pressure' in message or 'low' in message):
            if self.context:
                self.context.register_annotation(event.event_id, "⚠️ Memory pressure")


class KASANDecoderPlugin(KernelPlugin):
    """
    KASAN (Kernel Address Sanitizer) Decoder
    Parses and annotates KASAN bug detection events.
    Currently a stub - full implementation would parse KASAN output.
    """
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="KASAN Decoder",
            version="1.0",
            author="Kernel Log Team",
            description="Decode and analyze KASAN memory safety violations",
            capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.ANNOTATE_EVENTS}
        )
    
    async def on_load(self, context: PluginContext) -> bool:
        self.context = context
        self.logger.info("KASAN Decoder initialized")
        return True
    
    async def on_event(self, event: KernelEvent) -> None:
        """Detect KASAN errors."""
        message = event.message
        
        # KASAN patterns
        if 'kasan' in message.lower():
            bug_type = self._extract_kasan_type(message)
            annotation = f"🐛 KASAN: {bug_type}"
            
            if self.context:
                self.context.register_annotation(event.event_id, annotation)
    
    def _extract_kasan_type(self, message: str) -> str:
        """Extract KASAN bug type from message."""
        patterns = {
            'use-after-free': r'use-after-free',
            'double-free': r'double-free',
            'out-of-bounds': r'out-of-bounds',
            'buffer-overflow': r'buffer-overflow',
            'invalid-free': r'invalid-free',
        }
        
        for bug_type, pattern in patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return bug_type.upper()
        
        return "UNKNOWN"


class SecurityModuleMonitorPlugin(KernelPlugin):
    """
    Security Module Monitor
    Tracks AppArmor, SELinux, and other LSM (Linux Security Module) events.
    """
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Security Module Monitor",
            version="1.0",
            author="Kernel Log Team",
            description="Monitor LSM (AppArmor, SELinux) enforcement events",
            capabilities={PluginCapability.ANALYZE_EVENTS, PluginCapability.ANNOTATE_EVENTS}
        )
    
    async def on_load(self, context: PluginContext) -> bool:
        self.context = context
        self.denial_count = 0
        self.logger.info("Security Module Monitor initialized")
        return True
    
    async def on_event(self, event: KernelEvent) -> None:
        """Monitor security module events."""
        message = event.message.lower()
        
        # AppArmor denials
        if 'apparmor' in message and 'denied' in message:
            self.denial_count += 1
            annotation = f"🔒 AppArmor denial #{self.denial_count}"
            if self.context:
                self.context.register_annotation(event.event_id, annotation)
        
        # SELinux denials
        elif 'selinux' in message and 'denied' in message:
            annotation = "🔐 SELinux denial"
            if self.context:
                self.context.register_annotation(event.event_id, annotation)
