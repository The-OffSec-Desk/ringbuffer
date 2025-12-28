"""
Kernel log message parsing and event normalization.

This module provides a robust KernelLogParser implementation for converting
raw kernel log lines (from dmesg or journalctl) into normalized KernelEvent objects.
Handles multiple log formats including timestamped entries, kernel prefix formats,
and process-based messages.
"""

import re
import logging
import time
from datetime import datetime
from typing import Optional
from core.event import KernelEvent


logger = logging.getLogger(__name__)


# Calculate boot time for monotonic-to-realtime timestamp conversion.
# Prefer reading /proc/stat btime (epoch) when available; fall back to
# time.time() - time.monotonic() as an approximation.
BOOT_TIME = None
try:
    try:
        with open('/proc/stat', 'r') as f:
            for ln in f:
                if ln.startswith('btime'):
                    parts = ln.split()
                    if len(parts) >= 2:
                        BOOT_TIME = int(parts[1])
                    break
    except Exception:
        BOOT_TIME = None

    if BOOT_TIME is None:
        BOOT_TIME = time.time() - time.monotonic()
except Exception as e:
    logger.warning(f"Failed to calculate BOOT_TIME: {e}")
    BOOT_TIME = None


class KernelLogParser:
    """
    Parser for kernel log messages into normalized KernelEvent objects.
    
    Supports multiple kernel log formats:
    - Standard dmesg: [timestamp] subsystem: message
    - Process format: [timestamp] process[pid]: message
    - Kernel prefix: <level>subsystem: message
    - Plain messages without timestamps
    
    Features:
    - Automatic severity inference from message content
    - Monotonic to realtime timestamp conversion
    - CPU and PID extraction
    - Continuation line detection (stack traces, hex dumps)
    - Subsystem and process identification
    """

    # Kernel severity level mapping (0=highest priority, 7=lowest)
    SEVERITY_LEVELS = {
        0: 'EMERG',    # System is unusable
        1: 'ALERT',    # Action must be taken immediately
        2: 'CRIT',     # Critical conditions
        3: 'ERR',      # Error conditions
        4: 'WARN',     # Warning conditions
        5: 'NOTICE',   # Normal but significant
        6: 'INFO',     # Informational
        7: 'DEBUG',    # Debug-level messages
    }

    # Reverse mapping for severity lookup
    SEVERITY_TO_LEVEL = {v: k for k, v in SEVERITY_LEVELS.items()}

    # Regular expression patterns
    DMESG_PATTERN = re.compile(
        r'^\[\s*(?P<timestamp>[\d.]+)\]\s+(?P<rest>.*)$'
    )
    
    PROCESS_PATTERN = re.compile(
        r'^(?P<process>[^\[\]:]+)\[(?P<pid>\d+)\]:\s*(?P<message>.*)$'
    )

    KERNEL_PREFIX = re.compile(
        r'^<(\d)>(?:(?P<subsystem>[^:>\s]+)[:.\s]+)?(.*)$'
    )

    CPU_PATTERNS = [
        re.compile(r'on CPU (?P<cpu>\d+)', re.I),
        re.compile(r'CPU[:#\s]+(?P<cpu>\d+)', re.I)
    ]

    # Markers that indicate continuation lines
    CONTINUATION_MARKERS = [
        'Code:', 'Backtrace', 'Call Trace', 'Call trace',
        'EIP', 'RIP', 'RSP', '\t'
    ]

    @classmethod
    def parse_dmesg_line(cls, line: str, source: str = 'dmesg') -> Optional[KernelEvent]:
        """
        Parse a kernel log line into a KernelEvent object.
        
        Args:
            line: Raw kernel log line to parse
            source: Source identifier (e.g., 'dmesg', 'journalctl')
        
        Returns:
            KernelEvent object if parsing succeeds, None otherwise
            
        Examples:
            >>> parser.parse_dmesg_line('[123.456] usb 1-1: new device')
            >>> parser.parse_dmesg_line('[102484.883686] zsh[2481341]: segfault')
            >>> parser.parse_dmesg_line('<6>kernel: Out of memory')
        """
        try:
            if not line:
                return None

            # Preserve original line for raw field
            raw = line.rstrip('\n')
            text = line.strip()
            
            if not text:
                return None

            # Attempt to parse timestamped dmesg format first
            match = cls.DMESG_PATTERN.match(text)
            if not match:
                # Fall back to kernel prefix format without timestamp
                return cls._parse_kernel_prefix(text, source)

            # Extract components from matched pattern
            timestamp_mono = cls._parse_timestamp(match.group('timestamp'))
            rest = match.group('rest').strip()

            # Check for inline kernel priority prefix: <N>message
            severity = None
            priority_match = re.match(r'^<(?P<level>\d)>(?P<rest>.*)$', rest)
            
            if priority_match:
                try:
                    level = int(priority_match.group('level'))
                    severity = cls.SEVERITY_LEVELS.get(level)
                except (ValueError, AttributeError):
                    pass
                rest = priority_match.group('rest').strip()

            # Initialize extraction variables
            subsystem = None
            pid = None
            message = rest

            # Attempt to extract process[pid]: message format
            process_match = cls.PROCESS_PATTERN.match(rest)
            
            if process_match:
                subsystem = process_match.group('process')
                try:
                    pid = int(process_match.group('pid'))
                except (ValueError, TypeError):
                    pid = None
                message = process_match.group('message')
            else:
                # Try to extract subsystem: message format
                # Limit colon search to avoid false matches deep in message
                colon_idx = rest.find(':')
                
                if 0 < colon_idx < 50:
                    potential_subsystem = rest[:colon_idx].strip()
                    
                    # Validate subsystem name characteristics
                    if (len(potential_subsystem) < 30 and 
                        ' ' not in potential_subsystem and
                        potential_subsystem):
                        subsystem = potential_subsystem
                        message = rest[colon_idx + 1:].strip()

            # Infer severity from message content if not set by prefix
            if not severity:
                severity = cls._infer_severity(message)
            
            # Normalize severity to standard format
            severity = cls._normalize_severity(severity) if severity else 'INFO'

            # Detect continuation lines (stack traces, hex dumps, etc.)
            continuation = cls._is_continuation_line(message)

            # Build annotations dictionary
            annotations = {}
            if continuation:
                annotations['continuation'] = True

            # Convert monotonic timestamp to realtime (wall-clock)
            if timestamp_mono is not None and BOOT_TIME is not None:
                try:
                    ts_rt = datetime.fromtimestamp(BOOT_TIME + float(timestamp_mono))
                except (OSError, OverflowError, ValueError):
                    ts_rt = datetime.now()
            else:
                ts_rt = datetime.now()

            # Extract CPU information from message
            cpu = cls._extract_cpu(message)

            # Construct and return KernelEvent
            return KernelEvent(
                timestamp_monotonic=timestamp_mono,
                timestamp_realtime=ts_rt,
                severity=severity,
                subsystem=subsystem or 'KERNEL',
                message=message,
                raw=raw,
                source=source,
                pid=pid,
                annotations=annotations,
                cpu=cpu,
            )

        except Exception as e:
            logger.warning(f"Failed to parse dmesg line: {repr(line[:100])} - {e}")
            return None

    @classmethod
    def _parse_kernel_prefix(cls, line: str, source: str) -> Optional[KernelEvent]:
        """
        Parse kernel prefix format: <level>subsystem: message
        
        This format is used when no timestamp is available.
        """
        match = cls.KERNEL_PREFIX.match(line)
        if not match:
            return None
        
        level_str, subsystem, message = match.groups()
        
        try:
            level = int(level_str)
            severity = cls.SEVERITY_LEVELS.get(level, 'UNKNOWN')
        except (ValueError, TypeError):
            severity = 'UNKNOWN'

        return KernelEvent(
            timestamp_monotonic=None,
            timestamp_realtime=datetime.now(),
            severity=cls._normalize_severity(severity),
            subsystem=subsystem or 'KERNEL',
            message=(message or '').strip(),
            raw=line,
            source=source,
            pid=None,
            annotations={},
            cpu=None,
        )

    @classmethod
    def _parse_timestamp(cls, ts_str: Optional[str]) -> Optional[float]:
        """
        Parse monotonic timestamp string to float.
        
        Args:
            ts_str: Timestamp string (e.g., "123.456789")
        
        Returns:
            Float timestamp or None if parsing fails
        """
        if not ts_str:
            return None
        
        try:
            return float(ts_str.strip())
        except (ValueError, AttributeError):
            return None

    @classmethod
    def _normalize_severity(cls, severity_str: str) -> str:
        """
        Normalize severity string to standard kernel severity levels.
        
        Maps common variations (ERROR -> ERR, WARNING -> WARN, etc.)
        """
        if not severity_str:
            return 'INFO'
        
        normalized = severity_str.upper().strip()
        
        # Check if already in standard format
        if normalized in cls.SEVERITY_TO_LEVEL:
            return normalized
        
        # Map common severity variations
        severity_mapping = {
            'ERROR': 'ERR',
            'WARNING': 'WARN',
            'NOTE': 'NOTICE',
            'INFORMATION': 'INFO',
            'CRITICAL': 'CRIT',
            'EMERGENCY': 'EMERG',
        }
        
        return severity_mapping.get(normalized, normalized)

    @classmethod
    def _infer_severity(cls, message: str) -> str:
        """
        Infer severity level from message content using keyword matching.
        
        Priority order (highest to lowest):
        EMERG -> ALERT -> ERR -> WARN -> NOTICE -> DEBUG -> INFO
        """
        if not message:
            return 'INFO'
        
        message_lower = message.lower()
        
        # Check for emergency/panic conditions
        if any(keyword in message_lower for keyword in 
               ['panic', 'oops', 'fatal', 'emergency', 'crash', 'bug:']):
            return 'EMERG'
        
        # Check for alert conditions
        if any(keyword in message_lower for keyword in 
               ['alert', 'failure', 'critical', 'corruption']):
            return 'ALERT'
        
        # Check for errors
        if any(keyword in message_lower for keyword in 
               ['error', 'err', 'failed', 'segfault', 'fault', 
                'invalid', 'unable', 'cannot', 'timeout']):
            return 'ERR'
        
        # Check for warnings
        if any(keyword in message_lower for keyword in 
               ['warning', 'warn', 'deprecated', 'attention']):
            return 'WARN'
        
        # Check for notices
        if any(keyword in message_lower for keyword in 
               ['notice', 'note', 'fyi']):
            return 'NOTICE'
        
        # Check for debug messages
        if any(keyword in message_lower for keyword in 
               ['debug', 'trace', 'verbose', 'dump']):
            return 'DEBUG'
        
        # Default to INFO
        return 'INFO'

    @classmethod
    def _is_continuation_line(cls, message: str) -> bool:
        """
        Detect if this is a continuation line (stack trace, hex dump, etc.)
        
        Returns True for:
        - Lines starting with continuation markers (Code:, Call Trace, etc.)
        - Lines with hex dump patterns (pairs of hex bytes)
        - Indented lines (tabs or multiple spaces)
        """
        if not message:
            return False
        
        # Check for known continuation markers
        if any(message.startswith(marker) for marker in cls.CONTINUATION_MARKERS):
            return True

        # Check for hex dump pattern: "XX XX XX XX..." (6+ pairs)
        if re.match(r'^(?:[0-9A-Fa-f]{2}\s+){6,}', message):
            return True

        # Check for indentation (tabs or 2+ leading spaces)
        if re.match(r'^[\t ]{2,}', message):
            return True

        return False

    @classmethod
    def _extract_cpu(cls, message: str) -> Optional[int]:
        """
        Extract CPU number from message if present.
        
        Handles formats like:
        - "on CPU 3"
        - "CPU: 2"
        - "CPU#4"
        """
        if not message:
            return None
        
        for pattern in cls.CPU_PATTERNS:
            match = pattern.search(message)
            if match:
                try:
                    return int(match.group('cpu'))
                except (ValueError, TypeError, AttributeError):
                    continue
        
        return None


# Module-level convenience function
def parse_line(line: str, source: str = 'dmesg') -> Optional[KernelEvent]:
    """
    Convenience function to parse a kernel log line.
    
    Args:
        line: Kernel log line to parse
        source: Source identifier
    
    Returns:
        KernelEvent or None
    """
    return KernelLogParser.parse_dmesg_line(line, source)