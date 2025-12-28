"""
Kernel Event Definition
Structured event object for all kernel log messages.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4


@dataclass
class KernelEvent:
    """
    Normalized kernel event object.
    All downstream components consume only KernelEvent objects.
    """
    
    timestamp_monotonic: Optional[float]  # Monotonic time (seconds)
    timestamp_realtime: Optional[datetime]  # Wall-clock time
    severity: str  # EMERG, ALERT, CRIT, ERR, WARN, NOTICE, INFO, DEBUG
    subsystem: Optional[str]  # kernel, memory, usb, etc.
    message: str  # Parsed message text
    raw: str  # Original raw log line
    source: str  # 'dmesg' or 'journal'
    
    # Metadata
    event_id: str = field(default_factory=lambda: str(uuid4()))
    cpu: Optional[int] = None
    pid: Optional[int] = None
    annotations: dict = field(default_factory=dict)
    
    # Plugin data (added during processing)
    plugin_metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'timestamp_monotonic': self.timestamp_monotonic,
            'timestamp_realtime': self.timestamp_realtime.isoformat() if self.timestamp_realtime else None,
            'severity': self.severity,
            'subsystem': self.subsystem,
            'message': self.message,
            'raw': self.raw,
            'source': self.source,
            'cpu': self.cpu,
            'pid': self.pid,
            'annotations': self.annotations,
            'plugin_metadata': self.plugin_metadata,
        }
