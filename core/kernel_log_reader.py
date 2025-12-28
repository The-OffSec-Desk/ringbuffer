"""
Core kernel log reading logic
"""

import subprocess
import re
from datetime import datetime
from typing import List, Dict, Optional
import asyncio
import logging
from core.engine import KernelLogEngine
from core.event import KernelEvent
import threading

logger = logging.getLogger(__name__)


class KernelLogReader:
    """Handles reading and parsing kernel logs"""

    def __init__(self):
        self.engine = KernelLogEngine(buffer_size=10000)
        self.engine_initialized = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._engine_thread: Optional[threading.Thread] = None
        self._engine_loop: Optional[asyncio.AbstractEventLoop] = None
        self._last_buffer_index = 0
        self.last_log_timestamp = None
        self.severity_map = {
            0: "EMERG",
            1: "ALERT",
            2: "CRIT",
            3: "ERR",
            4: "WARN",
            5: "NOTICE",
            6: "INFO",
            7: "DEBUG",
        }

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent kernel logs - synchronous API."""
        if not self.engine_initialized:
            self._initialize_engine_sync()

        try:
            logs = self._run_async(self.engine.load_snapshot())
            # Convert KernelEvent to dict for UI compatibility
            return [event.to_dict() for event in logs[-limit:]]
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return self._get_mock_logs()

    def get_new_logs(self) -> List[Dict]:
        """Get new logs since last call."""
        if not self.engine_initialized:
            return []

        try:
            events = self.engine.get_buffer()
            # Return only events that haven't been reported yet
            if self._last_buffer_index < 0:
                self._last_buffer_index = 0

            new_events = events[self._last_buffer_index:]
            self._last_buffer_index = len(events)
            return [event.to_dict() for event in new_events]
        except Exception as e:
            logger.error(f"Failed to get new logs: {e}")
            return []

    def clear_buffer(self) -> bool:
        """Clear kernel buffer (requires elevated privileges)."""
        try:
            self.engine.flush_buffer()
            return True
        except Exception:
            return False

    def _initialize_engine_sync(self) -> None:
        """Initialize the async engine synchronously."""
        try:
            if self._run_async(self.engine.initialize()):
                self.engine_initialized = True
                logger.info("Kernel log engine initialized")

                # Log which source is active
                if self.engine.source:
                    source_name = self.engine.source.__class__.__name__
                    logger.info(f"Active source: {source_name}")

                # Start engine streaming in a background thread running its own event loop
                if not self._engine_thread:
                    def _runner():
                        loop = asyncio.new_event_loop()
                        self._engine_loop = loop
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self.engine.start_streaming())
                            loop.run_forever()
                        finally:
                            # cleanup
                            pending = asyncio.all_tasks(loop=loop)
                            for t in pending:
                                t.cancel()
                            try:
                                loop.run_until_complete(loop.shutdown_asyncgens())
                            except Exception:
                                pass
                            loop.close()

                    t = threading.Thread(target=_runner, daemon=True)
                    t.start()
                    self._engine_thread = t
            else:
                logger.error("Failed to initialize kernel log engine")
        except Exception as e:
            logger.error(f"Engine initialization error: {e}")

    def _run_async(self, coro):
        """Helper to run async code from sync context."""
        try:
            if self.loop is None or not self.loop.is_running():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
            return self.loop.run_until_complete(coro)
        except RuntimeError:
            # If in event loop context, create new one
            return asyncio.run(coro)

    def _parse_dmesg_output(self, output: str) -> List[Dict]:
        """Parse dmesg output into structured format"""
        logs = []

        # Pattern: [timestamp] severity subsystem: message
        pattern = r"\[([^\]]+)\]\s+(\w+)\s+(\w+):\s+(.*)"

        for line in output.strip().split("\n"):
            match = re.match(pattern, line)
            if match:
                timestamp, severity, subsystem, message = match.groups()

                logs.append(
                    {
                        "timestamp": timestamp,
                        "severity": severity.upper(),
                        "subsystem": subsystem.upper(),
                        "message": message,
                        "cpu": "N/A",
                        "pid": "N/A",
                    }
                )

        return logs

    def _get_mock_logs(self) -> List[Dict]:
        """Generate mock kernel logs for demonstration"""
        mock_logs = [
            {
                "event_id": "1",
                "timestamp_monotonic": 0.000000,
                "timestamp_realtime": None,
                "severity": "INFO",
                "subsystem": "KERNEL",
                "message": "Linux version 5.15.0-56-generic",
                "raw": "[0.000000] Linux version 5.15.0-56-generic",
                "source": "dmesg",
                "cpu": 0,
                "pid": 0,
                "annotations": {},
                "plugin_metadata": {},
            }
        ]
        return mock_logs
