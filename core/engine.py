"""
Main Kernel Log Engine
Async event ingestion, normalization, and streaming with backpressure.
"""

import asyncio
import logging
from typing import AsyncIterator, Optional, Callable, Any
from collections import deque

from core.event import KernelEvent
from core.sources import DmesgSource, JournalctlSource, LogSource
from core.permissions import PermissionChecker
from core.errors import SourceUnavailableError


logger = logging.getLogger(__name__)


class KernelLogEngine:
    """
    High-performance async kernel log engine.
    - Non-blocking event ingestion
    - Backpressure-aware buffering
    - Pause/resume support
    - Multi-source fallback
    """
    
    def __init__(self, buffer_size: int = 10000):
        self.buffer_size = buffer_size
        self.buffer: deque[KernelEvent] = deque(maxlen=buffer_size)
        self.source: Optional[LogSource] = None
        self.running = False
        self.paused = False
        self.event_callbacks: list[Callable[[KernelEvent], Any]] = []
        self._stream_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """
        Initialize the engine, detect available sources.
        Returns True if at least one source is available.
        """
        available_sources = PermissionChecker.get_available_sources()
        
        if not available_sources:
            logger.error("No kernel log sources available")
            return False
        
        # Prefer dmesg, fallback to journalctl
        if 'dmesg' in available_sources:
            self.source = DmesgSource(buffer_size=self.buffer_size)
            logger.info("Using dmesg as primary source")
        elif 'journal' in available_sources:
            self.source = JournalctlSource(buffer_size=self.buffer_size)
            logger.info("Using journalctl as primary source")
        else:
            return False
        
        return True
    
    async def load_snapshot(self) -> list[KernelEvent]:
        """Load initial snapshot of kernel logs."""
        if not self.source:
            raise RuntimeError("Engine not initialized")
        
        try:
            events = await self.source.get_snapshot()
            self.buffer.extend(events)
            logger.info(f"Loaded {len(events)} events from snapshot")
            return events
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            raise
    
    async def start_streaming(self) -> None:
        """Start streaming live kernel logs."""
        if self.running:
            logger.warning("Engine already streaming")
            return
        
        if not self.source:
            raise RuntimeError("Engine not initialized")
        
        self.running = True
        self._stream_task = asyncio.create_task(self._run_stream())
        logger.info("Kernel log streaming started")
    
    async def stop_streaming(self) -> None:
        """Stop streaming and cleanup."""
        self.running = False
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        logger.info("Kernel log streaming stopped")
    
    async def _run_stream(self) -> None:
        """Internal stream runner."""
        try:
            async for event in self.source.stream_live():
                if not self.running:
                    break
                
                # Respect pause state
                while self.paused and self.running:
                    await asyncio.sleep(0.1)
                # Handle continuation/merged lines: if parser flagged this as continuation,
                # merge into the last event rather than creating a new event.
                is_cont = False
                try:
                    is_cont = bool(event.annotations.get('continuation'))
                except Exception:
                    is_cont = False

                if is_cont and len(self.buffer) > 0:
                    # Merge into last event
                    last = self.buffer[-1]
                    try:
                        last.message = (last.message or '') + '\n' + (event.message or '')
                        last.raw = (last.raw or '') + '\n' + (event.raw or '')
                        # forward merged annotations
                        last.annotations.update(getattr(event, 'annotations', {}) or {})
                    except Exception as e:
                        logger.debug(f"Failed to merge continuation event: {e}")

                    # Notify subscribers with the updated last event
                    for callback in self.event_callbacks:
                        try:
                            result = callback(last)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(f"Event callback error: {e}")

                    # do not append the continuation event separately
                    continue

                # Add to buffer
                self.buffer.append(event)

                # Notify subscribers
                for callback in self.event_callbacks:
                    try:
                        result = callback(event)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"Event callback error: {e}")
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Stream error: {e}")
            self.running = False
    
    def subscribe(self, callback: Callable[[KernelEvent], Any]) -> None:
        """Subscribe to events. Callback can be sync or async."""
        self.event_callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable[[KernelEvent], Any]) -> None:
        """Unsubscribe from events."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def pause(self) -> None:
        """Pause event streaming (buffer still fills)."""
        self.paused = True
    
    def resume(self) -> None:
        """Resume event streaming."""
        self.paused = False
    
    def get_buffer(self) -> list[KernelEvent]:
        """Get current buffer contents."""
        return list(self.buffer)
    
    def flush_buffer(self) -> None:
        """Clear the event buffer."""
        self.buffer.clear()
        logger.info("Event buffer flushed")
    
    async def shutdown(self) -> None:
        """Clean shutdown."""
        await self.stop_streaming()
        self.flush_buffer()
        logger.info("Engine shutdown complete")
