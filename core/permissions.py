"""
Permission and capability checks for kernel log access.
"""

import os
import subprocess
import logging
from typing import Tuple


logger = logging.getLogger(__name__)


class PermissionChecker:
    """Check system permissions for kernel log access."""
    
    @staticmethod
    def can_read_dmesg() -> bool:
        """Check if we can read from dmesg."""
        try:
            result = subprocess.run(
                ['dmesg'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"dmesg check failed: {e}")
            return False
    
    @staticmethod
    def can_watch_dmesg() -> bool:
        """Check if we can use dmesg -w (live stream)."""
        try:
            # Try dmesg -w briefly
            result = subprocess.run(
                ['dmesg', '-w'],
                capture_output=True,
                timeout=0.5
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            # If it times out, it's probably working (waiting for logs)
            return True
        except Exception as e:
            logger.debug(f"dmesg -w check failed: {e}")
            return False
    
    @staticmethod
    def can_use_journalctl() -> bool:
        """Check if we can read kernel logs via journalctl."""
        try:
            result = subprocess.run(
                ['journalctl', '-k', '-n', '1'],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"journalctl check failed: {e}")
            return False
    
    @staticmethod
    def get_available_sources() -> list[str]:
        """Get list of available log sources."""
        sources = []
        if PermissionChecker.can_read_dmesg():
            sources.append('dmesg')
        if PermissionChecker.can_use_journalctl():
            sources.append('journal')
        return sources
